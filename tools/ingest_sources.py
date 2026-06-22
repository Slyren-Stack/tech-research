#!/usr/bin/env python3
"""
Normalize and merge the raw /source files into indexes/master.json.

This script encodes every curation decision (field mapping, category routing,
deduplication, and link backfills) so the merge is transparent and reproducible.
Run once after dropping new files in /source. It is idempotent: items already
present (matched by normalized title) are skipped, so re-running is safe.

After running, run tools/generate.py to rebuild all derived files.

Usage:  python3 tools/ingest_sources.py
"""

import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MASTER = os.path.join(ROOT, "indexes", "master.json")
SRC = os.path.join(ROOT, "source")
VIDEO = os.path.join(SRC, "curated_video_intelligence_archive.json")
VENTURE = os.path.join(SRC, "venture_studio_tech_intelligence_library.json")
NOTES = os.path.join(SRC, "INGESTION_NOTES.md")

# ----------------------------------------------------------------- decisions

# Drop these source items entirely. Each is a duplicate or a non-canonical
# fragment of an item we already keep (canonical version noted).
SKIP = {
    # video items folded into a more canonical kept item
    "video::Lecture 1 - How to Start a Startup":                         "→ how-to-start-a-startup-cs183b (full series)",
    "video::Lecture 2 - Team and Execution":                            "→ how-to-start-a-startup-cs183b (full series)",
    "video::The Hard Thing About Hard Things":                          "→ hard-thing-about-hard-things (book is canonical)",
    "video::The spelled-out intro to neural networks and backpropagation: building micrograd": "→ karpathy-zero-to-hero (course)",
    "video::Let's build GPT: from scratch, in code, spelled out":       "→ karpathy-zero-to-hero (course)",
    "video::CS229: Machine Learning Course":                            "→ andrew-ng-machine-learning",
    "video::CS231n Winter 2016: Lecture 4: Backpropagation, Neural Networks 1": "→ cs231n full course (venture)",
    "video::Natural Language Processing with Deep Learning Course":     "→ cs224n full course (venture)",
    "video::HAI Seminar with Nestor Maslej: Presenting the 2025 AI Index Report": "→ ai index report (venture)",
    "video::The Mother of All Demos":                                   "→ mother-of-all-demos (seed)",
    "video::The Lean Startup":                                          "→ the-lean-startup (book, venture)",
    "video::How To Talk To Your Customers (The Mom Test)":              "→ the-mom-test (book, venture)",
    "video::Continuous Discovery Habits":                              "→ continuous-discovery-habits (book, venture)",
    "video::Martin Fowler - Continuous Delivery":                      "→ continuous-delivery (essay, venture)",
    "video::The power of preparatory refactoring":                     "→ refactoring (book, venture)",
    "video::What is Design Thinking?":                                 "→ Tim Brown / IDEO design-thinking items (redundant explainer)",
    # venture items that duplicate an existing seed item
    "venture::Attention Is All You Need":                              "→ attention-is-all-you-need (seed)",
    "venture::The Hard Thing About Hard Things":                       "→ hard-thing-about-hard-things (seed)",
    "venture::Zero to One":                                            "→ zero-to-one (seed)",
    "venture::The Innovators":                                         "→ the-innovators-isaacson (seed)",
    "venture::The Design of Everyday Things":                          "→ design-of-everyday-things (seed)",
    "venture::Inspired":                                               "→ inspired-cagan (seed)",
    "venture::Triumph of the Nerds":                                   "→ triumph-of-the-nerds (seed)",
    "venture::CS229: Machine Learning":                                "→ andrew-ng-machine-learning (seed)",
    "venture::The Pragmatic Programmer: chapter on plain text / knowledge": "→ the-pragmatic-programmer (book)",
    "venture::Everyone Can Do Continuous Discovery":                   "→ continuous-discovery-habits (book)",
    "venture::YC's Essential Startup Advice":                          "→ yc-startup-library (superset)",
}

