#!/usr/bin/env python3
"""
One-time migration: parse llms-full.txt + metadata into meta/hub.db.

Usage:
    python meta/migrate_to_db.py
    python meta/migrate_to_db.py --dry-run
"""
import json
import os
import re
import sqlite3
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
LLMS_FULL = REPO_ROOT / "docs" / "llms-full.txt"
VERIFICATION_FILE = SCRIPT_DIR / "url-verification.json"
SOURCE_TARGETS = SCRIPT_DIR / "source-targets.json"
DB_PATH = SCRIPT_DIR / "hub.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS entries (
    num                  INTEGER PRIMARY KEY,
    title                TEXT NOT NULL,
    url                  TEXT NOT NULL,
    type                 TEXT NOT NULL,
    source               TEXT NOT NULL,
    url_confirmed        INTEGER NOT NULL DEFAULT 1,
    description_inferred INTEGER NOT NULL DEFAULT 0,
    date_added           TEXT NOT NULL,
    doi                  TEXT,
    license              TEXT,
    description          TEXT NOT NULL DEFAULT '',
    url_status           TEXT NOT NULL DEFAULT 'unverified',
    url_http_status      TEXT,
    last_verified        TEXT,
    excluded             INTEGER NOT NULL DEFAULT 0,
    exclude_reason       TEXT,
    created_at           TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    updated_at           TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE TABLE IF NOT EXISTS entry_tags (
    entry_num   INTEGER NOT NULL REFERENCES entries(num) ON DELETE CASCADE,
    tag         TEXT NOT NULL,
    PRIMARY KEY (entry_num, tag)
);

CREATE TABLE IF NOT EXISTS source_targets (
    source_name     TEXT PRIMARY KEY,
    known_total     INTEGER,
    priority        TEXT NOT NULL DEFAULT 'medium',
    status          TEXT NOT NULL DEFAULT 'active',
    discovery_url   TEXT,
    sample_url      TEXT,
    discovery_check TEXT,
    notes           TEXT
);

