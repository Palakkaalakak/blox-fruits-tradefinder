#!/usr/bin/env python3
"""
Moving the continents.

Warping Earth is not enough to disguise it. A smooth global warp bends
coastlines but preserves the ARRANGEMENT: North America stays north-west of
South America, Africa stays south of Europe, and the map still reads as Earth
however much the outlines wobble. Every earlier attempt failed for this
reason.

So the continents are cut out and moved independently. Each is lifted off the
globe, rotated to a new position and orientation, and set down again. Its own
internal terrain travels with it, so its mountain ranges, river valleys and
continental shelf are still Earth's, but the world they compose is new.

This is the right level of resemblance for the setting. A continent studied
closely still carries Earth's geology. The globe as a whole does not read as
Earth at all.

One continent is not replaced. It is the landmass the Doom drowned and never
gave back, and it is simply absent from the new world.
"""

import numpy as np
from scipy import ndimage
import generate_world as G

# Real Earth continents as (lat_min, lat_max, lon_min, lon_max)
CONTINENTS = {
    "north_america": (7.0, 84.0, -172.0, -52.0),
    "south_america": (-57.0, 13.0, -82.0, -33.0),
    "europe":        (35.0, 72.0, -12.0, 60.0),
    "asia":          (2.0, 78.0, 60.0, 180.0),
    "africa":        (-36.0, 38.0, -18.0, 52.0),
    "oceania":       (-48.0, 0.0, 112.0, 180.0),
    "antarctica":    (-90.0, -62.0, -180.0, 180.0),
}

# Where each continent is set down, as Euler angles. Chosen so that the new
# arrangement bears no relation to the old one.
# Found by searching random arrangements and scoring for the number of
# separate continents, their balance, and how little land is lost. This one
# gives six distinct continents with the largest holding a third of the land.
PLACEMENT = {
    "north_america": (-6.8, -15.5, -45.5),
    "south_america": (-30.2, -7.7, 33.8),
    "europe":        (25.0, 10.0, 15.0),   # unused: europe is the sunk one
    "asia":          (-108.9, -66.0, 60.1),  # nudged south of the previous spot
    # Earlier angles brought part of Africa close to the new pole - a patch
    # that crosses near a pole gets split across the left/right edges of an
    # equirectangular map, and the piece that reappeared on the far side
    # was landing directly on the polar continent's territory. A second
    # attempt avoided that but landed the whole continent on top of Asia
    # instead. Found by search, scored against every other continent's
    # final position: this orientation touches neither.
    "africa":        (-131.0, -39.7, 64.6),
    "oceania":       (171.0, -37.2, 69.8),
    "antarctica":    (0.0, 0.0, 0.0),      # stays polar; it is the ice cap
}


def _box_mask(h, w, bounds, rng=None, jitter=6.0):
    """A lat/lon box with a ragged edge.

    A clean box leaves straight-line coastlines wherever it slices through a
    continent - Eurasia cut at longitude 60, for instance. Perturbing the
    boundary with smooth noise makes those cuts look like coastline rather
    than like a crop.
    """
    lat = np.linspace(90, -90, h)[:, None]
    lon = np.linspace(-180, 180, w, endpoint=False)[None, :]
    la0, la1, lo0, lo1 = bounds

    if rng is not None:
        n1 = G.smooth_noise((h, w), w * 0.012, rng) * jitter
        n2 = G.smooth_noise((h, w), w * 0.012, rng) * jitter
        lat = lat + n1
        lon = lon + n2

    return (lat >= la0) & (lat <= la1) & (lon >= lo0) & (lon <= lo1)


def _drop_edge_filaments(moved, ocean_floor=-4200.0, margin_frac=0.03):
    """Remove any land within a margin of the map's left/right edge, then
    drop whatever that disconnects from the main body.

    Every continent's placement was chosen to sit away from the antimeridian
    seam, so land reaching the edge is never real coastline - it is a thin
    filament introduced by the box mask jitter or the rotation. Because the
    map wraps horizontally, two such filaments on unrelated continents can
    appear to connect into one long land bridge across the open ocean. A
    thin filament is still attached to its parent body (this is not a
    separate island), so clipping the edge and re-checking connectivity is
    what actually separates it, rather than just looking for components
    that already touch the edge in isolation.
    """
    h, w = moved.shape
    margin = max(int(w * margin_frac), 1)
    out = moved.copy()
    out[:, :margin] = ocean_floor
    out[:, -margin:] = ocean_floor

    land = out >= 0
    lab, n = ndimage.label(land, structure=np.ones((3, 3)))
    if n == 0:
        return out
    sizes = np.bincount(lab.ravel())
    main = np.argmax(sizes[1:]) + 1
    out[(lab != main) & (lab != 0)] = ocean_floor
    return out


