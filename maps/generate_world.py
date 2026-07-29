#!/usr/bin/env python3
"""
JR — world generation from real Earth topography.

Takes ETOPO1 (real Earth elevation + bathymetry) and applies the Doom:

  1. IMPACT      an oceanic strike: crater, ejecta ring, radial fracturing
  2. WARP        large-scale tectonic deformation ("baked" for the look of deep
                 time, though no such time passed in-story) via multi-octave
                 domain warping, which rearranges landmasses while preserving
                 the fractal character of real coastlines
  3. RIFT        fracture zones that split continents and spawn archipelagos
  4. DROWNING    sea-level redistribution: shelves drown, basins rise
  5. EROSION     fractal detail + smoothing so coastlines read as ancient

Output: an equirectangular heightmap PNG (importable into Azgaar's Fantasy Map
Generator) and a shaded colour render for eyeballing.

Usage:  python3 generate_world.py --seed 7 --land-fraction 0.30
"""

import argparse
import numpy as np
from scipy.io import netcdf_file
from scipy import ndimage
from PIL import Image

ETOPO = "/tmp/etopo.grd"
W, H = 2880, 1440          # working resolution (equirectangular, 2:1)


def set_resolution(w):
    global W, H
    W, H = w, w // 2


# ---------------------------------------------------------------- utilities

def smooth_noise(shape, scale, rng):
    """Band-limited noise, wrapping in longitude."""
    n = rng.standard_normal(shape)
    n = ndimage.gaussian_filter(n, sigma=scale, mode=("nearest", "wrap"))
    s = n.std()
    return n / s if s > 0 else n


def fbm(shape, rng, octaves=6, base=120.0, gain=0.5):
    """Fractal Brownian motion: sum of noise octaves. Gives coastlines their
    self-similar crinkle at every zoom level."""
    out = np.zeros(shape)
    amp, scale = 1.0, base
    for _ in range(octaves):
        out += amp * smooth_noise(shape, scale, rng)
        amp *= gain
        scale = max(1.0, scale * 0.5)
    return out / np.abs(out).std()


def latitude_weight(h, w, power=1.0):
    """Equirectangular distortion compensation: displacement near the poles
    covers far less ground than at the equator."""
    lat = np.linspace(np.pi / 2, -np.pi / 2, h)[:, None]
    return np.repeat(np.cos(lat) ** power, w, axis=1)


def sample(field, yy, xx):
    """Bilinear sample with longitude wrap and latitude clamp."""
    h, w = field.shape
    xx = np.mod(xx, w)
    yy = np.clip(yy, 0, h - 1.001)
    return ndimage.map_coordinates(field, [yy, xx], order=1, mode="grid-wrap")


# ---------------------------------------------------------------- the Doom

def load_earth():
    f = netcdf_file(ETOPO, "r", mmap=True)
    z = np.array(f.variables["z"][:], dtype=np.float32)
    z = np.flipud(z)                                   # north-up
    zoom = (H / z.shape[0], W / z.shape[1])
    z = ndimage.zoom(z, zoom, order=1)
    return z.astype(np.float32)


def spherical_rotate(z, alpha, beta, gamma):
    """Rotate the whole globe about an arbitrary axis.

    Unlike a longitudinal roll, this genuinely moves land between the tropics
    and the poles: a continent that sat on the equator can end up under ice.
    Every output pixel is converted to a unit vector, rotated, and read back
    from the source — so the poles behave correctly instead of smearing.

    In-world this is the pole shift: the Doom left the axis in a new place,
    and north is not where it was.
    """
    h, w = z.shape
    lat = np.linspace(np.pi / 2, -np.pi / 2, h)[:, None]
    lon = np.linspace(-np.pi, np.pi, w, endpoint=False)[None, :]

    cl = np.cos(lat)
    v = np.stack([
        np.broadcast_to(cl * np.cos(lon), (h, w)),
        np.broadcast_to(cl * np.sin(lon), (h, w)),
        np.broadcast_to(np.broadcast_to(np.sin(lat), (h, 1)), (h, w)),
    ])

    a, b, g = np.radians([alpha, beta, gamma])
    Rz = np.array([[np.cos(a), -np.sin(a), 0], [np.sin(a), np.cos(a), 0], [0, 0, 1]])
    Ry = np.array([[np.cos(b), 0, np.sin(b)], [0, 1, 0], [-np.sin(b), 0, np.cos(b)]])
    Rx = np.array([[1, 0, 0], [0, np.cos(g), -np.sin(g)], [0, np.sin(g), np.cos(g)]])
    R = Rz @ Ry @ Rx

    vr = np.tensordot(R, v, axes=(1, 0))
    lat2 = np.arcsin(np.clip(vr[2], -1, 1))
    lon2 = np.arctan2(vr[1], vr[0])

    yy = (np.pi / 2 - lat2) / np.pi * (h - 1)
    xx = (lon2 + np.pi) / (2 * np.pi) * w
    return sample(z, yy, xx)


