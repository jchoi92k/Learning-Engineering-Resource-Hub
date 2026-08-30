"""Tests for the backfill additions: request audit, type filter with kept
rejects, raw_item / source_subjects columns, verified status from detail fetches.

Run: python -m pytest tests/ -q
"""
import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from process_staged import EXTRA_COLUMNS, ensure_columns, insert_backlog_rows, insert_filtered_rows, insert_items  # noqa: E402
from scrape import apply_type_filter, audit_request_log, read_request_log  # noqa: E402
from test_pipeline import ENTRIES_DDL  # noqa: E402

LONG = "A description comfortably longer than the thirty-character minimum."


def mem_db():
    conn = sqlite3.connect(":memory:")
    conn.executescript(ENTRIES_DDL)
    ensure_columns(conn)
    return conn


# ── request audit ──

def test_audit_flags_repeated_urls_and_short_gaps():
    reqs = [
        (100.0, "get", "200", "https://a.org/robots.txt", False),
        (105.0, "get", "200", "https://a.org/p1", False),
        (110.0, "get", "200", "https://a.org/p2", False),
        (112.0, "get", "200", "https://a.org/p1", False),   # repeat, 2 s after the last
    ]
    a = audit_request_log(reqs, expected_delay=5)
    assert a["requests"] == 4 and a["unique_urls"] == 3
    assert a["repeated"] == {"https://a.org/p1": 2}
    assert a["duplicates_ok"] is False
    assert a["min_gap"] == 2.0 and a["throttle_ok"] is False


def test_audit_passes_clean_run_and_ignores_retries():
    reqs = [
        (100.0, "get", "200", "https://a.org/robots.txt", False),
        (105.0, "get", "503", "https://a.org/p1", False),
        (110.0, "get", "200", "https://a.org/p1", True),    # retry after 503 is allowed
        (115.2, "get", "200", "https://b.org/p9", False),
    ]
    a = audit_request_log(reqs, expected_delay=5)
    assert a["duplicates_ok"] is True and a["throttle_ok"] is True
    assert a["retries"] == 1
    assert a["statuses"] == {"200": 3, "503": 1}
    assert a["min_gap_by_host"]["https://a.org".split("//")[1]] == 5.0


def test_read_request_log_roundtrip(tmp_path):
    log = tmp_path / "x-requests.log"
    log.write_text("# run 2026-08-30\n100.500\tget\t200\t-\thttps://a.org/p1\n106.000\tget\t429\tretry\thttps://a.org/p1\n",
                   encoding="utf-8")
    reqs = read_request_log(log)
    assert reqs == [(100.5, "get", "200", "https://a.org/p1", False), (106.0, "get", "429", "https://a.org/p1", True)]


# ── type filter ──

def test_type_filter_keeps_allowed_and_untyped_and_labels_rejects():
    items = [{"url": "u1", "type": "Research"}, {"url": "u2", "type": "Commentary"},
             {"url": "u3", "type": ""}, {"url": "u4", "type": " research "}]
    kept, filtered = apply_type_filter(items, {"type_allow": ["Research", "Report"]})
    assert [i["url"] for i in kept] == ["u1", "u3", "u4"]
    assert [i["url"] for i in filtered] == ["u2"]
    assert filtered[0]["filter_reason"] == "type_filtered:Commentary"


def test_type_filter_noop_without_config():
    items = [{"url": "u1", "type": "Podcast"}]
    assert apply_type_filter(items, {}) == (items, [])


# ── columns and inserts ──

def test_ensure_columns_is_idempotent():
    conn = sqlite3.connect(":memory:")
    conn.executescript(ENTRIES_DDL)
    ensure_columns(conn)
    ensure_columns(conn)
    cols = {r[1] for r in conn.execute("PRAGMA table_info(entries)")}
    assert set(EXTRA_COLUMNS) <= cols


def test_insert_items_keeps_raw_item_subjects_and_verified_status():
    conn = mem_db()
    items = [
        {"title": "A", "url": "https://x.org/a", "type": "Report", "blurb": LONG, "blurb_source": "page-abstract",
         "tags": ["Reading", "K-12 Education"], "authors": ["Someone"], "fetched_status": 200, "fetched_at": "2026-08-30",
         "page_meta": {"og:title": "A"}},
        {"title": "B", "url": "https://x.org/b", "type": "Report", "blurb": LONG, "blurb_source": "listing"},
    ]
    assert insert_items(conn, items, "s", "S", 1) == 2
    a = conn.execute("SELECT url_status, url_http_status, last_verified, source_subjects, raw_item FROM entries WHERE num = 1").fetchone()
    assert a[:3] == ("verified", "200", "2026-08-30")
    assert json.loads(a[3]) == ["Reading", "K-12 Education"]
    raw = json.loads(a[4])
    assert raw["authors"] == ["Someone"] and raw["page_meta"] == {"og:title": "A"}
    b = conn.execute("SELECT url_status, url_http_status, source_subjects FROM entries WHERE num = 2").fetchone()
    assert b == ("unverified", None, None)


