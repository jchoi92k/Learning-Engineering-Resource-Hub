#!/usr/bin/env python3
"""
Build all published outputs from meta/hub.db.

Run from the docs/ directory:
    python build_from_db.py

Outputs:
    llms-full.txt     - full index with YAML entries + auto-generated header
    llms.txt          - compact index (no descriptions)
    data.json         - structured JSON for web UI + MCP worker
    tags/index.md     - tag index
    tags/{tag}.md     - per-tag files
    gem-knowledge.txt - Gemini Gem RAG corpus
"""
import json
import os
import re
import sqlite3
from collections import defaultdict
from datetime import date

WIKI_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(WIKI_DIR, "..", "meta", "hub.db")
FULL_FILE = os.path.join(WIKI_DIR, "llms-full.txt")
TAGS_DIR = os.path.join(WIKI_DIR, "tags")

TAG_CATEGORIES = {
    "Domain": [
        "learning-engineering", "math-education", "literacy", "k-12", "early-childhood",
        "english-learners", "higher-ed", "school-discipline",
    ],
    "Method": [
        "a-b-testing", "rct", "nlp", "llm-application", "genai", "coaching",
        "computer-assisted-learning", "automated-feedback", "qualitative-research",
        "meta-analysis", "longitudinal", "intelligent-tutoring", "response-to-intervention",
    ],
    "Topic": [
        "student-belonging", "math-motivation", "pii-privacy", "data-sharing",
        "professional-development", "formative-assessment", "digital-learning-platforms",
        "math-strategies", "personalized-learning", "attendance", "prekindergarten",
        "math-word-problems", "genai-tutoring", "open-datasets", "ai-policy",
        "ai-ethics", "inclusive-design", "sel", "writing-instruction",
        "college-access", "career-readiness", "dropout-prevention",
    ],
    "Affiliation": [
        "rppl", "upgrade-platform", "carnegie-learning", "khan-academy", "lsu",
        "northwestern-e4", "norc", "lastinger-center", "aims",
        "tla", "cmu-learnlab", "assistments", "cosn", "tools-competition",
        "wwc", "unesco", "cast", "iste-ascd", "digital-promise", "duolingo", "jedm",
        "lpi", "nap", "edtrust", "casel", "jla", "campbell-collaboration", "brookings",
    ],
}

LE_PRACTICE_TAGS = {"a-b-testing", "coaching", "intelligent-tutoring", "automated-feedback"}
LE_PRACTICE_TYPES = {"platform", "code", "framework"}
POLICY_TAGS = {"ai-policy", "ai-ethics", "college-access", "career-readiness"}
DATASET_TAGS = {"open-datasets"}

PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def load_entries():
    """Load all non-excluded entries with their tags."""
    conn = get_db()
    entries = []
    for row in conn.execute("SELECT * FROM entries WHERE excluded = 0 ORDER BY num"):
        e = dict(row)
        tags = [r[0] for r in conn.execute(
            "SELECT tag FROM entry_tags WHERE entry_num = ? ORDER BY tag", (e["num"],)
        )]
        e["tags"] = tags
        tag_set = set(tags)
        rtype = e["type"]
        if rtype == "dataset" or DATASET_TAGS.intersection(tag_set):
            e["domain"] = "datasets"
        elif POLICY_TAGS.intersection(tag_set):
            e["domain"] = "policy"
        elif LE_PRACTICE_TYPES.intersection({rtype}) or LE_PRACTICE_TAGS.intersection(tag_set):
            e["domain"] = "le-practice"
        else:
            e["domain"] = "research"
        e["desc"] = e.pop("description", "")
        entries.append(e)
    conn.close()
    return entries


