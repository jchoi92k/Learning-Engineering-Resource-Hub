"""Tests for scripts/curate.py against an in-memory database.

Run: python -m pytest tests/ -q
"""
import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import curate  # noqa: E402
from curate import (  # noqa: E402
    CurateError, exclude_entry, parse_tags, reactivate_entry, recent_entries, set_description, set_tags,
)
from test_pipeline import ENTRIES_DDL  # noqa: E402

LONG = "A description comfortably longer than the thirty-character minimum."
TAG_A, TAG_B = sorted(curate.TAG_VOCAB)[:2]


@pytest.fixture
def conn():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    c.executescript(ENTRIES_DDL)
    c.execute("INSERT INTO entries (num, title, url, type, source, date_added, description, "
              "description_source, updated_at) VALUES (1, 'One', 'https://x.org/1', 'report', 'S', "
              "'2026-01-01', ?, 'listing', '2000-01-01T00:00:00Z')", (LONG,))
    c.execute("INSERT INTO entries (num, title, url, type, source, date_added, description, excluded, "
              "exclude_reason, updated_at) VALUES (2, 'Two', 'https://x.org/2', 'report', 'T', "
              "'2026-01-02', '', 1, 'no_description_pending', '2000-01-01T00:00:00Z')")
    c.execute("INSERT INTO entry_tags VALUES (1, ?)", (TAG_A,))
    return c


def updated_at(conn, num):
    return conn.execute("SELECT updated_at FROM entries WHERE num = ?", (num,)).fetchone()[0]


# ── exclude / reactivate ──

def test_exclude_sets_flag_reason_and_bumps_updated_at(conn):
    assert exclude_entry(conn, 1, "out_of_scope") is True
    row = conn.execute("SELECT excluded, exclude_reason FROM entries WHERE num = 1").fetchone()
    assert tuple(row) == (1, "out_of_scope")
    assert updated_at(conn, 1) != "2000-01-01T00:00:00Z"


def test_exclude_refuses_unknown_reason(conn):
    with pytest.raises(CurateError, match="unknown exclude reason"):
        exclude_entry(conn, 1, "because")
    assert updated_at(conn, 1) == "2000-01-01T00:00:00Z"


def test_exclude_accepts_verify_urls_broken_pattern(conn):
    assert exclude_entry(conn, 1, "broken_url_404") is True


def test_exclude_same_reason_is_noop(conn):
    assert exclude_entry(conn, 2, "no_description_pending") is False
    assert updated_at(conn, 2) == "2000-01-01T00:00:00Z"


def test_exclude_unknown_entry(conn):
    with pytest.raises(CurateError, match="not found"):
        exclude_entry(conn, 99, "out_of_scope")


def test_reactivate_refuses_short_description(conn):
    with pytest.raises(CurateError, match="set-description first"):
        reactivate_entry(conn, 2)


def test_reactivate_clears_flag_after_description_set(conn):
    set_description(conn, 2, LONG, "page-abstract")
    assert reactivate_entry(conn, 2) is True
    row = conn.execute("SELECT excluded, exclude_reason FROM entries WHERE num = 2").fetchone()
    assert tuple(row) == (0, None)


def test_reactivate_active_entry_is_noop(conn):
    assert reactivate_entry(conn, 1) is False


# ── set-description ──

def test_set_description_cleans_text_and_records_source(conn):
    assert set_description(conn, 1, "  New text   with  odd\tspacing that is long enough.  ", "llm-summary")
    row = conn.execute("SELECT description, description_source FROM entries WHERE num = 1").fetchone()
    assert row[0] == "New text with odd spacing that is long enough."
    assert row[1] == "llm-summary"
    assert updated_at(conn, 1) != "2000-01-01T00:00:00Z"


def test_set_description_refuses_unknown_source(conn):
    with pytest.raises(CurateError, match="unknown description source"):
        set_description(conn, 1, LONG, "guess")


def test_set_description_refuses_short_text(conn):
    with pytest.raises(CurateError, match="minimum"):
        set_description(conn, 1, "too short", "manual")


def test_set_description_unchanged_is_noop(conn):
    assert set_description(conn, 1, LONG, "listing") is False
    assert updated_at(conn, 1) == "2000-01-01T00:00:00Z"


# ── set-tags ──

def test_parse_tags_normalises_and_dedupes():
    assert parse_tags(f" {TAG_A.upper()}, {TAG_B},{TAG_A},, ") == [TAG_A, TAG_B]


def test_parse_tags_refuses_unknown():
    with pytest.raises(CurateError, match="unknown tag"):
        parse_tags(f"{TAG_A},not-a-tag")


def test_parse_tags_refuses_empty():
    with pytest.raises(CurateError, match="no tags"):
        parse_tags(" , ")


def test_set_tags_replaces_whole_set(conn):
    assert set_tags(conn, 1, [TAG_B]) is True
    assert curate.get_tags(conn, 1) == [TAG_B]
    assert updated_at(conn, 1) != "2000-01-01T00:00:00Z"


def test_set_tags_same_set_is_noop(conn):
    assert set_tags(conn, 1, [TAG_A]) is False


# ── reads ──

def test_recent_lists_rows_after_num_with_tags(conn):
    rows = recent_entries(conn, 0)
    assert [r["num"] for r in rows] == [1, 2]
    assert rows[0]["tags"] == TAG_A
    assert rows[1]["tags"] is None
    assert [r["num"] for r in recent_entries(conn, 1)] == [2]
    assert [r["num"] for r in recent_entries(conn, 0, source="T")] == [2]


def test_entry_view_includes_tags_and_length(conn):
    view = curate.entry_view(conn, 1)
    assert view["tags"] == [TAG_A]
    assert view["description_chars"] == len(LONG)
    assert view["num"] == 1


# ── CLI ──

def test_cli_writes_through_a_file_db(tmp_path, capsys):
    db = tmp_path / "t.db"
    c = sqlite3.connect(db)
    c.executescript(ENTRIES_DDL)
    c.execute("INSERT INTO entries (num, title, url, type, source, date_added, description) "
              "VALUES (1, 'One', 'https://x.org/1', 'report', 'S', '2026-01-01', ?)", (LONG,))
    c.commit()
    c.close()
    assert curate.main(["--db", str(db), "set-tags", "1", f"{TAG_A},{TAG_B}"]) == 0
    assert curate.main(["--db", str(db), "exclude", "1", "--reason", "nope"]) == 1
    assert "unknown exclude reason" in capsys.readouterr().err
    assert curate.main(["--db", str(db), "show", "1", "--json"]) == 0
    assert f'"{TAG_A}"' in capsys.readouterr().out
    assert curate.main(["--db", str(tmp_path / "missing.db"), "show", "1"]) == 1
