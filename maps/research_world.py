#!/usr/bin/env python3
"""
MAP A — RESEARCH-LED (heavy bias to cartographic research, some simulation).

Built from what fantasy-cartography practice says makes a map that serves a
story, rather than from what physics happens to produce.

Principles applied, and where they come from:

  * THE MEDITERRANEAN MODEL. "Two or more landmasses separated by a middle
    sea" is the standard arrangement for stories about exploration, culture
    clash and two-sided conflict. It is Westeros/Essos, it is Greece/Anatolia,
    it is Europe/Africa. JR needs exactly this: Lidia and Reselia facing each
    other across the Almani Corridor, with Cevine holding the strait.

  * CONCENTRATION, NOT SPRAWL. Land gathered in the middle of the map, ocean
    at the edges. Sprawl makes every crossing routine; concentration makes the
    one long crossing extraordinary - which is what the Rediscovery has to be.

  * BLANK SPACE IS A FEATURE. Empty ocean reads as mystery and leaves room to
    expand. The third continent sits alone beyond a wide blank sea, so the
    Rediscovery is a genuine leap into nothing.

  * DISTINCT SILHOUETTES. Each continent must be recognisable in outline
    alone. Readers navigate by shape.

  * EVERY FEATURE EARNS ITS PLACE. Mountains where they create barriers and
    highland routes; straits where they create chokepoints; seas where they
    create trade.

Simulation contributes: fractal coastline detail, ridged mountain belts,
the impact crater from scaling laws, and the fracture network.

Usage:  python3 research_world.py --seed 3
"""

import argparse
import numpy as np
from scipy import ndimage

import physics as P
import generate_world as G

# --------------------------------------------------------------------------
# THE LAYOUT.  (lat, lon, radius_deg, weight) - deliberately placed.
# Everything sits between roughly 55N and 55S, and within +/-95 of centre,
# leaving the map's edges as open ocean.
# --------------------------------------------------------------------------

LIDIA = [                      # north-west of the Corridor: broad, blocky
    (34, -46, 20, 1.00), (26, -30, 18, 1.00), (40, -26, 15, 0.85),
    (18, -44, 15, 0.80), (44, -44, 13, 0.70), (12, -30, 12, 0.62),
    (30, -60, 13, 0.72), (46, -12, 11, 0.55),
]

RESELIA = [                    # south-east of the Corridor: longer, tapering
    (-6, 6, 17, 1.00), (-20, 16, 16, 0.95), (4, 14, 14, 0.85),
    (-32, 22, 13, 0.78), (-14, -4, 13, 0.80), (-42, 30, 11, 0.60),
    (10, 26, 12, 0.68), (-24, 38, 11, 0.58),
]

# The Corridor: the two above nearly touch near (16, -10). Cevine holds both
# shores. A small deliberate gap is carved after the field is built.
CORRIDOR = (16.0, -11.0)

THIRD = [                      # the Elsring continent, alone across the ocean
    (20, 104, 19, 1.00), (6, 96, 16, 0.90), (32, 96, 15, 0.85),
    (-6, 104, 14, 0.75), (24, 122, 14, 0.78), (40, 110, 12, 0.62),
    (-18, 96, 11, 0.55),
]

ARCHIPELAGOS = [               # stepping stones, deliberately NOT a bridge
    (26, 52, 5, 0.55), (18, 60, 4, 0.48), (34, 62, 4, 0.45),
    (-2, 54, 4, 0.45), (-14, 62, 3.5, 0.40), (10, 70, 3.5, 0.38),
    (44, 40, 4.5, 0.45), (-30, 48, 4, 0.42),
]

POLAR = [                      # thin polar land, so the map is not bare
    (-64, -20, 13, 0.55), (-66, 20, 12, 0.50), (68, -34, 10, 0.45),
]

MOUNTAIN_ARCS = [
    # (lat0, lon0, lat1, lon1, width_deg, height_m)  - barriers that matter
    ((40, -54), (16, -34), 5.0, 3600),     # Lidia's spine
    ((30, -20), (44, -14), 4.0, 2800),     # Lidian coastal range
    ((2, 2), (-30, 20), 5.5, 3900),        # Reselia's great range
    ((-8, 20), (-26, 34), 4.0, 2600),      # Reselian eastern range
    ((28, 96), (10, 108), 5.0, 3400),      # the third continent's barrier
]

MARRENI = (-44.0, 2.0)         # impact sea: south, between the two continents


def _blob_field(h, w, blobs):
    """Great-circle metaball field. Smooth, so continents merge naturally."""
    v = P._unit_vectors(h, w)
    field = np.zeros((h, w), dtype=np.float32)
    for lat, lon, rad, weight in blobs:
        la, lo = np.radians(lat), np.radians(lon)
        c = np.array([np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)])
        cosd = np.clip(np.tensordot(c, v, axes=(0, 0)), -1, 1)
        ang = np.degrees(np.arccos(cosd))
        field += weight * np.exp(-(ang / rad) ** 2)
    return field


