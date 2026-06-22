# Tech Research Knowledge Base — Project Instructions & Standards

A curated, shareable library of foundational tech, AI, startup, design, engineering, and venture media for builders (founders, engineers, designers, operators, researchers).

## Golden rule
**`indexes/master.json` is the single source of truth.** Every card, hub, index, learning path, and export is *generated* from it. Never hand-edit generated files — edit the JSON and re-run the generator:

```bash
python3 tools/generate.py
```

## Repository structure
```
/source            raw, unprocessed JSON & markdown inputs (preserved as-is)
/kb/cards          one generated markdown card per item
/kb/topic-hubs     generated grouped category pages (+ core-library)
/indexes           master.json (truth), master.md, top-25.md, learning paths
/exports           shareable outputs: library.json, library.csv, digest.md
/tools             generate.py — builds everything from master.json
```

## Item schema (every field in `master.json` items[])
| field | notes |
|---|---|
| `id` | stable kebab-case slug; the filename of its card. Never reuse or rename casually. |
| `title` | preserve the original title exactly |
| `creator` | author / speaker / director / org |
| `year` | integer, or `null` if genuinely unknown (do not guess) |
| `format` | Paper, Essay, Book, Talk, Video, Video Series, Course, Documentary, Podcast Series, Reference |
| `category` | must exactly match a hub `title` |
| `subcategory` | free-text, kept short |
| `summary` | 2–3 factual sentences; no hype |
| `key_takeaways` | 3 concise bullets |
| `why_it_matters` | 1–2 sentences on durable significance |
| `audience_fit` | who it's for |
| `difficulty` | Beginner / Intermediate / Advanced |
| `tags` | 4–6 lowercase kebab tags |
| `source_link` | canonical URL, or `null` if no single stable link (e.g. most books). Never fabricate a URL. |
| `credibility` | 1–10 — source authority, primary vs secondary, institutional weight |
| `usefulness` | 1–10 — practical value to a builder today |
| `status` | `raw` → `reviewed` → `recommended` → `core` |

## Curation standards
- **Factual over hype.** Summaries describe; they don't sell.
- **Primary sources win.** Prefer original recordings, papers, and canonical hosts over recaps.
- **Rank ruthlessly.** Ranking signal = `credibility + usefulness` (core gets a +1 tie-break). See `score()` in `generate.py`.
- **Separate historical importance from current usefulness.** A 1968 demo can be cred 10 / useful 7 — that's correct, not a bug.
- **Never invent facts.** Unknown year → `null`. No canonical link → `null`. Approximate dates are flagged in prose (see `dieter-rams-ten-principles`).
- **Dedupe by canonicity.** When two items overlap, keep the most authoritative/primary one and fold the rest into its card.

## Status ladder
- `raw` — ingested, not yet reviewed.
- `reviewed` — checked, accurate, belongs in the library.
- `recommended` — strong, worth most people's time.
- `core` — essential. Surfaces in the Must-Watch Core Library and gets ranking priority.

## Adding or changing items
1. Edit `indexes/master.json` (add to `items[]`, or adjust scores/status).
2. If adding a new category, also add a matching hub in `hubs[]` (title must match item `category`).
3. Run `python3 tools/generate.py`. It runs integrity checks (unique ids, every category has a hub, every learning-path item exists) and fails loudly if something is inconsistent.
4. Commit the JSON change **and** the regenerated output together.

## Merging raw source files (the `/source` workflow)
Drop incoming JSON/markdown into `/source` untouched. Normalize each item into the schema above, dedupe against existing `items[]` (match on title/creator/link), score it, and append to `master.json`. Keep the raw file in `/source` as provenance. See `source/README.md`.

## Invariants the generator guarantees
- The master index always matches the card files (same generation pass).
- Learning paths only reference items that exist.
- Every item's category has a topic hub.
- Re-running is idempotent and safe.
