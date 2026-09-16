"""Tests for the backfill additions: request audit, type filter with kept
rejects, raw_item / source_subjects columns, verified status from detail fetches.

Run: python -m pytest tests/ -q
"""
import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from process_staged import (  # noqa: E402
    EXTRA_COLUMNS,
    _authors_json,
    _norm_date,
    backfill_metadata,
    ensure_columns,
    insert_backlog_rows,
    insert_filtered_rows,
    insert_items,
)
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
    reqs.append((125.2, "post", "200", "https://api.example/query", False))
    reqs.append((130.4, "post", "200", "https://api.example/query", False))   # POST pagination: same URL, different body
    a = audit_request_log(reqs, expected_delay=5)
    assert a["duplicates_ok"] is True and a["throttle_ok"] is True
    assert a["retries"] == 1
    assert a["statuses"] == {"200": 5, "503": 1}
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


def test_field_filter_sets_aside_matching_values_with_the_rule_reason():
    from scrape import apply_field_filter
    cfg = {"exclude_when": [{"field": "evidence_tier", "values": ["-1"], "reason": "wwc_tier_minus1_no_evidence"}]}
    items = [{"url": "u1", "evidence_tier": "3"}, {"url": "u2", "evidence_tier": "-1"},
             {"url": "u3"}, {"url": "u4", "evidence_tier": " -1 "}]
    kept, filtered = apply_field_filter(items, cfg)
    assert [i["url"] for i in kept] == ["u1", "u3"]
    assert [(i["url"], i["filter_reason"]) for i in filtered] == [
        ("u2", "wwc_tier_minus1_no_evidence"), ("u4", "wwc_tier_minus1_no_evidence")]
    assert apply_field_filter(items, {}) == (items, [])


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
    assert valid_reason("essa_no_evidence")
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


def test_detail_fetch_metadata_only_with_list_and_regex_fields(monkeypatch):
    # WestEd (2026-09-15): dates and authors exist only on the item page; the
    # listing blurb is fine and must survive. fetch_all forces the fetch,
    # "multiple" collects one author per element, "regex" pulls the year out of
    # "Copyright: 2026", and no description selector means no blurb change.
    import scrape

    class Resp:
        status_code = 200
        text = ("<html><body><p class='byline'>By A. One and B. Two</p>"
                "<div class='ctb-item'><p class='ctb-name'>A. One</p></div>"
                "<div class='ctb-item'><p class='ctb-name'>B. Two</p></div>"
                "<p class='res-copyright'>Copyright: 2026</p></body></html>")

    monkeypatch.setattr(scrape, "fetch", lambda url, **kw: Resp())
    monkeypatch.setattr(scrape, "_save_progress", lambda *a, **kw: None)
    cfg = {"detail_fetch": {"fetch_all": True, "extra_fields": {
        "authors": {"selector": ".ctb-item .ctb-name", "multiple": True},
        "date": {"selector": "p.res-copyright", "regex": r"Copyright:\s*(\d{4})"}}}}
    item = {"title": "T", "url": "https://x.org/t", "blurb": "A listing blurb long enough to keep.", "blurb_source": "listing"}
    done = {"title": "D", "url": "https://x.org/d", "blurb": "Fetched earlier.", "fetched_status": 200, "authors": ["Kept"]}
    out, kept = scrape.fetch_detail_descriptions([item, done], cfg, "x")
    assert out["authors"] == ["A. One", "B. Two"]
    assert out["date"] == "2026"
    assert sorted(out["detail_fields"]) == ["authors", "date"]
    assert out["blurb"] == "A listing blurb long enough to keep." and out["blurb_source"] == "listing"
    # A resumed run (2026-09-16 DNS outage) must not re-fetch pages it already has.
    assert kept["authors"] == ["Kept"] and "date" not in kept