CREATE INDEX IF NOT EXISTS idx_entries_source ON entries(source);
CREATE INDEX IF NOT EXISTS idx_entries_type ON entries(type);
CREATE INDEX IF NOT EXISTS idx_entries_url ON entries(url);
CREATE INDEX IF NOT EXISTS idx_entries_url_status ON entries(url_status);
CREATE INDEX IF NOT EXISTS idx_entries_excluded ON entries(excluded);
CREATE INDEX IF NOT EXISTS idx_entry_tags_tag ON entry_tags(tag);
"""


def parse_entries():
    """Parse llms-full.txt into a list of entry dicts. Same logic as build_tags.py."""
    with open(LLMS_FULL, encoding="utf-8") as f:
        content = f.read()

    entry_pattern = re.compile(
        r'###\s+(\d+)\.\s+(.+?)\n\s*```yaml\n(.*?)```\s*\n(.*?)(?=\n---|\Z)',
        re.DOTALL
    )

    entries = []
    for m in entry_pattern.finditer(content):
        num = int(m.group(1))
        title = m.group(2).strip()
        yaml_block = m.group(3).strip()
        desc = m.group(4).strip()

        fields = {}
        for line in yaml_block.split("\n"):
            line = line.strip()
            if ":" in line:
                key, val = line.split(":", 1)
                fields[key.strip()] = val.strip()

        url = fields.get("url", "").strip('"')
        entry_type = fields.get("type", "report")
        source = fields.get("source", "").strip('"')
        url_confirmed = fields.get("url_confirmed", "true").lower() == "true"
        desc_inferred = fields.get("description_inferred", "false").lower() == "true"
        date_added = fields.get("date_added", "")
        doi = fields.get("doi", "null")
        if doi == "null":
            doi = None
        lic = fields.get("license", "null")
        if lic == "null":
            lic = None

        tags_raw = fields.get("tags", "[]")
        tags_match = re.match(r'\[(.*)\]', tags_raw)
        tags = [t.strip() for t in tags_match.group(1).split(",") if t.strip()] if tags_match else []

        entries.append({
            "num": num,
            "title": title,
            "url": url,
            "type": entry_type,
            "source": source,
            "url_confirmed": url_confirmed,
            "description_inferred": desc_inferred,
            "date_added": date_added,
            "doi": doi,
            "license": lic,
            "tags": tags,
            "description": desc,
        })

    return entries


def load_verification():
    if VERIFICATION_FILE.exists():
        with open(VERIFICATION_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def load_source_targets():
    if SOURCE_TARGETS.exists():
        with open(SOURCE_TARGETS, encoding="utf-8") as f:
            raw = f.read()
        data = json.loads(raw)
        data.pop("_comment", None)
        return data
    return {}


def main():
    dry_run = "--dry-run" in sys.argv

    print("[migrate] Parsing llms-full.txt...")
    entries = parse_entries()
    print(f"[migrate] Parsed {len(entries)} entries")

    verification = load_verification()
    targets = load_source_targets()

    if dry_run:
        print(f"[migrate] Dry run — would create hub.db with {len(entries)} entries")
        print(f"[migrate] Verification data for {len(verification)} URLs")
        print(f"[migrate] Source targets: {len(targets)} sources")
        return

    if DB_PATH.exists():
        DB_PATH.unlink()
        print("[migrate] Removed existing hub.db")

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(SCHEMA)

    # Insert entries (skip duplicates — keep first occurrence)
    seen_nums = set()
    skipped = 0
    for e in entries:
        if e["num"] in seen_nums:
            skipped += 1
            continue
        seen_nums.add(e["num"])
        url_key = e["url"].rstrip("/")
        url_status = "unverified"
        url_http_status = None
        last_verified = None
        excluded = 0
        exclude_reason = None

        if url_key in verification:
            v = verification[url_key]
            url_status = "verified" if v.get("ok") else "broken"
            url_http_status = str(v.get("status", ""))
            last_verified = v.get("last_verified")
            if url_status == "broken":
                excluded = 1
                exclude_reason = "broken_url"

        conn.execute("""
            INSERT INTO entries (num, title, url, type, source, url_confirmed,
                description_inferred, date_added, doi, license, description,
                url_status, url_http_status, last_verified, excluded, exclude_reason)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            e["num"], e["title"], e["url"], e["type"], e["source"],
            1 if e["url_confirmed"] else 0,
            1 if e["description_inferred"] else 0,
            e["date_added"], e["doi"], e["license"], e["description"],
            url_status, url_http_status, last_verified, excluded, exclude_reason,
        ))

        for tag in e["tags"]:
            conn.execute("INSERT INTO entry_tags (entry_num, tag) VALUES (?, ?)", (e["num"], tag))

    # Insert source targets
    for source_name, meta in targets.items():
        conn.execute("""
            INSERT INTO source_targets (source_name, known_total, priority, status,
                discovery_url, sample_url, discovery_check, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            source_name, meta.get("known_total"), meta.get("priority", "medium"),
            meta.get("status", "active"), meta.get("discovery_url"),
            meta.get("sample_url"), meta.get("discovery_check"), meta.get("notes"),
        ))

    conn.commit()

    # Summary
    entry_count = conn.execute("SELECT COUNT(*) FROM entries").fetchone()[0]
    tag_count = conn.execute("SELECT COUNT(DISTINCT tag) FROM entry_tags").fetchone()[0]
    verified = conn.execute("SELECT COUNT(*) FROM entries WHERE url_status='verified'").fetchone()[0]
    broken = conn.execute("SELECT COUNT(*) FROM entries WHERE url_status='broken'").fetchone()[0]
    excluded_count = conn.execute("SELECT COUNT(*) FROM entries WHERE excluded=1").fetchone()[0]
    source_count = conn.execute("SELECT COUNT(*) FROM source_targets").fetchone()[0]

    conn.close()

    print(f"[migrate] Created {DB_PATH}")
    if skipped:
        print(f"[migrate] Skipped {skipped} duplicate entry numbers")
    print(f"[migrate] Entries: {entry_count}")
    print(f"[migrate] Unique tags: {tag_count}")
    print(f"[migrate] URL status: {verified} verified, {broken} broken, {entry_count - verified - broken} unverified")
    print(f"[migrate] Excluded: {excluded_count}")
    print(f"[migrate] Source targets: {source_count}")


if __name__ == "__main__":
    main()
