"""Unit tests for the pure helpers in the scraping/build pipeline.

Run: python -m pytest tests/ -q
No network, no database writes — these cover the tagging/typing business
rules and JSON-path logic that change most often.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from scrape import clean_text, diff_items, early_stop_hit, resolve_json_path, split_by_blurb, strip_html
from process_staged import infer_tags, infer_type, insert_backlog_rows, insert_items


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
    # strip_html leaves a space per tag; clean_text collapses them
    assert clean_text(strip_html("<p>Hello <b>world</b></p>")) == "Hello world"


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


# ── early_stop_hit ──

def _items(*urls):
    return [{"url": u} for u in urls]


def test_early_stop_three_consecutive_known():
    existing = {"https://a.org/1", "https://a.org/2", "https://a.org/3"}
    page = _items("https://a.org/new", "https://a.org/1", "https://a.org/2", "https://a.org/3")
    assert early_stop_hit(page, existing) is True


def test_early_stop_not_triggered_when_known_are_interleaved():
    existing = {"https://a.org/1", "https://a.org/2", "https://a.org/3", "https://a.org/4"}
    page = _items("https://a.org/1", "https://a.org/n1", "https://a.org/2", "https://a.org/n2",
                  "https://a.org/3", "https://a.org/n3", "https://a.org/4")
    # 4 known, never 3 in a row, below the 5-total threshold
    assert early_stop_hit(page, existing) is False


def test_early_stop_five_total_known():
    existing = {f"https://a.org/{i}" for i in range(1, 6)}
    page = _items("https://a.org/1", "https://a.org/x", "https://a.org/2", "https://a.org/y",
                  "https://a.org/3", "https://a.org/z", "https://a.org/4", "https://a.org/w",
                  "https://a.org/5")
    assert early_stop_hit(page, existing) is True


def test_early_stop_normalizes_case_and_slash():
    existing = {"https://a.org/page"}
    page = _items("https://A.org/Page/", "https://a.org/PAGE", "https://a.org/page/")
    assert early_stop_hit(page, existing) is True


def test_early_stop_disabled_without_existing_urls():
    page = _items("https://a.org/1", "https://a.org/2", "https://a.org/3")
    assert early_stop_hit(page, None) is False
    assert early_stop_hit(page, set()) is False


def test_early_stop_all_new_page():
    page = _items("https://a.org/n1", "https://a.org/n2", "https://a.org/n3")
    assert early_stop_hit(page, {"https://a.org/old"}) is False


def test_scrape_pagination_stops_early_and_respects_hard_cap(monkeypatch):
    """Stub fetch: page N lists items /p{N}-1 .. /p{N}-4. Pages 2+ are all indexed."""
    import scrape

    class Resp:
        def __init__(self, n):
            self.text = "".join(
                f'<div class="c"><a class="t" href="/p{n}-{i}">T{n}{i}</a><p class="b">{"x" * 40}</p></div>'
                for i in range(1, 5)
            )

    fetched = []

    def fake_fetch(url, **kw):
        fetched.append(url)
        return Resp(len(fetched))

    monkeypatch.setattr(scrape, "fetch", fake_fetch)
    config = {
        "discovery_url": "https://a.org/list",
        "url_prefix": "https://a.org",
        "pagination": {"param": "page", "start": 1},
        "selectors": {"item": "div.c", "title": "a.t", "url": "a.t", "blurb": "p.b"},
        "early_stop": True,
    }
    existing = {f"https://a.org/p{n}-{i}" for n in (2, 3, 4, 5) for i in range(1, 5)}

    items = scrape.scrape_pagination(config, max_pages=None, existing_urls=existing)
    assert len(fetched) == 2, "should fetch page 1 (all new) and page 2 (all known), then stop"
    assert len(items) == 8

    fetched.clear()
    scrape.scrape_pagination(config, max_pages=1, existing_urls=existing)
    assert len(fetched) == 1, "--pages hard cap still applies"

    fetched.clear()
    existing_none = scrape.scrape_pagination(config, max_pages=3, existing_urls=None)
    assert len(fetched) == 3 and len(existing_none) == 12, "no early-stop when diff disabled"

    fetched.clear()
    undeclared = {k: v for k, v in config.items() if k != "early_stop"}
    scrape.scrape_pagination(undeclared, max_pages=3, existing_urls=existing)
    assert len(fetched) == 3, "no early-stop unless the config declares early_stop: true"


def test_extract_cards_applies_url_transform():
    """LPI's listing links one item through Drupal's /index%2Ephp/ front controller;
    the config's url_transform strips it so the diff sees the canonical path."""
    import scrape
    html = ('<div class="c"><a class="t" href="/index%2Ephp/product/x">T</a><p class="b">' + 'x' * 40 + '</p></div>'
            '<div class="c"><a class="t" href="/product/y">U</a><p class="b">' + 'y' * 40 + '</p></div>')
    config = {"url_prefix": "https://a.org", "url_transform": {"replace": "/index%2Ephp/", "with": "/"},
              "selectors": {"item": "div.c", "title": "a.t", "url": "a.t", "blurb": "p.b"}}
    items = scrape.extract_cards(scrape.BeautifulSoup(html, "html.parser"), config)
    assert [i["url"] for i in items] == ["https://a.org/product/x", "https://a.org/product/y"]