def test_fetch_stores_every_200_response_in_the_raw_sidecar(monkeypatch, tmp_path):
    # 2026-09-16: a field mapped after a crawl (WestEd's PDF link) must be a
    # local pass over stored pages, not another 900-page fetch. Only 200s are
    # kept; the index names the URL; read_raw finds the body by URL.
    import scrape

    class Resp:
        def __init__(self, status, text, ctype, url):
            self.status_code, self.text, self.url = status, text, url
            self.headers = {"Content-Type": ctype}

    calls = iter([Resp(200, "<html>page</html>", "text/html; charset=utf-8", "https://x.org/p"),
                  Resp(200, '{"a": 1}', "application/json", "https://x.org/api?q=1"),
                  Resp(404, "nope", "text/html", "https://x.org/missing")])
    monkeypatch.setattr(scrape.SESSION, "get", lambda url, **kw: next(calls))
    monkeypatch.setattr(scrape, "_throttle", lambda url: None)
    monkeypatch.setattr(scrape, "RAW_DIR", tmp_path)
    monkeypatch.setattr(scrape, "_request_log_path", None)
    monkeypatch.setattr(scrape, "CONSECUTIVE_FAILURES", 0)
    scrape._start_raw_store("src")
    assert scrape.fetch("https://x.org/p").status_code == 200
    assert scrape.fetch("https://x.org/api?q=1").status_code == 200
    assert scrape.fetch("https://x.org/missing") is None
    files = sorted(p.name for p in (tmp_path / "src").iterdir())
    assert len([f for f in files if f.endswith(".html.gz")]) == 1
    assert len([f for f in files if f.endswith(".json.gz")]) == 1
    index = (tmp_path / "src" / "index.tsv").read_text(encoding="utf-8").splitlines()
    assert len(index) == 2 and index[0].endswith("https://x.org/p")
    assert scrape.read_raw("src", "https://x.org/p/") == "<html>page</html>", "same dedup key as hub.db"
    assert scrape.read_raw("src", "https://x.org/missing") is None
    scrape._raw_source = None


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
    conn.execute("INSERT INTO entries (num, title, url, type, source, date_added, url_status, url_confirmed) "
                 "VALUES (1, 'A', 'https://x.org/old', 'report', 'S', '2026-01-01', 'verified', 1)")
    conn.execute("INSERT INTO entries (num, title, url, type, source, date_added) VALUES (2, 'B', 'https://x.org/b', 'report', 'S', '2026-01-01')")
    assert set_url(conn, 1, "https://x.org/new/") is True
    assert conn.execute("SELECT url FROM entries WHERE num = 1").fetchone()[0] == "https://x.org/new/"
    assert tuple(conn.execute("SELECT url_status, url_confirmed FROM entries WHERE num = 1").fetchone()) == ("unverified", 0), \
        "a changed URL is unverified until verify_urls.py checks it"
    with pytest.raises(CurateError, match="already used"):
        set_url(conn, 1, "https://x.org/b")
    with pytest.raises(CurateError, match="already used"):
        set_url(conn, 1, "https://X.org/B/")   # same row up to case and trailing slash
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


def test_scrape_api_windows_run_separate_passes(monkeypatch):
    import scrape
    bodies = []

    class Resp:
        status_code = 200
        url = "https://x.org/api"

        def __init__(self, body):
            self.body = body

        def json(self):
            tag = self.body.get("numericFilters", ["all"])[0]
            return {"hits": [{"post_title": f"T-{tag}", "permalink": f"https://x.org/{tag}"}]}

    def fake_post(url, headers=None, json_body=None):
        bodies.append(dict(json_body))
        return Resp(json_body)

    monkeypatch.setattr(scrape, "fetch_post", fake_post)
    monkeypatch.setattr(scrape, "_load_url_filter", lambda config: None)
    cfg = {"discovery_url": "https://x.org/api",
           "api": {"method": "POST", "body": {"query": ""}, "params": {},
                   "pagination": {"param": "page", "start": 0, "pages": 1},
                   "windows": [{"numericFilters": ["a"]}, {"numericFilters": ["b"]}],
                   "json_paths": {"items": "hits", "title": "post_title", "url": "permalink"}}}
    items = scrape.scrape_api(cfg)
    assert [b.get("numericFilters") for b in bodies] == [["a"], ["b"]]
    assert [i["url"] for i in items] == ["https://x.org/a", "https://x.org/b"]


