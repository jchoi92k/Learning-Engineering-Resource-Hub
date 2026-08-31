#!/usr/bin/env python3
"""
Build all published outputs from data/hub.db.

Usage (from repo root):
    python scripts/build_from_db.py            # rebuild docs/ from hub.db
    python scripts/build_from_db.py --check    # rebuild to a temp dir and diff against docs/;
                                               # exit 1 if docs/ is stale or entries fail validation

Outputs (written to docs/):
    llms-full.txt     - every entry with YAML + description, one file (self-contained)
    llms.txt          - root index: one line per source linking to the per-source files
    llms-<source>.txt - compact per-source lists (num, title, URL, type, tags), split into
                        parts under INDEX_CHAR_LIMIT; small sources share llms-other-sources.txt
    llms-full-<source>.txt - per-source full shards (same entry format as llms-full.txt)
    data.json         - structured JSON for web UI + MCP worker
    tags/index.md     - tag index
    tags/{tag}.md     - per-tag files
    gem-knowledge.txt - Gemini Gem RAG corpus
"""
import argparse
import filecmp
import json
import os
import re
import shutil
import sqlite3
import tempfile
from collections import defaultdict
from datetime import date

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
WIKI_DIR = os.path.join(REPO_ROOT, "docs")
DB_PATH = os.path.join(REPO_ROOT, "data", "hub.db")
TARGETS_FILE = os.path.join(REPO_ROOT, "data", "source-targets.json")
FULL_FILE = os.path.join(WIKI_DIR, "llms-full.txt")
TAGS_DIR = os.path.join(WIKI_DIR, "tags")

# Files that build_from_db.py owns inside docs/ (everything else there is hand-written).
GENERATED = ["llms-full.txt", "data.json", "gem-knowledge.txt", "sitemap.xml"]
# llms.txt and the per-source files are compared by glob in --check (see check_against_docs).
INDEX_CHAR_LIMIT = 100_000   # max characters per index file (the one published cap: Mintlify's)
DB_SIZE_LIMIT_MIB = 60       # --check fails above this. hub.db is a binary blob in git: GitHub warns at
                             # 50 MiB and blocks pushes of files over 100 MiB. First move when this trips:
                             # split raw_item/page_text into a sidecar (decisions 2026-08-30).
PER_SOURCE_MIN = 10          # sources with fewer entries share llms-other-sources.txt
OTHER_SLUG = "other-sources"
MCP_URL = "https://renaissance-hub.joon-96a.workers.dev/mcp"
MIN_DESCRIPTION_CHARS = 30
# Provenance of the description text (nullable in hub.db; NULL = not recorded)
DESCRIPTION_SOURCES = {"listing", "page-meta", "page-abstract", "llm-summary", "manual"}


def set_output_dir(path):
    """Redirect every builder to `path` (used by --check)."""
    global WIKI_DIR, FULL_FILE, TAGS_DIR
    WIKI_DIR = path
    FULL_FILE = os.path.join(path, "llms-full.txt")
    TAGS_DIR = os.path.join(path, "tags")

TAG_CATEGORIES = {
    "Domain": [
        "learning-engineering", "math-education", "literacy", "k-12", "early-childhood",
        "english-learners", "higher-ed", "school-discipline",
    ],
    "Method": [
        "a-b-testing", "rct", "nlp", "llm-application", "genai", "coaching",
        "computer-assisted-learning", "automated-feedback", "qualitative-research",
        "meta-analysis", "longitudinal", "intelligent-tutoring", "response-to-intervention",
        "instructional-coaching",
    ],
    "Topic": [
        "student-belonging", "math-motivation", "pii-privacy", "data-sharing",
        "professional-development", "formative-assessment", "digital-learning-platforms",
        "math-strategies", "personalized-learning", "attendance", "prekindergarten",
        "math-word-problems", "genai-tutoring", "open-datasets", "ai-policy",
        "ai-ethics", "inclusive-design", "sel", "writing-instruction",
        "college-access", "career-readiness", "dropout-prevention",
        "cognitive-science", "educational-systems-change",
    ],
    "Affiliation": [
        "rppl", "upgrade-platform", "carnegie-learning", "khan-academy", "lsu",
        "northwestern-e4", "norc", "lastinger-center", "aims",
        "tla", "cmu-learnlab", "assistments", "cosn", "tools-competition",
        "wwc", "unesco", "cast", "iste-ascd", "digital-promise", "duolingo",
        "lpi", "nap", "edtrust", "casel", "campbell-collaboration", "brookings",
        "jedm", "jla", "wpi",
    ],
}

