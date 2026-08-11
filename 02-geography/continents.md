# The continents

The world has **six continents**, one of which is polar and effectively uninhabited, and a **seventh which is submerged**.

Only three of the six are named so far. The remaining three are open, and naming them is a straightforward task whenever it becomes useful.

| # | Continent | Status |
|---|---|---|
| 1 | **Lidia** | Named. Retained firearms through the Doom. A Rediscovery power. The Academy stands here. |
| 2 | **Réselia** | Named. Retained firearms through the Doom. The other Rediscovery power. |
| 3 | *The Elsring continent* | Two competing names, one of them a corrupted Elsring word. Reached during the Rediscovery. Today a mixture of independent states and remaining colonies. |
| 4 | *Unnamed* | Open. |
| 5 | *Unnamed* | Open. |
| 6 | *Unnamed, polar* | The Antarctic equivalent. Ice-covered, effectively uninhabited, claimed by nobody in any meaningful sense. |
| 7 | *The submerged continent* | Drowned by the Doom and never resurfaced. See `the-lost-continent.md`. |

## Lidia and Réselia are continents, not countries

This distinction has been recorded inconsistently in earlier drafts of these documents and should be applied strictly from here on.

Lidia and Réselia are **landmasses**. Each contains many sovereign states. A person described as Lidian or Réselian is being identified by continent, in the same way that a person might be described as European or African — it indicates where they are from at the largest available scale, and very little else.

This has direct consequences for the manuscript. When a character says they are Réselian, they are giving a deliberately unspecific answer. When the extermination of the Elsring is attributed to "the Lidians and Réselians", the attribution is to peoples and states originating on those two continents, not to two governments acting in concert.

The states already named — Cevine, Parvaan, and the duchy that Edward's family rules — are polities located on or between these continents. They are not equivalents of them.

## The polar continent

The sixth continent is the polar landmass, equivalent to Antarctica. It is ice-covered and has no permanent population beyond whatever small presence a state might maintain there. Its function in the setting is chiefly to make the map complete rather than to carry story, though its existence supports the general point that the world is larger than the three continents the plot presently visits.

## The submerged continent

A seventh landmass was drowned during the Doom and never returned to the surface. It exists today as a shallow plateau on the seabed. Because the world is Earth and the Doom drowned land, this follows as a consequence rather than being an invention; the arithmetic of how much land there ought to be does not otherwise balance. Details are in `the-lost-continent.md`.

**This is Europe.** Despite being far from the Marreni impact site, it was wiped off the map entirely — sunk, not merely devastated. During the Dark Age, people descended from it only know their homeland is lost, not what actually happened to it; it's only once the Rediscovery's expeditions redraw the map that it becomes understood that Europe is literally gone, underwater. The Cevinese and the other northern peoples of the Africa-derived landmass (the "Fenes") carry migration-origin myths of a homeland across the water, warped over the generations but not false — they're descended from Europeans who fled south as Europe was sinking, which is also the source of Cevine's strong European character and influence.

## Positions on the final map

The base map (`maps/WORLD.png`, `maps/WORLD_elevation.npy`) was measured directly to find where each landmass ended up. By size, largest to smallest among the five non-polar continents:

| # | Continent | Share of world land | Centroid |
|---|---|---|---|
| — | Polar continent (#6) | ~40% | 79°S, 16°E |
| 1 | Lidia | ~31% | 48°N, 70°E |
| 2 | Réselia | ~20% | 3°N, 66°W |
| 3 | The Elsring continent | ~7.5% | 12°S, 169°W |
| 4 | Unnamed | ~1.4% | 3°N, 168°E |
| 5 | Unnamed | ~1.1% | 32°S, 176°E |

Lidia and Réselia being the two largest habitable landmasses fits their status as the Rediscovery's dominant powers. The Elsring continent being smaller than either fits its conquest by expeditions from both. Continents 4 and 5 are small — closer to large island groups than to Lidia's or Réselia's scale — which is consistent with their remaining unnamed and unvisited by the plot so far. The polar continent is by far the largest by area but is ice-locked and uninhabited.

These are raw measurements from the map, not narrative decisions — the numbers only fix relative size and rough position. Exact coastlines will still change once the base map is refined in Azgaar's Fantasy Map Generator.

## Open

- Names for continents 4 and 5
- Which continents were reached during the Rediscovery and which were already known
- Whether continents 4 and 5 are inhabited by peoples comparable to the Lidians and Réselians, or are less developed, or are colonial possessions
- Where each continent sits relative to the Almani Corridor and the Marreni Sea (not yet placed on the base map)
- **Pending map edit:** move the Elsring continent (currently the largest landmass, our working "Asia") further north, to increase its distance from Lidia/Réselia and reinforce why it was reached later and separately
- **Decided:** Lidia is the "America" continent (the Academy, Edward's marble homeland). Réselia is the "Africa" continent (Cevine, Parvaan, the Almani Corridor, the Fenes).
- **Pending fact to place:** traders from Lidia ("America") typically meet Réselia ("Africa") traders in East African ports, which is part of why a port like Ouspré is valuable. This still needs squaring with the size/centroid table above, which is stale (measured off an early map render, before most of the manual edits) and hasn't been recomputed against the final map yet
