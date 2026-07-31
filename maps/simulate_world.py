#!/usr/bin/env python3
"""
MAP B — 100% SIMULATION.

No aesthetic intervention. The world is whatever the physics produces.

  1. PLATE TECTONICS   pyplatec (Viitanen's PlaTec, the engine behind
                       WorldEngine): real plate creation, drift, collision,
                       subduction, orogeny and erosion over N cycles.
  2. THE IMPACT        crater from pi-group scaling, ejecta blanket with the
                       observed r^-3 falloff, antipodal seismic focusing.
  3. FLEXURE           lithospheric response to the new load.
  4. THE DROWNING      sea level from displaced ocean volume.
  5. THE CRAZING       fracture network driven by the impact stress field.

THE GEOMAGNETIC REVERSAL CONTRIBUTES NOTHING TO THIS MAP, and that is
correct. A magnetic reversal does not move the rotation axis, does not change
any continent's latitude, and has no topographic effect at all. Real reversals
take 2,000-12,000 years; the field weakens and wanders rather than snapping.
Its consequences are navigational and biological - compasses useless for
centuries, a weakened magnetosphere, aurorae in the tropics, magnetically
navigating animals lost - not geological.

The climate catastrophe is the IMPACT WINTER, not the reversal.

Usage:  python3 simulate_world.py --seed 7
"""

import argparse
import numpy as np
from scipy import ndimage
from PIL import Image

import platec
import physics as P
import generate_world as G


def run_tectonics(seed, w, h, plates=12, cycles=3, sea_level=0.65,
                  erosion_period=60, folding_ratio=0.02,
                  aggr_overlap_abs=1_000_000, aggr_overlap_rel=0.33,
                  verbose=True):
    """A real plate-tectonics run: plates form, drift, collide and subduct."""
    sw, sh = int(w), int(h)
    p = platec.create(seed=int(seed), width=sw, height=sh,
                      sea_level=float(sea_level),
                      erosion_period=int(erosion_period),
                      folding_ratio=float(folding_ratio),
                      aggr_overlap_abs=int(aggr_overlap_abs),
                      aggr_overlap_rel=float(aggr_overlap_rel),
                      cycle_count=int(cycles), num_plates=int(plates))
    steps = 0
    while not platec.is_finished(p):
        platec.step(p)
        steps += 1
        if verbose and steps % 100 == 0:
            print(f"    tectonic step {steps}", flush=True)
    hm = np.array(platec.get_heightmap(p), dtype=np.float32).reshape(sh, sw)
    platec.destroy(p)
    if verbose:
        print(f"    tectonics complete after {steps} steps "
              f"({plates} plates, {cycles} cycles)")

    # platec heights are dimensionless-ish; stretch to metres
    hm = (hm - hm.mean()) / (hm.std() or 1.0)
    return (hm * 1900.0).astype(np.float32)


def displaced_sea_level(z, target_land):
    wts = G.latitude_weight(*z.shape).ravel()
    vals = z.ravel()
    order = np.argsort(vals)
    cw = np.cumsum(wts[order]) / wts.sum()
    idx = np.searchsorted(cw, 1.0 - target_land)
    return z - vals[order][min(idx, len(vals) - 1)]


def build(seed=7, w=2048, plates=12, cycles=3, impactor_km=45.0,
          impact_lat=-40.0, impact_lon=0.0, land_fraction=0.29,
          bulge_response=0.0, settle_myr=0.0, smooth_px=2.2, verbose=True):
    h = w // 2
    rng = np.random.default_rng(seed)
    G.set_resolution(w)

    if verbose:
        print("[1/5] plate tectonics ...", flush=True)
    z = run_tectonics(seed, w, h, plates=plates, cycles=cycles, verbose=verbose)
    # platec works on a coarse lattice and its output is visibly gridded;
    # smoothing removes the stair-stepping without touching the landforms
    z = ndimage.gaussian_filter(z, smooth_px, mode=("nearest", "wrap"))

    if verbose:
        print("[2/5] impact ...", flush=True)
    field, D, _, _ = P.impact_field(h, w, impact_lat, impact_lon,
                              impactor_d_m=impactor_km * 1000.0)
    z = z + field
    if verbose:
        print(f"    impactor {impactor_km:.0f} km -> crater {D/1000:.0f} km wide, "
              f"{D/25/1000:.1f} km deep")

    if verbose:
        print("[3/5] flexural isostasy ...", flush=True)
    resp, alpha, sig = P.flexural_response(field, h, w)
    z = z + resp
    if verbose:
        print(f"    flexural parameter {alpha/1000:.0f} km")

    if bulge_response:
        z = z - P.bulge_readjustment(h, w, (0, 0, 0), bulge_response)

    if verbose:
        print("[4/5] the Drowning ...", flush=True)
    z = displaced_sea_level(z, land_fraction)

    if verbose:
        print("[5/6] the crazing ...", flush=True)
    # The same Voronoi crack network used everywhere else. The earlier version
    # drew cos(28*azimuth) and cos(46*angle) spokes and rings, which is a
    # high-frequency interference pattern, not a fracture network - that was
    # the source of the choppy radial dashes around the crater.
    z = G.fracture_network(z, rng, scales=3, depth=3100, density=0.75,
                           sharpness=14.0, cells=35,
                           impact_lat=impact_lat, impact_lon=impact_lon,
                           mountain_avoidance=0.6, smoothing=0.5,
                           crack_width=0.00112)

    if verbose:
        print("[6/6] cleanup ...", flush=True)
    z = P.cleanup(z)
    z = G.despeckle(z)

    if settle_myr:
        if verbose:
            print(f"    settling for {settle_myr} Myr ...", flush=True)
        z = P.settle(z, myr=settle_myr, verbose=verbose)
        z = displaced_sea_level(z, land_fraction)
        z = G.despeckle(z)
    return z


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--width", type=int, default=2048)
    ap.add_argument("--plates", type=int, default=12)
    ap.add_argument("--cycles", type=int, default=3)
    ap.add_argument("--impactor-km", type=float, default=45.0)
    ap.add_argument("--land-fraction", type=float, default=0.29)
    ap.add_argument("--settle-myr", type=float, default=0.0)
    ap.add_argument("--smooth", type=float, default=2.2)
    ap.add_argument("--out", default="SIM")
    a = ap.parse_args()

    z = build(a.seed, a.width, a.plates, a.cycles, a.impactor_km,
              land_fraction=a.land_fraction, settle_myr=a.settle_myr,
              smooth_px=a.smooth)

    G.render_colour(z).save(f"{a.out}_seed{a.seed}_colour.png")
    G.render_heightmap(z).save(f"{a.out}_seed{a.seed}_height.png")

    land = z >= 0
    lab, n = ndimage.label(land, structure=np.ones((3, 3)))
    sizes = np.sort(np.bincount(lab.ravel())[1:])[::-1]
    tot = sizes.sum()
    print(f"\nseed {a.seed}: {n} landmasses, largest {100*sizes[0]/tot:.1f}% of land")
    print("top:", ", ".join(f"{100*s/tot:.1f}" for s in sizes[:8]))


if __name__ == "__main__":
    main()