def hotspot_chains(z, rng, n_chains, length, strength):
    """Volcanic island chains, Hawaii-style: a plate creeping over a fixed
    mantle plume leaves a line of islands, oldest and lowest at one end."""
    h, w = z.shape
    out = z.copy()
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    latw = latitude_weight(h, w)

    for _ in range(n_chains):
        y0 = rng.uniform(h * 0.15, h * 0.85)
        x0 = rng.uniform(0, w)
        ang = rng.uniform(0, 2 * np.pi)
        n_isl = rng.integers(5, 13)
        for i in range(n_isl):
            t = i / max(n_isl - 1, 1)
            cy = y0 + np.sin(ang) * length * t
            cx = x0 + np.cos(ang) * length * t
            if not (0 < cy < h):
                break
            r = rng.uniform(3, 9) * (1.0 - 0.5 * t)
            dx = (np.mod(xx - cx + w / 2, w) - w / 2) * latw
            d2 = dx ** 2 + (yy - cy) ** 2
            out += strength * (1.0 - 0.55 * t) * np.exp(-d2 / (2 * r ** 2))
    return out


def orogeny(z, rng, field, strength):
    """Mountain belts where platforms collide. Real ranges sit along plate
    margins, not scattered at random — so uplift follows the steepest
    gradients of the platform field, giving coastal cordilleras and interior
    spines rather than noise."""
    gy, gx = np.gradient(ndimage.gaussian_filter(field, 6, mode=("nearest", "wrap")))
    belt = np.sqrt(gx ** 2 + gy ** 2)
    belt /= belt.max() or 1
    belt = belt ** 1.6
    ridged = 1.0 - np.abs(fbm(z.shape, rng, octaves=4, base=30))
    return z + strength * belt * (0.55 + 0.45 * np.clip(ridged, 0, 1))


def impact(z, rng, lat_deg, lon_deg, radius_px, depth):
    """Oceanic strike. Excavates a crater, throws up a ring, and radiates
    fracture lines that later become rifts and island arcs."""
    h, w = z.shape
    cy = int((90 - lat_deg) / 180 * h)
    cx = int((lon_deg + 180) / 360 * w)

    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    dx = np.mod(xx - cx + w / 2, w) - w / 2
    dx *= latitude_weight(h, w)                        # true ground distance
    dy = yy - cy
    d = np.sqrt(dx ** 2 + dy ** 2)

    bowl = -depth * np.exp(-(d / radius_px) ** 2)
    ring = 0.45 * depth * np.exp(-((d - radius_px * 1.5) / (radius_px * 0.55)) ** 2)

    theta = np.arctan2(dy, dx)
    spokes = np.sin(theta * 5 + 2.0 * fbm((h, w), rng, octaves=3, base=90))
    fracture = 0.30 * depth * spokes * np.exp(-(d / (radius_px * 4.5)) ** 2)

    return z + bowl + ring + fracture


def tectonic_warp(z, rng, amplitude, base_scale):
    """Multi-octave domain warping. This is what rearranges the continents:
    every point is displaced by a smooth vector field, so landmasses stretch,
    rotate, tear and collide while keeping believable coastal geometry."""
    h, w = z.shape
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    latw = latitude_weight(h, w)

    for octave, (scale, amp) in enumerate([
        (base_scale, amplitude),
        (base_scale * 0.45, amplitude * 0.55),
        (base_scale * 0.20, amplitude * 0.28),
    ]):
        vx = smooth_noise((h, w), scale, rng) * amp
        vy = smooth_noise((h, w), scale, rng) * amp * 0.65
        xx = xx + vx / np.maximum(latw, 0.25)
        yy = yy + vy
    return sample(z, yy, xx)