LE_PRACTICE_TAGS = {"a-b-testing", "coaching", "intelligent-tutoring", "automated-feedback"}
LE_PRACTICE_TYPES = {"platform", "code", "framework"}
POLICY_TAGS = {"ai-policy", "ai-ethics", "college-access", "career-readiness"}
DATASET_TAGS = {"open-datasets"}

PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


def get_db():
    # Reader (WAL mode: never blocked by a writer); the timeout only matters if a writer holds a checkpoint.
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn


def load_entries():
    """Load all publishable entries with their tags.

    Entries with url_status='broken' stay in hub.db (for dedup and later
    re-checking) but are held out of every published output — the hub's
    promise is verifiable links, so known-dead ones don't ship."""
    conn = get_db()
    held_back = conn.execute(
        "SELECT COUNT(*) FROM entries WHERE excluded = 0 AND url_status = 'broken'"
    ).fetchone()[0]
    if held_back:
        print(f"[build] Holding back {held_back} entries with broken URLs (kept in hub.db, not published)")
    entries = []
    for row in conn.execute(
        "SELECT * FROM entries WHERE excluded = 0 AND url_status != 'broken' ORDER BY num"
    ):
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


def load_targets():
    """Coverage targets: data/source-targets.json is canonical (the source_targets
    table in hub.db is a legacy mirror used only if the file is missing)."""
    if os.path.exists(TARGETS_FILE):
        with open(TARGETS_FILE, encoding="utf-8") as f:
            data = json.load(f)
        return [{"source_name": k, **v} for k, v in data.items() if not k.startswith("_")]
    conn = get_db()
    rows = [dict(r) for r in conn.execute("SELECT * FROM source_targets")]
    conn.close()
    return rows


def load_coverage():
    """Per-source indexed counts (from hub.db) against known totals (from source-targets.json)."""
    conn = get_db()
    indexed_counts = {}
    for row in conn.execute("SELECT source, COUNT(*) as cnt FROM entries WHERE excluded = 0 AND url_status != 'broken' GROUP BY source"):
        indexed_counts[row["source"]] = row["cnt"]
    conn.close()

    coverage = []
    for row in load_targets():
        source = row["source_name"]
        indexed = indexed_counts.get(source, 0)
        known_total = row.get("known_total")
        pct = round(indexed / known_total * 100) if known_total else None
        coverage.append({
            "source": source,
            "indexed": indexed,
            "known_total": known_total,
            "pct": pct,
            "priority": row.get("priority", "medium"),
            "status": row.get("status", "active"),
        })
    coverage.sort(key=lambda x: (PRIORITY_ORDER.get(x["priority"], 1), x["pct"] if x["pct"] is not None else 999))
    return coverage


