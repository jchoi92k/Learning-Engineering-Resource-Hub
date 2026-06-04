#!/usr/bin/env python3
"""
Process staged JSON from scrape.py into llms-full.txt entries.

Handles mechanical tagging (source affiliation, grade level mappings)
and entry formatting. Topic/method tags require LLM review — the script
outputs entries with a base tag set that the LLM augments.

Usage:
    python meta/process_staged.py wwc                # process all ready items
    python meta/process_staged.py wwc --limit 5      # process first 5 items
    python meta/process_staged.py wwc --preview       # show formatted entries without writing
    python meta/process_staged.py wwc --offset 10     # skip first 10 items

Output appends to docs/llms-full.txt. Run `python build_tags.py` from docs/ after.
"""
import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
STAGING_DIR = REPO_ROOT / "docs" / "staging"
LLMS_FULL = REPO_ROOT / "docs" / "llms-full.txt"
PROCESSING_LOG = SCRIPT_DIR / "processing-log.md"

TODAY = date.today().isoformat()

SOURCE_TAG_MAP = {
    "wwc": "wwc",
    "lpi": "lpi",
    "digital-promise": "digital-promise",
    "edtrust": "edtrust",
    "wested": None,
    "nwea-research": None,
    "brookings": "brookings",
    "tntp": None,
    "uchicago-consortium": None,
    "campbell-collaboration": "campbell-collaboration",
    "evidence-for-essa": None,
    "mathematica": None,
}

SOURCE_NAME_MAP = {
    "wwc": "What Works Clearinghouse",
    "lpi": "Learning Policy Institute",
    "digital-promise": "Digital Promise",
    "edtrust": "The Education Trust",
    "wested": "WestEd",
    "nwea-research": "NWEA Research",
    "brookings": "Brookings Institution",
    "tntp": "TNTP",
    "uchicago-consortium": "UChicago Consortium on School Research",
    "campbell-collaboration": "Campbell Collaboration",
    "evidence-for-essa": "Evidence for ESSA",
    "mathematica": "Mathematica",
}

TYPE_MAP = {
    "intervention report": "report",
    "practice guide": "framework",
    "report": "report",
    "brief": "report",
    "fact sheet": "report",
    "article": "paper",
    "book": "report",
    "snapshot": "report",
    "blog": "blog-post",
    "video": "presentation",
    "research": "report",
    "commentary": "blog-post",
    "training and professional development": "framework",
    "webinar": "presentation",
    "issue brief": "report",
    "resource guide": "framework",
    "toolkit": "tool",
    "infographic": "report",
    "reading": "report",
    "math": "report",
    "social-emotional": "report",
    "attendance": "report",
    "science": "report",
    "family engagement": "report",
    "project report": "report",
    "journal article": "paper",
    "working paper": "paper",
    "professional or conference paper": "paper",
    "executive summary": "report",
    "survey instrument": "tool",
    "book chapter": "paper",
    "presentation": "presentation",
    "data set": "dataset",
    "testimony": "report",
    "appendix": "report",
    "other": "report",
}

GRADE_TAG_MAP = {
    "pk": "prekindergarten",
    "pre-k": "prekindergarten",
    "prek": "prekindergarten",
    "k": "k-12",
    "ps": "higher-ed",
    "postsecondary": "higher-ed",
}


def get_last_entry_num():
    """Find the highest entry number in llms-full.txt."""
    if not LLMS_FULL.exists():
        return 0
    highest = 0
    with open(LLMS_FULL, encoding="utf-8") as f:
        for line in f:
            m = re.match(r'^### (\d+)\.', line)
            if m:
                highest = max(highest, int(m.group(1)))
    return highest


def infer_type(item):
    """Map raw type string to schema type."""
    raw = item.get("type", "").strip().lower()
    return TYPE_MAP.get(raw, "report")


KEYWORD_TAGS = [
    (r'\breading\b|phonics|phonemic|phonological|read(ers?|ability)\b|literacy|decod(e|ing)\b|vocabulary|comprehension|oral reading|beginning reading|reading fluency|reading instruction', "literacy"),
    (r'\bmath|algebra|arithmetic|calcul|numer(acy|ical)|geometry|fraction|equation', "math-education"),
    (r'\benglish learner|bilingual|esl\b|english language learner|dual.language|multilingual', "english-learners"),
    (r'\bsocial.emotional|sel\b|behavio(r|ur|ral)|social skills|emotional|self.regulation|character', "sel"),
    (r'\bdropout|graduation rate|credit recovery|staying in school|leaving school', "dropout-prevention"),
    (r'\battendance|absent|chronic absence|truancy', "attendance"),
    (r'\bcollege|postsecondary|university|undergraduate|higher education', "college-access"),
    (r'\bprekindergarten|preschool|pre.k\b|head start|early childhood|ages? [3-5]|toddler', "early-childhood"),
    (r'\bwriting|composition|essay|written expression', "writing-instruction"),
    (r'\bprofessional development|teacher training|teacher preparation|coaching|mentoring', "professional-development"),
    (r'\bassessment|formative|diagnostic test|screening|progress monitor', "formative-assessment"),
    (r'\btutor|intervention|remediat|supplemental instruction|response to intervention|rti\b', "response-to-intervention"),
    (r'\btechnology|computer|digital|software|online|web.based|app\b|tablet|device', "computer-assisted-learning"),
    (r'\bpersonaliz|adaptive|individuali[zs]ed instruction|differentiat', "personalized-learning"),
    (r'\bstem\b|science education|science instruction|science achievement', "k-12"),
    (r'\bspecial education|disabilit|iep\b|inclusion|inclusive', "inclusive-design"),
    (r'\bcareer|workforce|vocational|cte\b|career.technical', "career-readiness"),
    (r'\bdata.driven|data.use|data.based|learning analytics', "learning-engineering"),
]