# Backfill canonical links onto existing seed items that lacked one.
BACKFILL_LINKS = {
    "hard-thing-about-hard-things": "https://www.harpercollins.com/products/the-hard-thing-about-hard-things-ben-horowitz",
    "zero-to-one":                  "https://www.penguinrandomhouse.com/books/234730/zero-to-one-by-peter-thiel-with-blake-masters/",
    "the-innovators-isaacson":      "https://www.penguinrandomhouse.com/books/617365/los-innovadores--the-innovators-by-walter-isaacson/",
    "design-of-everyday-things":    "https://mitpress.mit.edu/9780262525671/the-design-of-everyday-things/",
    "inspired-cagan":               "https://www.wiley.com/en-us/INSPIRED%3A+How+to+Create+Tech+Products+Customers+Love%2C+2nd+Edition-p-9781119387503",
    "triumph-of-the-nerds":         "https://www.pbs.org/nerds/",
}

# Per-item hub overrides (win over the category map below).
HUB_OVERRIDE = {
    "Artificial Intelligence Index Report 2024": "AI in Practice",
    "GPT-4 Technical Report": "AI in Practice",
    "OpenAI DevDay: Opening Keynote": "AI in Practice",
    "Software Is Changing (Again)": "AI in Practice",
    "Before the Startup": "Founder Mental Models",
    "How to Get Startup Ideas": "Founder Mental Models",
    "How Will You Measure Your Life?": "Founder Mental Models",
    "What You Do Is Who You Are": "Founder Mental Models",
    "Essays by Paul Graham": "Founder Mental Models",
    "Inside Apple Software Design": "Product and Design",
    "Shape Up": "Product and Design",
    "The Playbook: Lessons from 200+ Company Stories": "Documentary and Long-Form Media",
    "The Computer Chronicles - The Internet (1993)": "Documentary and Long-Form Media",
    "The Machine That Changed the World - Episode 1: Great Brains": "Documentary and Long-Form Media",
    "The Machine That Changed the World - Episode 2: Inventing the Future": "Documentary and Long-Form Media",
}

VIDEO_CAT = {
    "Startups & Founders": "Startup History",
    "AI & Machine Learning": "AI Foundations",
    "Product & Design": "Product and Design",
    "Engineering": "Engineering and Systems",
    "Internet & Computing History": "Internet and Big Tech History",
}
VENTURE_CAT = {
    "AI / ML": "AI Foundations",
    "History / Media": "Internet and Big Tech History",
    "Product / Design": "Product and Design",
    "Software / Engineering": "Engineering and Systems",
    "Startup / Business": "Startup History",
}

# Net-new items promoted to the must-watch core set.
CORE_TITLES = {
    "CS224N: Natural Language Processing with Deep Learning",
    "The Lean Startup",
    "The Mom Test",
    "The Innovator's Dilemma",
    "10 Usability Heuristics for User Interface Design",
    "Refactoring",
    "The Pragmatic Programmer",
    "Software Is Changing (Again)",
    "Continuous Discovery Habits",
    "Artificial Intelligence Index Report 2024",
}

# Explicit id assignments where slug would collide or needs disambiguation.
TITLE_ID = {
    "video::Do things that don't scale": "do-things-that-dont-scale-chesky",
}

# ----------------------------------------------------------------- helpers
def slugify(text):
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return re.sub(r"-+", "-", s)[:60].strip("-")


def parse_year(val):
    if isinstance(val, int):
        return val
    if isinstance(val, str):
        m = re.search(r"\b(19|20)\d{2}\b", val)
        if m:
            return int(m.group(0))
    return None


def norm_difficulty(val):
    if not val:
        return "Intermediate"
    first = val.split()[0].strip().capitalize()
    return first if first in ("Beginner", "Intermediate", "Advanced") else "Intermediate"


def status_for(title, cred, useful):
    if title in CORE_TITLES:
        return "core"
    return "recommended" if (cred + useful) >= 17 else "reviewed"


def hub_for(title, base_cat):
    return HUB_OVERRIDE.get(title, base_cat)


# ----------------------------------------------------------------- normalize
def from_video(it):
    title = it["title"]
    base = VIDEO_CAT.get(it["category"], "Startup History")
    cred, useful = it["credibility_score"], it["usefulness_score"]
    return {
        "id": None,
        "title": title,
        "creator": it["speaker_creator"],
        "year": parse_year(it.get("year")),
        "format": it.get("format", "Video"),
        "category": hub_for(title, base),
        "subcategory": it.get("subcategory", ""),
        "summary": it["summary"],
        "key_takeaways": it.get("core_ideas", [])[:4],
        "why_it_matters": it.get("why_it_matters", ""),
        "audience_fit": it.get("target_audience", ""),
        "difficulty": norm_difficulty(it.get("difficulty")),
        "tags": it.get("tags", []),
        "source_link": it.get("link"),
        "credibility": cred,
        "usefulness": useful,
        "status": status_for(title, cred, useful),
        "venue": it.get("source_event_channel"),
        "runtime": it.get("runtime"),
    }


