#!/usr/bin/env python3
"""
JR — the working world map.

This is the settled recipe. It supersedes the earlier experiments in this
directory (simulate_world.py, research_world.py), which are retained for
reference.

METHOD

The world is Earth, deformed by the Doom, rather than a new planet invented
from scratch. Real Earth elevation and bathymetry (ETOPO1) is the starting
point, and the Doom's effects are applied to it:

  1. Crustal deformation, as moderate domain warping. Kept deliberately
     restrained so that the positions of the continents survive.
  2. The impact at 48 degrees south, using pi-group crater scaling.
  3. The Drowning, applied as a substantial fall in the amount of land
     standing above sea level.
  4. The crazing: the saltwater fracture network.

WHY THE DROWNING DOES THE WORK

Warping alone does not disguise Earth. Domain warping bends and moves
coastlines but preserves their silhouettes, so at any warp strength weak
enough to keep continents intact, Africa still looks like Africa.

Lowering the land fraction is what actually changes the map. It floods the
lowlands and leaves the highlands standing, so the continents survive as
scattered highland archipelago in roughly their former positions. Land is
approximately where it used to be; its shape is not. That is what "a faint
resemblance to the old continents" means in practice, and it is also exactly
what the Doom is described as having done.

Land is set to about 19 percent after fracturing, against Earth's 29 percent.

THE MAGNETIC REVERSAL CONTRIBUTES NOTHING HERE, correctly: it does not move
the axis, change any latitude, or alter the terrain. Its consequences are
navigational and biological.

Usage:  python3 build_world.py --width 2200
"""

import argparse
import numpy as np
import generate_world as G

PARAMS = dict(
    land_fraction=0.28,      # ~19% after the fractures remove their share
    warp=0.030,              # crustal deformation; higher merges continents
    rift=0.25,
    mountains=0.35,
    seas=2,
    hotspots=5,
    platform=0.0,            # 0 = keep Earth's own continents
    lost_continent=True,     # the drowned seventh
    rotation=(0, 0, 0),      # no axial shift: the reversal is magnetic only
    sunder=False,            # the Almani Corridor is hand-drawn, not generated
    crazing=0.75,
    crazing_cells=35,
    crack_width=0.00112,
    crack_smoothing=0.5,
    mountain_avoidance=0.6,
    blob=0.9,
    impact_lat=-48.0,        # the Marreni Sea: southern, central
    impact_lon=0.0,
)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=44)
    ap.add_argument("--width", type=int, default=2200)
    ap.add_argument("--out", default="WORLD")
    a = ap.parse_args()

    G.set_resolution(a.width)
    z, lost = G.build(a.seed, **PARAMS)

    G.render_colour(z).save(f"{a.out}.png")
    G.render_heightmap(z).save(f"{a.out}_height.png")
    np.save(f"{a.out}_elevation.npy", z)

    land = z >= 0
    wts = G.latitude_weight(*z.shape)
    lab, n = G.ndimage.label(land, structure=np.ones((3, 3)))
    sizes = np.sort(np.bincount(lab.ravel())[1:])[::-1]
    tot = sizes.sum()
    print(f"land {100*(land*wts).sum()/wts.sum():.1f}% | {n} landmasses | "
          f"largest {100*sizes[0]/tot:.1f}%")
    print("top:", ", ".join(f"{100*s/tot:.1f}" for s in sizes[:8]))
    if lost:
        print(f"drowned continent: {100*lost:.1f}% of former land")
    print(f"\nwrote {a.out}.png (view), {a.out}_height.png (import to Azgaar), "
          f"{a.out}_elevation.npy (metres)")


if __name__ == "__main__":
    main()
