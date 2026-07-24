"""Unit tests for the pure helpers in the scraping/build pipeline.

Run: python -m pytest tests/ -q
No network, no database writes — these cover the tagging/typing business
rules and JSON-path logic that change most often.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from scrape import diff_items, resolve_json_path, split_by_blurb, strip_html
from process_staged import infer_tags, infer_type


# ── resolve_json_path ──

def test_json_path_nested_dict():
    obj = {"a": {"b": {"c": 42}}}
    assert resolve_json_path(obj, "a/b/c") == 42


def test_json_path_dotted_keys():
    obj = {"metadata": {"dc.title": [{"value": "Hello"}]}}
    assert resolve_json_path(obj, "metadata/dc.title/0/value") == "Hello"


def test_json_path_array_wildcard():
    obj = {"items": [{"name": "x"}, {"name": "y"}]}
    assert resolve_json_path(obj, "items/*/name") == ["x", "y"]


def test_json_path_wildcard_terminal():
    obj = {"items": [1, 2, 3]}
    assert resolve_json_path(obj, "items/*") == [1, 2, 3]


def test_json_path_missing_key():
    assert resolve_json_path({"a": 1}, "b/c") is None


def test_json_path_bad_index():
    assert resolve_json_path({"a": [1]}, "a/5") is None
    assert resolve_json_path({"a": [1]}, "a/x") is None


def test_json_path_wildcard_on_non_list():
    assert resolve_json_path({"a": {"b": 1}}, "a/*") is None


# ── strip_html ──

def test_strip_html_tags():
    assert strip_html("<p>Hello <b>world</b></p>") == "Hello world"


def test_strip_html_empty():
    assert strip_html("") == ""
    assert strip_html(None) == ""


# ── infer_type ──

def test_infer_type_known():
    assert infer_type({"type": "Practice Guide"}) == "framework"
    assert infer_type({"type": "journal article"}) == "paper"
    assert infer_type({"type": "toolkit"}) == "tool"
    assert infer_type({"type": "data set"}) == "dataset"


def test_infer_type_unknown_defaults_to_report():
    assert infer_type({"type": "mystery format"}) == "report"
    assert infer_type({}) == "report"


# ── infer_tags ──

def test_infer_tags_keyword_literacy():
    item = {"title": "Improving reading comprehension", "blurb": ""}
    assert "literacy" in infer_tags(item, "unknown-source")


def test_infer_tags_keyword_math():
    item = {"title": "Algebra intervention outcomes", "blurb": ""}
    tags = infer_tags(item, "unknown-source")
    assert "math-education" in tags


def test_infer_tags_grade_level():
    item = {"title": "x", "blurb": "", "grade_level": "PK-2"}
    tags = infer_tags(item, "unknown-source")
    assert "prekindergarten" in tags


def test_infer_tags_numeric_grade_implies_k12():
    item = {"title": "x", "blurb": "", "grade_level": "3-5"}
    assert "k-12" in infer_tags(item, "unknown-source")


def test_infer_tags_evidence_tier_rct():
    item = {"title": "x", "blurb": "", "evidence_tier": "1"}
    assert "rct" in infer_tags(item, "unknown-source")


def test_infer_tags_no_duplicates():
    item = {"title": "reading and more reading literacy", "blurb": "reading"}
    tags = infer_tags(item, "unknown-source")
    assert len(tags) == len(set(tags))


# ── diff_items ──

def test_diff_items_splits_new_and_existing():
    items = [{"url": "https://a.org/1"}, {"url": "https://a.org/2/"}]
    existing = {"https://a.org/2"}
    new, seen = diff_items(items, existing)
    assert [i["url"] for i in new] == ["https://a.org/1"]
    assert [i["url"] for i in seen] == ["https://a.org/2/"]


def test_diff_items_normalizes_case_and_slash():
    items = [{"url": "https://A.org/Page/"}]
    new, seen = diff_items(items, {"https://a.org/page"})
    assert new == [] and len(seen) == 1


# ── split_by_blurb ──

def test_split_by_blurb():
    long_blurb = "x" * 500
    items = [{"blurb": long_blurb}, {"blurb": "short"}, {}]
    ready, backlog = split_by_blurb(items, threshold=100)
    assert len(ready) == 1
    assert len(backlog) == 2
    assert all("backlog_reason" in i for i in backlog)
