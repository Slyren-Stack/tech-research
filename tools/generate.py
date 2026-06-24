#!/usr/bin/env python3
"""
Generate the entire knowledge base from indexes/master.json (the source of truth).

Outputs:
  kb/cards/<id>.md         one card per item
  kb/topic-hubs/<hub>.md   one page per topic hub (+ core-library)
  indexes/master.md        human-readable master overview
  indexes/top-25.md        top items by combined signal
  indexes/<path>.md        one page per learning path
  exports/library.json     pretty machine-readable copy of items
  exports/library.csv      spreadsheet-friendly flat export
  exports/digest.md        single-file shareable digest (all cards inline)

Usage:  python3 tools/generate.py
Idempotent: safe to run repeatedly. Edit master.json, then re-run.
"""

import csv
import json
import os
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MASTER = os.path.join(ROOT, "indexes", "master.json")


def load():
    with open(MASTER, encoding="utf-8") as f:
        return json.load(f)


def score(item):
    """Combined ranking signal: credibility + usefulness, core gets a nudge."""
    base = item.get("credibility", 0) + item.get("usefulness", 0)
    return base + (1 if item.get("status") == "core" else 0)


def slug_link(item):
    return f"../cards/{item['id']}.md"


def fmt_link(url):
    return f"[Open source]({url})" if url else "_No single canonical link — see card notes._"


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"  wrote {os.path.relpath(path, ROOT)}")


# ---------------------------------------------------------------- cards
def render_card(item):
    tags = " ".join(f"`{t}`" for t in item.get("tags", []))
    takeaways = "\n".join(f"- {t}" for t in item.get("key_takeaways", []))
    year = item.get("year") or "Unknown"
    link = item.get("source_link")
    src = f"[{link}]({link})" if link else "Unknown / no single canonical link (see summary)."
    venue = f"\nvenue: \"{item['venue']}\"" if item.get("venue") else ""
    runtime = f"\nruntime: \"{item['runtime']}\"" if item.get("runtime") else ""
    provenance = ""
    extras = []
    if item.get("venue"):
        extras.append(f"**Where:** {item['venue']}")
    if item.get("runtime"):
        extras.append(f"**Runtime:** {item['runtime']}")
    if extras:
        provenance = "\n" + " · ".join(extras) + "\n"
    conversation = ""
    if item.get("conversation_note"):
        conversation = f"\n## 💬 Good conversation topic\n{item['conversation_note']}\n"
    return f"""---
id: {item['id']}
title: "{item['title']}"
creator: "{item['creator']}"
year: {item.get('year') if item.get('year') is not None else 'null'}
format: {item['format']}
category: {item['category']}
subcategory: {item['subcategory']}
difficulty: {item['difficulty']}
credibility: {item['credibility']}
usefulness: {item['usefulness']}
status: {item['status']}{venue}{runtime}
---

# {item['title']}

**{item['creator']}** · {year} · {item['format']}{provenance}
**Category:** {item['category']} → {item['subcategory']}
**Difficulty:** {item['difficulty']} · **Status:** `{item['status']}` · **Credibility:** {item['credibility']}/10 · **Usefulness:** {item['usefulness']}/10

## Summary
{item['summary']}
{conversation}
## Key takeaways
{takeaways}

## Why it matters
{item['why_it_matters']}

## Audience fit
{item['audience_fit']}

## Tags
{tags}

## Source
{src}

---
*Part of the [Tech Research Knowledge Base](../../indexes/master.md). Generated from `indexes/master.json` — edit there, not here.*
"""


