# Handoff — context for continuing this work with another assistant

Paste the section below into a new conversation, in a session that has access to this repository. It tells the assistant what the project is, where the actual facts live, and how to work — it does not repeat the facts themselves, since those are already committed to the repo and would go stale here.

---

## Paste from here

I am writing **JR** (working title), the first book of a series, set on Earth roughly fifteen hundred years after a catastrophe called **the Doom**. I have a partial manuscript and am building out the world: history, geography, peoples, states, houses. This repository's docs are reference material, not the manuscript itself.

**Before doing anything else, read these files in full, in this order** — they contain the actual established canon, and are more current and authoritative than any summary I or a prior assistant could give you:

1. `07-reference/canon-from-manuscript.md` — what's directly evidenced from the manuscript text itself (locked, can't be contradicted without a rewrite)
2. `01-cataclysm/the-doom.md` and `01-cataclysm/the-lost-continent.md` — the Doom's mechanism and Europe's fate
3. `02-geography/continents.md` and `02-geography/world-structure.md` — the map, the continents, Cevine, Parvaan, the Corridor, the Marreni Sea
4. `04-history/chronology.md` — the full era-by-era timeline (Dark Age through present), this is the single densest and most current file
5. `03-peoples/` and `05-states/` — languages, peoples, political/economic structure
6. `07-reference/seeded-mysteries.md` and `07-reference/OPEN-QUESTIONS.md` (or `01-cataclysm/OPEN-QUESTIONS.md`) — what's deliberately still undecided

Every one of these files is kept current — when a fact changes, the file is edited and committed, not left stale. Trust the files over anything else, including anything you think you remember about this project from elsewhere.

**Working style, this matters a lot:**

- **Plain, factual, complete prose only.** Normal sentences and paragraphs. No dramatic fragments, no rhetorical flourishes, no tricolons or parallel-clause rhythm for effect, no restating a point for emphasis, no editorializing about how an event "is remembered/taught/felt" unless I've explicitly said so. If you catch yourself writing something that sounds like it's trying to sound like a real historian or trying to sound literary, stop and flatten it.
- **Don't invent facts.** Where a decision is genuinely open, ask me — the established working pattern is a short multiple-choice quiz (2–4 options per question, my recommendation marked, batched 1–3 questions at a time), not an open-ended question and not you picking an answer for me.
- **Log answers immediately.** When I answer a quiz or state a new fact, write it into the correct existing doc file right away (small, targeted edits — don't rewrite whole files) and commit + push it before moving on. Don't let facts pile up unsaved in the conversation.
- **Verify before asserting continuity.** Several real errors happened this way earlier: claiming two things were geographically linked when they weren't (Lidia/Réselia falsely described as one torn continent), reusing a name inconsistently, or introducing something dramatic that I never said. Before stating a "fact," check it actually appears in the docs or in what I just said.
- **Some things are deliberately deferred** — don't answer these unless I explicitly ask: Queen Renilda's murderer, who proposed the Academy, the philosophical framework referred to as "Laurevinism" (not to be mentioned at all until I raise it), and the Azgaar Fantasy Map Generator integration / further map-tooling work (built and working, paused on purpose).
- **The map toolchain** lives in `maps/` (`generate_world.py`, `rearrange.py`, `build_world.py`, `physics.py`) and the current frozen/approved base map is `maps/WORLD_sundered_shifted_elevation.npy` with its renders. Do not regenerate or reshape the map without being asked — it took a long, carefully hand-verified process to reach its current state, and past mistakes here (accidentally reshaping a continent while only meaning to touch the ocean nearby, silently fusing two landmasses) were costly to fix. If asked to edit it, use direct array manipulation with explicit before/after verification (connected-component counts, pixel-overlap checks, distance checks), not full pipeline regeneration.

Please continue helping me build this world from here, following everything above.

## Paste to here

---

## Notes for me (not for pasting)

This file is deliberately a pointer, not a fact-dump — the facts live in the numbered doc directories and change over time, so duplicating them here would just create a second copy that goes stale. If a future me is tempted to paste a big fact-summary back into this file "for safety," don't — fix whichever real doc is missing the fact instead.

Current open decisions, roughly in priority order — see `04-history/chronology.md` and `02-geography/*.md` "Open" sections for the full, current list, but as of the last time this file was touched:

1. Religion/faith systems — largely undefined
2. The Elsring's own culture/society/government before extermination
3. Present-day military/state structure in detail
4. Which Elsring lands are free vs. still colonized, and by which Houses
5. Names: the third continent, its oceans, the two remaining unnamed continents
6. Economy/currency detail beyond the existing council/economy doc
7. Robert's exact parentage (Karois side vs. Marain side)
8. Renilda's murderer / Academy's proposer — explicitly deferred, do not answer without being asked
9. Resuming the Azgaar map integration — explicitly deferred
