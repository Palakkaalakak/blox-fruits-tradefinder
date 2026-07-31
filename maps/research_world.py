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

LIDIA = [                      # north-west of the Corridor
    (36, -48, 16, 1.00), (27, -33, 15, 1.00), (42, -28, 12, 0.90),
    (19, -46, 12, 0.85), (47, -45, 10, 0.72), (13, -32, 10, 0.66),
    (31, -63, 11, 0.76), (48, -14, 9, 0.60), (22, -20, 9, 0.70),
    (38, -60, 8, 0.62), (10, -46, 8, 0.55), (44, -36, 9, 0.72),
    (52, -34, 7, 0.48), (16, -58, 7, 0.50), (30, -16, 8, 0.58),
]

RESELIA = [                    # south-east of the Corridor: longer, tapering
    (-6, 7, 14, 1.00), (-20, 17, 13, 0.98), (5, 15, 12, 0.88),
    (-33, 23, 11, 0.80), (-14, -3, 11, 0.84), (-44, 31, 9, 0.62),
    (11, 27, 10, 0.72), (-25, 39, 9, 0.60), (-2, 24, 9, 0.66),
    (-38, 16, 8, 0.58), (-11, 32, 8, 0.55), (2, -2, 8, 0.62),
    (-28, 8, 8, 0.60), (-48, 24, 6, 0.42),
]

# The Corridor: the two above nearly touch near (16, -10). Cevine holds both
# shores. A small deliberate gap is carved after the field is built.
CORRIDOR = (16.0, -11.0)

THIRD = [                      # the Elsring continent, alone across the ocean
    (21, 106, 15, 1.00), (7, 98, 13, 0.92), (33, 97, 12, 0.88),
    (-6, 106, 11, 0.78), (25, 124, 11, 0.80), (41, 112, 10, 0.66),
    (-18, 98, 9, 0.58), (14, 116, 10, 0.74), (34, 128, 8, 0.55),
    (-2, 92, 9, 0.62), (-14, 116, 8, 0.50), (46, 100, 8, 0.48),
]

# Subtractive blobs: gulfs, bays and inland seas bitten OUT of the continents.
# Continents made only by adding circles look like circles; the bays are what
# give a coastline character.
BITES = [
    (30, -38, 7, 0.85), (20, -52, 5, 0.70), (41, -20, 5, 0.65),
    (-14, 12, 6, 0.80), (-30, 28, 5, 0.62), (2, 20, 5, 0.68),
    (18, 108, 6, 0.72), (30, 116, 4.5, 0.60), (-6, 98, 4, 0.55),
    (44, -50, 4, 0.55), (-24, 4, 5, 0.62),
]

# Far-flung things: mystery, and room to expand. Deliberately unexplained.
OUTLIERS = [
    (52, 150, 7, 0.70),     # a large island alone in the far ocean
    (-52, -78, 6, 0.62),    # another, opposite
    (8, -128, 5, 0.58),     # a lone island mid-ocean
    (-36, -132, 4.5, 0.52),
    (62, 66, 5, 0.55),
    (-58, 104, 5, 0.55),
    (40, -110, 4, 0.48),
    (-20, 152, 4.5, 0.50),
]

ARCHIPELAGOS = [               # stepping stones, deliberately NOT a bridge
    (26, 52, 4, 0.58), (18, 60, 3.2, 0.50), (34, 62, 3.2, 0.48),
    (-2, 54, 3.2, 0.48), (-14, 62, 3.0, 0.44), (10, 70, 3.0, 0.42),
    (44, 40, 3.6, 0.48), (-30, 48, 3.2, 0.45), (22, 74, 2.8, 0.40),
    (-8, 44, 3.0, 0.44), (36, 46, 3.0, 0.44), (-22, 56, 2.8, 0.40),
    (6, 62, 2.6, 0.38), (30, 34, 3.2, 0.46), (-40, 44, 2.8, 0.38),
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
             + _blob_field(h, w, POLAR) + _blob_field(h, w, OUTLIERS))
    # bite out the gulfs and bays
    field = field - 1.15 * _blob_field(h, w, BITES)

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
    for scale, amp in [(0.045, 0.030), (0.020, 0.016), (0.009, 0.007)]:
        wx = G.smooth_noise((h, w), w * scale, rng) * (w * amp)
        wy = G.smooth_noise((h, w), w * scale, rng) * (w * amp * 0.8)
        yy, xx = yy + wy, xx + wx
    field = G.sample(field, yy, xx)
    field = field + detail * 0.72

    z = (field - land_threshold) * 2600.0

    if verbose:
        print("[3/5] mountain barriers ...")
    z = z + _arc_ridges(h, w, MOUNTAIN_ARCS, rng)
    z = z + 260.0 * G.fbm((h, w), rng, octaves=5, base=w * 0.02)

    if verbose:
        print("[4/5] the Marreni impact ...")
    imp, D, _, _ = P.impact_field(h, w, MARRENI[0], MARRENI[1],
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
    z = G.despeckle(z)
    return P.cleanup(z, median_px=1)


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
