"""
Curate individual hub.db entries from the command line.

This is the agent-side writer for hub.db: alongside process_staged.py
(inserts) and verify_urls.py (URL status), it is the only sanctioned way to
change an existing row. Every write bumps updated_at, prints the before/after
of the touched fields, and refuses values outside the controlled vocabularies
(tags: TAG_CATEGORIES; description_source: DESCRIPTION_SOURCES; exclude
reasons: EXCLUDE_REASONS).

Usage (from repo root):
    python scripts/curate.py show NUM [--json]
    python scripts/curate.py recent --since-num N [--source NAME] [--json]
    python scripts/curate.py exclude NUM --reason REASON
    python scripts/curate.py reactivate NUM
    python scripts/curate.py set-description NUM --source SRC (--file PATH | --text TEXT)
    python scripts/curate.py set-tags NUM tag1,tag2,...

    --db PATH   use another database file (default data/hub.db)

Exit status: 0 on success or a no-op, 1 on a refused/invalid request.
After any write, run `python scripts/build_from_db.py` to regenerate docs/.
"""
import argparse
import json
import os
import re
import sqlite3
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from build_from_db import DESCRIPTION_SOURCES, MIN_DESCRIPTION_CHARS, TAG_CATEGORIES  # noqa: E402
from scrape import clean_text  # noqa: E402

REPO_ROOT = os.path.dirname(SCRIPT_DIR)
DB_PATH = os.path.join(REPO_ROOT, "data", "hub.db")

TAG_VOCAB = frozenset(t for tags in TAG_CATEGORIES.values() for t in tags)

# Reasons an entry may be excluded from the published outputs. The first
# block is what the pipeline and the June 2026 clean-ups already wrote;
# `out_of_scope` is the weekly review's reason for dropping a row whose
# subject is not education. verify_urls.py also writes `broken_url_<status>`.
EXCLUDE_REASONS = frozenset({
    "broken_url",
    "campbell_not_education_group",
    "duplicate_url",
    "essa_no_evidence_no_description",
    "mathematica_no_description",
    "no_description_pending",
    "wwc_tier_minus1_no_evidence",
    "out_of_scope",
})
BROKEN_URL_RE = re.compile(r"^broken_url_\d{3}$")
# process_staged.py writes type_filtered:<source type label> for items a
# config's type_allow list set aside (kept so the scope call can be reversed).
TYPE_FILTERED_RE = re.compile(r"^type_filtered:\S.*$")

NOW_SQL = "strftime('%Y-%m-%dT%H:%M:%SZ', 'now')"
SHOW_FIELDS = ("num", "title", "url", "type", "source", "date_added", "excluded", "exclude_reason",
               "description_source", "description_inferred", "url_status", "url_confirmed",
               "doi", "license", "created_at", "updated_at")
OPTIONAL_FIELDS = ("source_subjects", "raw_item")   # present once process_staged has added them


class CurateError(Exception):
    """A refused request: unknown entry, invalid value, or a bad argument."""


# ── helpers ──

def get_db(path=DB_PATH):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def get_entry(conn, num):
    row = conn.execute("SELECT * FROM entries WHERE num = ?", (num,)).fetchone()
    if row is None:
        raise CurateError(f"entry #{num} not found")
    return dict(row)


def get_tags(conn, num):
    return [r[0] for r in conn.execute(
        "SELECT tag FROM entry_tags WHERE entry_num = ? ORDER BY tag", (num,))]


def valid_reason(reason):
    return reason in EXCLUDE_REASONS or bool(BROKEN_URL_RE.match(reason)) or bool(TYPE_FILTERED_RE.match(reason))


def parse_tags(spec):
    """Split a comma-separated tag list, normalise, validate, dedupe (order kept)."""
    tags = []
    for raw in spec.split(","):
        tag = raw.strip().lower()
        if not tag:
            continue
        if tag not in TAG_VOCAB:
            raise CurateError(f"unknown tag '{tag}' — see TAG_CATEGORIES in build_from_db.py")
        if tag not in tags:
            tags.append(tag)
    if not tags:
        raise CurateError("no tags given")
    return tags


def _short(text, n=80):
    text = text or ""
    return text if len(text) <= n else text[:n - 1] + "…"


def _print_change(label, before, after):
    print(f"  {label}: {before!r} -> {after!r}")


# ── writes ──