def test_detail_fetch_keeps_richer_existing_page_text(monkeypatch):
    import scrape

    class Resp:
        status_code = 200
        text = "<html><body><main><p>Short page text.</p></main></body></html>"

    monkeypatch.setattr(scrape, "fetch", lambda url, **kw: Resp())
    monkeypatch.setattr(scrape, "_save_progress", lambda *a, **kw: None)
    rich = "An already-supplied body text from the API that is much longer than the page extraction. " * 3
    cfg = {"detail_fetch": {"selector": "main p"}}
    out = scrape.fetch_detail_descriptions([{"title": "T", "url": "https://x.org/t", "blurb": "", "page_text": rich}], cfg, "x")
    assert out[0]["page_text"] == rich
    out2 = scrape.fetch_detail_descriptions([{"title": "T", "url": "https://x.org/t", "blurb": ""}], cfg, "x")
    assert out2[0]["page_text"] == "Short page text."


def test_failure_streaks_count_per_host(monkeypatch):
    import scrape
    monkeypatch.setattr(scrape, "_FAILURES_BY_HOST", {})
    monkeypatch.setattr(scrape, "CONSECUTIVE_FAILURES", 0)
    scrape._note_failure("https://a.org/1")
    scrape._note_failure("https://b.org/1")
    scrape._note_failure("https://c.org/1")
    assert scrape.CONSECUTIVE_FAILURES == 1, "three different hosts failing once is not a streak"
    scrape._note_failure("https://a.org/2")
    scrape._note_failure("https://a.org/3")
    assert scrape.CONSECUTIVE_FAILURES == 3, "one host failing three times in a row is"
    scrape._note_success("https://a.org/4")
    assert scrape.CONSECUTIVE_FAILURES == 1, "a success clears that host's streak; b.org still has one"


def test_403_from_primary_host_trips_block_stop(monkeypatch):
    import scrape
    monkeypatch.setattr(scrape, "_FAILURES_BY_HOST", {})
    monkeypatch.setattr(scrape, "_BLOCK_BY_HOST", {})
    monkeypatch.setattr(scrape, "CONSECUTIVE_FAILURES", 0)
    monkeypatch.setattr(scrape, "HOST_BLOCKED", None)
    monkeypatch.setattr(scrape, "PRIMARY_HOST", "primary.org")

    # A single 403 from the primary host is not yet a block.
    scrape._note_failure("https://primary.org/a", status=403)
    assert scrape.HOST_BLOCKED is None
    # Two consecutive 403s from the primary host trip the fast stop (< the
    # generic 3-failure threshold).
    scrape._note_failure("https://primary.org/b", status=403)
    assert scrape.HOST_BLOCKED == "primary.org"
    # A 200 from the primary host clears the block.
    scrape._note_success("https://primary.org/c")
    assert scrape.HOST_BLOCKED is None


def test_403_from_external_host_does_not_trip_block_stop(monkeypatch):
    # Outbound paywall 403s (e.g. CASEL -> tandfonline) must never halt a run.
    import scrape
    monkeypatch.setattr(scrape, "_FAILURES_BY_HOST", {})
    monkeypatch.setattr(scrape, "_BLOCK_BY_HOST", {})
    monkeypatch.setattr(scrape, "CONSECUTIVE_FAILURES", 0)
    monkeypatch.setattr(scrape, "HOST_BLOCKED", None)
    monkeypatch.setattr(scrape, "PRIMARY_HOST", "casel.org")

    scrape._note_failure("https://tandfonline.com/x", status=403)
    scrape._note_failure("https://tandfonline.com/y", status=403)
    assert scrape.HOST_BLOCKED is None, "external-host 403s are not a block of our source"


# ── metadata backfill (dates / authors / subjects on existing rows) ──

def test_norm_date_keeps_given_granularity():
    assert _norm_date("2026-09") == "2026-09"
    assert _norm_date("2026-09-14") == "2026-09-14"
    assert _norm_date("September 9, 2026") == "2026-09-09"
    assert _norm_date("August 2026") == "2026-08"
    assert _norm_date("Sept 2026") == "2026-09"
    assert _norm_date("2026") == "2026"
    assert _norm_date("") is None
    assert _norm_date("no date here") is None
    assert _norm_date("2026-13") is None, "month out of range is not a date"
    assert _norm_date("2026-02-31") == "2026-02-31", "day range is 1-31 only (calendar not checked)"
    assert _norm_date("2026-02-00") is None
    assert _norm_date("2025/04/23") == "2025-04-23", "OJS citation_date uses slashes (2026-09-16)"
    assert _norm_date("06/06/2023") == "2023-06-06" and _norm_date("12/12/2020") == "2020-12-12", "CREDO listing, US order"
    assert _norm_date("13/06/2023") is None
    assert _norm_date("2026-03-04T12:50:00+00:00") == "2026-03-04"


