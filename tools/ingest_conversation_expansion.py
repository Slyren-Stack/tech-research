#!/usr/bin/env python3
"""
Merge source/conversation_topics_expansion.json into indexes/master.json.

Entries are already in the master item schema plus conversation fields.
- flag_only:true  -> match an existing item by title; attach conversation
                     fields only (no new card, no duplication).
- otherwise       -> append as a new item in its natural home hub, flagged
                     as a conversation starter.

Idempotent (dedupes by normalized title). Usage:
  python3 tools/ingest_conversation_expansion.py   (then generate.py)
"""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MASTER = os.path.join(ROOT, "indexes", "master.json")
SRC = os.path.join(ROOT, "source", "conversation_topics_expansion.json")
NOTES = os.path.join(ROOT, "source", "INGESTION_NOTES.md")


def norm(t):
    return re.sub(r"[^a-z0-9]+", "", t.lower().replace("’", "'"))


def slugify(t):
    s = re.sub(r"[^a-z0-9]+", "-", t.lower().replace("’", "")).strip("-")
    return re.sub(r"-+", "-", s)[:60].strip("-")


CONV_FIELDS = ("conversation", "conversation_note", "conversation_value")


def main():
    m = json.load(open(MASTER, encoding="utf-8"))
    items = m["items"]
    ids = {i["id"] for i in items}
    by_norm = {norm(i["title"]): i for i in items}

    src = json.load(open(SRC, encoding="utf-8"))
    # carry the synthesis line into meta for the generator to render
    if src.get("conversation_synthesis"):
        m["meta"]["conversation_synthesis"] = src["conversation_synthesis"]

    flagged, created, warned = [], [], []

    for e in src["items"]:
        title = e["title"]
        target = by_norm.get(norm(title))

        if e.get("flag_only"):
            if not target:
                warned.append(title)
                continue
            target["conversation"] = True
            target["conversation_note"] = e.get("conversation_note", "")
            if e.get("conversation_value") is not None:
                target["conversation_value"] = e["conversation_value"]
            flagged.append((title, target["id"]))
            continue

        if target:  # already present -> flag in place rather than duplicate
            target["conversation"] = True
            target["conversation_note"] = e.get("conversation_note", "")
            if e.get("conversation_value") is not None:
                target["conversation_value"] = e["conversation_value"]
            flagged.append((title, target["id"]))
            continue

        uid, n = slugify(title), 2
        while uid in ids:
            uid = f"{slugify(title)}-{n}"; n += 1
        ids.add(uid)
        item = {k: v for k, v in e.items() if k != "flag_only"}
        item["id"] = uid
        item["conversation"] = True
        item = {k: v for k, v in item.items() if v not in (None, "", [])}
        items.append(item)
        by_norm[norm(title)] = item
        created.append((title, uid))

    m["meta"]["version"] = "1.8.0"
    json.dump(m, open(MASTER, "w", encoding="utf-8"), indent=2, ensure_ascii=False)

    note = ["", "---", "",
            "## Conversation Topics expansion (conversation_topics_expansion.json)",
            "",
            "Ruthlessly-ranked SV conversation map. New topics added to home hubs and flagged; "
            "existing library items flagged in place (no duplicates).",
            f"- **New items created:** {len(created)}",
            f"- **Existing items flagged:** {len(flagged)}",
            (f"- **WARNINGS (flag_only with no match):** {', '.join(warned)}" if warned else "- No warnings."),
            ""]
    for t, i in created:
        note.append(f"- new `{i}` — {t}")
    for t, i in flagged:
        note.append(f"- flag `{i}` — {t}")
    with open(NOTES, "a", encoding="utf-8") as f:
        f.write("\n".join(note) + "\n")

    total_conv = sum(1 for i in items if i.get("conversation"))
    print(f"Created {len(created)} new, flagged {len(flagged)} existing"
          + (f", {len(warned)} WARNINGS" if warned else "")
          + f". Conversation collection now {total_conv}. Total items {len(items)}.")


if __name__ == "__main__":
    main()
