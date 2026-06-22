# 📚 Tech Research Knowledge Base

A curated, shareable library of the most foundational media for people who build technology — founders, engineers, designers, operators, and researchers.

It answers: *how does AI work, where did startups and the internet come from, what is good product and design sense, how do systems and venture really work* — through the canonical talks, papers, books, essays, and documentaries worth your time.

**142 curated items · 10 topic hubs · 6 learning paths.** Curated, not dumped.

---

## Start here

| If you want to… | Go to |
|---|---|
| See everything, organized | **[indexes/master.md](indexes/master.md)** |
| Read/watch the best first | **[indexes/top-25.md](indexes/top-25.md)** |
| Hit only the essentials | **[Must-Watch Core Library](kb/topic-hubs/core-library.md)** |
| Follow a structured path | [Beginner](indexes/beginner-path.md) · [Advanced Builder](indexes/advanced-path.md) · [Founder / Startup](indexes/founder-path.md) · [AI Engineering](indexes/ai-engineering-path.md) · [Product & Design](indexes/product-design-path.md) · [VC History](indexes/vc-history-path.md) |
| Send someone ONE file | **[exports/digest.md](exports/digest.md)** |
| Load it into a tool / sheet | [exports/library.json](exports/library.json) · [exports/library.csv](exports/library.csv) |

## Topic hubs
- [AI Foundations](kb/topic-hubs/ai-foundations.md) — how AI actually works
- [AI in Practice](kb/topic-hubs/ai-in-practice.md) — building with AI
- [Startup History](kb/topic-hubs/startup-history.md)
- [Founder Mental Models](kb/topic-hubs/founder-mental-models.md)
- [Product and Design](kb/topic-hubs/product-and-design.md)
- [Engineering and Systems](kb/topic-hubs/engineering-and-systems.md)
- [Venture Capital and Fundraising](kb/topic-hubs/venture-capital.md)
- [Internet and Big Tech History](kb/topic-hubs/internet-history.md)
- [Documentary and Long-Form Media](kb/topic-hubs/documentary-long-form.md)
- [Must-Watch Core Library](kb/topic-hubs/core-library.md)

## How it's built
Everything is generated from one source-of-truth file, **[`indexes/master.json`](indexes/master.json)**, by **[`tools/generate.py`](tools/generate.py)**. To change the library, edit the JSON and run:

```bash
python3 tools/generate.py
```

The generator runs integrity checks and rebuilds all cards, hubs, indexes, and exports so the library is always internally consistent. Standards and schema live in **[CLAUDE.md](CLAUDE.md)**.

## Have your own data to add?
Drop raw JSON/markdown into **[`/source`](source/)** and follow the merge workflow in [source/README.md](source/README.md). This library was seeded with a verified canonical core so your items merge cleanly into the same schema.

---
*Built to be handed to a teammate as-is. Scores and status reflect editorial judgment about signal, credibility, and usefulness to builders — see [CLAUDE.md](CLAUDE.md).*