def test_norm_date_epoch_ms_takes_the_eastern_calendar_day():
    # Mathematica's Coveo index (2026-09-15): the page shows "Published: Jul 17, 2026"
    # for 1784264400000 (2026-07-17 05:00 UTC), and an entry made at 22:10 EDT on
    # 2024-11-01 is stored as 1730513400000 = 2024-11-02 02:10 UTC.
    assert _norm_date(1784264400000) == "2026-07-17"
    assert _norm_date("1730513400000") == "2024-11-01", "evening entry must not roll to the UTC day"
    assert _norm_date(1732074720000) == "2024-11-19"


def test_metadata_provenance_follows_where_the_field_came_from():
    from process_staged import _meta_source_label
    listing_item = {"date": "2026-08", "blurb_source": "page-abstract"}
    assert _meta_source_label(listing_item, ("date",)) == "listing", \
        "a detail-fetched description does not make the listing date page-derived"
    page_item = {"date": "2026-08", "detail_fields": ["date"]}
    assert _meta_source_label(page_item, ("date",)) == "page-meta"
    assert _meta_source_label(page_item, ("authors",)) == "listing"


def test_authors_json_normalises_list_and_string():
    assert json.loads(_authors_json(["White, Latia", "Gaviria, Grecia"])) == ["White, Latia", "Gaviria, Grecia"]
    assert json.loads(_authors_json("Solo, Han")) == ["Solo, Han"]
    assert _authors_json([]) is None
    assert _authors_json(None) is None


def test_backfill_metadata_fills_only_empty_by_default():
    conn = mem_db()
    # An existing row with no date/authors, and one that already has a date.
    conn.execute("INSERT INTO entries (num, title, url, type, source, date_added, published_date, date_source) "
                 "VALUES (1, 'A', 'https://x.org/a', 'report', 'S', '2026-01-01', NULL, NULL)")
    conn.execute("INSERT INTO entries (num, title, url, type, source, date_added, published_date, date_source) "
                 "VALUES (2, 'B', 'https://x.org/b', 'report', 'S', '2026-01-01', '1999-01', 'manual')")
    items = [
        {"url": "https://X.org/a/", "date": "August 2026", "authors": ["Doe, Jane"],
         "tags": ["equity"], "blurb_source": "listing"},
        {"url": "https://x.org/b", "date": "2026-07", "authors": ["Roe, R"]},
        {"url": "https://x.org/missing", "date": "2026-01"},   # no matching row
    ]
    counts, matched, unmatched = backfill_metadata(conn, items)
    assert (matched, unmatched) == (2, 1)
    a = conn.execute("SELECT published_date, date_source, authors, source_subjects FROM entries WHERE num=1").fetchone()
    assert a[0] == "2026-08" and a[1] == "listing"
    assert json.loads(a[2]) == ["Doe, Jane"]
    assert json.loads(a[3]) == ["equity"]
    # Row 2 already had a date from 'manual' — not overwritten by default.
    b = conn.execute("SELECT published_date, date_source, authors FROM entries WHERE num=2").fetchone()
    assert b[0] == "1999-01" and b[1] == "manual"
    assert json.loads(b[2]) == ["Roe, R"]   # authors was empty, so it fills
    assert counts["published_date"] == 1 and counts["authors"] == 2


def test_backfill_metadata_overwrite_replaces_values():
    conn = mem_db()
    conn.execute("INSERT INTO entries (num, title, url, type, source, date_added, published_date, date_source) "
                 "VALUES (1, 'A', 'https://x.org/a', 'report', 'S', '2026-01-01', '1999-01', 'manual')")
    counts, matched, _ = backfill_metadata(
        conn, [{"url": "https://x.org/a", "date": "2026-08", "blurb_source": "listing"}], overwrite=True)
    row = conn.execute("SELECT published_date, date_source FROM entries WHERE num=1").fetchone()
    assert row == ("2026-08", "listing")