def load_coverage():
    """Build coverage list from source_targets table."""
    conn = get_db()
    indexed_counts = {}
    for row in conn.execute("SELECT source, COUNT(*) as cnt FROM entries WHERE excluded = 0 GROUP BY source"):
        indexed_counts[row["source"]] = row["cnt"]

    coverage = []
    for row in conn.execute("SELECT * FROM source_targets"):
        source = row["source_name"]
        indexed = indexed_counts.get(source, 0)
        known_total = row["known_total"]
        pct = round(indexed / known_total * 100) if known_total else None
        coverage.append({
            "source": source,
            "indexed": indexed,
            "known_total": known_total,
            "pct": pct,
            "priority": row["priority"],
            "status": row["status"],
        })
    coverage.sort(key=lambda x: (PRIORITY_ORDER.get(x["priority"], 1), x["pct"] if x["pct"] is not None else 999))
    conn.close()
    return coverage


def _tag_summary(entries):
    tag_counts = defaultdict(int)
    type_counts = defaultdict(int)
    source_counts = defaultdict(int)
    for e in entries:
        for t in e["tags"]:
            tag_counts[t] += 1
        type_counts[e["type"]] += 1
        source_counts[e["source"]] += 1
    return tag_counts, type_counts, source_counts


def _tag_directory_lines(tag_counts, prefix="# "):
    lines = []
    for category in ["Domain", "Method", "Topic", "Affiliation"]:
        cat_tags = [(t, tag_counts[t]) for t in TAG_CATEGORIES.get(category, []) if t in tag_counts]
        if cat_tags:
            cat_tags.sort(key=lambda x: -x[1])
            tag_list = ", ".join(f"{t} ({c})" for t, c in cat_tags)
            lines.append(f"{prefix}{category}: {tag_list}")
    return lines


