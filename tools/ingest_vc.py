#!/usr/bin/env python3
"""
Normalize and merge source/vc_history_intelligence_archive.json into
indexes/master.json. All items route to the "Venture Capital and Fundraising"
hub, using the archive's section names as subcategories.

Idempotent: items already present (matched by normalized title) are skipped.
Appends a provenance section to source/INGESTION_NOTES.md.

Usage:  python3 tools/ingest_vc.py   (then run tools/generate.py)
"""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MASTER = os.path.join(ROOT, "indexes", "master.json")
VC = os.path.join(ROOT, "source", "vc_history_intelligence_archive.json")
NOTES = os.path.join(ROOT, "source", "INGESTION_NOTES.md")

HUB = "Venture Capital and Fundraising"

# Net-new items promoted to the must-watch core set (kept tight).
CORE_TITLES = {
    "VC: An American History",
    "The Power Law: Venture Capital and the Making of the New Future",
    "The Money of Invention: How Venture Capital Creates New Wealth",
}


def slugify(text):
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return re.sub(r"-+", "-", s)[:60].strip("-")


def norm_difficulty(val):
    if not val:
        return "Intermediate"
    first = val.split()[0].strip().capitalize()
    return first if first in ("Beginner", "Intermediate", "Advanced") else "Intermediate"


def status_for(title, cred, useful):
    if title in CORE_TITLES:
        return "core"
    return "recommended" if (cred + useful) >= 17 else "reviewed"


def normalize(it):
    title = it["title"]
    cred, useful = it["credibility_score"], it["usefulness_score"]
    return {
        "id": None,
        "title": title,
        "creator": it["creator_or_publisher"],
        "year": it["year"] if isinstance(it.get("year"), int) else None,
        "format": it.get("format", "Reference"),
        "category": HUB,
        "subcategory": it.get("category", ""),  # archive section name reads well as subcategory
        "summary": it["summary"],
        "key_takeaways": it.get("key_themes", [])[:4],
        "why_it_matters": it.get("why_it_matters", ""),
        "audience_fit": it.get("audience_fit", ""),
        "difficulty": norm_difficulty(it.get("difficulty")),
        "tags": it.get("tags", []),
        "source_link": it.get("link"),
        "credibility": cred,
        "usefulness": useful,
        "status": status_for(title, cred, useful),
    }


def main():
    master = json.load(open(MASTER, encoding="utf-8"))
    items = master["items"]
    ids = {i["id"] for i in items}
    titles = {i["title"].strip().lower() for i in items}

    raw = json.load(open(VC, encoding="utf-8"))["items"]
    added, skipped = [], []

    for r in raw:
        norm = normalize(r)
        if norm["title"].strip().lower() in titles:
            skipped.append(norm["title"])
            continue
        uid, base, n = slugify(norm["title"]), slugify(norm["title"]), 2
        while uid in ids:
            uid = f"{base}-{n}"
            n += 1
        norm["id"] = uid
        ids.add(uid)
        titles.add(norm["title"].strip().lower())
        norm = {k: v for k, v in norm.items() if v not in (None, "", [])}
        items.append(norm)
        added.append(norm)

    master["meta"]["version"] = "1.6.0"
    json.dump(master, open(MASTER, "w", encoding="utf-8"), indent=2, ensure_ascii=False)

    note = [
        "",
        "---",
        "",
        "## VC History archive ingest (vc_history_intelligence_archive.json)",
        "",
        f"- **Added:** {len(added)} → all routed to '{HUB}'",
        f"- **Skipped (title dup):** {len(skipped)}{' — ' + ', '.join(skipped) if skipped else ''}",
        "",
    ]
    for a in added:
        note.append(f"- `{a['id']}` — {a['title']} ({a['subcategory']}, {a['status']})")
    with open(NOTES, "a", encoding="utf-8") as f:
        f.write("\n".join(note) + "\n")

    print(f"Added {len(added)}, skipped {len(skipped)}. Total items now {len(items)}.")


if __name__ == "__main__":
    main()