def _arc_ridges(h, w, arcs, rng):
    """Mountain belts along chosen arcs: barriers placed for story reasons."""
    v = P._unit_vectors(h, w)
    out = np.zeros((h, w), dtype=np.float32)
    for (lat0, lon0), (lat1, lon1), width, height in arcs:
        acc = np.full((h, w), 9e9, dtype=np.float32)
        for t in np.linspace(0, 1, 40):
            la = np.radians(lat0 + (lat1 - lat0) * t)
            lo = np.radians(lon0 + (lon1 - lon0) * t)
            c = np.array([np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)])
            cosd = np.clip(np.tensordot(c, v, axes=(0, 0)), -1, 1)
            acc = np.minimum(acc, np.degrees(np.arccos(cosd)))
        ridged = 1.0 - np.abs(G.fbm((h, w), rng, octaves=4, base=26))
        out += height * np.exp(-(acc / width) ** 2) * (0.55 + 0.45 *
                                                       np.clip(ridged, 0, 1))
    return out


def build(seed=3, w=2400, land_threshold=0.40, crazing=0.75, cells=35,
          crack_width=0.00112, verbose=True):
    h = w // 2
    rng = np.random.default_rng(seed)
    G.set_resolution(w)

    if verbose:
        print("[1/5] laying out continents (Mediterranean model) ...")
    field = (_blob_field(h, w, LIDIA) + _blob_field(h, w, RESELIA)
             + _blob_field(h, w, THIRD) + _blob_field(h, w, ARCHIPELAGOS)
             + _blob_field(h, w, POLAR))

    if verbose:
        print("[2/5] fractal coastlines ...")
    # Coastline detail at several scales: this is what stops a metaball map
    # looking like a metaball map.
    detail = (0.34 * G.fbm((h, w), rng, octaves=7, base=w * 0.045)
              + 0.22 * G.fbm((h, w), rng, octaves=6, base=w * 0.018)
              + 0.12 * G.fbm((h, w), rng, octaves=5, base=w * 0.007))
    # Warp the field itself so coasts wander instead of bulging: this is what
    # stops a metaball layout reading as circles.
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    wx = G.smooth_noise((h, w), w * 0.02, rng) * (w * 0.012)
    wy = G.smooth_noise((h, w), w * 0.02, rng) * (w * 0.012)
    field = G.sample(field, yy + wy, xx + wx)
    field = field + detail * 0.60

    z = (field - land_threshold) * 2600.0

    if verbose:
        print("[3/5] mountain barriers ...")
    z = z + _arc_ridges(h, w, MOUNTAIN_ARCS, rng)
    z = z + 260.0 * G.fbm((h, w), rng, octaves=5, base=w * 0.02)

    if verbose:
        print("[4/5] the Marreni impact ...")
    imp, D = P.impact_field(h, w, MARRENI[0], MARRENI[1],
                            impactor_d_m=42000.0)
    z = z + imp
    resp, _, _ = P.flexural_response(imp, h, w)
    z = z + resp
    if verbose:
        print(f"    crater {D/1000:.0f} km across")

    # The Corridor: a deliberate narrow strait where Lidia and Reselia meet.
    v = P._unit_vectors(h, w)
    la, lo = np.radians(CORRIDOR[0]), np.radians(CORRIDOR[1])
    c = np.array([np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)])
    ang = np.degrees(np.arccos(np.clip(np.tensordot(c, v, axes=(0, 0)), -1, 1)))
    z = z - 2600.0 * np.exp(-(ang / 3.0) ** 2)

    z = ndimage.gaussian_filter(z, 1.1, mode=("nearest", "wrap"))

    if verbose:
        print("[5/5] the crazing ...")
    if crazing:
        z = G.fracture_network(z, rng, scales=3, depth=3100, density=crazing,
                               sharpness=14.0, cells=cells,
                               impact_lat=MARRENI[0], impact_lon=MARRENI[1],
                               mountain_avoidance=0.6, smoothing=0.5,
                               crack_width=crack_width)
    return G.despeckle(z)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=3)
    ap.add_argument("--width", type=int, default=2400)
    ap.add_argument("--crazing", type=float, default=0.75)
    ap.add_argument("--crazing-cells", type=int, default=35)
    ap.add_argument("--crack-width", type=float, default=0.00112)
    ap.add_argument("--land-threshold", type=float, default=0.40)
    ap.add_argument("--out", default="RESEARCH")
    a = ap.parse_args()

    z = build(a.seed, a.width, land_threshold=a.land_threshold,
              crazing=a.crazing, cells=a.crazing_cells,
              crack_width=a.crack_width)

    G.render_colour(z).save(f"{a.out}_seed{a.seed}_colour.png")
    G.render_heightmap(z).save(f"{a.out}_seed{a.seed}_height.png")

    land = z >= 0
    lab, n = ndimage.label(land, structure=np.ones((3, 3)))
    sizes = np.sort(np.bincount(lab.ravel())[1:])[::-1]
    tot = sizes.sum()
    wts = G.latitude_weight(*z.shape)
    print(f"\nland {100*(land*wts).sum()/wts.sum():.1f}% | {n} landmasses | "
          f"largest {100*sizes[0]/tot:.1f}%")
    print("top:", ", ".join(f"{100*s/tot:.1f}" for s in sizes[:8]))


if __name__ == "__main__":
    main()
