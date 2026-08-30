#!/usr/bin/env python3
"""
Process staged JSON from scrape.py into hub.db.

Handles mechanical tagging (source affiliation, grade level, keyword matching)
and inserts entries into the SQLite database. Backlog items (found on the
listing but without a usable description) are inserted as excluded rows with
exclude_reason='no_description_pending' so scrape.py's diff and early-stop
treat them as known and they stop showing up as "new" every run; a later
backfill fills the description and clears `excluded`. Each active row records
description_source (listing / page-meta / page-abstract) from the staged
item's blurb_source, written by scrape.py.

Usage:
    python scripts/process_staged.py wwc                # process all ready items
    python scripts/process_staged.py wwc --limit 5      # process first 5 items
    python scripts/process_staged.py wwc --preview       # show entries without writing
    python scripts/process_staged.py wwc --offset 10     # skip first 10 items

After processing, run `python scripts/build_from_db.py` to regenerate published files.
"""
import argparse
import json
import re
import sqlite3
import sys
from datetime import date
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
STAGING_DIR = REPO_ROOT / "docs" / "staging"
DB_PATH = REPO_ROOT / "data" / "hub.db"
PROCESSING_LOG = REPO_ROOT / "meta" / "processing-log.md"

TODAY = date.today().isoformat()
PENDING_REASON = "no_description_pending"

SOURCE_TAG_MAP = {
    "wwc": "wwc",
    "lpi": "lpi",
    "lpi-briefs": "lpi",
    "lpi-fact-sheets": "lpi",
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
    "jedm": "jedm",
    "jla": "jla",
    "casel": None,
}

SOURCE_NAME_MAP = {
    "wwc": "What Works Clearinghouse",
    "lpi": "Learning Policy Institute",
    "lpi-briefs": "Learning Policy Institute",
    "lpi-fact-sheets": "Learning Policy Institute",
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
    "credo": "CREDO at Stanford",
    "jedm": "Journal of Educational Data Mining",
    "jla": "Journal of Learning Analytics",
    "casel": "CASEL",
}