def test_early_stop_requires_config_flag_in_api_path(monkeypatch):
    """scrape_api must scan every page when the config lacks early_stop, even
    if every item on page 0 is already indexed (Digital Promise regression)."""
    import scrape

    calls = []

    class Resp:
        def __init__(self, page):
            self.page = page

        def json(self):
            return {"items": [{"t": f"T{self.page}{i}", "u": f"https://a.org/{self.page}-{i}"} for i in range(3)]}

    def fake_fetch(url, **kw):
        calls.append(kw["params"]["page"])
        return Resp(kw["params"]["page"])

    monkeypatch.setattr(scrape, "fetch", fake_fetch)
    config = {
        "discovery_url": "https://a.org/api",
        "api": {"params": {}, "pagination": {"param": "page", "start": 0, "pages": 3},
                "json_paths": {"items": "items", "title": "t", "url": "u"}},
    }
    existing = {f"https://a.org/{p}-{i}" for p in range(3) for i in range(3)}
    scrape.scrape_api(config, existing_urls=existing)
    assert calls == [0, 1, 2], "all three pages fetched without the flag"

    calls.clear()
    scrape.scrape_api({**config, "early_stop": True}, existing_urls=existing)
    assert calls == [0], "early-stop after page 0 once declared"


# ── clean_text ──

def test_clean_text_collapses_whitespace_and_nbsp():
    raw = "Get\u00a0early  insights\n\tfrom\r\n the  study "
    assert clean_text(raw) == "Get early insights from the study"


def test_clean_text_handles_empty_and_non_str():
    assert clean_text("") == ""
    assert clean_text(None) == ""
    assert clean_text(42) == "42"


# ── text extraction: word boundaries, entities, invisible characters (H7) ──

def test_strip_html_keeps_word_boundaries():
    assert strip_html("<p>Ends here.</p><p>Next</p>") == "Ends here.  Next"
    assert clean_text(strip_html("<p>Ends here.</p><p>Next</p>")) == "Ends here. Next"
    assert clean_text(strip_html("<em>ThinkerTools</em>is a program")) == "ThinkerTools is a program"


def test_clean_text_tightens_symbols_and_punctuation():
    # what get_text(" ") produces for "Composition<sup>®</sup> (CIRC<sup>®</sup>)"
    assert clean_text("Composition \u00ae (CIRC \u00ae ) is") == "Composition\u00ae (CIRC\u00ae) is"
    assert clean_text("Packs \u2122 \u2013 Family ( Reading ) .") == "Packs\u2122 \u2013 Family (Reading)."
    assert clean_text("a , b ; c ?") == "a, b; c?"