def test_backfill_metadata_does_not_bump_updated_at():
    conn = mem_db()
    conn.execute("INSERT INTO entries (num, title, url, type, source, date_added, updated_at) "
                 "VALUES (1, 'A', 'https://x.org/a', 'report', 'S', '2026-01-01', 'ORIGINAL')")
    backfill_metadata(conn, [{"url": "https://x.org/a", "date": "2026-08", "blurb_source": "listing"}])
    assert conn.execute("SELECT updated_at FROM entries WHERE num=1").fetchone()[0] == "ORIGINAL"


def test_document_url_is_a_registry_field_with_provenance():
    # 2026-09-16: the direct report link (WestEd's "Get This Resource" S3 file)
    # replaces grade level as the next universal field; page-supplied -> page-meta.
    from process_staged import _document_url
    assert _document_url("https://x.org/f.pdf") == "https://x.org/f.pdf"
    assert _document_url(["https://x.org/a.pdf", "https://x.org/b.pdf"]) == "https://x.org/a.pdf"
    assert _document_url("/relative/f.pdf") is None and _document_url("") is None
    conn = mem_db()
    conn.execute("INSERT INTO entries (num, title, url, type, source, date_added) "
                 "VALUES (1, 'A', 'https://x.org/a', 'report', 'S', '2026-01-01')")
    item = {"url": "https://x.org/a", "document_url": "https://cdn.x.org/a.pdf", "detail_fields": ["document_url"]}
    counts, _, _ = backfill_metadata(conn, [item])
    assert counts["document_url"] == 1
    assert conn.execute("SELECT document_url, document_url_source FROM entries WHERE num=1").fetchone() == \
        ("https://cdn.x.org/a.pdf", "page-meta")


def test_url_date_inference_is_flagged_url_and_never_overrides():
    # 2026-09-16 (user: inference is fine if flagged): WordPress permalink dates
    # and CREDO's slug year are taken from the URL and stamped date_source "url";
    # a date from anywhere else wins; a URL-only stub row never gets a raw_item.
    from process_staged import apply_url_date_inference, _meta_source_label
    cfg = {"date_from_url": [{"host": "e4.northwestern.edu", "regex": r"/(\d{4})/(\d{2})/(\d{2})/"},
                             {"regex": r"-(20\d{2})(?:-\d)?/?$"}]}
    items = [{"url": "https://e4.northwestern.edu/2024/06/25/some-post/"},
             {"url": "https://credo.stanford.edu/reports/item/rhode-island-2025/", "_stub": True},
             {"url": "https://credo.stanford.edu/reports/item/report-3/", "_stub": True},
             {"url": "https://e4.northwestern.edu/2024/06/25/other/", "date": "March 2024"}]
    apply_url_date_inference(items, cfg)
    assert items[0]["date"] == "2024-06-25" and _meta_source_label(items[0], ("date",)) == "url"
    assert items[1]["date"] == "2025"
    assert "date" not in items[2]
    assert items[3]["date"] == "March 2024" and _meta_source_label(items[3], ("date",)) == "listing"
    conn = mem_db()
    conn.execute("INSERT INTO entries (num, title, url, type, source, date_added) "
                 "VALUES (1, 'A', 'https://credo.stanford.edu/reports/item/rhode-island-2025/', 'report', 'S', '2026-01-01')")
    counts, _, _ = backfill_metadata(conn, [items[1]])
    assert conn.execute("SELECT published_date, date_source, raw_item FROM entries WHERE num=1").fetchone() == ("2025", "url", None)


