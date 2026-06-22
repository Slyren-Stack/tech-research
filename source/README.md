# /source — raw inputs

Drop raw, unprocessed JSON and markdown here, **exactly as received**. Nothing in this folder is edited or deleted — it's the provenance trail for the curated library.

> **Current contents:** two raw datasets (`curated_video_intelligence_archive.*` and `venture_studio_tech_intelligence_library.*`) have been ingested via `tools/ingest_sources.py`. See [`INGESTION_NOTES.md`](INGESTION_NOTES.md) for exactly what was added, skipped (deduped), and backfilled. The raw files are preserved here as provenance.

## Merge workflow
For each raw file you add:

1. **Keep the original here untouched** (rename to something descriptive if helpful, e.g. `2026-06-export-from-notion.json`).
2. **Normalize** each item into the standard schema (see [`../CLAUDE.md`](../CLAUDE.md)):
   `id, title, creator, year, format, category, subcategory, summary, key_takeaways, why_it_matters, audience_fit, difficulty, tags, source_link, credibility, usefulness, status`.
3. **Dedupe** against existing `items[]` in `indexes/master.json` — match on title + creator + source link. When two items overlap, keep the most canonical/primary one; fold extra detail into its card; drop the rest.
4. **Score** credibility (1–10) and usefulness (1–10), and set `status` (`raw`/`reviewed`/`recommended`/`core`).
5. **Append** the normalized items to `indexes/master.json`. New `id`s must be unique kebab-case slugs. If you introduce a new `category`, add a matching hub in `hubs[]`.
6. **Regenerate:** `python3 tools/generate.py`. It validates and rebuilds everything. Fix any assertion errors it reports.
7. **Commit** the raw file, the `master.json` change, and regenerated output together.

## Notes
- Don't fabricate missing facts. Unknown year → `null`. No stable link → `null`.
- New items should enter as `raw` or `reviewed` until verified, then be promoted.
