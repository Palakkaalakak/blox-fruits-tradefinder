# The Drowned Fractures

**The single most distinctive physical feature of this world.**

When the crust gave way during the Doom, it did not open a handful of great rifts. It **crazed** — like a dropped pane of glass, a web of cracks propagating through everything at once. And then the sea rose into every one of them.

What remains, fifteen centuries later, is a network of narrow saltwater channels burrowing through the land like roots. Not a few great seaways. **Everywhere.**

## There is no continuous landmass anywhere in the world

This is the load-bearing consequence, and it should never be softened.

**A "continent" in this world is not a solid body of land. It is a cluster** — hundreds of fragments packed tightly together, separated by channels narrow enough to see across and deep enough to drown in. What makes a continent a continent is that its pieces are *close*, not that they are joined.

So:

- You cannot walk across a continent. Nobody in the history of the world has ever walked across a continent.
- Every journey of any length is a sequence of crossings.
- The largest single piece of dry land anyone has ever stood on is measured in a few days' walk, not weeks.
- "Mainland" is a relative word here. There is no mainland. There is only bigger and smaller.
- The word *island* is close to meaningless — everywhere is an island — so the language would not lean on it. There'll be a native vocabulary for *sizes* of fragment instead, the way Arabic has many words for camel.

The distinction that matters: the fractures do not *erode the shores*. They **cut clean through the land** — interior plains as readily as coasts. The crust parted, and it did not care what farmland or forest was standing on top of it.

With one exception, and it is the important one: **the mountains.** See below.

## They are straight

Fractures do not meander. **Brittle material breaks in straight lines that meet at angular junctions**, enclosing polygonal fragments — crazed glass, dried mud, cracked rock, cooling basalt. Every one of those breaks the same way, and so did the crust.

This is what makes the world unmistakable at a glance, and it's the opposite of how a river system looks. A river wanders because water follows the path of least resistance across a gradient over ages. A fracture is a *failure*: it propagates in an instant along the line of greatest stress, and that line is straight.

So the map reads as a shattered pane. Fragments are angular. Coasts have long straight runs meeting at sharp corners. Channels cross one another at abrupt angles instead of merging in smooth confluences. Nothing curves except where a fracture happens to open onto the old, water-worn coastline of the world before.

*(In generation terms: the network is built from Voronoi cell walls, not noise. Several earlier attempts used ridged noise and produced meandering root-like curves — the wrong model, and no amount of tuning made it look fractured. The lesson generalises: match the algorithm to the physics you're imitating.)*

## They are not rivers

This is the point, and it should be established early and never explained twice.

They *look* like river systems: branching, meandering, joining and dividing, threading from the coast deep into the interior. They are nothing of the kind.

| A river | A fracture |
|---|---|
| Fresh | **Salt** |
| Rises in high ground | **Has no source** |
| Flows to the sea | **Is the sea** |
| Runs one way | **Does not flow — it tides** |
| Cuts its own valley over ages | **Was opened in an afternoon** |
| Deposits silt, builds deltas | **Deposits nothing; the walls are raw rock** |

A fracture has no upstream. Follow one inland far enough and it simply ends — a dead channel of still salt water against a rock face, going nowhere. Follow another and it comes out on the far coast, having cut clean through a continent.

## What this does to the world

**Fresh water is the scarce thing.** In a land veined with salt, the wells and the true rivers off the mountains are the valuable ground. **Settlements sit where fresh water meets a fracture** — that is the whole logic of where towns are in this world, and it is a rule you can apply consistently without thinking about it again.

**Everything travels by boat.** A continent laced with navigable salt channels is a continent where the road network is water. Small craft go everywhere. This suits a world of trade and chokepoints, explains why a naval power became paramount on a *continent* rather than merely at sea, and means an army's problem is never distance but crossings.

**Every fracture is a border and a chokepoint.** A hundred-odd realms in a landscape sliced into fragments — of course the map is fragmented. The Dark Age produced power at the scale of whatever one strong family could hold, and the fractures decided how big that was. **The political map is the fracture map.** This is why the world has hundreds of states and no empire ever finished the job.

**Bridges are enormous.** A bridge over a tidal salt channel is infrastructure, strategy and status at once. Who built it, who maintains it, who may cross it, and what happens when it is dropped.

**The mountains are the only unbroken ground.** Fractures deflect around a mountain root rather than crossing it — the crack front takes the weakness, and a range is not weak. So the highlands came through the Doom whole, and they are the only places in the world where you can travel any distance without a boat.

That inverts the usual logic of terrain completely. In our world mountains are the barrier and the lowland is the road. **Here the mountains are the roads** — the only continuous land in existence — and the fertile lowlands are the impassable part, diced into fragments by salt channels. Highland routes are therefore strategic in a way no lowland road can be: an army that wants to march rather than sail must go up. Passes are worth more than ports to anyone without a fleet. And the peoples of the high country are the only ones who have never needed boats, which will have made them very strange to everybody else.

**The land remembers the disaster in its shape.** Nobody has to be told what the fractures are. Everyone knows. It is simply the shape of the world — the Doom written across every continent, so ubiquitous that no one sees it any more. Which is exactly how real trauma sits in a landscape.

## Texture to draw on

- Tides running inland for hundreds of miles, twice a day, in channels with no current of their own
- Salt marsh and dead ground where a fracture floods its margins
- Fishing villages a thousand miles from open ocean, catching sea fish
- Dead-end channels: still, deep, saltwater culs-de-sac. Places to hide things
- Fracture-mouths as natural harbours — most great cities will sit on one
- The first crossing of a major fracture as a founding legend
- Winter ice in northern fractures closing a realm's arteries for months
- Something drowned in a fracture during the Doom, still down there, in salt water that preserves

## Open

- How wide, typically? (Generated narrow — hundreds of metres to a few miles. Crossable but not casually.)
- Are they deepening, silting, or stable? Ties to the unresolved "is the Doom over?" argument
- Is there a word for them in-world? It should be an ordinary, worn-down word — people do not use grand names for the ordinary shape of their own country
- Do the Elsring use them? A network of deep salt channels reaching under every continent is an interesting thing for a subterranean people to live beside

---

*Generated by the `fracture_network` stage in `maps/generate_world.py`: Voronoi cell walls from a jittered polar lattice of nuclei laid out around **each continent's own centre**, so cracks radiate outward per landmass. Many small cells, so each cut is a short straight segment and chains of them describe curves. The field is then warped up the local elevation gradient so fractures deflect around mountain roots, and cut dead above the ridge threshold so no crack survives on high ground.*

*Tunable: `--crazing` (density), `--crazing-cells` (how short each cut is), `--crack-width` (channel width), `--crack-smoothing` (junction rounding), `--mountain-avoidance` (how hard they deflect).*