def continental_platforms(z, rng, strength, scale, separation=1.0):
    """Broad isostatic reorganisation: a few regions ride high as continental
    platforms, everything else founders into deep ocean basins.

    `separation` controls how decisively the two are split. High values give
    compact continents divided by wide, deep oceans — which is what makes
    crossing them an age of exploration rather than an afternoon."""
    field = smooth_noise(z.shape, scale, rng)

    # Bias downward so only the highest regions become platforms, then split
    # hard into plateau / basin. The offset sets how much of the globe qualifies.
    field = np.tanh((field - 0.45 * separation) * (1.4 + 1.6 * separation))

    # Push the basins down harder than the platforms up: oceans get deep and
    # wide while continents stay compact.
    up = np.clip(field, 0, None)
    down = np.clip(field, None, 0)
    return z + strength * (up + down * (0.6 + 0.9 * separation)), field


def fracture(z, rng, n_cuts, width, depth):
    """Break continents into subcontinents with WIDE seaways.

    The distinction that matters: thin cuts give a stringy, lacy coastline —
    Indonesia. Wide cuts give chunky landmasses separated by real seas, with
    solid interiors — Europe, or Westeros and Essos. So these troughs are
    broad and smooth, and they follow meandering paths rather than straight
    lines, producing gulfs, inland seas and short crossings between
    neighbours who are properly separated but not isolated.
    """
    h, w = z.shape
    out = z.copy()
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    latw = latitude_weight(h, w)

    for _ in range(n_cuts):
        # A meandering path across the map
        y0 = rng.uniform(h * 0.12, h * 0.88)
        x0 = rng.uniform(0, w)
        ang = rng.uniform(0, 2 * np.pi)
        wobble = rng.uniform(-0.5, 0.5)
        length = rng.uniform(w * 0.18, w * 0.42)
        wid = width * rng.uniform(0.7, 1.5)

        acc = np.full((h, w), 1e9, dtype=np.float32)
        steps = 26
        for i in range(steps):
            t = i / (steps - 1)
            a = ang + wobble * np.sin(t * 2.6)
            cy = y0 + np.sin(a) * length * t
            cx = x0 + np.cos(a) * length * t
            if not (-h * 0.1 < cy < h * 1.1):
                break
            dx = (np.mod(xx - cx + w / 2, w) - w / 2) * latw
            acc = np.minimum(acc, np.sqrt(dx ** 2 + (yy - cy) ** 2))

        out -= depth * np.exp(-(acc / wid) ** 2)
    return out