def validate_entries(entries):
    """Sanity checks on what is about to be published. Returns (errors, warnings)
    as lists of strings. Errors: missing title/description, description shorter
    than MIN_DESCRIPTION_CHARS, non-http URL, duplicate URL (case/trailing-slash
    insensitive), description_source outside DESCRIPTION_SOURCES. Warnings:
    tags outside TAG_CATEGORIES."""
    errors, warnings = [], []
    vocab = {t for tags in TAG_CATEGORIES.values() for t in tags}
    seen = {}
    for e in entries:
        num = e["num"]
        if not (e["title"] or "").strip():
            errors.append(f"#{num}: empty title")
        desc = (e["desc"] or "").strip()
        if not desc:
            errors.append(f"#{num}: empty description")
        elif len(desc) < MIN_DESCRIPTION_CHARS:
            errors.append(f"#{num}: description shorter than {MIN_DESCRIPTION_CHARS} chars ({len(desc)})")
        url = (e["url"] or "").strip()
        if not url.startswith(("http://", "https://")):
            errors.append(f"#{num}: URL is not http(s): {url[:60]}")
        k = url.rstrip("/").lower()
        if k in seen:
            errors.append(f"#{num}: duplicate URL of #{seen[k]}: {url[:60]}")
        seen.setdefault(k, num)
        ds = e.get("description_source")
        if ds is not None and ds not in DESCRIPTION_SOURCES:
            errors.append(f"#{num}: unknown description_source: {ds}")
        for t in e["tags"]:
            if t not in vocab:
                warnings.append(f"#{num}: tag not in vocabulary: {t}")
    return errors, warnings


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


def _entry_block(e):
    """The llms-full.txt block for one entry (also used by the per-source shards)."""
    tags_str = ", ".join(e["tags"])
    url_confirmed = "true" if e["url_confirmed"] else "false"
    desc_inferred = "true" if e["description_inferred"] else "false"
    doi = e["doi"] if e["doi"] else "null"
    lic = e["license"] if e["license"] else "null"
    lines = [
        "",
        "---",
        "",
        f"### {e['num']}. {e['title']}",
        "",
        "```yaml",
        f'url: "{e["url"]}"',
        f"type: {e['type']}",
        f'source: "{e["source"]}"',
        f"url_confirmed: {url_confirmed}",
        f"description_inferred: {desc_inferred}",
        f"description_source: {e.get('description_source') or 'null'}",
        f"date_added: {e['date_added']}",
        f"doi: {doi}",
        f"license: {lic}",
        f"tags: [{tags_str}]",
        "```",
        "",
    ]
    if e["desc"]:
        lines.append(e["desc"])
    lines.append("")
    lines.append("---")
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
        lines.extend(_entry_block(e))

    content = "\n".join(lines)
    with open(FULL_FILE, "w", encoding="utf-8") as f:
        f.write(content)
    size_kb = len(content.encode("utf-8")) / 1024
    print(f"[build] Written llms-full.txt ({total} entries, {size_kb:.0f} KB, ~{len(content) // 4:,} est. tokens)")


# ── llms.txt: root index + per-source files ──

def source_slug(name):
    """'What Works Clearinghouse' -> 'what-works-clearinghouse'."""
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", name.lower())).strip("-")


def compact_line(e):
    return f"- {e['num']}. [{e['title']}]({e['url']}) | {e['type']} | {', '.join(e['tags'])}"


def split_lines(lines, header_chars, limit=INDEX_CHAR_LIMIT):
    """Greedily pack lines into parts so that header + lines stays under `limit`
    characters. Order is kept; a single over-long line still gets its own part."""
    parts, current, size = [], [], header_chars
    for ln in lines:
        need = len(ln) + 1
        if current and size + need > limit:
            parts.append(current)
            current, size = [], header_chars
        current.append(ln)
        size += need
    if current:
        parts.append(current)
    return parts


def group_by_source(entries, per_source_min=PER_SOURCE_MIN):
    """[(slug, display_name, entries)] — sources with >= per_source_min entries
    first (largest first), then one 'other-sources' group holding the rest."""
    by_source = defaultdict(list)
    for e in entries:
        by_source[e["source"]].append(e)
    big = [(source_slug(s), s, sorted(es, key=lambda x: x["num"]))
           for s, es in by_source.items() if len(es) >= per_source_min]
    big.sort(key=lambda g: (-len(g[2]), g[1]))
    small_names = sorted(s for s, es in by_source.items() if len(es) < per_source_min)
    if small_names:
        small_entries = sorted((e for s in small_names for e in by_source[s]), key=lambda x: (x["source"], x["num"]))
        big.append((OTHER_SLUG, f"Other sources ({len(small_names)} organizations)", small_entries))
    slugs = [g[0] for g in big]
    assert len(slugs) == len(set(slugs)), f"source slug collision: {slugs}"
    return big


