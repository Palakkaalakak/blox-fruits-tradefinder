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

**How I actually work, learned over a long session — read this carefully:**

- **Use the quiz tool (multiple-choice, my recommendation marked, batched 1–3 per round) as the default way to move worldbuilding forward.** This worked far better than open questions or than you just proposing an answer. When I say "quiz" or "let's continue," that's the format I mean, and I'll usually keep saying "continue" round after round — keep going with more quiz rounds on the same topic until I say to move on or say "let's move on," rather than stopping after one round.
- **After I answer a quiz round, log the answer into the right doc file and commit/push immediately, then optionally react to the new lore with genuine interest** — what's interesting about it, what it connects to, what it changes — not a graded evaluation of the answer ("this is stronger than the other one") unless I specifically ask you to compare or critique. I've corrected you on this exact thing before.
- **I self-correct and contradict my own prior instructions sometimes** (e.g., I've said "let's move on" then immediately clarified I meant staying on the same topic). Read my most recent clarification as authoritative, and if genuinely ambiguous, it is fine to ask rather than guess — but don't guess and then insist you were right when I push back. If I say you got something wrong, assume I'm right and fix it rather than re-litigating.
- **I get real, sharp anger when you (a) assert something as fact that isn't actually established, (b) add unprompted dramatic/rhetorical flourish to reference docs, (c) contradict yourself and don't own it plainly, or (d) keep making the same category of mistake after being corrected once.** When corrected, fix it cleanly and briefly — don't over-apologize, don't re-explain at length, don't hedge. Just fix it and show the fix.
- **Sweep for related inconsistencies, not just the one flagged.** Several times this session, fixing one error surfaced 2-3 other stale references to the same wrong fact elsewhere in the repo (e.g. "Age of Heroes," Latin/Greek as scholarly language, "~1,000 years" vs the later-revised "~800 years"). After any correction, grep the repo for the old wrong phrasing before considering the fix done.
- **I make final calls on ambiguous or ret-conned things fast and expect them acted on immediately** — e.g. changing the manuscript's own stated figures ("it's my manuscript, I'll change it to 800"), fixing wrong geography I never actually said, renaming or reassigning things. Don't push back on this kind of authorial decision; just execute it and propagate the change everywhere it appears.
- **I like maximal token efficiency and minimal ceremony** in ongoing work: small targeted edits over full-file rewrites, commit+push without asking permission each time (I've never objected to this), short replies over long ones once we're in a working rhythm — save the longer, more considered replies for genuinely new topics or when I explicitly ask for discussion/opinion.

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