def build_llms_full(entries):
    """Generate llms-full.txt — header + all entries with YAML + descriptions."""
    today = date.today().isoformat()
    total = len(entries)
    tag_counts, type_counts, source_counts = _tag_summary(entries)

    lines = [
        "# Renaissance AI and Education Resource Hub — Full Index",
        f"# {total} entries | Last updated: {today}",
        "#",
        "# HOW TO USE THIS FILE",
        "# This file contains all entries with full descriptions — everything is here.",
        "# 1. Use the tag directory below to identify relevant topics.",
        "# 2. Scan entries by their tags to find matches.",
        "# 3. Present matching entries (title, URL, description) to the user.",
        "# Do NOT attempt to fetch other files. This file is self-contained.",
        "#",
    ]
    lines.append("# TAGS")
    lines.extend(_tag_directory_lines(tag_counts, prefix="# "))
    lines.append("#")

    type_list = ", ".join(f"{t} ({c})" for t, c in sorted(type_counts.items(), key=lambda x: -x[1]))
    lines.append(f"# TYPES: {type_list}")
    lines.append("#")

    source_list = ", ".join(f"{s} ({c})" for s, c in sorted(source_counts.items(), key=lambda x: -x[1]))
    lines.append(f"# SOURCES: {source_list}")

    for e in entries:
        tags_str = ", ".join(e["tags"])
        url_confirmed = "true" if e["url_confirmed"] else "false"
        desc_inferred = "true" if e["description_inferred"] else "false"
        doi = e["doi"] if e["doi"] else "null"
        lic = e["license"] if e["license"] else "null"

        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append(f"### {e['num']}. {e['title']}")
        lines.append("")
        lines.append("```yaml")
        lines.append(f'url: "{e["url"]}"')
        lines.append(f"type: {e['type']}")
        lines.append(f'source: "{e["source"]}"')
        lines.append(f"url_confirmed: {url_confirmed}")
        lines.append(f"description_inferred: {desc_inferred}")
        lines.append(f"date_added: {e['date_added']}")
        lines.append(f"doi: {doi}")
        lines.append(f"license: {lic}")
        lines.append(f"tags: [{tags_str}]")
        lines.append("```")
        lines.append("")
        if e["desc"]:
            lines.append(e["desc"])
        lines.append("")
        lines.append("---")

    content = "\n".join(lines)
    with open(FULL_FILE, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[build] Written llms-full.txt ({total} entries)")


def build_llms_txt(entries):
    today = date.today().isoformat()
    total = len(entries)
    tag_counts, type_counts, source_counts = _tag_summary(entries)

    lines = [
        "# Renaissance AI and Education Resource Hub — Compact Index",
        "",
        f"> {total} curated evidence-based K-12 and higher education resources.",
        f"> Last updated: {today}",
        "",
        "This file lists all entries (title, URL, type, tags) without descriptions.",
        "",
    ]
    lines.append("## Tags")
    lines.append("")
    for category in ["Domain", "Method", "Topic", "Affiliation"]:
        cat_tags = [(t, tag_counts[t]) for t in TAG_CATEGORIES.get(category, []) if t in tag_counts]
        if cat_tags:
            cat_tags.sort(key=lambda x: -x[1])
            tag_list = ", ".join(f"{t} ({c})" for t, c in cat_tags)
            lines.append(f"**{category}:** {tag_list}")
            lines.append("")

    lines.append("## Types")
    lines.append("")
    for t, c in sorted(type_counts.items(), key=lambda x: -x[1]):
        lines.append(f"- {t}: {c}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(f"## Entries ({total})")
    lines.append("")

    by_source = defaultdict(list)
    for e in entries:
        by_source[e["source"]].append(e)
    for source in sorted(by_source.keys()):
        source_entries = sorted(by_source[source], key=lambda x: x["num"])
        lines.append(f"### {source} ({len(source_entries)})")
        lines.append("")
        for e in source_entries:
            tags_str = ", ".join(e["tags"])
            lines.append(f"- {e['num']}. [{e['title']}]({e['url']}) | {e['type']} | {tags_str}")
        lines.append("")

    content = "\n".join(lines)
    out = os.path.join(WIKI_DIR, "llms.txt")
    with open(out, "w", encoding="utf-8") as f:
        f.write(content)
    size_kb = len(content.encode("utf-8")) / 1024
    est_tokens = len(content) // 4
    print(f"[build] Written llms.txt ({size_kb:.0f} KB, ~{est_tokens:,} est. tokens)")


def build_json(entries):
    sources = sorted(set(e["source"] for e in entries if e["source"]))
    coverage = load_coverage()

    data = {
        "meta": {
            "total": len(entries),
            "last_updated": date.today().isoformat(),
            "sources": sources,
            "coverage": coverage,
        },
        "entries": [{
            "num": e["num"],
            "title": e["title"],
            "url": e["url"],
            "type": e["type"],
            "source": e["source"],
            "url_confirmed": bool(e["url_confirmed"]),
            "tags": e["tags"],
            "desc": e["desc"],
            "domain": e["domain"],
            "url_verified": True if e["url_status"] == "verified" else (False if e["url_status"] == "broken" else None),
            "last_verified": e["last_verified"],
        } for e in entries],
    }
    out = os.path.join(WIKI_DIR, "data.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"[build] Written data.json ({len(entries)} entries, {len(coverage)} coverage rows)")


def build_tags(entries):
    os.makedirs(TAGS_DIR, exist_ok=True)
    tag_entries = defaultdict(list)
    for entry in entries:
        for tag in entry["tags"]:
            tag_entries[tag].append(entry)

    tag_to_category = {}
    for category, tags in TAG_CATEGORIES.items():
        for tag in tags:
            tag_to_category[tag] = category

    for tag, tag_list in sorted(tag_entries.items()):
        filename = os.path.join(TAGS_DIR, f"{tag}.md")
        lines = [
            f"# Tag: {tag} ({len(tag_list)} {'entry' if len(tag_list) == 1 else 'entries'})",
            "",
            "| # | Title | Type | Description |",
            "|---|---|---|---|",
        ]
        for e in sorted(tag_list, key=lambda x: x["num"]):
            lines.append(f"| {e['num']} | [{e['title']}]({e['url']}) | {e['type']} | {e['desc']} |")
        lines += ["", "*Generated by build_from_db.py*"]
        with open(filename, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    categorized = defaultdict(list)
    uncategorized = []
    for tag in sorted(tag_entries.keys()):
        cat = tag_to_category.get(tag)
        if cat:
            categorized[cat].append(tag)
        else:
            uncategorized.append(tag)

    lines = [
        "# Tag Index", "",
        "> Browse entries by tag.", "",
    ]
    for category in ["Domain", "Method", "Topic", "Affiliation"]:
        tags_in_cat = [(t, len(tag_entries[t])) for t in categorized.get(category, []) if t in tag_entries]
        if tags_in_cat:
            lines.append(f"## {category}")
            lines.append("")
            for tag, count in sorted(tags_in_cat, key=lambda x: -x[1]):
                lines.append(f"- [{tag}]({tag}.md) — {count} {'entry' if count == 1 else 'entries'}")
            lines.append("")
    if uncategorized:
        lines.append("## Other")
        lines.append("")
        for tag in uncategorized:
            count = len(tag_entries[tag])
            lines.append(f"- [{tag}]({tag}.md) — {count} {'entry' if count == 1 else 'entries'}")
        lines.append("")
    lines.append("*Generated by build_from_db.py*")

    with open(os.path.join(TAGS_DIR, "index.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"[build] Generated {len(tag_entries)} tag files in tags/")


def build_gem_knowledge(entries):
    today = date.today().isoformat()
    total = len(entries)
    tag_counts, type_counts, source_counts = _tag_summary(entries)

    lines = [
        "# Renaissance AI and Education Resource Hub",
        f"# {total} curated evidence-based K-12 and higher education resources.",
        f"# Last updated: {today}",
        "", "## Tag Directory", "",
    ]
    for category in ["Domain", "Method", "Topic", "Affiliation"]:
        cat_tags = [(t, tag_counts[t]) for t in TAG_CATEGORIES.get(category, []) if t in tag_counts]
        if cat_tags:
            cat_tags.sort(key=lambda x: -x[1])
            tag_list = ", ".join(f"{t} ({c})" for t, c in cat_tags)
            lines.append(f"**{category}:** {tag_list}")
            lines.append("")

    lines += ["## Resource Types", ""]
    for t, c in sorted(type_counts.items(), key=lambda x: -x[1]):
        lines.append(f"- {t}: {c} entries")
    lines += ["", "## Sources", ""]
    for s, c in sorted(source_counts.items(), key=lambda x: -x[1]):
        lines.append(f"- {s}: {c} entries")
    lines += ["", "---", ""]

    for e in entries:
        tags_str = ", ".join(e["tags"])
        lines.append(f"### {e['num']}. {e['title']}")
        lines.append("")
        lines.append(f"Type: {e['type']} | Source: {e['source']}")
        lines.append(f"Tags: {tags_str}")
        lines.append(f"URL: {e['url']}")
        lines.append("")
        if e["desc"]:
            lines.append(e["desc"])
            lines.append("")
        lines.append("---")
        lines.append("")

    content = "\n".join(lines)
    out = os.path.join(WIKI_DIR, "gem-knowledge.txt")
    with open(out, "w", encoding="utf-8") as f:
        f.write(content)
    size_kb = len(content.encode("utf-8")) / 1024
    print(f"[build] Written gem-knowledge.txt ({size_kb:.0f} KB, {total} entries)")


if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        print(f"[build] Error: {DB_PATH} not found. Run `python meta/migrate_to_db.py` first.")
        raise SystemExit(1)
    entries = load_entries()
    print(f"[build] Loaded {len(entries)} entries from hub.db")
    build_llms_full(entries)
    build_llms_txt(entries)
    build_tags(entries)
    build_json(entries)
    build_gem_knowledge(entries)
    print("[build] Done.")