def _part_names(slug, n_parts):
    if n_parts == 1:
        return [f"llms-{slug}.txt"]
    return [f"llms-{slug}-{i}.txt" for i in range(1, n_parts + 1)]


def _write_index_file(name, content):
    if len(content) > INDEX_CHAR_LIMIT:
        print(f"[build] ERROR: {name} is {len(content):,} chars; index files must stay under {INDEX_CHAR_LIMIT:,}.")
        raise SystemExit(1)
    with open(os.path.join(WIKI_DIR, name), "w", encoding="utf-8") as f:
        f.write(content)


def build_llms_txt(entries):
    """Write llms.txt (root index), llms-<source>[-N].txt (compact parts) and
    llms-full-<source>.txt (full shards). Returns the file names written."""
    today = date.today().isoformat()
    total = len(entries)
    tag_counts, type_counts, source_counts = _tag_summary(entries)
    groups = group_by_source(entries)
    written = []
    index_rows = []

    for slug, display, group in groups:
        full_name = f"llms-full-{slug}.txt"
        # compact parts
        lines = [compact_line(e) for e in group]
        header_allowance = 1500
        parts = split_lines(lines, header_allowance)
        names = _part_names(slug, len(parts))
        for i, (name, part) in enumerate(zip(names, parts), 1):
            first, last = part[0].split(".")[0].lstrip("- "), part[-1].split(".")[0].lstrip("- ")
            head = [
                f"# Renaissance AI and Education Resource Hub — {display}" + (f" (part {i} of {len(parts)})" if len(parts) > 1 else ""),
                "",
                f"> {len(group)} entries from {display}" + (f"; this part lists {len(part)} of them (entry numbers {first}–{last})." if len(parts) > 1 else "."),
                f"> Compact form: entry number, title, URL, type, tags. Descriptions for these entries: {SITE_BASE}/{full_name}",
                f"> Root index of all sources: {SITE_BASE}/llms.txt · Last updated: {today}",
                "",
            ]
            if len(parts) > 1 and i < len(parts):
                head.append(f"Next part: {SITE_BASE}/{names[i]}")
                head.append("")
            _write_index_file(name, "\n".join(head + part))
            written.append(name)
        # full shard (no size cap: it mirrors llms-full.txt for one source)
        shard = [
            f"# Renaissance AI and Education Resource Hub — {display} (full)",
            f"# {len(group)} entries with descriptions | Last updated: {today}",
            f"# Compact list: {SITE_BASE}/{names[0]} · Root index: {SITE_BASE}/llms.txt",
        ]
        for e in group:
            shard.extend(_entry_block(e))
        with open(os.path.join(WIKI_DIR, full_name), "w", encoding="utf-8") as f:
            f.write("\n".join(shard))
        written.append(full_name)
        part_note = "" if len(parts) == 1 else f", {len(parts)} parts"
        index_rows.append(f"- [{display}]({SITE_BASE}/{names[0]}): {len(group)} entries{part_note}; with descriptions: {SITE_BASE}/{full_name}")

    lines = [
        "# Renaissance AI and Education Resource Hub",
        "",
        f"> {total} curated evidence-based K-12 and higher education resources — links with metadata and a description each, from organizations with documented review (What Works Clearinghouse, Learning Policy Institute, Mathematica, Digital Promise, Evidence for ESSA and others). Last updated: {today}",
        "",
        "This is the root index. Each source below links to a compact list of its entries (entry number, title, URL, type, tags); large sources are split into parts under 100,000 characters. Every source also has a file with full descriptions. For the whole corpus in one file see llms-full.txt; for search use the MCP endpoint.",
        "",
        "## Sources",
        "",
    ]
    lines.extend(index_rows)
    lines += [
        "",
        "## Whole corpus",
        "",
        f"- [llms-full.txt]({SITE_BASE}/llms-full.txt): all {total} entries with descriptions in one self-contained file (large)",
        f"- [data.json]({SITE_BASE}/data.json): the same entries as structured JSON",
        f"- [MCP endpoint]({MCP_URL}): semantic search over the corpus (tools: search, fetch, search_resources, get_entries_batch, list_tags, list_sources)",
        "",
        "## Tags",
        "",
        "Tag vocabulary with entry counts; filter values for the MCP tools.",
        "",
    ]
    for category in ["Domain", "Method", "Topic", "Affiliation"]:
        cat_tags = [(t, tag_counts[t]) for t in TAG_CATEGORIES.get(category, []) if t in tag_counts]
        if cat_tags:
            cat_tags.sort(key=lambda x: -x[1])
            lines.append(f"**{category}:** " + ", ".join(f"{t} ({c})" for t, c in cat_tags))
            lines.append("")
    lines += [
        "## Types",
        "",
        ", ".join(f"{t} ({c})" for t, c in sorted(type_counts.items(), key=lambda x: -x[1])),
        "",
        "## Optional",
        "",
        f"- [schema.md]({SITE_BASE}/schema.md): field definitions and the tag vocabulary",
        f"- [how-to-use.md]({SITE_BASE}/how-to-use.md): access options (web, files, MCP, Gem)",
        f"- [purpose.md]({SITE_BASE}/purpose.md): what the hub is for and how entries are chosen",
    ]
    content = "\n".join(lines)
    _write_index_file("llms.txt", content)
    written.insert(0, "llms.txt")
    n_parts = sum(1 for w in written if w.startswith("llms-") and not w.startswith("llms-full-"))
    print(f"[build] Written llms.txt ({len(content) // 1024} KB root index), {n_parts} compact source files, {len(groups)} full shards")
    return written


