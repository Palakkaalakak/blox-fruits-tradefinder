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
    "africa":        (-155.1, 27.0, 8.8),      # kept; 148px clear of the polar continent already
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


def rearrange(z, sink="europe", ocean_floor=-4200.0, seed=0, verbose=True):
    """Cut the continents out of Earth and set them down somewhere else."""
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
            patch = G.tectonic_warp(patch, rng, amplitude=w * 0.05,
                                     base_scale=w * 0.22)
            patch = G.tectonic_warp(patch, rng, amplitude=w * 0.035,
                                     base_scale=w * 0.08)

        moved = G.spherical_rotate(patch, *PLACEMENT[name])
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
