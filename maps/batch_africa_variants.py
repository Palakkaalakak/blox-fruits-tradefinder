#!/usr/bin/env python3
"""Generate several Africa treatments and verify each one before it's
trusted: no landmass may come unreasonably close to the polar continent,
and no landmass other than Africa/Antarctica may touch the map's left or
right edge (that combination is what produced the cross-ocean arm before)."""

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

MIN_ANTARCTICA_GAP_PX = 40


def verify(z, w):
    land = z >= 0
    lab, n = ndimage.label(land, structure=np.ones((3, 3)))
    sizes = np.bincount(lab.ravel())
    order = np.argsort(sizes[1:])[::-1] + 1
    significant = [i for i in order if sizes[i] > 0.003 * land.sum()]

    # Antarctica = the significant component with the southernmost mean row.
    mean_y = {}
    for i in significant:
        ys, _ = np.where(lab == i)
        mean_y[i] = ys.mean()
    antarctica_id = max(mean_y, key=mean_y.get)

    problems = []

    # Edge check: only Africa and Antarctica may touch column 0 or w-1.
    edge_ids = set(lab[:, 0][lab[:, 0] > 0]) | set(lab[:, -1][lab[:, -1] > 0])
    edge_ids.discard(antarctica_id)
    # whichever remaining edge id(s) are largest = Africa's two halves;
    # anything else touching the edge is a bug.
    edge_sizes = sorted(((sizes[i], i) for i in edge_ids), reverse=True)
    africa_ids = {i for _, i in edge_sizes[:2]} if edge_sizes else set()
    stray_edge = edge_ids - africa_ids
    if stray_edge:
        problems.append(f"non-Africa landmass touches map edge: ids {stray_edge}")

    # Distance check: every significant non-Antarctica component vs Antarctica.
    ay, ax = np.where(lab == antarctica_id)
    apts = np.column_stack([ay, ax]).astype(np.float32)
    # subsample Antarctica for a fast tree (it's a long thin band; a stride
    # keeps the true nearest-edge points densely enough represented)
    apts = apts[::4]
    tree = cKDTree(apts)
    for i in significant:
        if i == antarctica_id:
            continue
        ys, xs = np.where(lab == i)
        pts = np.column_stack([ys, xs]).astype(np.float32)
        d, _ = tree.query(pts, workers=-1)
        gap = d.min()
        if gap < MIN_ANTARCTICA_GAP_PX:
            problems.append(f"component {i} ({sizes[i]}px) is {gap:.0f}px from Antarctica")

    return problems, antarctica_id, significant, sizes


def main():
    for v in VARIANTS:
        name = v.pop("name")
        z = B.build(seed=44, w=2200, verbose=False, **v)
        G.render_colour(z).save(f"variant_{name}.png")
        np.save(f"variant_{name}_elevation.npy", z)
        problems, antarctica_id, significant, sizes = verify(z, 2200)
        status = "FAIL" if problems else "OK"
        print(f"{name}: {status}  landmasses={len(significant)}")
        for p in problems:
            print(f"    - {p}")


if __name__ == "__main__":
    main()