def from_venture(it):
    title = it["title"]
    base = VENTURE_CAT.get(it["category"], "Startup History")
    cred, useful = it["credibility_score"], it["usefulness_score"]
    return {
        "id": None,
        "title": title,
        "creator": it["author_creator"],
        "year": parse_year(it.get("year")),
        "format": it.get("format", "Reference"),
        "category": hub_for(title, base),
        "subcategory": it.get("subcategory", ""),
        "summary": it["summary"],
        "key_takeaways": it.get("key_ideas", [])[:4],
        "why_it_matters": it.get("why_important", ""),
        "audience_fit": it.get("who_for", ""),
        "difficulty": norm_difficulty(it.get("difficulty")),
        "tags": it.get("tags", []),
        "source_link": it.get("link"),
        "credibility": cred,
        "usefulness": useful,
        "status": status_for(title, cred, useful),
        "venue": it.get("source"),
    }


# ----------------------------------------------------------------- main
def main():
    master = json.load(open(MASTER, encoding="utf-8"))
    existing = master["items"]
    existing_ids = {i["id"] for i in existing}
    existing_titles = {i["title"].strip().lower() for i in existing}

    video = json.load(open(VIDEO, encoding="utf-8"))
    venture = json.load(open(VENTURE, encoding="utf-8"))["items"]

    added, skipped, backfilled = [], [], []

    # backfill links onto existing seed items
    for i in existing:
        if i["id"] in BACKFILL_LINKS and not i.get("source_link"):
            i["source_link"] = BACKFILL_LINKS[i["id"]]
            backfilled.append(i["id"])

    def consider(src_tag, raw, normf):
        key = f"{src_tag}::{raw['title']}"
        if key in SKIP:
            skipped.append((key, SKIP[key]))
            return
        norm = normf(raw)
        if norm["title"].strip().lower() in existing_titles:
            skipped.append((key, "→ duplicate of existing item (title match)"))
            return
        # assign id
        wanted = TITLE_ID.get(key) or slugify(norm["title"])
        uid, n = wanted, 2
        while uid in existing_ids:
            uid = f"{wanted}-{n}"
            n += 1
        norm["id"] = uid
        existing_ids.add(uid)
        existing_titles.add(norm["title"].strip().lower())
        # drop empty optional fields
        norm = {k: v for k, v in norm.items() if v not in (None, "", [])}
        existing.append(norm)
        added.append(norm)

    for raw in video:
        consider("video", raw, from_video)
    for raw in venture:
        consider("venture", raw, from_venture)

    master["meta"]["last_updated"] = "2026-06-23"
    master["meta"]["version"] = "1.1.0"
    json.dump(master, open(MASTER, "w", encoding="utf-8"), indent=2, ensure_ascii=False)

    # write a human-readable provenance note
    lines = [
        "# Ingestion Notes",
        "",
        "Auto-generated by `tools/ingest_sources.py`. Records how the raw `/source` files were merged.",
        "",
        f"- **Items added:** {len(added)}",
        f"- **Items skipped (dedup/fold):** {len(skipped)}",
        f"- **Existing items backfilled with links:** {len(backfilled)} ({', '.join(backfilled)})",
        f"- **Total items now in master.json:** {len(existing)}",
        "",
        "## Added",
        "",
    ]
    for a in added:
        lines.append(f"- `{a['id']}` — {a['title']} → {a['category']} ({a['status']})")
    lines += ["", "## Skipped (with rationale)", ""]
    for key, why in skipped:
        lines.append(f"- {key}  {why}")
    open(NOTES, "w", encoding="utf-8").write("\n".join(lines) + "\n")

    print(f"Added {len(added)}, skipped {len(skipped)}, backfilled {len(backfilled)}. "
          f"Total now {len(existing)}. See source/INGESTION_NOTES.md")


if __name__ == "__main__":
    main()