def fracture_network(z, rng, scales=3, base_scale=None, depth=5200,
                     density=1.0, sharpness=7.0, land_only=True, cells=140):
    """The Drowned Fractures — the world's most distinctive feature.

    When the crust gave way, it did not open a few great rifts. It *crazed*,
    like glass, and then the sea came into every crack. What is left is a
    branching network of narrow saltwater channels running through the
    continents — they look like river systems and behave like nothing of the
    sort. They have no source and no mouth. They do not flow. They are the
    ocean, reaching inland through a shattered land.

    Built from ridged noise at several scales: broad channels at the coarsest
    scale, ever-finer tributaries below it, so the network has the branching
    hierarchy of drainage without any of its logic. Narrow, because these are
    fractures, not straits.
    """
    h, w = z.shape

    # STRAIGHT cracks, not meandering ones.
    #
    # Brittle material does not craze in curves. Glass, dried mud and rock
    # break along straight segments that meet at angular junctions, enclosing
    # polygonal fragments. That is a Voronoi diagram, not a noise field — and
    # using ridged noise here was simply the wrong model, which is why no
    # amount of tuning ever made it look fractured.
    #
    # A pixel lies on a crack when it is nearly equidistant from its two
    # nearest fracture nuclei: those loci are exactly the straight cell walls.
    from scipy.spatial import cKDTree

    crack = np.zeros((h, w), dtype=np.float32)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    pts_grid = np.column_stack([yy.ravel(), xx.ravel()])

    n_cells = max(int(cells), 8)
    for i in range(scales):
        k = int(n_cells * (2.6 ** i))
        py = rng.uniform(0, h, k)
        px = rng.uniform(0, w, k)
        # Wrap in longitude so cracks cross the seam cleanly
        seeds = np.column_stack([
            np.concatenate([py, py, py]),
            np.concatenate([px - w, px, px + w]),
        ])
        d, _ = cKDTree(seeds).query(pts_grid, k=2, workers=-1)
        gap = (d[:, 1] - d[:, 0]).reshape(h, w)

        # Width of the wall, in pixels, shrinking with each finer generation
        width = max(w * 0.0016 * (0.72 ** i), 0.9)
        wall = np.clip(1.0 - gap / (2.0 * width), 0.0, 1.0)
        crack = np.maximum(crack, wall * (0.88 ** i))

    # CUT, don't subtract.
    #
    # Subtracting depth only breaks the surface where land is already low,
    # which is why an earlier version merely nibbled the coasts and left every
    # interior solid. A fracture does not care how high the ground above it
    # was: the crust parted, and the sea came in. So the channel is forced
    # below sea level wherever the crack is strong enough, through highlands
    # and lowlands alike.
    m = np.clip((crack - (1.0 - 0.55 * np.clip(density, 0, 3))) / 0.35, 0.0, 1.0)
    m = np.clip(m, 0.0, 1.0)
    m = m * m * (3 - 2 * m)                      # smoothstep for clean walls

    if land_only:
        # The crust cracked; the seafloor is not our concern. Confine the
        # network to land (feathered slightly so channels reach the coast
        # and open into the sea rather than stopping short of it).
        near_land = ndimage.gaussian_filter((z >= 0).astype(np.float32), 2.0,
                                            mode=("nearest", "wrap"))
        m *= np.clip(near_land * 1.6, 0.0, 1.0)

    floor = -abs(depth) * (0.35 + 0.65 * m)
    return z * (1.0 - m) + floor * m


def inland_seas(z, rng, n, radius, depth):
    """Broad depressions in continental interiors: epicontinental seas and
    great lakes. Gives interiors coastline without breaking them apart."""
    h, w = z.shape
    out = z.copy()
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    latw = latitude_weight(h, w)
    for _ in range(n):
        cy = rng.uniform(h * 0.18, h * 0.82)
        cx = rng.uniform(0, w)
        r = radius * rng.uniform(0.6, 1.6)
        dx = (np.mod(xx - cx + w / 2, w) - w / 2) * latw
        d2 = dx ** 2 + (yy - cy) ** 2
        blob = np.exp(-d2 / (2 * r ** 2))
        blob *= (0.7 + 0.6 * fbm((h, w), rng, octaves=3, base=40))
        out -= depth * blob
    return out


def sunder_pair(z, rng, rank=0, width_px=6.0, taper=0.55):
    """The Sundering of a single continent into two.

    Cuts a channel through one landmass so that it becomes two continents
    that are unmistakably *former neighbours* — close enough to touch at one
    point, far enough apart elsewhere to have become separate worlds.

    This is Lidia and Réselia, and the cut is the Almani Corridor: not an
    ocean between strangers but a drowned rift through what used to be one
    country. It is why the two continents lie diagonal and offset, meeting
    nowhere else; why their peoples are more closely related than either
    admits; and why whoever holds the strait holds the world's throat.

    The channel widens along its length (`taper`), so the two halves splay
    apart — near-touching at the Corridor, far apart at the far end.
    """
    h, w = z.shape
    land = z >= 0
    lab, n = ndimage.label(land, structure=np.ones((3, 3)))
    if n == 0:
        return z, None
    sizes = np.bincount(lab.ravel())[1:]
    target = np.argsort(sizes)[::-1][min(rank, n - 1)] + 1
    mask = lab == target

    ys, xs = np.nonzero(mask)
    cy, cx = ys.mean(), xs.mean()
    ang = rng.uniform(0, np.pi)

    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    latw = latitude_weight(h, w)
    dx = (np.mod(xx - cx + w / 2, w) - w / 2) * latw
    dy = yy - cy

    # Signed distance from the cut line, and position along it
    perp = dx * np.sin(ang) - dy * np.cos(ang)
    along = dx * np.cos(ang) + dy * np.sin(ang)

    span = max(np.ptp(ys), np.ptp(xs)) / 2 + 1e-6
    t = np.clip((along + span) / (2 * span), 0, 1)      # 0..1 across the mass
    wobble = width_px * 0.9 * np.sin(t * 5.0 + rng.uniform(0, 6.283))
    local_w = width_px * (1.0 + taper * 2.2 * t) + wobble

    channel = np.exp(-(perp / np.maximum(local_w, 1.0)) ** 2)
    z = z.copy()
    z[mask] -= 6000.0 * channel[mask]
    return z, (cy / h, cx / w)


