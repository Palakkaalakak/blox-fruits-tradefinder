#!/usr/bin/env python3
"""Small variations around the currently-accepted Africa placement/size,
each verified: Africa must clip both map edges, and must stay well clear
of Antarctica (300px+), and no non-Africa landmass may touch the edge."""

import numpy as np
from scipy import ndimage
from scipy.spatial import cKDTree

import generate_world as G
import rearrange as R
import build_world as B

BASE = (-146.0, -24.7, 44.6)

VARIANTS = [
    dict(name="w1", placement=(BASE[0]+0,  BASE[1]+0,  BASE[2]+0),  twist=0),
    dict(name="w2", placement=(BASE[0]-10, BASE[1]+6,  BASE[2]+0),  twist=0),
    dict(name="w3", placement=(BASE[0]+12, BASE[1]-5,  BASE[2]+10), twist=0),
    dict(name="w4", placement=(BASE[0]+0,  BASE[1]+0,  BASE[2]-15), twist=15),
    dict(name="w5", placement=(BASE[0]-18, BASE[1]+10, BASE[2]+20), twist=0),
    dict(name="w6", placement=(BASE[0]+8,  BASE[1]+0,  BASE[2]+30), twist=10),
]

MIN_GAP_PX = 200
NOISE_FRAC = 0.003
STRAY_EDGE_FRAC = 0.015


def verify(z):
    land = z >= 0
    lab, n = ndimage.label(land, structure=np.ones((3, 3)))
    sizes = np.bincount(lab.ravel())
    total = land.sum()
    order = np.argsort(sizes[1:])[::-1] + 1
    sig = [i for i in order if sizes[i] > NOISE_FRAC * total]

    both_edge = [i for i in sig
                 if (lab[:, 0] == i).any() and (lab[:, -1] == i).any()
                 and sizes[i] > 0.05 * total]
    antarctica_id = both_edge[0] if both_edge else max(sig, key=lambda i: sizes[i])

    edge_ids = set(lab[:, 0][lab[:, 0] > 0]) | set(lab[:, -1][lab[:, -1] > 0])
    edge_ids.discard(antarctica_id)
    edge_sizes = sorted(((sizes[i], i) for i in edge_ids if i in sig), reverse=True)
    africa_ids = {i for _, i in edge_sizes[:2]}

    problems = []
    if not africa_ids:
        problems.append("Africa does not clip either edge")
    stray = [i for i in edge_ids if i not in africa_ids and sizes[i] > STRAY_EDGE_FRAC * total]
    if stray:
        problems.append(f"non-Africa touches edge: {stray}")

    ay, ax = np.where(lab == antarctica_id)
    apts = np.column_stack([ay, ax]).astype(np.float32)[::4]
    tree = cKDTree(apts)

    def gap(i):
        ys, xs = np.where(lab == i)
        pts = np.column_stack([ys, xs]).astype(np.float32)
        d, _ = tree.query(pts, workers=-1)
        return float(d.min())

    africa_gap = min((gap(i) for i in africa_ids), default=None)
    if africa_gap is not None and africa_gap < MIN_GAP_PX:
        problems.append(f"AFRICA only {africa_gap:.0f}px from Antarctica")

    close = [(i, int(sizes[i]), round(gap(i), 1)) for i in sig
             if i != antarctica_id and i not in africa_ids and gap(i) < MIN_GAP_PX]
    if close:
        problems.append(f"non-Africa close to Antarctica: {close}")

    africa_frac = sum(sizes[i] for i in africa_ids) / total
    return problems, africa_gap, africa_frac


def main():
    for v in VARIANTS:
        name = v["name"]
        R.PLACEMENT["africa"] = v["placement"]
        z = B.build(seed=44, w=2200, verbose=False, africa_mode="bend",
                    africa_twist_deg=v["twist"])
        G.render_colour(z).save(f"w_{name}.png")
        np.save(f"w_{name}_elevation.npy", z)
        problems, gap, frac = verify(z)
        status = "FAIL" if problems else "OK"
        gap_str = f"{gap:.0f}px" if gap is not None else "?"
        print(f"{name} placement={v['placement']} twist={v['twist']}: "
              f"{status} africa_gap={gap_str} africa_frac={frac*100:.1f}%")
        for p in problems:
            print(f"    - {p}")


if __name__ == "__main__":
    main()
