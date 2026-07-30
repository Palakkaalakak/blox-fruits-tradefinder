# Handoff — context for continuing this work with another assistant

Paste the section below into a new conversation. It contains everything an assistant needs to pick up the worldbuilding without re-deriving it.

---

## Paste from here

I am writing **JR** (working title), the first book of a series. It is set on **Earth**, roughly fifteen hundred years after a catastrophe called **the Doom**, which reshaped the planet. I have a partial manuscript and I am building out the world: history, geography, peoples, states and houses. The story is not being written in these documents — they are reference material, so I want **plain, factual, complete prose**: normal sentences and paragraphs, no dramatic fragments, no rhetorical flourishes, no summarising a point and then restating it for effect.

**The premise.** The Doom was not one disaster but a coincidence of several ordinary ones occurring within the same few decades: a geomagnetic reversal that was already overdue and already underway, an oceanic impact, the tsunami after it, a decade or more of impact winter, and the failure of crust that was already strained. Each was survivable alone; together they were not, because every redundancy assumed the others still worked. The key consequence is that **recorded knowledge survived but the capacity to use it did not** — books need a shelf, factories need ore, fuel, power and a trained workforce. The bottleneck in the centuries afterwards was never understanding; it was means.

**Important precision about the magnetic reversal.** It is the ordinary periodic kind, long overdue for Earth. It is *not* a physical movement of the planet: the rotation axis does not shift, no continent changes latitude, no climate zone moves. Real reversals take 2,000–12,000 years, with the field weakening and wandering throughout, so there is no reliable magnetic north for centuries. Its effects are navigational and biological — useless compasses, a thinned magnetosphere, tropical aurorae, and the collapse of migrations among animals that navigate magnetically. **It does not cause the climate catastrophe**; the impact winter does.

**Why the world had to be rediscovered.** The impact rearranged the map, and communication between regions failed completely for centuries. By the time ships were being built again and compasses could be trusted, people sailing out were finding places they did not know existed. Only ancestors several centuries dead had known the true geography of the old Earth, and what survives of that knowledge exists in manuscripts held almost entirely by the wealthier families — so an accurate account of the old world is effectively private property.

**Geography.** There are **six continents plus a seventh that is submerged**. Three are named: **Lidia** and **Réselia** (the two that retained firearms through the collapse, by luck of where their industry happened to be), and the **third continent**, home of the Elsring, which carries two competing names. Three continents are unnamed, one of them polar and effectively uninhabited. The seventh drowned in the Doom and never resurfaced; since this is Earth and the Doom drowned land, its existence follows as arithmetic rather than invention.

**Lidia and Réselia are CONTINENTS, not countries.** This gets misclassified constantly. Calling someone Lidian or Réselian is like calling someone European — it identifies a landmass and little else. Each contains many sovereign states.

**Key places.** The **Almani Corridor** is a strait, the only practical passage between two continents, and the world's main chokepoint. **Cevine** is the paramount power, a naval state on the Venetian model but with the mass and manpower of France, holding both shores of the Corridor; its monarchs sit the **Throne of Thalassus**; the first villages after the Doom arose there and grew into it. **Parvaan** seceded from Cevine about fifteen years ago and was given the **Port of Ouspré** as a gesture of goodwill — a good but not major port, calibrated to be believable — which was in fact a deliberate vector for the **sevaravirus** plague that killed roughly a third of its people. The **Marreni Sea**, in the south, is the impact crater; compasses fail over it because of the magnetic anomaly in the rock, which conveniently explains a line already in the manuscript about sailors losing their way there.

**Technology and society.** Technology is modern — aircraft, vaccines, cyber-attacks, wristwatches — while the political order is feudal, with kings, dukes, household guards and direct vassals. The reason is that technology recovered quickly and society did not: in the collapse, the families that became richest and strongest locally became the aristocracy, exactly as happened in our own history, and no later technological advance displaced them because each one simply made the incumbents richer. There are roughly 100–200 sovereign states, in layered tiers.

**The Elsring.** The native people of the third continent, destroyed during the Rediscovery about a thousand years ago by disease, dispossession and firearms. **This is a footnote, not a theme.** It is regarded today the way the fate of the Native Americans is regarded in ours: known, taught, discussed, and productive of no action whatsoever. It should not be inflated into a central moral engine. It may become important in a later book if I decide to bring them back, but that decision has not been made.

**Do not mention or incorporate any philosophical framework.** I have one and it will be introduced later. For now, build the world on its own terms.

**The Academy**, where the book is set, was founded by a near-unanimous Great Council of the world's rulers after the murder of **Queen Renilda**, to raise the heirs of the world together. Sixty students, three classes named for colours, on the continent of Lidia. The Council met once and has never met again.

**Maps.** I have a Python toolchain that generates the world map from real Earth elevation data (ETOPO1) by applying the Doom's effects, with impact scaling laws, ejecta falloff and lithospheric flexure computed properly. There is also a version using real plate-tectonics simulation, and a version built from fantasy-cartography principles. The intended workflow is: generate a base, refine it in Azgaar's Fantasy Map Generator (which handles rivers, biomes, climate and states), then hand-edit the features the story requires — chiefly the Almani Corridor, which no generator will produce by chance. A design goal is that the map should retain a **faint** resemblance to the real continents, recognisable on close study but not at a glance.

Please continue helping me build this world. Ask me questions where decisions are needed rather than inventing answers, and keep the register factual.

## Paste to here

---

## Notes for me (not for pasting)

Current open decisions, roughly in priority order:

1. Names for continents 4, 5 and 6, and for the third continent's two competing names
2. Which of the six continents were known before the Rediscovery and which were found during it
3. How many realms sit on each continent, and which are ex-colonies
4. The identity of Queen Renilda's murderer, and who proposed the Academy
5. Where each continent sits relative to the Almani Corridor and the Marreni Sea
6. Choosing a final base map from the candidates in `maps/`