def test_insert_filtered_rows_excluded_with_label_reason_and_dedup():
    conn = mem_db()
    conn.execute("INSERT INTO entries (num, title, url, type, source, date_added) VALUES (1, 'K', 'https://x.org/known', 'report', 'S', '2026-01-01')")
    filtered = [
        {"title": "Op-ed", "url": "https://x.org/op", "type": "Commentary", "blurb": LONG, "blurb_source": "listing",
         "filter_reason": "type_filtered:Commentary", "tags": ["Education"]},
        {"title": "Known", "url": "https://x.org/known", "type": "Commentary", "filter_reason": "type_filtered:Commentary"},
        {"title": "No blurb", "url": "https://x.org/pod", "type": "Podcast", "filter_reason": "type_filtered:Podcast"},
    ]
    n, last = insert_filtered_rows(conn, filtered, "S", 2)
    assert (n, last) == (2, 3)
    row = conn.execute("SELECT excluded, exclude_reason, description, description_source, source_subjects FROM entries WHERE num = 2").fetchone()
    assert row == (1, "type_filtered:Commentary", LONG, "listing", '["Education"]')
    row3 = conn.execute("SELECT excluded, exclude_reason, description, description_source FROM entries WHERE num = 3").fetchone()
    assert row3 == (1, "type_filtered:Podcast", "", None)


def test_backlog_rows_keep_raw_item():
    conn = mem_db()
    n, last = insert_backlog_rows(conn, [{"title": "T", "url": "https://x.org/t", "type": "Brief", "reason": "blurb too short (0 chars)", "date": "2026-05-01"}], "S", 1)
    assert (n, last) == (1, 1)
    raw = json.loads(conn.execute("SELECT raw_item FROM entries WHERE num = 1").fetchone()[0])
    assert raw["date"] == "2026-05-01" and raw["reason"].startswith("blurb too short")


def test_curate_accepts_type_filtered_reason():
    from curate import valid_reason
    assert valid_reason("type_filtered:Commentary")
    assert valid_reason("type_filtered:Training and Professional Development")
    assert not valid_reason("type_filtered:")
    assert not valid_reason("filtered")


# ── detail fetch: extra fields, page_meta, fetched_status ──

def test_detail_fetch_records_page_meta_extra_fields_and_status(monkeypatch):
    import scrape

    class Resp:
        status_code = 200
        text = ("<html><head><title>Page T</title>"
                "<meta name=\"description\" content=\"Teaser from the page that is long enough.\">"
                "<meta property=\"og:type\" content=\"article\">"
                "<meta property=\"article:published_time\" content=\"2026-03-04T00:00:00Z\">"
                "<link rel=\"canonical\" href=\"https://x.org/t\"></head>"
                "<body><span class=\"ptype\">Podcast</span></body></html>")

    monkeypatch.setattr(scrape, "fetch", lambda url, **kw: Resp())
    monkeypatch.setattr(scrape, "_save_progress", lambda *a, **kw: None)
    cfg = {"detail_fetch": {"selector": "meta[name='description']", "attr": "content",
                            "extra_fields": {"type": {"selector": "span.ptype"}}}}
    out = scrape.fetch_detail_descriptions([{"title": "T", "url": "https://x.org/t", "blurb": "", "type": ""}], cfg, "x")
    item = out[0]
    assert item["fetched_status"] == 200 and item["fetched_at"]
    assert item["type"] == "Podcast"
    assert item["page_meta"]["og:type"] == "article"
    assert item["page_meta"]["article:published_time"] == "2026-03-04T00:00:00Z"
    assert item["page_meta"]["canonical"] == "https://x.org/t"
    assert item["page_meta"]["title"] == "Page T"
    kept, filtered = scrape.apply_type_filter(out, {"type_allow": ["Report"]})
    assert kept == [] and filtered[0]["filter_reason"] == "type_filtered:Podcast"


# ── persistent per-host throttle ──

def test_throttle_waits_after_previous_process_request(monkeypatch, tmp_path):
    import time
    import scrape
    monkeypatch.setattr(scrape, "LAST_REQUEST_FILE", tmp_path / "last-request.json")
    monkeypatch.setattr(scrape, "_request_delay", 0.4)
    monkeypatch.setattr(scrape, "_last_fetch_time", 0)      # a fresh process: no in-memory clock
    scrape._save_last_request("example.org", time.time())    # ...but another process just hit the host
    t0 = time.time()
    scrape._throttle("https://example.org/page")
    assert time.time() - t0 >= 0.35, "waited for the delay recorded by the previous process"
    monkeypatch.setattr(scrape, "_last_fetch_time", 0)      # fresh process again
    t1 = time.time()
    scrape._throttle("https://other.org/page")               # a host nobody has hit: no wait
    assert time.time() - t1 < 0.2