TYPE_MAP = {
    "intervention report": "report",
    "practice guide": "framework",
    "report": "report",
    "brief": "report",
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
    "paper": "paper",
    "guide": "framework",
    "family playbook": "framework",
    "model paper": "paper",
    "literature review": "review",
    # WestEd library labels (2026-08-30 backfill)
    "research and evaluation": "report",
    "case study": "report",
    "collection": "report",
    "edited volume": "report",
    "data visualization and infographic": "report",
    "tool": "tool",
    "assessment resource": "tool",
    "curriculum": "framework",
    "wested perspectives": "blog-post",
    "audiocast": "presentation",
    # EdTrust type-of-content labels (2026-08-30 backfill)
    "compilation": "report",
    "fact sheet": "report",
    "podcast": "presentation",
    "data tool": "tool",
    "digital report": "report",
    "infographic": "report",
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


EXTRA_COLUMNS = {
    # Everything the scraper collected for the row, as staged (JSON): listing
    # fields, API extras, page_meta from a detail fetch. Kept so later passes
    # (tagging, type review, description upgrades) never need a re-fetch.
    "raw_item": "TEXT",
    # The publisher's own topic labels for the item (JSON list), unmapped.
    "source_subjects": "TEXT",
}


def ensure_columns(conn):
    """Add any missing EXTRA_COLUMNS to entries (idempotent)."""
    have = {r[1] for r in conn.execute("PRAGMA table_info(entries)")}
    for col, typ in EXTRA_COLUMNS.items():
        if col not in have:
            conn.execute(f"ALTER TABLE entries ADD COLUMN {col} {typ}")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys=ON")
    ensure_columns(conn)
    return conn


def _raw_json(item):
    return json.dumps(item, ensure_ascii=False, sort_keys=True)


def _subjects_json(item):
    tags = item.get("tags")
    if isinstance(tags, list) and tags:
        return json.dumps([str(t) for t in tags], ensure_ascii=False)
    if isinstance(tags, str) and tags.strip():
        return json.dumps([tags.strip()], ensure_ascii=False)
    return None


def _verified_fields(item):
    """A detail fetch that returned 200 already proves the URL is live: record it
    so verify_urls.py does not request the same page again."""
    if item.get("fetched_status") == 200:
        return ("verified", "200", item.get("fetched_at") or TODAY)
    return ("unverified", None, None)


def get_last_entry_num():
    conn = get_db()
    row = conn.execute("SELECT MAX(num) FROM entries").fetchone()
    conn.close()
    return row[0] or 0


def infer_type(item):
    raw = item.get("type", "").strip().lower()
    return TYPE_MAP.get(raw, "report")


def insert_backlog_rows(conn, backlog_items, source_name, start_num):
    """Insert backlog items as excluded, pending rows. Skips URLs already in
    hub.db (active or excluded) and repeats within the batch. Returns
    (inserted_count, last_num_used)."""
    existing = {r[0] for r in conn.execute("SELECT url FROM entries")}
    num = start_num
    inserted = 0
    for item in backlog_items:
        url = (item.get("url") or "").strip()
        if not url or url in existing:
            continue
        existing.add(url)
        title = (item.get("title") or "").strip() or url
        url_status, http_status, verified_on = _verified_fields(item)
        conn.execute("""
            INSERT INTO entries (num, title, url, type, source, url_confirmed,
                description_inferred, date_added, doi, license, description,
                url_status, url_http_status, last_verified, excluded, exclude_reason,
                raw_item, source_subjects)
            VALUES (?, ?, ?, ?, ?, 0, 0, ?, NULL, NULL, '', ?, ?, ?, 1, ?, ?, ?)
        """, (num, title, url, infer_type(item), source_name, TODAY, url_status, http_status,
              verified_on, PENDING_REASON, _raw_json(item), _subjects_json(item)))
        num += 1
        inserted += 1
    return inserted, num - 1


def insert_filtered_rows(conn, filtered_items, source_name, start_num):
    """Insert items the type filter set aside as excluded rows with reason
    'type_filtered:<label>', keeping title, URL, any blurb and the raw item, so
    the scope call can be reversed with curate.py reactivate. Returns
    (inserted_count, last_num_used)."""
    existing = {r[0] for r in conn.execute("SELECT url FROM entries")}
    num = start_num
    inserted = 0
    for item in filtered_items:
        url = (item.get("url") or "").strip()
        if not url or url in existing:
            continue
        existing.add(url)
        title = (item.get("title") or "").strip() or url
        blurb = (item.get("blurb") or "").strip()
        desc_source = item.get("blurb_source") if blurb else None
        if desc_source not in DESCRIPTION_SOURCES:
            desc_source = None
        reason = item.get("filter_reason") or "type_filtered:unknown"
        url_status, http_status, verified_on = _verified_fields(item)
        conn.execute("""
            INSERT INTO entries (num, title, url, type, source, url_confirmed,
                description_inferred, date_added, doi, license, description,
                url_status, url_http_status, last_verified, excluded, exclude_reason,
                description_source, raw_item, source_subjects)
            VALUES (?, ?, ?, ?, ?, 1, 0, ?, NULL, NULL, ?, ?, ?, ?, 1, ?, ?, ?, ?)
        """, (num, title, url, infer_type(item), source_name, TODAY, blurb, url_status, http_status,
              verified_on, reason, desc_source, _raw_json(item), _subjects_json(item)))
        num += 1
        inserted += 1
    return inserted, num - 1


DESCRIPTION_SOURCES = ("listing", "page-meta", "page-abstract", "llm-summary", "manual")


def insert_items(conn, items, source_slug, source_name, start_num):
    """Insert ready items as active rows numbered from start_num; returns the
    count inserted. description_source comes from the item's blurb_source
    (scrape.py writes 'listing' or the detail_fetch label); a staging file
    without it, or with an unknown value, gets NULL rather than a guess."""
    inserted = 0
    for i, item in enumerate(items):
        num = start_num + i
        blurb = item.get("blurb", "").strip()
        desc_source = item.get("blurb_source")
        if desc_source not in DESCRIPTION_SOURCES:
            desc_source = None
        url_status, http_status, verified_on = _verified_fields(item)
        conn.execute("""
            INSERT INTO entries (num, title, url, type, source, url_confirmed,
                description_inferred, date_added, doi, license, description,
                url_status, url_http_status, last_verified, description_source,
                raw_item, source_subjects)
            VALUES (?, ?, ?, ?, ?, 1, 0, ?, NULL, NULL, ?, ?, ?, ?, ?, ?, ?)
        """, (num, item["title"].strip(), item["url"].strip(), infer_type(item),
              source_name, TODAY, blurb, url_status, http_status, verified_on, desc_source,
              _raw_json(item), _subjects_json(item)))
        for tag in infer_tags(item, source_slug):
            conn.execute("INSERT OR IGNORE INTO entry_tags (entry_num, tag) VALUES (?, ?)", (num, tag))
        inserted += 1
    return inserted


def infer_tags(item, source):
    tags = []
    src_tag = SOURCE_TAG_MAP.get(source)
    if src_tag:
        tags.append(src_tag)

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

    tier = item.get("evidence_tier", "").strip()
    if tier == "1":
        tags.append("rct")

    text = (item.get("title", "") + " " + item.get("blurb", "")).lower()
    for pattern, tag in KEYWORD_TAGS:
        if tag not in tags and re.search(pattern, text):
            tags.append(tag)

    return tags


def main():
    parser = argparse.ArgumentParser(description="Process staged JSON into hub.db")
    parser.add_argument("source", help="Source slug matching the staged JSON filename")
    parser.add_argument("--limit", type=int, default=None, help="Process only the first N items")
    parser.add_argument("--offset", type=int, default=0, help="Skip the first N items")
    parser.add_argument("--preview", action="store_true", help="Show entries without writing to DB")
    args = parser.parse_args()

    staged_path = STAGING_DIR / f"{args.source}.json"
    if not staged_path.exists():
        print(f"Error: no staged file at {staged_path}", file=sys.stderr)
        sys.exit(1)

    with open(staged_path, encoding="utf-8") as f:
        data = json.load(f)

    items = data.get("items", [])
    backlog = data.get("backlog_items", [])
    filtered = data.get("filtered_items", [])
    if not items and not backlog and not filtered:
        print("No ready, backlog or filtered items in staged file.")
        return

    items = items[args.offset:]
    if args.limit:
        items = items[:args.limit]

    print(f"[process] Source: {args.source}, {len(items)} items to process")

    start_num = get_last_entry_num() + 1
    source_name = SOURCE_NAME_MAP.get(args.source, args.source)

    if args.preview:
        for i, item in enumerate(items[:5]):
            num = start_num + i
            tags = infer_tags(item, args.source)
            print(f"  #{num} {item['title'][:60]}")
            print(f"    type={infer_type(item)} tags={tags}")
            print(f"    url={item['url'][:70]}")
            print()
        end_num = start_num + len(items) - 1
        print(f"[process] Preview: {len(items)} entries ({start_num}-{end_num})")
        return

    conn = get_db()

    # Dedup guard: never insert a URL already in hub.db (active or excluded —
    # excluded rows are kept precisely so they aren't re-indexed), and skip
    # within-batch repeats. scrape.py's diff normally handles this, but this
    # guard makes re-running a staging file (or a --no-diff scrape) safe.
    existing_urls = {r[0] for r in conn.execute("SELECT url FROM entries")}
    seen_batch = set()
    deduped = []
    for item in items:
        url = item["url"].strip()
        if url in existing_urls or url in seen_batch:
            continue
        seen_batch.add(url)
        deduped.append(item)
    if len(deduped) < len(items):
        print(f"[process] Skipped {len(items) - len(deduped)} duplicate URLs already in hub.db or repeated in batch")
    items = deduped

    inserted = insert_items(conn, items, args.source, source_name, start_num)
    end_num = start_num + inserted - 1
    if inserted:
        print(f"[process] Inserted {inserted} entries ({start_num}-{end_num}) into hub.db")
    else:
        print("[process] Nothing new to insert.")

    pending, pending_end = insert_backlog_rows(conn, backlog, source_name, start_num + inserted)
    if pending:
        print(f"[process] Backlog: {pending} pending rows ({start_num + inserted}-{pending_end}) "
              f"inserted as excluded ({PENDING_REASON})")
    filtered_n, filtered_end = insert_filtered_rows(conn, filtered, source_name, start_num + inserted + pending)
    if filtered_n:
        print(f"[process] Type filter: {filtered_n} rows ({start_num + inserted + pending}-{filtered_end}) "
              f"inserted as excluded (type_filtered:<label>)")
    conn.commit()
    conn.close()

    if inserted or pending or filtered_n:
        print("[process] Next: run `python scripts/build_from_db.py`")
        write_log(args.source, data, items, start_num, end_num, pending + filtered_n)


def write_log(source, staged_data, items, start_num, end_num, pending=0):
    source_name = SOURCE_NAME_MAP.get(source, source)
    total_staged = staged_data.get("total_ready", 0) + staged_data.get("total_backlog", 0)
    ready = staged_data.get("total_ready", 0)
    backlog = staged_data.get("total_backlog", 0)

    processed = f"- Processed: {len(items)} entries"
    if items:
        processed += f" ({start_num}-{end_num})"
    entry = (
        f"\n## {TODAY} - {source_name}\n"
        f"- Source slug: `{source}`\n"
        f"- Scraped: {total_staged} total, {ready} ready, {backlog} backlog\n"
        f"{processed}\n"
        f"- Backlog rows recorded as pending (excluded): {pending}\n"
        f"- Tags: keyword auto-tagged\n"
    )

    with open(PROCESSING_LOG, "a", encoding="utf-8") as f:
        f.write(entry)
    print(f"[process] Logged to {PROCESSING_LOG}")


if __name__ == "__main__":
    main()
