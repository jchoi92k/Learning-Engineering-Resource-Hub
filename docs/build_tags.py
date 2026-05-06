#!/usr/bin/env python3
"""
Build tag index, per-tag files, llms.txt, and data.json from llms-full.txt.

Run from the docs/ directory:
    python build_tags.py

Outputs:
    llms.txt             - LLM entry point: navigation guide + compact full index
    tags/index.md        - all tags with entry counts and links
    tags/{tag-name}.md   - per-tag lightweight entry table
    data.json            - structured JSON for the human-facing site
"""

import re
import os
import json
from datetime import date
from collections import defaultdict

WIKI_DIR = os.path.dirname(os.path.abspath(__file__))
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


def determine_domain(entry):
    tags = set(entry["tags"])
    rtype = entry["type"]
    if rtype == "dataset" or DATASET_TAGS.intersection(tags):
        return "datasets"
    if POLICY_TAGS.intersection(tags):
        return "policy"
    if LE_PRACTICE_TYPES.intersection([rtype]) or LE_PRACTICE_TAGS.intersection(tags):
        return "le-practice"
    return "research"


def parse_entries(filepath):
    with open(filepath, encoding="utf-8") as f:
        content = f.read()

    entries = []
    blocks = content.split("\n---\n")

    for block in blocks:
        header_match = re.search(r"### (\d+)\.\s+(.+)", block)
        if not header_match:
            continue

        entry_num = int(header_match.group(1))
        title = header_match.group(2).strip()

        yaml_match = re.search(r"```yaml\n(.*?)```", block, re.DOTALL)
        if not yaml_match:
            continue
        yaml_str = yaml_match.group(1)

        url_match = re.search(r'^url:\s+"?([^"\n]+)"?', yaml_str, re.MULTILINE)
        url = url_match.group(1).strip().strip('"') if url_match else ""

        type_match = re.search(r"^type:\s+(\S+)", yaml_str, re.MULTILINE)
        resource_type = type_match.group(1).strip() if type_match else ""

        source_match = re.search(r'^source:\s+"?([^"\n]+)"?', yaml_str, re.MULTILINE)
        source = source_match.group(1).strip().strip('"') if source_match else ""

        url_confirmed_match = re.search(r"^url_confirmed:\s+(\S+)", yaml_str, re.MULTILINE)
        url_confirmed = url_confirmed_match.group(1).strip().lower() == "true" if url_confirmed_match else False

        tags_match = re.search(r"^tags:\s+\[([^\]]+)\]", yaml_str, re.MULTILINE)
        tags = (
            [t.strip() for t in tags_match.group(1).split(",")]
            if tags_match
            else []
        )

        after_yaml = re.search(r"```\n\n(.+)", block, re.DOTALL)
        if after_yaml:
            desc_text = after_yaml.group(1).strip()
            # Strip leading metadata: "Published/Released [date]." prefix
            desc = re.sub(r"^(Published|Released|Updated|Revised|First published)[^.]+\.\s*", "", desc_text, flags=re.I)
            # Strip metadata blocks (Panel:/Authors:/Research staff: etc.) iteratively —
            # some entries chain multiple blocks (e.g. Panel: ... Research staff: ...)
            meta_re = re.compile(
                r"^(?:Panel|Research staff|Authors?|Editors?|Contributors?):.*?\.\s+(?=[A-Z][a-z]{2,}\s+[a-z])",
                flags=re.DOTALL
            )
            prev = None
            while prev != desc:
                prev = desc
                desc = meta_re.sub("", desc)
            desc = desc.strip()
        else:
            desc = ""

        entry = {
            "num": entry_num,
            "title": title,
            "url": url,
            "type": resource_type,
            "source": source,
            "url_confirmed": url_confirmed,
            "tags": tags,
            "desc": desc,
        }
        entry["domain"] = determine_domain(entry)
        entries.append(entry)

    return entries


