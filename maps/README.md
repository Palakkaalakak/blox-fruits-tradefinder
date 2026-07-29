# Maps

## How the world is generated

`generate_world.py` derives the world from **real Earth topography** — ETOPO1, NOAA's 1-arc-minute global elevation and bathymetry grid — and applies the Doom to it as a sequence of transformations.

This is not a geophysical simulation. A true finite-element model of crustal response and mantle convection is out of scope. What it *is* is Earth's actual terrain — with all the fractal character that makes real coastlines look real — deformed by processes that stand in for the Doom's mechanisms. The output is geologically plausible in its shapes because the input was geological, and unrecognisable because the deformation is severe.

### Pipeline

| Stage | What it does | In-world meaning |
|---|---|---|
| **Load** | Real Earth elevation + bathymetry | The world before |
| **Roll / flip** | Longitudinal shift, hemisphere inversion | Disguise. Geologically meaningless, visually essential |
| **Impact** | Crater, ejecta ring, radial fracture spokes | The strike |
| **Tectonic warp** | Multi-octave domain warping — every point displaced by a smooth vector field | Deep-time deformation, "baked in" for the look. *No such time passed in-story* |
| **Platforms** | Broad regions ride high or founder, sharpened with `tanh` | Isostatic reorganisation. This is what keeps land in coherent continents rather than confetti |
| **Rifting** | Long fracture zones that open seas or raise arcs | New straits, new island chains |
| **Erosion** | Smoothing plus low-amplitude fractal detail | Aged coastlines |
| **Drowning** | Sea level set to a target land fraction, area-weighted | Shelves drown, basins rise |

### Why the parameters matter

- `--warp` — how far the continents are dragged. **High values shred them into tendrils.** 0.03–0.045 is the useful band.
- `--platform` / `--platform-scale` — the strength and size of continental platforms. This is the knob that decides whether you get solid continents or a lace of islands. Larger scale → fewer, bigger continents.
- `--rift` — island chains and inland seas. Above ~1.0 it starts cutting continents apart.
- `--land-fraction` — Earth is 0.29. Lower means more ocean and more isolation, which suits a world where the Rediscovery took centuries.

### Output

- `*_height.png` — 8-bit greyscale, sea level at 127. **Import this into Azgaar** (Tools → Heightmap → Image) to get rivers, biomes, cultures, states, burgs and routes on top of it.
- `*_colour.png` — shaded render for eyeballing candidates.

### Usage

```bash
pip install numpy scipy pillow
# ETOPO1 must be at /tmp/etopo.grd — see the download note below
python3 generate_world.py --seed 11 --warp 0.042 --platform 4200 --platform-scale 0.095
```

ETOPO1 source (395 MB gzipped):
`https://www.ngdc.noaa.gov/mgg/global/relief/ETOPO1/data/ice_surface/grid_registered/netcdf/ETOPO1_Ice_g_gmt4.grd.gz`
Decompress to `/tmp/etopo.grd`.

---

## What the map has to accommodate

Once a candidate is chosen, these are the fixed requirements the geography must satisfy. Manual editing follows — the generator produces the canvas, not the answer.

1. **Lidia and Réselia** — two large continents, set diagonal and offset, overlapping only where they meet at the Almani Corridor. Each therefore spans latitudes the other does not.
2. **The Almani Corridor** — a narrow strait between them, the only practical passage. The world's throat.
3. **Cevine** — territory on *both shores* of the Corridor. The cradle of the post-Doom world and its paramount power.
4. **The third continent** — the Elsring homeland, across an ocean. Far enough that reaching it required the Rediscovery. Carries two competing names.
5. **The Marreni Sea of the South** — deep, aquamarine, southern.
6. **Parvaan** — formerly landlocked, adjacent to Cevine, with the Port of Ouspré now its outlet.
7. **The Academy** — on Lidia, in an Anglo-Saxon-majority region, ringed by light woodland.
8. **Archipelagos** — several, substantial. Trade, piracy, isolation, refuges.
9. **Room for 100–200 realms.** The map must support that density: many small states, a handful of giants.
10. **Drowned coasts.** Every shoreline should have sunken ruins offshore somewhere.

## Selection log

| Seed | Land | Landmasses | Continents >4% | Verdict |
|---|---|---|---|---|
| 7 (first attempt) | 34% | 535 | 7 | Rejected — confetti. Erosion detail and rifting too high |
| 7 (platforms added) | 32% | 201 | 5 | Coherent continents, but still visibly Earth — Africa unmistakable |
| 3 | 32% | 157 | 5 | Rejected — one continent held 64% of all land |
| 11 (warp 0.06) | 34% | 195 | 6 | Good balance (29/19/14/13/8/7), unrecognisable, but stringy — tendrils not continents |
| *tuned batch* | | | | *pending* |