# ---------------------------------------------------------------- hubs
def render_hub(hub, items):
    members = [i for i in items if i["category"] == hub["title"]]
    members.sort(key=score, reverse=True)
    rows = []
    for i in members:
        star = "⭐ " if i["status"] == "core" else ""
        rows.append(
            f"### {star}[{i['title']}]({slug_link(i)})\n"
            f"*{i['creator']} · {i.get('year') or 'Unknown'} · {i['format']} · {i['difficulty']}*\n\n"
            f"{i['summary']}\n\n"
            f"**Why it matters:** {i['why_it_matters']}\n"
        )
    body = "\n".join(rows) if rows else "_No items yet._"
    return f"""# {hub['title']}

{hub['blurb']}

{len(members)} item(s), ranked by signal. ⭐ = core / must-experience.

---

{body}

---
*[← Back to master index](../../indexes/master.md) · Generated from `indexes/master.json`.*
"""


def render_conversation_hub(hub, items, meta):
    members = [i for i in items if i.get("conversation")]
    cv = lambda i: (i.get("conversation_value", 0), score(i))
    ranked = sorted(members, key=cv, reverse=True)

    def line(i):
        return (f"- **[{i['title']}]({slug_link(i)})** — *{i['creator']}, "
                f"{i.get('year') or 'Unknown'} ({i['format']})* — {i.get('conversation_note', '')}")

    out = [
        f"# {hub['title']}", "", hub["blurb"], "",
        f"**{len(members)} conversation-worthy items** across every theme, ranked by conversation value. "
        "Each also lives in its home hub.", "",
    ]
    if meta.get("conversation_synthesis"):
        out += [f"> **The recurring themes:** {meta['conversation_synthesis']}", ""]

    # Top 25
    out += ["## Top 25 — the highest-signal starters", "",
            "| # | Topic | Creator | Format | Conv. |", "|---|---|---|---|---|"]
    for n, i in enumerate(ranked[:25], 1):
        out.append(f"| {n} | [{i['title']}]({slug_link(i)}) | {i['creator']} | "
                   f"{i['format']} | {i.get('conversation_value', '—')} |")
    out.append("")

    # By theme (home category)
    out += ["## By theme", ""]
    by_cat = {}
    for i in ranked:
        by_cat.setdefault(i["category"], []).append(i)
    for cat in sorted(by_cat, key=lambda c: -len(by_cat[c])):
        out.append(f"### {cat} ({len(by_cat[cat])})")
        out += [line(i) for i in by_cat[cat]]
        out.append("")

    # Curated cross-lists derived from fields
    dinner = [i for i in ranked if i["difficulty"] == "Beginner"]
    builders = [i for i in ranked if i["category"] in
                ("AI Foundations", "AI in Practice", "Engineering and Systems")]
    investor = [i for i in ranked if i["category"] == "Venture Capital and Fundraising"
                or "investor" in i.get("tags", [])]

    def names(lst, k):
        return " · ".join(f"[{i['title']}]({slug_link(i)})" for i in lst[:k])

    out += [
        "## Quick lists", "",
        f"**🍷 Safe at dinner or networking** (accessible, broadly known): {names(dinner, 12)}", "",
        f"**🛠️ For builders & engineers** (technical depth): {names(builders, 12)}", "",
        f"**💰 Investor lens** (capital, markets, moats): {names(investor, 12)}", "",
        "---",
        "*[← Back to master index](../../indexes/master.md) · Generated from `indexes/master.json`.*",
    ]
    return "\n".join(out)


def render_core_hub(hub, items):
    members = [i for i in items if i["status"] == "core"]
    members.sort(key=score, reverse=True)
    rows = []
    for i in members:
        rows.append(
            f"### [{i['title']}]({slug_link(i)})\n"
            f"*{i['creator']} · {i.get('year') or 'Unknown'} · {i['format']} · {i['category']}*\n\n"
            f"{i['summary']}\n"
        )
    body = "\n".join(rows)
    return f"""# {hub['title']}

{hub['blurb']}

The {len(members)} essential items across every category — the highest-signal starting set.

---

{body}

---
*[← Back to master index](../../indexes/master.md) · Generated from `indexes/master.json`.*
"""