def build_json(entries):
    sources = sorted(set(e["source"] for e in entries if e["source"]))
    data = {
        "meta": {
            "total": len(entries),
            "last_updated": date.today().isoformat(),
            "sources": sources,
        },
        "entries": entries,
    }
    out = os.path.join(WIKI_DIR, "data.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"[build_tags] Written data.json ({len(entries)} entries)")


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
            lines.append(
                f"| {e['num']} | [{e['title']}]({e['url']}) | {e['type']} | {e['desc']} |"
            )
        lines += ["", "*Generated by build_tags.py — run to regenerate after adding entries.*"]
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
        "# Tag Index",
        "",
        "> Browse entries by tag. Each tag page lists matching entries with title, type, and description.",
        "> Run `python build_tags.py` from the docs/ directory to regenerate after adding entries.",
        "",
    ]
    for category in ["Domain", "Method", "Topic", "Affiliation"]:
        tags_in_cat = [
            (t, len(tag_entries[t]))
            for t in categorized.get(category, [])
            if t in tag_entries
        ]
        if tags_in_cat:
            lines.append(f"## {category}")
            lines.append("")
            for tag, count in sorted(tags_in_cat, key=lambda x: -x[1]):
                lines.append(
                    f"- [{tag}]({tag}.md) — {count} {'entry' if count == 1 else 'entries'}"
                )
            lines.append("")

    if uncategorized:
        lines.append("## Other")
        lines.append("")
        for tag in uncategorized:
            count = len(tag_entries[tag])
            lines.append(
                f"- [{tag}]({tag}.md) — {count} {'entry' if count == 1 else 'entries'}"
            )
        lines.append("")

    lines.append("*Generated by build_tags.py from llms-full.txt*")

    with open(os.path.join(TAGS_DIR, "index.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"[build_tags] Generated {len(tag_entries)} tag files in tags/")


BASE_URL = "https://jchoi92k.github.io/Learning-Engineering-Resource-Hub"


def build_llms_txt(entries):
    today = date.today().isoformat()
    total = len(entries)
    sources = sorted(set(e["source"] for e in entries if e["source"]))

    tag_counts = defaultdict(int)
    for e in entries:
        for t in e["tags"]:
            tag_counts[t] += 1

    type_counts = defaultdict(int)
    for e in entries:
        type_counts[e["type"]] += 1

    full_size_kb = os.path.getsize(FULL_FILE) / 1024
    full_tokens = int(os.path.getsize(FULL_FILE) / 4)

    lines = []

    # --- Section 1: Navigation guide ---
    lines.append("# Learning Engineering Resource Hub")
    lines.append("")
    lines.append(f"> {total} curated evidence-based K-12 and higher education resources.")
    lines.append(f"> Last updated: {today}")
    lines.append("")
    lines.append("## How to navigate this resource (for LLM agents)")
    lines.append("")
    lines.append("You are reading the entry point. This file contains a compact version of")
    lines.append(f"all {total} entries (title, URL, type, source, tags) — no descriptions.")
    lines.append("Use this to answer discovery questions, then fetch deeper layers for detail.")
    lines.append("")
    lines.append("### Layers")
    lines.append("")
    lines.append("| Layer | File | What you get |")
    lines.append("|---|---|---|")
    lines.append(f"| Compact index | **llms.txt (this file)** | All {total} entries — title, URL, type, source, tags. No descriptions. |")
    lines.append(f"| Tag detail | tags/{{tag}}.md | Filtered entries with full descriptions for one topic. Most are 500–5,000 tokens. |")
    lines.append(f"| Full dump | llms-full.txt | Every entry with full descriptions. ~{full_tokens:,} tokens — too large for a single web fetch. |")
    lines.append("")
    lines.append("### Recommended flows")
    lines.append("")
    lines.append("| User asks | What to do |")
    lines.append("|---|---|")
    lines.append("| \"What resources exist?\" / \"What's in here?\" | Answer from this file — you already have the full catalog. |")
    lines.append("| \"What's available on [topic]?\" | Search this file by tag, then optionally fetch the tag file for descriptions. |")
    lines.append("| \"Tell me more about entry N\" | Follow the entry's URL directly. |")
    lines.append("| \"Give me everything on math education\" | Fetch tags/math-education.md |")
    lines.append("")
    lines.append(f"Tag file URL pattern: {BASE_URL}/tags/{{tag-name}}.md")
    lines.append("")
    lines.append("### Do NOT fetch llms-full.txt via web browser tools.")
    lines.append(f"At ~{full_size_kb:.0f} KB / ~{full_tokens:,} tokens, it will be truncated by most fetchers.")
    lines.append("Use this file (llms.txt) for discovery, tag files for detail.")
    lines.append("")

    # --- Tag directory ---
    lines.append("### Available tags")
    lines.append("")
    for category in ["Domain", "Method", "Topic", "Affiliation"]:
        cat_tags = [(t, tag_counts[t]) for t in TAG_CATEGORIES.get(category, []) if t in tag_counts]
        if cat_tags:
            cat_tags.sort(key=lambda x: -x[1])
            tag_list = ", ".join(
                f"[{t}]({BASE_URL}/tags/{t}.md) ({c})" for t, c in cat_tags
            )
            lines.append(f"**{category}:** {tag_list}")
            lines.append("")

    # --- Type summary ---
    lines.append("### Entry types")
    lines.append("")
    for t, c in sorted(type_counts.items(), key=lambda x: -x[1]):
        lines.append(f"- {t}: {c}")
    lines.append("")

    # --- Section 2: Compact index ---
    lines.append("---")
    lines.append("")
    lines.append(f"## Complete index ({total} entries)")
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
    print(f"[build_tags] Written llms.txt ({size_kb:.0f} KB, ~{est_tokens:,} est. tokens)")


MOJIBAKE_PATTERNS = [
    "â€”",   # em dash double-encoded via CP1252
    "â€“",   # en dash double-encoded via CP1252
    "Â®",         # ® double-encoded
    "Â©",         # © double-encoded
    "â„¢",   # ™ double-encoded
    "﻿",               # BOM
]


def check_encoding(filepath):
    with open(filepath, encoding="utf-8") as f:
        content = f.read()
    found = []
    for pattern in MOJIBAKE_PATTERNS:
        count = content.count(pattern)
        if count:
            found.append((repr(pattern), count))
    if found:
        print("[build_tags] WARNING: mojibake detected in llms-full.txt!")
        for pat, count in found:
            print(f"  {pat} x{count}")
        print("[build_tags] Fix encoding before building. See meta/agent-guide.md.")
        return False
    return True


if __name__ == "__main__":
    if not check_encoding(FULL_FILE):
        raise SystemExit(1)
    entries = parse_entries(FULL_FILE)
    print(f"[build_tags] Parsed {len(entries)} entries")
    build_llms_txt(entries)
    build_tags(entries)
    build_json(entries)
    print("[build_tags] Done.")