def test_clean_text_decodes_entities_and_drops_invisible_chars():
    assert clean_text("Cognitive Tutor&reg; Algebra &amp; more &#8217;s") == "Cognitive Tutor® Algebra & more ’s"
    assert clean_text("zero​width soft­hyphen") == "zerowidth softhyphen"


def test_extract_cards_keeps_space_between_inline_elements():
    from bs4 import BeautifulSoup
    from scrape import extract_cards
    html_doc = ('<div class="c"><a class="t" href="/x"><em>Project SEED</em>is</a>'
                '<p class="b"><em>ThinkerTools</em>is a computer-based program. It has <b>two</b>parts.</p></div>')
    soup = BeautifulSoup(html_doc, "html.parser")
    config = {"selectors": {"item": "div.c", "title": "a.t", "url": "a.t", "blurb": "p.b"}}
    [item] = extract_cards(soup, config)
    assert item["title"] == "Project SEED is"
    assert item["blurb"] == "ThinkerTools is a computer-based program. It has two parts."


# ── backlog rows (pending, excluded) ──

ENTRIES_DDL = """
CREATE TABLE entries (
    num INTEGER PRIMARY KEY, title TEXT NOT NULL, url TEXT NOT NULL, type TEXT NOT NULL,
    source TEXT NOT NULL, url_confirmed INTEGER NOT NULL DEFAULT 1,
    description_inferred INTEGER NOT NULL DEFAULT 0, date_added TEXT NOT NULL, doi TEXT,
    license TEXT, description TEXT NOT NULL DEFAULT '', url_status TEXT NOT NULL DEFAULT 'unverified',
    url_http_status TEXT, last_verified TEXT, excluded INTEGER NOT NULL DEFAULT 0,
    exclude_reason TEXT, created_at TEXT NOT NULL DEFAULT '', updated_at TEXT NOT NULL DEFAULT '',
    description_source TEXT, raw_item TEXT, source_subjects TEXT
);
CREATE TABLE entry_tags (entry_num INTEGER, tag TEXT, PRIMARY KEY (entry_num, tag));
CREATE UNIQUE INDEX idx_entries_url_norm ON entries(lower(rtrim(url,'/')));
"""


def test_insert_backlog_rows_marks_pending_and_dedupes():
    import sqlite3
    conn = sqlite3.connect(":memory:")
    conn.executescript(ENTRIES_DDL)
    conn.execute("INSERT INTO entries (num, title, url, type, source, date_added) "
                 "VALUES (1, 'Known', 'https://x.org/known', 'report', 'S', '2026-01-01')")
    backlog = [
        {"url": "https://x.org/known", "title": "already in db"},
        {"url": "https://X.org/KNOWN/", "title": "case and trailing-slash variant of a known row"},
        {"url": "https://x.org/new", "title": "", "type": "Brief"},
        {"url": "https://x.org/new", "title": "repeat in batch"},
        {"url": "", "title": "no url"},
    ]
    n, last = insert_backlog_rows(conn, backlog, "S", 2)
    assert (n, last) == (1, 2)
    row = conn.execute("SELECT title, type, excluded, exclude_reason, description, url_confirmed "
                       "FROM entries WHERE num = 2").fetchone()
    assert row == ("https://x.org/new", "report", 1, "no_description_pending", "", 0)
    assert conn.execute("SELECT COUNT(*) FROM entries").fetchone()[0] == 2



# ── throttle hardening ──

def test_effective_delay_floors_config_values():
    from scrape import DEFAULT_DELAY, MIN_DELAY, effective_delay
    assert effective_delay({}) == DEFAULT_DELAY
    assert effective_delay({"request_delay": 2}) == MIN_DELAY
    assert effective_delay({"request_delay": 60}) == 60
    assert effective_delay({"request_delay": "fast"}) == DEFAULT_DELAY