def test_page_meta_fallback_fills_date_authors_and_pdf_from_citation_tags():
    # 2026-09-16: AIMS entries on bepress / OJS / DSpace hosts state date,
    # authors and PDF in standard meta tags; with no selector mapped, the
    # fallback uses them and labels the fields page-meta. A value a selector
    # already supplied is left alone.
    from process_staged import apply_page_meta_fallback, _meta_source_label
    items = [{"url": "https://r.edu/x", "page_meta": {"bepress_citation_date": "2025",
              "bepress_citation_author": ["Burns, Andrew R"], "bepress_citation_pdf_url": "https://r.edu/x.pdf"}},
             {"url": "https://j.org/y", "date": "2020-01", "page_meta": {"citation_date": "2019/05/01"}},
             {"url": "https://n.org/z", "page_meta": {"jsonld:datePublished": "2026-05-11T13:21:55Z"}}]
    apply_page_meta_fallback(items)
    assert items[0]["date"] == "2025" and items[0]["authors"] == ["Burns, Andrew R"]
    assert items[0]["document_url"] == "https://r.edu/x.pdf"
    assert sorted(items[0]["detail_fields"]) == ["authors", "date", "document_url"]
    assert _meta_source_label(items[0], ("date",)) == "page-meta"
    assert items[1]["date"] == "2020-01" and "detail_fields" not in items[1]
    assert items[2]["date"] == "2026-05-11T13:21:55Z"


def test_load_db_items_takes_active_rows_of_the_named_sources(monkeypatch, tmp_path):
    # --from-db (2026-09-16): a metadata pass over already-indexed pages. Only
    # active rows of the named sources, only allowed hosts when host_allow is set.
    import sqlite3
    import scrape
    db = tmp_path / "hub.db"
    conn = sqlite3.connect(db)
    conn.executescript(ENTRIES_DDL)
    conn.executemany("INSERT INTO entries (num, title, url, type, source, date_added, excluded) VALUES (?,?,?,?,?,?,?)", [
        (1, "A", "https://repository.lsu.edu/a", "report", "AIMS Collaboratory", "2026-01-01", 0),
        (2, "B", "https://link.springer.com/b", "paper", "AIMS Collaboratory", "2026-01-01", 0),
        (3, "C", "https://repository.lsu.edu/c", "report", "AIMS Collaboratory", "2026-01-01", 1),
        (4, "D", "https://tntp.org/d", "report", "TNTP", "2026-01-01", 0)])
    conn.commit()
    conn.close()
    monkeypatch.setattr(scrape, "DB_PATH", db)
    cfg = {"from_db": {"source_names": ["AIMS Collaboratory"], "host_allow": ["repository.lsu.edu"]}}
    assert [i["url"] for i in scrape.load_db_items(cfg)] == ["https://repository.lsu.edu/a"]
    cfg = {"from_db": {"source_names": ["AIMS Collaboratory", "TNTP"]}}
    assert [i["url"] for i in scrape.load_db_items(cfg)] == ["https://repository.lsu.edu/a", "https://link.springer.com/b", "https://tntp.org/d"]


def test_authors_json_splits_bylines_and_rejects_paragraphs():
    from process_staged import _authors_json
    assert json.loads(_authors_json("By: Megan Kuhfeld, Daniel Long, Scott J. Peters")) == \
        ["Megan Kuhfeld", "Daniel Long", "Scott J. Peters"]
    assert json.loads(_authors_json("By A. One and B. Two.")) == ["A. One", "B. Two"]
    assert json.loads(_authors_json(["Doe, Jane"])) == ["Doe, Jane"], "a list element is one name, commas kept"
    assert json.loads(_authors_json("By: Naomi Duran, PhD, Karyn Lewis, Ed.D.")) == ["Naomi Duran", "Karyn Lewis"]
    # Brookings byline: a comma list of full names without a prefix is a list
    assert json.loads(_authors_json("Katharine Meyer, Isabel McMullen")) == ["Katharine Meyer", "Isabel McMullen"]
    assert _authors_json("In this prospective longitudinal study (N = 1094), the authors examined family "
                         "factors associated with school mobility and asked whether moves matter.") is None