# ---------------------------------------------------------------- master.md
def render_master(data):
    items = data["items"]
    hubs = data["hubs"]
    by_cat = {}
    for i in items:
        by_cat.setdefault(i["category"], []).append(i)

    lines = [
        "# Tech Research — Master Index",
        "",
        f"> {data['meta']['description']}",
        "",
        f"**{len(items)} curated items** · {len([i for i in items if i['status']=='core'])} core · "
        f"last updated {data['meta']['last_updated']} · version {data['meta']['version']}",
        "",
        "This is the human-readable overview. The machine-readable source of truth is "
        "[`master.json`](master.json). Everything in this repo is generated from it.",
        "",
        "## How to use this library",
        "- **Just exploring?** Browse the [topic hubs](#topic-hubs) below.",
        "- **Short on time?** Start with the [Top 25](top-25.md) or the "
        "[Must-Watch Core Library](../kb/topic-hubs/core-library.md).",
        "- **Learning a path?** Pick one: "
        + " · ".join(f"[{p['title']}]({p['id']}.md)" for p in data["learning_paths"]) + ".",
        "- **Want one file to send someone?** Share [`exports/digest.md`](../exports/digest.md).",
        "",
        "## Topic hubs",
        "",
    ]
    for h in hubs:
        if h["id"] == "core-library":
            count = len([i for i in items if i["status"] == "core"])
        elif h["id"] == "conversation-starters":
            count = len([i for i in items if i.get("conversation")])
        else:
            count = len(by_cat.get(h["title"], []))
        lines.append(f"- **[{h['title']}](../kb/topic-hubs/{h['id']}.md)** ({count}) — {h['blurb']}")
    lines += ["", "## Learning paths", ""]
    for p in data["learning_paths"]:
        lines.append(f"- **[{p['title']}]({p['id']}.md)** — {p['audience']}")

    lines += ["", "## All items by category", ""]
    for cat in sorted(by_cat):
        lines.append(f"### {cat}")
        lines.append("")
        lines.append("| Item | Creator | Year | Format | Difficulty | Status | Score |")
        lines.append("|---|---|---|---|---|---|---|")
        for i in sorted(by_cat[cat], key=score, reverse=True):
            lines.append(
                f"| [{i['title']}](../kb/cards/{i['id']}.md) | {i['creator']} | "
                f"{i.get('year') or '—'} | {i['format']} | {i['difficulty']} | "
                f"`{i['status']}` | {score(i)} |"
            )
        lines.append("")
    lines += [
        "---",
        "*Generated from `indexes/master.json` via `tools/generate.py`. "
        "To add or edit items, change the JSON and re-run the generator.*",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------- top-25
def render_top(data, n=25):
    ranked = sorted(data["items"], key=score, reverse=True)[:n]
    lines = [
        f"# Top {len(ranked)} — Highest-Signal Items",
        "",
        "Ranked by combined credibility + usefulness (core items get a tie-break nudge). "
        "If you read/watch nothing else, work down this list.",
        "",
        "| # | Item | Creator | Format | Category | Score |",
        "|---|---|---|---|---|---|",
    ]
    for n_, i in enumerate(ranked, 1):
        lines.append(
            f"| {n_} | [{i['title']}](../kb/cards/{i['id']}.md) | {i['creator']} | "
            f"{i['format']} | {i['category']} | {score(i)} |"
        )
    lines += ["", "---", "*Generated from `indexes/master.json`.*"]
    return "\n".join(lines)


# ---------------------------------------------------------------- paths
def render_path(path, items_by_id):
    lines = [
        f"# {path['title']}",
        "",
        f"**For:** {path['audience']}",
        "",
        path["intro"],
        "",
        "Work through these in order:",
        "",
    ]
    for n, iid in enumerate(path["items"], 1):
        i = items_by_id.get(iid)
        if not i:
            lines.append(f"{n}. _Missing item: `{iid}`_")
            continue
        lines.append(
            f"{n}. **[{i['title']}](../kb/cards/{i['id']}.md)** — "
            f"{i['creator']}, {i.get('year') or 'Unknown'} ({i['format']}, {i['difficulty']})  \n"
            f"   {i['why_it_matters']}"
        )
    lines += ["", "---", "*[← Back to master index](master.md) · Generated from `indexes/master.json`.*"]
    return "\n".join(lines)


# ---------------------------------------------------------------- exports
def render_csv(items, path):
    cols = ["id", "title", "creator", "year", "format", "category", "subcategory",
            "difficulty", "credibility", "usefulness", "status", "source_link", "tags"]
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for i in sorted(items, key=score, reverse=True):
            row = [i.get(c, "") for c in cols[:-1]]
            row.append("; ".join(i.get("tags", [])))
            w.writerow(row)
    print(f"  wrote {os.path.relpath(path, ROOT)}")


def render_digest(data):
    items = sorted(data["items"], key=score, reverse=True)
    lines = [
        f"# {data['meta']['name']} — Shareable Digest",
        "",
        f"> {data['meta']['description']}",
        "",
        f"{len(items)} curated items · generated {date.today().isoformat()}. "
        "This single file is meant to be sent to a teammate as a complete snapshot.",
        "",
        "---",
        "",
    ]
    for i in items:
        star = "⭐ " if i["status"] == "core" else ""
        link = i.get("source_link")
        src = f"[{link}]({link})" if link else "_No single canonical link._"
        lines += [
            f"## {star}{i['title']}",
            f"*{i['creator']} · {i.get('year') or 'Unknown'} · {i['format']} · {i['category']} → {i['subcategory']}*",
            f"`{i['difficulty']}` · cred {i['credibility']}/10 · useful {i['usefulness']}/10 · status `{i['status']}`",
            "",
            i["summary"],
            "",
            "**Key takeaways:** " + " ".join(f"({n+1}) {t}" for n, t in enumerate(i["key_takeaways"])),
            "",
            f"**Why it matters:** {i['why_it_matters']}",
            "",
            f"**Source:** {src}",
            "",
            "---",
            "",
        ]
    return "\n".join(lines)


# ---------------------------------------------------------------- main
def main():
    data = load()
    items = data["items"]
    items_by_id = {i["id"]: i for i in items}

    # integrity checks
    ids = [i["id"] for i in items]
    assert len(ids) == len(set(ids)), "Duplicate item ids in master.json"
    hub_titles = {h["title"] for h in data["hubs"]}
    for i in items:
        assert i["category"] in hub_titles, f"{i['id']}: category '{i['category']}' has no hub"
    for p in data["learning_paths"]:
        for iid in p["items"]:
            assert iid in items_by_id, f"path {p['id']} references missing item '{iid}'"

    print("Cards:")
    for i in items:
        write(os.path.join(ROOT, "kb", "cards", f"{i['id']}.md"), render_card(i))

    print("Topic hubs:")
    for h in data["hubs"]:
        path = os.path.join(ROOT, "kb", "topic-hubs", f"{h['id']}.md")
        if h["id"] == "core-library":
            write(path, render_core_hub(h, items))
        elif h["id"] == "conversation-starters":
            write(path, render_conversation_hub(h, items, data["meta"]))
        else:
            write(path, render_hub(h, items))

    print("Indexes:")
    write(os.path.join(ROOT, "indexes", "master.md"), render_master(data))
    write(os.path.join(ROOT, "indexes", "top-25.md"), render_top(data, 25))
    for p in data["learning_paths"]:
        write(os.path.join(ROOT, "indexes", f"{p['id']}.md"), render_path(p, items_by_id))

    print("Exports:")
    write(os.path.join(ROOT, "exports", "library.json"),
          json.dumps({"meta": data["meta"], "items": sorted(items, key=score, reverse=True)},
                     indent=2, ensure_ascii=False))
    render_csv(items, os.path.join(ROOT, "exports", "library.csv"))
    write(os.path.join(ROOT, "exports", "digest.md"), render_digest(data))

    print(f"\nDone. {len(items)} items → cards, {len(data['hubs'])} hubs, "
          f"{len(data['learning_paths'])} paths, 3 exports.")


if __name__ == "__main__":
    main()