def exclude_entry(conn, num, reason):
    """Mark an entry excluded. Returns True if the row changed."""
    if not valid_reason(reason):
        raise CurateError(f"unknown exclude reason '{reason}' — allowed: "
                          + ", ".join(sorted(EXCLUDE_REASONS)) + ", broken_url_<status>, type_filtered:<label>")
    row = get_entry(conn, num)
    if row["excluded"] and row["exclude_reason"] == reason:
        print(f"#{num} already excluded ({reason}); nothing to do")
        return False
    with conn:
        conn.execute(f"UPDATE entries SET excluded = 1, exclude_reason = ?, updated_at = {NOW_SQL} "
                     "WHERE num = ?", (reason, num))
    print(f"#{num} excluded — {_short(row['title'])}")
    _print_change("excluded", row["excluded"], 1)
    _print_change("exclude_reason", row["exclude_reason"], reason)
    return True


def reactivate_entry(conn, num):
    """Clear the excluded flag. Refuses rows whose description is too short to publish."""
    row = get_entry(conn, num)
    if not row["excluded"]:
        print(f"#{num} is already active; nothing to do")
        return False
    if len(row["description"] or "") < MIN_DESCRIPTION_CHARS:
        raise CurateError(f"#{num} has a {len(row['description'] or '')}-char description "
                          f"(minimum {MIN_DESCRIPTION_CHARS}); set-description first")
    with conn:
        conn.execute(f"UPDATE entries SET excluded = 0, exclude_reason = NULL, updated_at = {NOW_SQL} "
                     "WHERE num = ?", (num,))
    print(f"#{num} reactivated — {_short(row['title'])}")
    _print_change("excluded", row["excluded"], 0)
    _print_change("exclude_reason", row["exclude_reason"], None)
    if not row["description_source"]:
        print("  warning: description_source is NULL — set-description to record provenance")
    return True


def set_description(conn, num, text, source):
    """Replace the description and record where the text came from."""
    if source not in DESCRIPTION_SOURCES:
        raise CurateError(f"unknown description source '{source}' — allowed: "
                          + ", ".join(sorted(DESCRIPTION_SOURCES)))
    text = clean_text(text or "")
    if len(text) < MIN_DESCRIPTION_CHARS:
        raise CurateError(f"description is {len(text)} chars (minimum {MIN_DESCRIPTION_CHARS})")
    row = get_entry(conn, num)
    if row["description"] == text and row["description_source"] == source:
        print(f"#{num} description unchanged; nothing to do")
        return False
    with conn:
        conn.execute(f"UPDATE entries SET description = ?, description_source = ?, updated_at = {NOW_SQL} "
                     "WHERE num = ?", (text, source, num))
    old = row["description"] or ""
    print(f"#{num} description set — {_short(row['title'])}")
    print(f"  length: {len(old)} -> {len(text)}")
    _print_change("description_source", row["description_source"], source)
    print(f"  before: {_short(old, 120)}")
    print(f"  after:  {_short(text, 120)}")
    return True


def set_tags(conn, num, tags):
    """Replace the entry's full tag set (validated against TAG_CATEGORIES)."""
    row = get_entry(conn, num)
    before = get_tags(conn, num)
    if sorted(tags) == before:
        print(f"#{num} tags unchanged; nothing to do")
        return False
    with conn:
        conn.execute("DELETE FROM entry_tags WHERE entry_num = ?", (num,))
        conn.executemany("INSERT INTO entry_tags (entry_num, tag) VALUES (?, ?)",
                         [(num, t) for t in tags])
        conn.execute(f"UPDATE entries SET updated_at = {NOW_SQL} WHERE num = ?", (num,))
    print(f"#{num} tags set — {_short(row['title'])}")
    _print_change("tags", ", ".join(before) or "(none)", ", ".join(sorted(tags)))
    return True


# ── reads ──

def entry_view(conn, num):
    row = get_entry(conn, num)
    view = {k: row[k] for k in SHOW_FIELDS}
    for k in OPTIONAL_FIELDS:
        if k in row:
            try:
                view[k] = json.loads(row[k]) if row[k] else None
            except ValueError:
                view[k] = row[k]
    view["tags"] = get_tags(conn, num)
    view["description_chars"] = len(row["description"] or "")
    view["description"] = row["description"]
    return view


