#!/usr/bin/env python3
"""
JR — the working world map.

METHOD

The world is Earth after the Doom. It is not a new planet invented from
scratch, and it is not Earth with the coastlines merely nudged. The
continents are Earth's own, but they have been moved.

  1. REARRANGE. Each continent is cut off the globe, rotated to a new
     position and orientation, and set down again. Its internal terrain
     travels with it, so its mountains, valleys and shelf are still Earth's,
     but the arrangement of the world is new. ONE CONTINENT IS NOT REPLACED:
     Europe is the landmass the Doom drowned, and it is simply absent.
  2. IMPACT. The Marreni basin, at 48 degrees south.
  3. DROWNING. Sea level falls, flooding lowlands and leaving highlands.
  4. CRAZING. The saltwater fracture network.

WHY REARRANGING WAS NECESSARY

Earlier versions only warped Earth. Warping bends coastlines but preserves
the ARRANGEMENT - North America stays north-west of South America, Africa
stays below Europe - so the map still read as Earth at a glance no matter how
strong the warp. Moving the continents independently is what actually
produces a new world while keeping each continent's geology recognisably
Earth's on close inspection.

WHY EUROPE IS THE SUNK ONE

It explains something already in the canon. If the classical homeland is
under water, then Latin and Greek survive only in manuscripts, which is
exactly why an accurate account of the old world is the private property of
wealthy families.

A NOTE ON THE CRATER'S SIZE

The crater is generated from real pi-group scaling laws, but the impactor
required to make a basin large enough to read on a world map is far larger
than anything that would leave a habitable planet. The scaling is used here
for the SHAPE of the basin - cavity, rim, ejecta falloff - not as a claim
about survivability.

Usage:  python3 build_world.py --width 2200
"""

import argparse
import numpy as np

import generate_world as G
import physics as P
import rearrange as R

SINK = "europe"
IMPACT_LAT, IMPACT_LON = -48.0, 0.0
IMPACTOR_KM = 400.0          # sized for visibility; see note above
LAND_FRACTION = 0.30
CRAZING = dict(scales=3, depth=3100, density=0.75, sharpness=14.0, cells=35,
               mountain_avoidance=0.6, smoothing=0.9, crack_width=0.00112)


def carve_channel(z, p0, p1, width, floor=-250.0):
    """Cut a strait between two points. Only ever lowers ground - it cannot
    raise land that fracturing or erosion left below sea level."""
    h, w_ = z.shape
    yy, xx = np.mgrid[0:h, 0:w_].astype(np.float32)
    y0, x0 = p0
    y1, x1 = p1
    dx, dy = x1 - x0, y1 - y0
    length = max(np.hypot(dx, dy), 1e-6)
    ux, uy = dx / length, dy / length
    t = np.clip((xx - x0) * ux + (yy - y0) * uy, 0, length)
    projx, projy = x0 + t * ux, y0 + t * uy
    d = np.hypot(xx - projx, yy - projy)
    trough = np.exp(-(d / (width * 0.5)) ** 2)
    return np.minimum(z, z * (1 - trough) + floor * trough)


def build(seed=44, w=2200, verbose=True, africa_mode="bend"):
    G.set_resolution(w)
    h = G.H
    rng = np.random.default_rng(seed)

    if verbose:
        print("[1/5] rearranging the continents ...")
    earth = G.load_earth()
    z = R.rearrange(earth, sink=SINK, seed=seed, verbose=verbose,
                     africa_mode=africa_mode)
    z = R.blend_seafloor(z, earth)

    if verbose:
        print("[2/5] the impact ...")
    field, D, dist, r_px = P.impact_field(h, w, IMPACT_LAT, IMPACT_LON,
                              impactor_d_m=IMPACTOR_KM * 1000.0)
    z = z + field
    resp, _, _ = P.flexural_response(field, h, w)
    z = z + resp
    basin = dist < 1.4 * r_px
    if verbose:
        print(f"    Marreni basin {D/1000:.0f} km across at "
              f"{abs(IMPACT_LAT):.0f}S")

    if verbose:
        print("[3/5] the Drowning ...")
    z = G.erode(z, rng)
    wts = G.latitude_weight(h, w).ravel()
    vals = z.ravel()
    order = np.argsort(vals)
    cw = np.cumsum(wts[order]) / wts.sum()
    z = z - vals[order][min(int(np.searchsorted(cw, 1 - LAND_FRACTION)),
                            vals.size - 1)]

    # Marreni is canonically a sea. Whatever the local seafloor height ended
    # up being after erosion and the sea-level cut, the crater and its rim
    # must not break the surface - apply the clamp LAST, after every step
    # that shifts elevation, or an earlier clamp just gets undone.
    z[basin] = np.minimum(z[basin], -60.0)

    if verbose:
        print("[4/5] the crazing ...")
    z = G.fracture_network(z, rng, impact_lat=IMPACT_LAT,
                           impact_lon=IMPACT_LON, **CRAZING)

    if verbose:
        print("[5/5] cleanup ...")
    z = P.cleanup(z, median_px=1)
    z = G.despeckle(z)
    return z


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=44)
    ap.add_argument("--width", type=int, default=2200)
    ap.add_argument("--out", default="WORLD")
    ap.add_argument("--africa-mode", default="bend",
                    choices=["bend", "sunder", "none"])
    a = ap.parse_args()

    z = build(a.seed, a.width, africa_mode=a.africa_mode)
    G.render_colour(z).save(f"{a.out}.png")
    G.render_heightmap(z).save(f"{a.out}_height.png")
    np.save(f"{a.out}_elevation.npy", z)

    land = z >= 0
    wts = G.latitude_weight(*z.shape)
    lab, n = G.ndimage.label(land, structure=np.ones((3, 3)))
    sz = np.sort(np.bincount(lab.ravel())[1:])[::-1]
    tot = sz.sum()
    print(f"\nland {100*(land*wts).sum()/wts.sum():.1f}% | {n} landmasses")
    print("continents:", ", ".join(f"{100*s/tot:.1f}%" for s in sz[:8]))
    print(f"wrote {a.out}.png, {a.out}_height.png, {a.out}_elevation.npy")


if __name__ == "__main__":
    main()