def despeckle(z, min_fraction=0.000012):
    """Delete the confetti.

    Hundreds of one-pixel islands read as noise, not archipelago, and they are
    what makes a map look procedurally generated. Anything below the threshold
    is sunk. Real island chains built by hotspots and rifting survive because
    they are larger than this."""
    land = z >= 0
    lab, n = ndimage.label(land, structure=np.ones((3, 3)))
    if n == 0:
        return z
    sizes = np.bincount(lab.ravel())
    min_px = max(int(min_fraction * land.size), 6)
    doomed = np.isin(lab, np.where(sizes < min_px)[0]) & land
    z = z.copy()
    z[doomed] = -60.0
    return z


def drown_a_continent(z, rank=1, margin=180.0):
    """The lost continent.

    This world is Earth, and the Doom drowned land. It follows necessarily
    that some of Earth's original landmass never came back up. One continental
    platform is sunk just beneath the waves — shallow enough to be a plateau
    on any depth chart, deep enough that nobody has stood on it in 1,500 years.

    `rank` selects which landmass to sink (0 = largest; 1 = second largest).
    """
    land = z >= 0
    lab, n = ndimage.label(land, structure=np.ones((3, 3)))
    if n == 0:
        return z, None
    sizes = np.bincount(lab.ravel())[1:]
    order = np.argsort(sizes)[::-1]
    target = order[min(rank, len(order) - 1)] + 1
    mask = lab == target

    # Sink it so its highest ground sits just below the surface.
    z = z.copy()
    z[mask] -= (z[mask].max() + margin)
    return z, mask.sum() / land.sum()


def rifting(z, rng, strength, n_rifts=7):
    """Long fracture zones. Where they cross continents they open seas and
    straits; where they cross shelf they leave island chains behind."""
    h, w = z.shape
    out = z.copy()
    for _ in range(n_rifts):
        band = smooth_noise((h, w), rng.uniform(25, 70), rng)
        ridge = 1.0 - np.abs(band) / (np.abs(band).std() * 1.2)
        ridge = np.clip(ridge, 0, 1) ** 3
        if rng.random() < 0.55:
            out -= strength * ridge                    # rift valley / new sea
        else:
            out += strength * 0.8 * ridge              # island arc / range
    return out


def erode(z, rng, detail=0.10, smooth=2.0):
    """Age the surface: soften large forms, then add a little fractal texture
    so coasts crinkle at every scale. Detail is kept low deliberately — too
    much and continents dissolve into noise islands."""
    z = ndimage.gaussian_filter(z, sigma=smooth, mode=("nearest", "wrap"))
    relief = np.abs(z).std()
    z = z + detail * relief * fbm(z.shape, rng, octaves=4, base=45)
    return z


def set_sea_level(z, land_fraction):
    """The Drowning. Choose the level that yields the desired land fraction,
    weighting by true surface area."""
    wts = latitude_weight(*z.shape).ravel()
    vals = z.ravel()
    order = np.argsort(vals)
    cw = np.cumsum(wts[order])
    cw /= cw[-1]
    idx = np.searchsorted(cw, 1.0 - land_fraction)
    return z - vals[order][min(idx, len(vals) - 1)]


# ---------------------------------------------------------------- rendering