def prune_stale_index_files(written):
    """Remove docs/llms-*.txt files that this build did not produce (renamed or
    dropped sources), so the published set always matches hub.db."""
    keep = set(written) | {"llms-full.txt"}
    removed = []
    for name in sorted(os.listdir(WIKI_DIR)):
        if name.startswith("llms") and name.endswith(".txt") and name not in keep:
            os.remove(os.path.join(WIKI_DIR, name))
            removed.append(name)
    if removed:
        print(f"[build] Removed stale index files: {', '.join(removed)}")




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
            "description_source": e.get("description_source"),
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


SITE_BASE = "https://jchoi92k.github.io/Learning-Engineering-Resource-Hub"


def build_sitemap():
    """Sitemap for the GitHub Pages site. AI search features (Google AI
    Overviews etc.) retrieve from the ordinary search index, so standard
    crawlability of the main pages is what earns visibility there."""
    today = date.today().isoformat()
    pages = [
        "",  # site root (index.html)
        "purpose.md",
        "how-to-use.md",
        "schema.md",
        "llms.txt",
        "llms-full.txt",
        "tags/index.md",
    ]
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for page in pages:
        loc = f"{SITE_BASE}/{page}" if page else f"{SITE_BASE}/"
        lines += ["  <url>", f"    <loc>{loc}</loc>", f"    <lastmod>{today}</lastmod>", "  </url>"]
    lines.append("</urlset>")
    out = os.path.join(WIKI_DIR, "sitemap.xml")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"[build] Written sitemap.xml ({len(pages)} URLs)")


def build_all(entries):
    build_llms_full(entries)
    written = build_llms_txt(entries)
    prune_stale_index_files(written)
    build_tags(entries)
    build_json(entries)
    build_gem_knowledge(entries)
    build_sitemap()


VOLATILE_MARKERS = ("Last updated:", "<lastmod>", '"last_updated"')


def _stable_lines(path):
    """File contents minus the lines that change on every build (dates)."""
    with open(path, encoding="utf-8") as f:
        return [ln for ln in f if not any(m in ln for m in VOLATILE_MARKERS)]