def infer_tags(item, source):
    """Build tag list from mechanical signals and keyword matching."""
    tags = []

    # Source affiliation tag
    src_tag = SOURCE_TAG_MAP.get(source)
    if src_tag:
        tags.append(src_tag)

    # Grade level → domain tag
    grade = item.get("grade_level", "").lower().strip()
    if grade:
        for prefix, tag in GRADE_TAG_MAP.items():
            if prefix in grade:
                if tag not in tags:
                    tags.append(tag)
                break
        if any(c.isdigit() for c in grade) and "higher-ed" not in tags:
            if "k-12" not in tags:
                tags.append("k-12")

    # Evidence tier (WWC-specific)
    tier = item.get("evidence_tier", "").strip()
    if tier == "1":
        tags.append("rct")

    # Keyword-based topic tags from title + blurb
    text = (item.get("title", "") + " " + item.get("blurb", "")).lower()
    for pattern, tag in KEYWORD_TAGS:
        if tag not in tags and re.search(pattern, text):
            tags.append(tag)

    return tags


def format_entry(num, item, source):
    """Format a single item as an llms-full.txt entry."""
    title = item["title"].strip()
    url = item["url"].strip()
    entry_type = infer_type(item)
    source_name = SOURCE_NAME_MAP.get(source, source)
    tags = infer_tags(item, source)
    blurb = item.get("blurb", "").strip()

    tag_str = ", ".join(tags) if tags else "TODO"

    lines = [
        f"### {num}. {title}",
        "",
        "```yaml",
        f'url: "{url}"',
        f"type: {entry_type}",
        f'source: "{source_name}"',
        "url_confirmed: true",
        "description_inferred: false",
        f"date_added: {TODAY}",
        "doi: null",
        "license: null",
        f"tags: [{tag_str}]",
        "```",
        "",
        blurb,
        "",
        "---",
        "",
    ]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Process staged JSON into llms-full.txt entries")
    parser.add_argument("source", help="Source slug matching the staged JSON filename")
    parser.add_argument("--limit", type=int, default=None, help="Process only the first N items")
    parser.add_argument("--offset", type=int, default=0, help="Skip the first N items")
    parser.add_argument("--preview", action="store_true", help="Print entries without writing")
    args = parser.parse_args()

    staged_path = STAGING_DIR / f"{args.source}.json"
    if not staged_path.exists():
        print(f"Error: no staged file at {staged_path}", file=sys.stderr)
        sys.exit(1)

    with open(staged_path, encoding="utf-8") as f:
        data = json.load(f)

    items = data.get("items", [])
    if not items:
        print("No ready items in staged file.")
        return

    items = items[args.offset:]
    if args.limit:
        items = items[:args.limit]

    print(f"[process] Source: {args.source}, {len(items)} items to process")

    start_num = get_last_entry_num() + 1
    entries_text = ""

    for i, item in enumerate(items):
        num = start_num + i
        entry = format_entry(num, item, args.source)
        entries_text += entry

    if args.preview:
        print(entries_text)
        print(f"\n[process] Preview: {len(items)} entries ({start_num}–{start_num + len(items) - 1})")
        return

    with open(LLMS_FULL, "a", encoding="utf-8") as f:
        f.write(entries_text)

    end_num = start_num + len(items) - 1
    print(f"[process] Appended {len(items)} entries ({start_num}-{end_num}) to {LLMS_FULL}")
    print(f"[process] Next: review tags, then run `cd docs && python build_tags.py`")

    # Auto-log
    write_log(args.source, data, items, start_num, end_num)


def write_log(source, staged_data, items, start_num, end_num):
    """Append a processing record to meta/processing-log.md."""
    source_name = SOURCE_NAME_MAP.get(source, source)
    total_staged = staged_data.get("total_ready", 0) + staged_data.get("total_backlog", 0)
    ready = staged_data.get("total_ready", 0)
    backlog = staged_data.get("total_backlog", 0)

    # Count tag quality
    todo_count = sum(1 for item in items if not infer_tags(item, source))

    entry = (
        f"\n## {TODAY} - {source_name}\n"
        f"- Source slug: `{source}`\n"
        f"- Scraped: {total_staged} total, {ready} ready, {backlog} backlog\n"
        f"- Processed: {len(items)} entries ({start_num}-{end_num})\n"
        f"- Tags: keyword auto-tagged"
    )
    if todo_count:
        entry += f" ({todo_count} untagged)"
    entry += "\n"

    with open(PROCESSING_LOG, "a", encoding="utf-8") as f:
        f.write(entry)
    print(f"[process] Logged to {PROCESSING_LOG}")


if __name__ == "__main__":
    main()