def render_colour(z):
    h, w = z.shape
    img = np.zeros((h, w, 3), dtype=np.uint8)
    sea, land = z < 0, z >= 0

    if sea.any():
        d = z[sea] / (z[sea].min() or -1)
        img[sea] = np.stack([
            (12 + 40 * (1 - d)), (35 + 85 * (1 - d)), (75 + 110 * (1 - d))
        ], axis=-1).astype(np.uint8)

    if land.any():
        e = z[land] / (z[land].max() or 1)
        ramp = np.array([
            [ 96, 132,  86], [122, 150,  92], [160, 166,  98],
            [168, 142,  96], [150, 120,  96], [205, 205, 208],
        ], dtype=float)
        pos = np.clip(e * (len(ramp) - 1), 0, len(ramp) - 1.001)
        lo = pos.astype(int)
        t = (pos - lo)[:, None]
        img[land] = (ramp[lo] * (1 - t) + ramp[lo + 1] * t).astype(np.uint8)

    # hillshade
    gy, gx = np.gradient(ndimage.gaussian_filter(z, 1.0))
    shade = np.clip(0.5 + (gx * 0.9 - gy * 0.9) / (np.abs(z).std() + 1e-6) * 0.35,
                    0.55, 1.45)
    img = np.clip(img * shade[..., None], 0, 255).astype(np.uint8)

    return Image.fromarray(img)


def render_heightmap(z):
    """8-bit greyscale for Azgaar import: sea level lands at 127."""
    out = np.zeros_like(z)
    sea, land = z < 0, z >= 0
    if sea.any():
        out[sea] = 127 * (1 - z[sea] / (z[sea].min() or -1))
    if land.any():
        out[land] = 128 + 127 * (z[land] / (z[land].max() or 1)) ** 0.65
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), mode="L")


# ---------------------------------------------------------------- main

