#!/usr/bin/env python3
"""Generate several Africa treatments and verify each one before it's
trusted: Africa itself must stay clear of the polar continent by a real
margin, no OTHER landmass may touch the map's left/right edge, and nothing
non-Africa may sit unreasonably close to Antarctica either."""

import numpy as np
from scipy import ndimage
from scipy.spatial import cKDTree

import generate_world as G
import build_world as B

VARIANTS = [
    dict(name="v1_twist00_bend",   africa_mode="bend",   africa_twist_deg=0),
    dict(name="v2_twist15_bend",   africa_mode="bend",   africa_twist_deg=15),
    dict(name="v3_twist30_bend",   africa_mode="bend",   africa_twist_deg=30),
    dict(name="v4_twist45_bend",   africa_mode="bend",   africa_twist_deg=45),
    dict(name="v5_twist20_sunder", africa_mode="sunder", africa_twist_deg=20, africa_split_angle=0.3),
    dict(name="v6_twist40_sunder", africa_mode="sunder", africa_twist_deg=40, africa_split_angle=1.0),
    dict(name="v7_twist60_sunder", africa_mode="sunder", africa_twist_deg=60, africa_split_angle=1.8),
    dict(name="v8_twist80_sunder", africa_mode="sunder", africa_twist_deg=80, africa_split_angle=2.6),
]

MIN_GAP_PX = 40
NOISE_FRAC = 0.003     # ignore components smaller than this fraction of land
STRAY_EDGE_FRAC = 0.015


def verify(z):
    land = z >= 0
    lab, n = ndimage.label(land, structure=np.ones((3, 3)))
    sizes = np.bincount(lab.ravel())
    total = land.sum()
    order = np.argsort(sizes[1:])[::-1] + 1
    sig = [i for i in order if sizes[i] > NOISE_FRAC * total]

    w = z.shape[1]
    # Antarctica: the largest component that spans both map edges (a real
    # circumpolar band, not just an incidental touch).
    both_edge = [i for i in sig
                 if (lab[:, 0] == i).any() and (lab[:, -1] == i).any()
                 and sizes[i] > 0.05 * total]
    antarctica_id = both_edge[0] if both_edge else max(sig, key=lambda i: sizes[i])

    edge_ids = set(lab[:, 0][lab[:, 0] > 0]) | set(lab[:, -1][lab[:, -1] > 0])
    edge_ids.discard(antarctica_id)
    edge_sizes = sorted(((sizes[i], i) for i in edge_ids if i in sig), reverse=True)
    africa_ids = {i for _, i in edge_sizes[:2]}

    problems = []
    stray = [i for i in edge_ids if i not in africa_ids and sizes[i] > STRAY_EDGE_FRAC * total]
    if stray:
        problems.append(f"non-Africa landmass touches map edge: {stray}")

    ay, ax = np.where(lab == antarctica_id)
    apts = np.column_stack([ay, ax]).astype(np.float32)[::4]
    tree = cKDTree(apts)

    def gap_to_antarctica(i):
        ys, xs = np.where(lab == i)
        pts = np.column_stack([ys, xs]).astype(np.float32)
        d, _ = tree.query(pts, workers=-1)
        return float(d.min())

    # Africa's own gap - this is the one that actually matters most, and the
    # one the previous version of this script computed but never checked.
    africa_gap = min((gap_to_antarctica(i) for i in africa_ids), default=None)
    if africa_gap is not None and africa_gap < MIN_GAP_PX:
        problems.append(f"AFRICA is {africa_gap:.0f}px from Antarctica")

    close = []
    for i in sig:
        if i == antarctica_id or i in africa_ids:
            continue
        g = gap_to_antarctica(i)
        if g < MIN_GAP_PX:
            close.append((i, int(sizes[i]), round(g, 1)))
    if close:
        problems.append(f"non-Africa landmass close to Antarctica: {close}")

    return problems, africa_gap, len(sig)


def main():
    for v in VARIANTS:
        name = v.pop("name")
        z = B.build(seed=44, w=2200, verbose=False, **v)
        G.render_colour(z).save(f"variant_{name}.png")
        np.save(f"variant_{name}_elevation.npy", z)
        problems, africa_gap, n_landmasses = verify(z)
        status = "FAIL" if problems else "OK"
        gap_str = f"{africa_gap:.0f}px" if africa_gap is not None else "?"
        print(f"{name}: {status}  landmasses={n_landmasses}  africa_gap={gap_str}")
        for p in problems:
            print(f"    - {p}")


if __name__ == "__main__":
    main()
