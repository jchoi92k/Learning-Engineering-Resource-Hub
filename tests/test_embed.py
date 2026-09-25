"""Tests for the index pruning helpers in scripts/embed_corpus.py.

Run: python -m pytest tests/ -q
Guards the cloud deploy (2026-09-25): a runner has no data/embed-cache.json,
so vectors of de-published entries are found only by listing the index.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from embed_corpus import list_index_ids, stale_ids  # noqa: E402


class FakeResponse:
    def __init__(self, body):
        self.body = body

    def raise_for_status(self):
        pass

    def json(self):
        return self.body


class FakeSession:
    """Serves list-vectors pages keyed by the cursor it is asked for."""

    def __init__(self, pages):
        self.pages = pages
        self.cursors = []

    def get(self, url, params, timeout):
        cursor = params.get("cursor")
        self.cursors.append(cursor)
        return FakeResponse({"success": True, "result": self.pages[cursor]})


def test_stale_ids_without_a_cache_come_from_the_index():
    assert stale_ids({}, ["1", "2", "9001"], {"1", "2"}) == ["9001"]


def test_stale_ids_merge_cache_and_index_without_duplicates():
    assert stale_ids({"5": "h", "7": "h"}, ["5", "8"], {"7"}) == ["5", "8"]


def test_list_index_ids_follows_the_cursor_until_the_last_page():
    session = FakeSession({
        None: {"vectors": [{"id": "1"}, {"id": "2"}], "isTruncated": True, "nextCursor": "c1"},
        "c1": {"vectors": [{"id": "3"}], "isTruncated": False, "nextCursor": None},
    })
    assert list_index_ids(session, "acct") == ["1", "2", "3"]
    assert session.cursors == [None, "c1"]