def db_size_check(path=DB_PATH, limit_mib=DB_SIZE_LIMIT_MIB):
    """Size of the tracked database in MiB, plus an error message when it is
    over the limit. The limit sits well under GitHub's 100 MiB block so there
    is time to slim the file before a push is refused."""
    size_mib = os.path.getsize(path) / (1024 * 1024)
    if size_mib > limit_mib:
        return size_mib, (f"data/hub.db is {size_mib:.1f} MiB, over the {limit_mib} MiB limit "
                          f"(GitHub blocks files over 100 MiB); move raw_item/page_text out of the tracked file")
    return size_mib, None


def check_against_docs(entries):
    """Rebuild into a temp dir and compare with docs/. Returns a list of
    human-readable differences (empty when docs/ is current)."""
    real_docs = WIKI_DIR
    tmp = tempfile.mkdtemp(prefix="hub-build-check-")
    try:
        set_output_dir(tmp)
        build_all(entries)
        set_output_dir(real_docs)
        diffs = []
        index_files = [n for n in os.listdir(tmp) if n.startswith("llms") and n.endswith(".txt") and n != "llms-full.txt"]
        for rel in GENERATED + sorted(index_files):
            a, b = os.path.join(tmp, rel), os.path.join(real_docs, rel)
            if not os.path.exists(b):
                diffs.append(f"missing in docs/: {rel}")
            elif _stable_lines(a) != _stable_lines(b):
                diffs.append(f"stale: docs/{rel}")
        for name in sorted(os.listdir(real_docs)):
            if name.startswith("llms") and name.endswith(".txt") and name != "llms-full.txt" and name not in index_files:
                diffs.append(f"orphan (source file no longer built): docs/{name}")
        tmp_tags = sorted(os.listdir(os.path.join(tmp, "tags")))
        real_tags_dir = os.path.join(real_docs, "tags")
        real_tags = sorted(os.listdir(real_tags_dir)) if os.path.isdir(real_tags_dir) else []
        for name in tmp_tags:
            b = os.path.join(real_tags_dir, name)
            if not os.path.exists(b):
                diffs.append(f"missing in docs/tags/: {name}")
            elif not filecmp.cmp(os.path.join(tmp, "tags", name), b, shallow=False):
                diffs.append(f"stale: docs/tags/{name}")
        for name in real_tags:
            if name not in tmp_tags:
                diffs.append(f"orphan (tag no longer used): docs/tags/{name}")
        return diffs
    finally:
        set_output_dir(real_docs)
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    parser = argparse.ArgumentParser(description="Build published files from hub.db")
    parser.add_argument("--check", action="store_true",
                        help="Validate entries and verify docs/ matches a fresh build; write nothing")
    args = parser.parse_args()

    if not os.path.exists(DB_PATH):
        print(f"[build] Error: {DB_PATH} not found.")
        raise SystemExit(1)
    entries = load_entries()
    print(f"[build] Loaded {len(entries)} entries from hub.db")

    errors, warnings = validate_entries(entries)
    for w in warnings[:20]:
        print(f"[build] warning: {w}")
    if len(warnings) > 20:
        print(f"[build] ... {len(warnings) - 20} more warnings")
    for err in errors[:50]:
        print(f"[build] ERROR: {err}")
    print(f"[build] Validation: {len(errors)} errors, {len(warnings)} warnings")
    size_mib, size_error = db_size_check()
    print(f"[build] hub.db {size_mib:.1f} MiB (limit {DB_SIZE_LIMIT_MIB} MiB)")
    if size_error:
        print(f"[build] {'ERROR' if args.check else 'warning'}: {size_error}")

    if args.check:
        diffs = check_against_docs(entries)
        for d in diffs:
            print(f"[build] CHECK: {d}")
        ok = not errors and not diffs and not size_error
        print("[build] Check passed: docs/ is current and entries validate." if ok
              else f"[build] Check FAILED: {len(errors)} validation errors, {len(diffs)} stale/missing files"
                   + (", hub.db over the size limit" if size_error else "") + ".")
        raise SystemExit(0 if ok else 1)

    if errors:
        print("[build] Refusing to build with validation errors. Fix the rows above (or run with --check for details).")
        raise SystemExit(1)
    build_all(entries)
    print("[build] Done.")


if __name__ == "__main__":
    main()
