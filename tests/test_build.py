"""Tests for the llms.txt index builders in scripts/build_from_db.py.

Run: python -m pytest tests/ -q
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from build_from_db import (  # noqa: E402
    INDEX_CHAR_LIMIT, OTHER_SLUG, compact_line, db_size_check, find_duplicate_urls, group_by_source, source_slug,
    split_lines,
)
from test_pipeline import ENTRIES_DDL  # noqa: E402


def entry(num, source, title="T", tags=None):
    return {"num": num, "source": source, "title": title, "url": f"https://x.org/{num}", "type": "report",
            "tags": tags or ["k-12"], "desc": "d", "url_confirmed": 1, "description_inferred": 0,
            "doi": None, "license": None, "date_added": "2026-01-01", "description_source": "listing"}


def test_db_size_check(tmp_path):
    db = tmp_path / "hub.db"
    db.write_bytes(b"x" * 2048)
    size, err = db_size_check(str(db), limit_mib=60)
    assert err is None and 0 < size < 0.01
    size, err = db_size_check(str(db), limit_mib=0.001)
    assert "over the 0.001 MiB limit" in err and "100 MiB" in err


def test_find_duplicate_urls_covers_excluded_rows_and_ignores_markers():
    import sqlite3
    conn = sqlite3.connect(":memory:")
    conn.executescript(ENTRIES_DDL)
    conn.execute("DROP INDEX idx_entries_url_norm")   # the check exists for databases that predate the index
    ins = ("INSERT INTO entries (num, title, url, type, source, date_added, excluded, exclude_reason) "
           "VALUES (?, 'T', ?, 'report', 'S', '2026-01-01', ?, ?)")
    conn.executemany(ins, [
        (1, "https://x.org/a", 0, None),
        (2, "https://x.org/a", 1, "wwc_tier_minus1_no_evidence"),   # exact copy, excluded
        (3, "https://X.org/A/", 1, "wwc_tier_minus1_no_evidence"),  # case + trailing slash
        (4, "https://x.org/b", 0, None),
        (5, "https://x.org/b", 1, "duplicate_url"),                 # deliberate marker: ignored
        (6, "https://x.org/c", 1, "out_of_scope"),
    ])
    assert find_duplicate_urls(conn) == [("https://x.org/a", [1, 2, 3])]


def test_source_slug():
    assert source_slug("What Works Clearinghouse") == "what-works-clearinghouse"
    assert source_slug("National Center for Education Statistics (NCES)") == "national-center-for-education-statistics-nces"
    assert source_slug("U.S. Department of Education") == "u-s-department-of-education"


def test_split_lines_respects_limit_and_order():
    lines = [f"line-{i:04d}-" + "x" * 90 for i in range(50)]   # ~100 chars each
    parts = split_lines(lines, header_chars=100, limit=1000)
    assert [ln for part in parts for ln in part] == lines
    for part in parts:
        assert 100 + sum(len(ln) + 1 for ln in part) <= 1000
    assert len(parts) == 7   # 8 lines fit per part under the limit


def test_split_lines_single_part_when_small():
    assert split_lines(["a", "b"], 10, limit=INDEX_CHAR_LIMIT) == [["a", "b"]]


def test_group_by_source_puts_small_sources_together():
    entries = [entry(i, "Big") for i in range(1, 13)] + [entry(20, "Tiny A"), entry(21, "Tiny B"), entry(22, "Tiny A")]
    groups = group_by_source(entries, per_source_min=10)
    assert [g[0] for g in groups] == ["big", OTHER_SLUG]
    assert len(groups[0][2]) == 12
    other = groups[1][2]
    assert [e["num"] for e in other] == [20, 22, 21]       # sorted by source name, then num
    assert "2 organizations" in groups[1][1]


def test_group_by_source_orders_largest_first():
    entries = [entry(i, "A") for i in range(1, 11)] + [entry(i, "B") for i in range(11, 31)]
    assert [g[0] for g in group_by_source(entries, per_source_min=10)] == ["b", "a"]


def test_compact_line_shape():
    assert compact_line(entry(7, "S", "Title", ["rct", "k-12"])) == "- 7. [Title](https://x.org/7) | report | rct, k-12"