def test_metadata_map_copies_page_keys_with_page_meta_provenance():
    # NWEA (2026-09-16): the API post date is wrong on most rows and bio_link is
    # empty, but the detail fetch stored date_page / authors_page. The map fills
    # the registry fields and, because those keys came from the item page,
    # labels them page-meta. The mapped key overrides a value already in the
    # field (the wrong API date is the point); an empty key changes nothing.
    from process_staged import apply_metadata_map, _meta_source_label
    cfg = {"metadata_map": {"date": "date_page", "authors": "authors_page"},
           "detail_fetch": {"extra_fields": {"date_page": {"selector": "x"}, "authors_page": {"selector": "y"}}}}
    items = [{"date": "2022-10-11", "date_page": "June 2022", "authors": [], "authors_page": "By: A. One"},
             {"date": "2020-01-01", "date_page": ""}]
    apply_metadata_map(items, cfg)
    assert items[0]["date"] == "June 2022" and items[0]["authors"] == "By: A. One"
    assert sorted(items[0]["detail_fields"]) == ["authors", "date"]
    assert _meta_source_label(items[0], ("date",)) == "page-meta"
    assert items[1]["date"] == "2020-01-01" and "detail_fields" not in items[1]


def test_items_from_db_feeds_stored_raw_items_to_the_backfill():
    # 2026-09-15: EdTrust's stored raw items already carry the post date; a
    # from-db pass must date the row without a staging file and leave rows of
    # other sources and rows without a raw item alone.
    from process_staged import items_from_db
    conn = mem_db()
    conn.execute("INSERT INTO entries (num, title, url, type, source, date_added, raw_item) VALUES "
                 "(1, 'A', 'https://x.org/a', 'report', 'S', '2026-01-01', "
                 "'{\"date\": \"2026-08-26T12:42:49\", \"blurb_source\": \"page-meta\"}')")
    conn.execute("INSERT INTO entries (num, title, url, type, source, date_added, raw_item) VALUES "
                 "(2, 'B', 'https://x.org/b', 'report', 'S', '2026-01-01', NULL)")
    conn.execute("INSERT INTO entries (num, title, url, type, source, date_added, raw_item) VALUES "
                 "(3, 'C', 'https://y.org/c', 'report', 'Other', '2026-01-01', '{\"date\": \"2020-01\"}')")
    items = items_from_db(conn, "S")
    # Row 2 has no raw item: it comes back as a URL-only stub (so URL inference
    # can run) and contributes nothing else.
    assert [(i["url"], i.get("_stub", False)) for i in items] == [("https://x.org/a", False), ("https://x.org/b", True)]
    counts, matched, unmatched = backfill_metadata(conn, items)
    assert (matched, unmatched, counts["published_date"]) == (2, 0, 1)
    assert conn.execute("SELECT published_date, date_source FROM entries WHERE num=1").fetchone() == ("2026-08-26", "listing")
    assert conn.execute("SELECT published_date FROM entries WHERE num IN (2, 3)").fetchall() == [(None,), (None,)]


def test_backfill_metadata_keeps_the_staged_item_as_raw_item():
    # 2026-09-15: rows inserted before raw_item existed (May/June) have none, and
    # a backfill that discarded the staged item would force a re-fetch for any
    # field mapped later. Fill-empty stores it; an existing raw_item is kept
    # unless overwrite=True.
    conn = mem_db()
    conn.execute("INSERT INTO entries (num, title, url, type, source, date_added, raw_item) "
                 "VALUES (1, 'A', 'https://x.org/a', 'report', 'S', '2026-01-01', NULL)")
    conn.execute("INSERT INTO entries (num, title, url, type, source, date_added, raw_item) "
                 "VALUES (2, 'B', 'https://x.org/b', 'report', 'S', '2026-01-01', '{\"old\": true}')")
    items = [{"url": "https://x.org/a", "date": "2026-08", "category": "Brief", "blurb_source": "listing"},
             {"url": "https://x.org/b", "date": "2026-07", "blurb_source": "listing"}]
    counts, _, _ = backfill_metadata(conn, items)
    assert json.loads(conn.execute("SELECT raw_item FROM entries WHERE num=1").fetchone()[0])["category"] == "Brief"
    assert conn.execute("SELECT raw_item FROM entries WHERE num=2").fetchone()[0] == '{"old": true}'
    assert counts["raw_item"] == 1
    backfill_metadata(conn, items, overwrite=True)
    assert "date" in json.loads(conn.execute("SELECT raw_item FROM entries WHERE num=2").fetchone()[0])