def bend_hunchback(moved, pivot_frac=0.42, max_shift_frac=0.42, power=2.0):
    """Curve a continent's northward point over to the right, like a
    hunchback's shoulder. Works in final map space: finds the landmass's own
    bounding box, then shifts each row rightward by an amount that grows
    toward the north (small y), tapering to nothing at and below the pivot
    row, so only the point itself bends and the rest of the body stays put.
    """
    land = moved >= 0
    ys, xs = np.where(land)
    if len(ys) == 0:
        return moved
    y0, y1 = ys.min(), ys.max()
    x0, x1 = xs.min(), xs.max()
    pivot = y0 + (y1 - y0) * pivot_frac
    max_shift = (x1 - x0) * max_shift_frac
    h, w = moved.shape
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    t = np.clip((pivot - yy) / max(pivot - y0, 1e-6), 0.0, 1.0)
    shift = max_shift * (t ** power)
    return G.sample(moved, yy, xx - shift)


def rearrange(z, sink="europe", ocean_floor=-4200.0, seed=0, verbose=True,
              africa_mode="bend"):
    """Cut the continents out of Earth and set them down somewhere else.

    africa_mode: "bend" curves Africa's northward point over to the right;
    "sunder" cuts Africa itself into two separate landmasses, the way the
    Almani Corridor split one continent into Lidia and Réselia; "none"
    leaves it as placed.
    """
    h, w = z.shape
    rng = np.random.default_rng(seed)
    out = np.full((h, w), ocean_floor, dtype=np.float32)

    for name, bounds in CONTINENTS.items():
        if name == sink:
            if verbose:
                print(f"    {name}: SUNK — this is the drowned continent")
            continue

        mask = _box_mask(h, w, bounds, rng) & (z > -250.0)   # land and shelf
        if not mask.any():
            continue

        # Isolate the continent, with deep water everywhere else, so that
        # rotating it does not smear its neighbours across the globe.
        patch = np.where(mask, z, ocean_floor).astype(np.float32)

        if name == "africa":
            # Distorted harder than the rest: still readable as Africa even
            # after one warp pass, including when the map is recentred so
            # the piece isn't split across the seam. Two passes at different
            # scales - one large-scale to break the silhouette, one finer to
            # break the coastline detail - so it stops reading as a rotated
            # crop of the real continent.
            patch = G.tectonic_warp(patch, rng, amplitude=w * 0.022,
                                     base_scale=w * 0.22)
            patch = G.tectonic_warp(patch, rng, amplitude=w * 0.016,
                                     base_scale=w * 0.08)

        moved = G.spherical_rotate(patch, *PLACEMENT[name])
        if name != "antarctica":
            # Antarctica alone is meant to touch both edges - it keeps its
            # real, unrotated position and legitimately wraps around every
            # longitude at the pole.
            moved = _drop_edge_filaments(moved, ocean_floor)

        if name == "africa":
            if africa_mode == "bend":
                # The point that used to run north now curves over to the
                # right, like a hunchback's shoulder, instead of standing
                # straight up.
                moved = bend_hunchback(moved)
            elif africa_mode == "sunder":
                # Cut clean through, the same way the Almani Corridor
                # split one landmass into Lidia and Réselia - the two
                # halves splay apart from a single near-touching point.
                moved, _ = G.sunder_pair(moved, rng, rank=0,
                                         width_px=w * 0.006, taper=0.7)

        out = np.maximum(out, moved)

        if verbose:
            print(f"    {name}: moved to {PLACEMENT[name]}")

    return out


def blend_seafloor(z, earth, ocean_floor=-4200.0):
    """Give the new oceans a plausible floor.

    Without this the continents sit on a flat abyssal plain. Real seafloor has
    ridges, rises and fracture zones, so Earth's own bathymetry is reused as
    texture underneath, rotated so that it does not reproduce the Atlantic
    ridge in a recognisable place.
    """
    bath = np.where(earth < 0, earth, ocean_floor)
    bath = G.spherical_rotate(bath, 73.0, 41.0, -22.0)
    bath = ndimage.gaussian_filter(bath, 9.0, mode=("nearest", "wrap"))
    # Flatten the texture toward the ocean floor rather than reusing Earth's
    # ridges at full strength - real bathymetry variation read as visible
    # cracking in open water once the map was viewed at world scale.
    bath = ocean_floor + 0.35 * (bath - ocean_floor)
    deep = z <= ocean_floor + 1.0
    out = z.copy()
    out[deep] = bath[deep]
    return out