def build(seed, land_fraction, warp, rift, impact_lat, impact_lon,
          platform=2600.0, platform_scale=0.075, separation=1.0,
          lost_continent=True, lost_rank=1, rotation=(121.0, 47.0, 29.0),
          hotspots=6, mountains=1.0, fractures=7, fracture_width=0.020,
          seas=4, sunder=False, sunder_width=0.0045,
          crazing=1.0, crazing_scales=3, crazing_sharp=14.0,
          crazing_cells=140):
    rng = np.random.default_rng(seed)
    z = load_earth()

    # --- the pole shift -------------------------------------------------
    # A true rotation of the sphere about an arbitrary axis. Land moves
    # between the tropics and the poles; north is no longer where it was.
    z = spherical_rotate(z, *rotation)

    z = impact(z, rng, impact_lat, impact_lon, radius_px=W * 0.035, depth=4200)
    z = tectonic_warp(z, rng, amplitude=W * warp, base_scale=W * 0.060)
    z, field = continental_platforms(z, rng, platform, W * platform_scale,
                                     separation)
    z = orogeny(z, rng, field, strength=2100 * mountains)
    z = rifting(z, rng, strength=2400 * rift, n_rifts=4)
    if fractures:
        z = fracture(z, rng, n_cuts=fractures, width=W * fracture_width,
                     depth=5200)
    if seas:
        z = inland_seas(z, rng, n=seas, radius=W * 0.022, depth=3400)
    if hotspots:
        z = hotspot_chains(z, rng, n_chains=hotspots, length=W * 0.055,
                           strength=2500)
    z = erode(z, rng)

    lost = None
    if lost_continent:
        # Sink one platform before the final sea level is fixed, then re-level
        # so the intended land fraction still holds.
        z = set_sea_level(z, land_fraction)
        z, lost = drown_a_continent(z, rank=lost_rank)
        z = set_sea_level(z, land_fraction)
    else:
        z = set_sea_level(z, land_fraction)
    # Crazing must come AFTER the datum is fixed: the fractures are cut to an
    # absolute depth below sea level, so if the sea level is recomputed
    # afterwards the channels simply fill back in.
    if crazing:
        z = fracture_network(z, rng, scales=crazing_scales,
                             depth=2200, density=crazing,
                             sharpness=crazing_sharp, cells=crazing_cells)

    corridor = None
    if sunder:
        z, corridor = sunder_pair(z, rng, rank=0, width_px=W * sunder_width)
        z = set_sea_level(z, land_fraction)
    z = despeckle(z)
    return z, lost


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--seed", type=int, default=7)
    p.add_argument("--land-fraction", type=float, default=0.30)
    p.add_argument("--warp", type=float, default=0.030,
                   help="tectonic displacement, as a fraction of map width")
    p.add_argument("--rift", type=float, default=0.6)
    p.add_argument("--platform", type=float, default=2600.0)
    p.add_argument("--platform-scale", type=float, default=0.075)
    p.add_argument("--impact-lat", type=float, default=-46.0,
                   help="the Marreni Sea is southern, per canon")
    p.add_argument("--impact-lon", type=float, default=-25.0)
    p.add_argument("--separation", type=float, default=1.0,
                   help="how decisively continents are split by deep ocean")
    p.add_argument("--no-lost-continent", action="store_true")
    p.add_argument("--lost-rank", type=int, default=1)
    p.add_argument("--width", type=int, default=2880)
    p.add_argument("--rot", type=float, nargs=3, default=[121.0, 47.0, 29.0],
                   help="pole-shift rotation: three Euler angles in degrees")
    p.add_argument("--hotspots", type=int, default=6)
    p.add_argument("--mountains", type=float, default=1.0)
    p.add_argument("--fractures", type=int, default=7)
    p.add_argument("--fracture-width", type=float, default=0.020)
    p.add_argument("--seas", type=int, default=4)
    p.add_argument("--sunder", action="store_true",
                   help="cut a continent in two (OFF by default: the Almani "
                        "Corridor is hand-authored, see maps/README.md)")
    p.add_argument("--sunder-width", type=float, default=0.0045)
    p.add_argument("--crazing", type=float, default=1.0,
                   help="density of drowned saltwater fracture channels")
    p.add_argument("--crazing-scales", type=int, default=3)
    p.add_argument("--crazing-cells", type=int, default=140,
                   help="number of fracture nuclei at the coarsest generation")
    p.add_argument("--crazing-sharp", type=float, default=14.0)
    p.add_argument("--out", default="world")
    a = p.parse_args()
    set_resolution(a.width)

    z, lost = build(a.seed, a.land_fraction, a.warp, a.rift,
                    a.impact_lat, a.impact_lon, a.platform, a.platform_scale,
                    a.separation, not a.no_lost_continent, a.lost_rank,
                    tuple(a.rot), a.hotspots, a.mountains,
                    a.fractures, a.fracture_width, a.seas,
                    a.sunder, a.sunder_width,
                    a.crazing, a.crazing_scales, a.crazing_sharp,
                    a.crazing_cells)

    render_colour(z).save(f"{a.out}_seed{a.seed}_colour.png")
    render_heightmap(z).save(f"{a.out}_seed{a.seed}_height.png")

    land = (z >= 0)
    lab, n = ndimage.label(land, structure=np.ones((3, 3)))
    sizes = np.bincount(lab.ravel())[1:]
    total = sizes.sum()
    big = np.sort(sizes)[::-1]

    # isolation: mean distance from land to the nearest other landmass
    dist = ndimage.distance_transform_edt(~land)
    shallow = ((z < 0) & (z > -600)).sum() / max((z < 0).sum(), 1)

    wts = latitude_weight(H, W)
    land_frac = (land * wts).sum() / wts.sum()
    print(f"seed {a.seed}: land {100*land_frac:.1f}% (area-weighted) | {n} landmasses")
    print("  largest (% of all land):",
          ", ".join(f"{100*s/total:.1f}" for s in big[:8]))
    print(f"  continents (>4%): {(big > total*0.04).sum()} | "
          f"islands (<0.1%): {(big < total*0.001).sum()}")
    print(f"  widest ocean gap: {dist.max()/W*360:.0f} deg of longitude | "
          f"shallow sea: {100*shallow:.0f}% of ocean")
    if lost:
        print(f"  lost continent drowned: {100*lost:.1f}% of former land")


if __name__ == "__main__":
    main()