def test_no_source_config_undercuts_the_delay_floor():
    import json
    from scrape import MIN_DELAY, SOURCES_DIR
    configs = sorted(SOURCES_DIR.glob("*.json"))
    assert configs, "no source configs found"
    for path in configs:
        cfg = json.loads(path.read_text(encoding="utf-8"))
        assert cfg.get("request_delay", MIN_DELAY) >= MIN_DELAY, path.name


def test_check_robots_starts_the_throttle_clock(monkeypatch):
    import scrape

    class Resp:
        status_code = 200
        text = "User-agent: *\nDisallow: /search/\n"

    monkeypatch.setattr(scrape.SESSION, "get", lambda url, **kw: Resp())
    monkeypatch.setattr(scrape, "_last_fetch_time", 0)
    assert scrape.check_robots({"robots_txt": "https://x.org/robots.txt"})
    assert scrape._last_fetch_time > 0, "the next fetch must wait a full delay after robots.txt"


def test_backoff_retry_restarts_the_throttle_clock(monkeypatch):
    import scrape

    class Resp:
        status_code = 200

    monkeypatch.setattr(scrape.time, "sleep", lambda s: None)
    monkeypatch.setattr(scrape.SESSION, "request", lambda *a, **kw: Resp())
    monkeypatch.setattr(scrape, "_last_fetch_time", 0)
    assert scrape._handle_rate_limit(429, "https://x.org/p") is not None
    assert scrape._last_fetch_time > 0


# ── description_source provenance ──

def test_insert_items_records_description_source():
    import sqlite3
    conn = sqlite3.connect(":memory:")
    conn.executescript(ENTRIES_DDL)
    items = [
        {"title": "A", "url": "https://x.org/a", "type": "Report", "blurb": "From the listing",
         "blurb_source": "listing"},
        {"title": "B", "url": "https://x.org/b", "type": "Brief", "blurb": "From the page",
         "blurb_source": "page-abstract"},
        {"title": "C", "url": "https://x.org/c", "type": "", "blurb": "Old staging file, no label"},
        {"title": "D", "url": "https://x.org/d", "type": "", "blurb": "Bad label", "blurb_source": "guess"},
    ]
    assert insert_items(conn, items, "wwc", "What Works Clearinghouse", 10) == 4
    rows = conn.execute("SELECT num, description_source FROM entries ORDER BY num").fetchall()
    assert rows == [(10, "listing"), (11, "page-abstract"), (12, None), (13, None)]
    assert conn.execute("SELECT excluded, description FROM entries WHERE num = 11").fetchone() == (0, "From the page")
    assert conn.execute("SELECT COUNT(*) FROM entry_tags WHERE entry_num = 10 AND tag = 'wwc'").fetchone()[0] == 1


def test_detail_fetch_labels_description_source(monkeypatch):
    import scrape

    class Resp:
        text = '<html><head><meta name="description" content="Teaser sentence from the page."></head></html>'

    monkeypatch.setattr(scrape, "fetch", lambda url, **kw: Resp())
    monkeypatch.setattr(scrape, "_save_progress", lambda *a, **kw: None)
    cfg = {"detail_fetch": {"selector": "meta[name='description']", "attr": "content"}}
    out = scrape.fetch_detail_descriptions([{"title": "T", "url": "https://x.org/t", "blurb": ""}], cfg, "x")
    assert out[0]["blurb"] == "Teaser sentence from the page."
    assert out[0]["blurb_source"] == "page-meta", "meta tags default to page-meta"
    cfg["detail_fetch"]["description_source"] = "page-abstract"
    out = scrape.fetch_detail_descriptions([{"title": "T", "url": "https://x.org/t", "blurb": ""}], cfg, "x")
    assert out[0]["blurb_source"] == "page-abstract", "config label wins"