def show_entry(conn, num, as_json=False):
    view = entry_view(conn, num)
    if as_json:
        print(json.dumps(view, ensure_ascii=False, indent=2))
        return
    for k in SHOW_FIELDS:
        print(f"{k:20s} {view[k]}")
    print(f"{'tags':20s} {', '.join(view['tags']) or '(none)'}")
    if view.get("source_subjects"):
        print(f"{'source_subjects':20s} {', '.join(view['source_subjects'])}")
    if view.get("raw_item"):
        keys = sorted(view["raw_item"]) if isinstance(view["raw_item"], dict) else []
        print(f"{'raw_item':20s} ({len(keys)} fields: {', '.join(keys)})")
    print(f"{'description':20s} ({view['description_chars']} chars)")
    print(view["description"] or "")


def recent_entries(conn, since_num, source=None):
    sql = ("SELECT e.*, (SELECT group_concat(tag, ', ') FROM (SELECT tag FROM entry_tags "
           "WHERE entry_num = e.num ORDER BY tag)) AS tags FROM entries e WHERE e.num > ?")
    params = [since_num]
    if source:
        sql += " AND e.source = ?"
        params.append(source)
    sql += " ORDER BY e.num"
    return [dict(r) for r in conn.execute(sql, params)]


def print_recent(rows, as_json=False):
    if as_json:
        keep = ("num", "title", "url", "type", "source", "date_added", "excluded", "exclude_reason",
                "description_source", "description", "tags")
        print(json.dumps([{k: r[k] for k in keep} for r in rows], ensure_ascii=False, indent=2))
        return
    if not rows:
        print("no entries")
        return
    print(f"{'num':>5}  {'source':22.22}  {'type':10.10}  {'state':22.22}  {'desc':>5}  {'src':13.13}  title / tags")
    for r in rows:
        state = f"excluded:{r['exclude_reason']}" if r["excluded"] else "active"
        print(f"{r['num']:>5}  {r['source']:22.22}  {r['type']:10.10}  {state:22.22}  "
              f"{len(r['description'] or ''):>5}  {(r['description_source'] or '-'):13.13}  {_short(r['title'], 70)}")
        print(f"{'':5}  tags: {r['tags'] or '(none)'}")


# ── CLI ──

def build_parser():
    p = argparse.ArgumentParser(description="Curate hub.db entries (the agent-side writer).")
    p.add_argument("--db", default=DB_PATH, help="database file (default data/hub.db)")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("show", help="print one entry with its tags")
    s.add_argument("num", type=int)
    s.add_argument("--json", action="store_true")

    s = sub.add_parser("recent", help="list entries with num > N (a run's inserts)")
    s.add_argument("--since-num", type=int, required=True)
    s.add_argument("--source", help="restrict to one source name (as stored in hub.db)")
    s.add_argument("--json", action="store_true")

    s = sub.add_parser("exclude", help="hold an entry out of the published outputs")
    s.add_argument("num", type=int)
    s.add_argument("--reason", required=True)

    s = sub.add_parser("reactivate", help="clear the excluded flag")
    s.add_argument("num", type=int)

    s = sub.add_parser("set-description", help="replace the description and its provenance")
    s.add_argument("num", type=int)
    s.add_argument("--source", required=True, choices=sorted(DESCRIPTION_SOURCES))
    g = s.add_mutually_exclusive_group(required=True)
    g.add_argument("--file", help="UTF-8 text file holding the new description")
    g.add_argument("--text", help="the new description")

    s = sub.add_parser("set-tags", help="replace the entry's tags (comma-separated)")
    s.add_argument("num", type=int)
    s.add_argument("tags")
    return p


def run(args, conn):
    if args.cmd == "show":
        show_entry(conn, args.num, args.json)
    elif args.cmd == "recent":
        print_recent(recent_entries(conn, args.since_num, args.source), args.json)
    elif args.cmd == "exclude":
        exclude_entry(conn, args.num, args.reason)
    elif args.cmd == "reactivate":
        reactivate_entry(conn, args.num)
    elif args.cmd == "set-description":
        if args.file:
            with open(args.file, encoding="utf-8") as f:
                text = f.read()
        else:
            text = args.text
        set_description(conn, args.num, text, args.source)
    elif args.cmd == "set-tags":
        set_tags(conn, args.num, parse_tags(args.tags))


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    args = build_parser().parse_args(argv)
    if not os.path.exists(args.db):
        print(f"error: database not found: {args.db}", file=sys.stderr)
        return 1
    conn = get_db(args.db)
    try:
        run(args, conn)
    except CurateError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