def test_read_request_log_returns_latest_run_by_default(tmp_path):
    log = tmp_path / 'x-requests.log'
    nl, tab = chr(10), chr(9)
    log.write_text('# run 1' + nl + tab.join(['100.0', 'get', '200', '-', 'https://a.org/1']) + nl
                   + '# run 2' + nl + tab.join(['200.0', 'get', '200', '-', 'https://a.org/2']) + nl,
                   encoding='utf-8')
    assert [r[3] for r in read_request_log(log)] == ['https://a.org/2']
    assert [r[3] for r in read_request_log(log, last_run_only=False)] == ['https://a.org/1', 'https://a.org/2']


def test_extract_page_text_strips_chrome_and_caps():
    from bs4 import BeautifulSoup
    import scrape
    html = ("<html><body><nav>Menu Menu</nav><header>Site header</header>"
            "<main><h1>Title</h1><p>First   paragraph of the article.</p><script>var x=1;</script>"
            "<p>Second paragraph.</p><aside>Related links</aside></main><footer>Footer text</footer></body></html>")
    text = scrape.extract_page_text(BeautifulSoup(html, "html.parser"))
    assert text == "Title First paragraph of the article. Second paragraph."
    assert scrape.extract_page_text(BeautifulSoup("<html><body>" + "word " * 100 + "</body></html>", "html.parser"), max_chars=20) == "word word word word "


# ── lookups and set-url ──

def test_resolve_lookups_maps_ids_to_names(monkeypatch):
    import scrape

    class Resp:
        status_code = 200

        @staticmethod
        def json():
            return [{"id": 235, "name": "Report"}, {"id": 247, "name": "Blog &amp; Commentary"}]

    monkeypatch.setattr(scrape, "fetch", lambda url, **kw: Resp())
    items = [{"type": [235], "tags": [235, 247]}, {"type": [247, 235]}, {"type": ""}, {"type": [999]}]
    cfg = {"lookups": [{"field": "type", "url": "https://x.org/tax"}, {"field": "tags", "url": "https://x.org/tax"}]}
    out = scrape.resolve_lookups(items, cfg)
    assert out[0]["type"] == "Report" and out[0]["type_ids"] == ["235"]
    assert out[0]["tags"] == ["Report", "Blog & Commentary"] and out[0]["tags_ids"] == ["235", "247"]
    assert out[1]["type"] == "Blog & Commentary" and out[1]["type_labels"] == ["Blog & Commentary", "Report"]
    assert out[2]["type"] == "" and out[3]["type"] == [999]


def test_set_url_replaces_and_refuses_collisions():
    from curate import CurateError, set_url
    import pytest
    conn = mem_db()
    conn.row_factory = sqlite3.Row
    conn.execute("INSERT INTO entries (num, title, url, type, source, date_added) VALUES (1, 'A', 'https://x.org/old', 'report', 'S', '2026-01-01')")
    conn.execute("INSERT INTO entries (num, title, url, type, source, date_added) VALUES (2, 'B', 'https://x.org/b', 'report', 'S', '2026-01-01')")
    assert set_url(conn, 1, "https://x.org/new/") is True
    assert conn.execute("SELECT url FROM entries WHERE num = 1").fetchone()[0] == "https://x.org/new/"
    with pytest.raises(CurateError, match="already used"):
        set_url(conn, 1, "https://x.org/b")
    with pytest.raises(CurateError, match="not a URL"):
        set_url(conn, 1, "b")


# ── API pagination stops on a short page ──

def test_scrape_api_stops_after_short_page(monkeypatch):
    import scrape
    calls = []

    class Resp:
        status_code = 200

        def __init__(self, page):
            self.page = page
            self.url = f"https://x.org/api?page={page}"

        def json(self):
            n = 3 if self.page == 1 else 1          # per_page=3, page 2 is short
            return [{"title": f"T{self.page}-{i}", "link": f"https://x.org/{self.page}-{i}"} for i in range(n)]

    def fake_fetch(url, **kw):
        calls.append(kw.get("params", {}).get("page"))
        return Resp(kw["params"]["page"])

    monkeypatch.setattr(scrape, "fetch", fake_fetch)
    monkeypatch.setattr(scrape, "_load_url_filter", lambda config: None)
    cfg = {"discovery_url": "https://x.org/api",
           "api": {"params": {"per_page": 3}, "pagination": {"param": "page", "start": 1, "pages": 10},
                   "json_paths": {"title": "title", "url": "link"}}}
    items = scrape.scrape_api(cfg)
    assert calls == [1, 2], "stopped after the short page instead of running to the cap"
    assert len(items) == 4


def test_extract_page_text_honours_selector():
    from bs4 import BeautifulSoup
    import scrape
    html = "<html><body><nav>Menu</nav><div class='txtcol'><h4>Description</h4><p>The abstract.</p></div><div>Elsewhere</div></body></html>"
    soup = BeautifulSoup(html, "html.parser")
    assert scrape.extract_page_text(soup, selector="div.txtcol") == "Description The abstract."
    assert scrape.extract_page_text(soup, selector="div.missing") == "Menu Description The abstract. Elsewhere".replace("Menu ", "")
