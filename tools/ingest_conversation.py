#!/usr/bin/env python3
"""
Merge source/conversation_topics.json into indexes/master.json as a
cross-cutting "Conversation Starters" collection (modeled on the Core Library:
a view over items, not a home category).

Most conversation topics already exist in the library — those are FLAGGED in
place (conversation: true + a conversation_note) rather than duplicated. Items
that are genuinely new are added to their natural home hub and also flagged.

Idempotent. Usage:  python3 tools/ingest_conversation.py  (then generate.py)
"""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MASTER = os.path.join(ROOT, "indexes", "master.json")
SRC = os.path.join(ROOT, "source", "conversation_topics.json")
NOTES = os.path.join(ROOT, "source", "INGESTION_NOTES.md")

# Conversation titles that map to an existing item under a different title.
ALIAS = {
    "2026 ai index report": "artificial-intelligence-index-report-2024",
}

# Conversation titles that are genuinely new -> create with this home hub + extra fields.
NEW_ITEMS = {
    "Startup = Growth": {
        "category": "Founder Mental Models",
        "key_takeaways": [
            "A startup is a company designed to grow fast; growth rate is its defining metric.",
            "Small differences in weekly growth compound into radically different outcomes.",
            "Optimizing relentlessly for growth forces clarity about what users actually want.",
        ],
        "why_it_matters": "Gives a precise, widely-cited definition of what makes a startup a startup, anchoring how founders and investors reason about progress.",
        "usefulness": 9,
        "status": "recommended",
    },
    "Founder Mode": {
        "category": "Founder Mental Models",
        "key_takeaways": [
            "Founders may need to run companies more hands-on than conventional 'manager mode' advice allows.",
            "Blanket advice to fully delegate can hurt founder-led companies as they scale.",
            "The idea is hotly debated precisely because the right limits of founder involvement are unclear.",
        ],
        "why_it_matters": "Sparked a major Silicon Valley debate about how founders should lead as companies scale, shaping current management discourse.",
        "usefulness": 8,
        "status": "recommended",
    },
}


def norm_title(t):
    t = t.lower().replace("’", "'").replace("‘", "'")
    return re.sub(r"[^a-z0-9]+", "", t)


def slugify(text):
    s = re.sub(r"[^a-z0-9]+", "-", text.lower().replace("’", "")).strip("-")
    return re.sub(r"-+", "-", s)[:60].strip("-")


def norm_difficulty(val):
    if not val:
        return "Intermediate"
    f = val.split()[0].strip().capitalize()
    return f if f in ("Beginner", "Intermediate", "Advanced") else "Intermediate"


def main():
    m = json.load(open(MASTER, encoding="utf-8"))
    items = m["items"]
    ids = {i["id"] for i in items}
    by_norm = {norm_title(i["title"]): i for i in items}

    src = json.load(open(SRC, encoding="utf-8"))["items"]
    flagged, created = [], []

    for c in src:
        title = c["title"]
        note = c.get("why_it_is_a_good_conversation_topic", "")
        cval = c.get("conversation_value_score")
        nt = norm_title(title)

        target = None
        if nt in by_norm:
            target = by_norm[nt]
        elif title.lower() in ALIAS or norm_title(title) in {norm_title(k) for k in ALIAS}:
            key = next(k for k in ALIAS if norm_title(k) == nt or k == title.lower())
            target = next(i for i in items if i["id"] == ALIAS[key])

        if target:
            target["conversation"] = True
            target["conversation_note"] = note
            if cval is not None:
                target["conversation_value"] = cval
            flagged.append((title, target["id"]))
            continue

        # genuinely new item
        spec = NEW_ITEMS.get(title)
        if not spec:
            print(f"  WARNING: no match and no NEW_ITEMS spec for '{title}' — skipped")
            continue
        uid = slugify(title)
        n = 2
        while uid in ids:
            uid = f"{slugify(title)}-{n}"; n += 1
        ids.add(uid)
        item = {
            "id": uid,
            "title": title,
            "creator": c["creator_author_speaker_publisher"],
            "year": c["year"] if isinstance(c.get("year"), int) else None,
            "format": c.get("format", "Essay"),
            "category": spec["category"],
            "subcategory": c.get("subcategory", ""),
            "summary": c["summary"],
            "key_takeaways": spec["key_takeaways"],
            "why_it_matters": spec["why_it_matters"],
            "audience_fit": c.get("what_kind_of_people_would_discuss_it", ""),
            "difficulty": norm_difficulty(c.get("difficulty_level")),
            "tags": c.get("tags", []),
            "source_link": c.get("link"),
            "credibility": c.get("credibility_score", 8),
            "usefulness": spec["usefulness"],
            "status": spec["status"],
            "conversation": True,
            "conversation_note": note,
        }
        if cval is not None:
            item["conversation_value"] = cval
        item = {k: v for k, v in item.items() if v not in (None, "", [])}
        items.append(item)
        by_norm[norm_title(title)] = item
        created.append((title, uid))

    # register the cross-cutting hub if absent
    if not any(h["id"] == "conversation-starters" for h in m["hubs"]):
        m["hubs"].append({
            "id": "conversation-starters",
            "title": "Conversation Starters",
            "blurb": "High-signal topics worth raising in technical and founder circles — each is something smart people genuinely argue about. A cross-cutting collection; every item also lives in its home hub.",
        })

    m["meta"]["version"] = "1.7.0"
    json.dump(m, open(MASTER, "w", encoding="utf-8"), indent=2, ensure_ascii=False)

    note = ["", "---", "",
            "## Conversation Topics ingest (conversation_topics.json)",
            "",
            "Built as a cross-cutting 'Conversation Starters' hub (like Core Library).",
            f"- **Flagged existing items (no duplicates):** {len(flagged)}",
            f"- **New items created:** {len(created)}",
            ""]
    for t, i in flagged:
        note.append(f"- flag `{i}` — {t}")
    for t, i in created:
        note.append(f"- new `{i}` — {t}")
    with open(NOTES, "a", encoding="utf-8") as f:
        f.write("\n".join(note) + "\n")

    print(f"Flagged {len(flagged)} existing, created {len(created)} new. Total items {len(items)}.")


if __name__ == "__main__":
    main()
