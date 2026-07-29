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


def continental_platforms(z, rng, strength, scale):
    """Broad isostatic reorganisation: some regions ride high as continental
    platforms, others founder into ocean basins. This is what keeps land
    gathered into a handful of coherent masses instead of scattering it."""
    field = smooth_noise(z.shape, scale, rng)
    # sharpen into plateaus and basins rather than gentle swells
    field = np.tanh(field * 1.6)
    return z + strength * field


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

    coast = np.abs(ndimage.gaussian_filter((z >= 0).astype(float), 0.8) - 0.5) < 0.22
    img[coast] = (245, 240, 225)
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
          platform=2600.0, platform_scale=0.075):
    rng = np.random.default_rng(seed)
    z = load_earth()
    z = np.roll(z, rng.integers(W // 6, W - W // 6), axis=1)   # break Earth's look
    if rng.random() < 0.5:
        z = np.fliplr(z)
    z = np.flipud(z)                                   # disguise: hemispheres swap
    z = impact(z, rng, impact_lat, impact_lon, radius_px=W * 0.035, depth=4200)
    z = tectonic_warp(z, rng, amplitude=W * warp, base_scale=W * 0.060)
    z = continental_platforms(z, rng, platform, W * platform_scale)
    z = rifting(z, rng, strength=2400 * rift, n_rifts=4)
    z = erode(z, rng)
    z = set_sea_level(z, land_fraction)
    return z


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--seed", type=int, default=7)
    p.add_argument("--land-fraction", type=float, default=0.30)
    p.add_argument("--warp", type=float, default=0.030,
                   help="tectonic displacement, as a fraction of map width")
    p.add_argument("--rift", type=float, default=0.6)
    p.add_argument("--platform", type=float, default=2600.0)
    p.add_argument("--platform-scale", type=float, default=0.075)
    p.add_argument("--impact-lat", type=float, default=8.0)
    p.add_argument("--impact-lon", type=float, default=-150.0)
    p.add_argument("--out", default="world")
    a = p.parse_args()

    z = build(a.seed, a.land_fraction, a.warp, a.rift, a.impact_lat, a.impact_lon,
             a.platform, a.platform_scale)

    render_colour(z).save(f"{a.out}_seed{a.seed}_colour.png")
    render_heightmap(z).save(f"{a.out}_seed{a.seed}_height.png")

    land = (z >= 0)
    lab, n = ndimage.label(land, structure=np.ones((3, 3)))
    sizes = np.bincount(lab.ravel())[1:]
    total = sizes.sum()
    big = np.sort(sizes)[::-1]
    print(f"seed {a.seed}: land {100*total/land.size:.1f}% | {n} landmasses")
    print("  largest (% of all land):",
          ", ".join(f"{100*s/total:.1f}" for s in big[:10]))
    print(f"  continents (>4% of land): {(big > total*0.04).sum()}")
    print(f"  islands (<0.1%): {(big < total*0.001).sum()}")


if __name__ == "__main__":
    main()
