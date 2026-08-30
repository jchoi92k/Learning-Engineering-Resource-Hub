#!/usr/bin/env python3
"""
Generic scraper for the Renaissance AI and Education Resource Hub.

Reads per-source configs from sources/{source}.json, fetches listing
data (sitemap, API, or paginated HTML), and outputs structured JSON.
The LLM agent never sees raw HTML — only the extracted fields.

Usage:
    python scripts/scrape.py wested                  # full scrape
    python scripts/scrape.py wested --pages 3        # limit pagination to 3 pages
    python scripts/scrape.py wested --test           # test selectors against one page
    python scripts/scrape.py wested --no-diff        # include already-indexed items, no early-stop

Early-stop: a paginated or API source whose config declares "early_stop": true
(meaning its listing is newest-first) stops fetching once a page contains 3
consecutive or 5 total already-indexed URLs. Configs without the flag scan
every page up to --pages / api.pagination.pages. Declare it only for a source
whose ordering has been checked -- Digital Promise's API returned relevance
order until a sort param was added (2026-08-28).

Output goes to docs/staging/{source}.json (or stdout with --stdout).
"""
import argparse
import html
import json
import re
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import requests
from bs4 import BeautifulSoup

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
SOURCES_DIR = REPO_ROOT / "sources"
STAGING_DIR = REPO_ROOT / "docs" / "staging"
LLMS_FULL = REPO_ROOT / "docs" / "llms-full.txt"

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
})

CONSECUTIVE_FAILURES = 0
MAX_CONSECUTIVE_FAILURES = 3
MIN_BLURB_LENGTH = 30
DEFAULT_DELAY = 5  # seconds between requests (no-policy default)
MIN_DELAY = 5  # hard floor: a config's request_delay cannot go below this
_request_delay = DEFAULT_DELAY
_last_fetch_time = 0
BACKOFF_SCHEDULE = [5, 10, 20]  # seconds on 429/503, then give up

# Every HTTP request a run makes is appended to docs/staging/logs/<source>-requests.log
# (send time, method, status, URL) so a run can be audited for repeated URLs and
# throttle violations. See audit_request_log() and `--audit`.
LOGS_DIR = STAGING_DIR / "logs"
_request_log_path = None
_run_requests = []   # (sent_epoch, method, status, url, retry) for this process


def _start_request_log(source):
    global _request_log_path
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    _request_log_path = LOGS_DIR / f"{source}-requests.log"
    with open(_request_log_path, "a", encoding="utf-8") as f:
        f.write(f"# run {time.strftime('%Y-%m-%dT%H:%M:%S')} delay={_request_delay}s\n")


def _record(url, status, method="get", sent=None, retry=False):
    sent = sent if sent is not None else time.time()
    _run_requests.append((sent, method, str(status), url, retry))
    if _request_log_path:
        with open(_request_log_path, "a", encoding="utf-8") as f:
            f.write(f"{sent:.3f}\t{method}\t{status}\t{'retry' if retry else '-'}\t{url}\n")


def audit_request_log(requests_list, expected_delay):
    """Check a list of (sent, method, status, url, retry) tuples: any URL requested
    more than once (retries after 429/503 excepted), and the smallest gap between
    consecutive send times against the expected delay. Returns a dict."""
    from collections import Counter
    from urllib.parse import urlsplit
    reqs = sorted(requests_list, key=lambda r: r[0])
    urls = Counter(r[3] for r in reqs if not r[4])
    repeated = {u: n for u, n in urls.items() if n > 1}
    gaps = [b[0] - a[0] for a, b in zip(reqs, reqs[1:])]
    by_host = {}
    for r in reqs:
        by_host.setdefault(urlsplit(r[3]).netloc, []).append(r[0])
    host_gaps = {h: min((b - a for a, b in zip(t, t[1:])), default=None) for h, t in by_host.items()}
    tolerance = 0.25
    return {
        "requests": len(reqs),
        "unique_urls": len(urls),
        "repeated": repeated,
        "retries": sum(1 for r in reqs if r[4]),
        "statuses": dict(Counter(r[2] for r in reqs)),
        "min_gap": min(gaps) if gaps else None,
        "min_gap_by_host": host_gaps,
        "throttle_ok": all(g >= expected_delay - tolerance for g in gaps),
        "duplicates_ok": not repeated,
    }


def read_request_log(path, last_run_only=True):
    """Parse a -requests.log file into audit tuples. Runs are separated by
    "# run ..." header lines; by default only the most recent run is returned."""
    runs = [[]]
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.startswith("# run"):
                runs.append([])
                continue
            if line.startswith("#") or not line.strip():
                continue
            sent, method, status, retry, url = line.rstrip("\n").split("\t", 4)
            runs[-1].append((float(sent), method, status, url, retry == "retry"))
    runs = [r for r in runs if r]
    if not runs:
        return []
    return runs[-1] if last_run_only else [r for run in runs for r in run]


def print_request_audit(audit, expected_delay):
    print(f"[scrape] Request audit: {audit['requests']} requests, {audit['unique_urls']} unique URLs, "
          f"{audit['retries']} retries, statuses {audit['statuses']}, "
          f"min gap {audit['min_gap']:.2f}s (expected >= {expected_delay}s)" if audit["min_gap"] is not None
          else f"[scrape] Request audit: {audit['requests']} request(s)")
    if not audit["duplicates_ok"]:
        print(f"[scrape] WARNING: URLs requested more than once: {audit['repeated']}", file=sys.stderr)
    if not audit["throttle_ok"]:
        print("[scrape] WARNING: throttle violated — a gap between requests was shorter than the delay",
              file=sys.stderr)
# Early-stop: stop paginating once a page shows this many already-indexed URLs.
# Valid only for listings the config declares newest-first ("early_stop": true);
# with sparse coverage or unknown ordering it silently skips new items.
EARLY_STOP_CONSECUTIVE = 3
EARLY_STOP_TOTAL = 5


def resolve_source(source):
    """Case-insensitive config lookup."""
    exact = SOURCES_DIR / f"{source}.json"
    if exact.exists():
        return source
    for f in SOURCES_DIR.glob("*.json"):
        if f.stem.lower() == source.lower():
            return f.stem
    return source


def load_config(source):
    source = resolve_source(source)
    path = SOURCES_DIR / f"{source}.json"
    if not path.exists():
        print(f"Error: no config at {path}", file=sys.stderr)
        sys.exit(1)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def effective_delay(config, floor=MIN_DELAY, default=DEFAULT_DELAY):
    """Per-source request delay: the config's request_delay, never below the
    floor. robots.txt Crawl-delay can raise it further (see check_robots)."""
    asked = config.get("request_delay", default)
    if isinstance(asked, bool) or not isinstance(asked, (int, float)):
        print(f"  request_delay {asked!r} is not a number - using {default}s", file=sys.stderr)
        return default
    if asked < floor:
        print(f"  request_delay {asked}s is below the {floor}s floor - using {floor}s", file=sys.stderr)
        return floor
    return asked


def check_robots(config):
    """Fetch robots.txt. Parse crawl-delay if present and use it as the request delay."""
    global _request_delay
    url = config.get("robots_txt")
    if not url:
        return True
    try:
        _throttle(url)  # robots.txt is a request to the host too: start the clock
        r = SESSION.get(url, timeout=15)
        _record(url, r.status_code, "get", sent=_last_fetch_time)
        if r.status_code != 200:
            print(f"  Warning: robots.txt returned {r.status_code}")
            return True
        print(f"  robots.txt fetched OK ({len(r.text)} bytes)")
        for line in r.text.splitlines():
            line = line.strip().lower()
            if line.startswith("crawl-delay:"):
                try:
                    delay = float(line.split(":", 1)[1].strip())
                    if delay > _request_delay:
                        _request_delay = delay
                        print(f"  robots.txt crawl-delay: {delay}s (using it)")
                except ValueError:
                    pass
        return True
    except Exception as e:
        print(f"  Warning: could not fetch robots.txt: {e}", file=sys.stderr)
        return True


LAST_REQUEST_FILE = STAGING_DIR / "logs" / "last-request.json"


def _host(url):
    from urllib.parse import urlsplit
    return urlsplit(url).netloc.lower() if url else ""


def _load_last_request(host):
    """Send time of the last request this machine made to `host`, from any
    process (the in-memory clock only covers this process)."""
    try:
        with open(LAST_REQUEST_FILE, encoding="utf-8") as f:
            return float(json.load(f).get(host, 0))
    except (OSError, ValueError):
        return 0.0


def _save_last_request(host, when):
    try:
        LAST_REQUEST_FILE.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(LAST_REQUEST_FILE, encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, ValueError):
            data = {}
        data[host] = when
        with open(LAST_REQUEST_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except OSError:
        pass


def _throttle(url=None):
    """Wait to respect the request delay between fetches. The clock is kept in
    memory for this process and, per host, on disk — so a second invocation
    right after the first (a --test then a run, or two configs on one host)
    still waits the full delay."""
    global _last_fetch_time
    last = _last_fetch_time
    host = _host(url)
    if host:
        last = max(last, _load_last_request(host))
    elapsed = time.time() - last
    if last > 0 and elapsed < _request_delay:
        time.sleep(_request_delay - elapsed)
    _last_fetch_time = time.time()
    if host:
        _save_last_request(host, _last_fetch_time)


def _handle_rate_limit(status_code, url, method="get", request_kwargs=None):
    """Retry with exponential backoff on 429/503, replaying the original
    method and kwargs (params/headers/json) so paginated and POST requests
    are not corrupted on retry. Returns response or None."""
    global _last_fetch_time
    request_kwargs = request_kwargs or {}
    for attempt, wait in enumerate(BACKOFF_SCHEDULE):
        print(f"  HTTP {status_code} — backing off {wait}s (attempt {attempt + 1}/{len(BACKOFF_SCHEDULE)})...",
              file=sys.stderr)
        time.sleep(wait)
        try:
            _last_fetch_time = time.time()  # the retry is a request too: restart the clock
            _save_last_request(_host(url), _last_fetch_time)
            r = SESSION.request(method, url, timeout=30, **request_kwargs)
            _record(url, r.status_code, method, sent=_last_fetch_time, retry=True)
            if r.status_code == 200:
                return r
            if r.status_code not in (429, 503):
                print(f"  HTTP {r.status_code} on retry — giving up.", file=sys.stderr)
                return None
        except Exception as e:
            print(f"  Retry error: {e}", file=sys.stderr)
    print(f"  Exhausted {len(BACKOFF_SCHEDULE)} retries — giving up.", file=sys.stderr)
    return None


def fetch(url, **kwargs):
    """Fetch a URL with throttling, backoff on 429/503, and failure tracking."""
    global CONSECUTIVE_FAILURES
    _throttle(url)
    sent = _last_fetch_time
    try:
        r = SESSION.get(url, timeout=30, **kwargs)
        _record(r.url or url, r.status_code, "get", sent=sent)   # r.url carries the query params
        if r.status_code == 200:
            CONSECUTIVE_FAILURES = 0
            return r
        if r.status_code in (429, 503):
            result = _handle_rate_limit(r.status_code, url, "get", kwargs)
            if result:
                CONSECUTIVE_FAILURES = 0
                return result
        CONSECUTIVE_FAILURES += 1
        print(f"  HTTP {r.status_code}: {url}", file=sys.stderr)
        if CONSECUTIVE_FAILURES >= MAX_CONSECUTIVE_FAILURES:
            print(f"  {MAX_CONSECUTIVE_FAILURES} consecutive failures — stopping.", file=sys.stderr)
        return None
    except Exception as e:
        _record(url, "ERR", sent=sent)
        CONSECUTIVE_FAILURES += 1
        print(f"  Fetch error: {e} — {url}", file=sys.stderr)
        if CONSECUTIVE_FAILURES >= MAX_CONSECUTIVE_FAILURES:
            print(f"  {MAX_CONSECUTIVE_FAILURES} consecutive failures — stopping.", file=sys.stderr)
        return None


def fetch_post(url, headers=None, json_body=None):
    """POST request for API sources, with throttling and backoff."""
    global CONSECUTIVE_FAILURES
    _throttle(url)
    sent = _last_fetch_time
    try:
        r = SESSION.post(url, headers=headers, json=json_body, timeout=30)
        _record(url, r.status_code, "post", sent=sent)
        if r.status_code == 200:
            CONSECUTIVE_FAILURES = 0
            return r
        if r.status_code in (429, 503):
            result = _handle_rate_limit(r.status_code, url, "post",
                                        {"headers": headers, "json": json_body})
            if result:
                CONSECUTIVE_FAILURES = 0
                return result
        CONSECUTIVE_FAILURES += 1
        print(f"  HTTP {r.status_code}: {url}", file=sys.stderr)
        return None
    except Exception as e:
        _record(url, "ERR", sent=sent)
        CONSECUTIVE_FAILURES += 1
        print(f"  Fetch error: {e} — {url}", file=sys.stderr)
        return None


# ── Discovery methods ──


def scrape_sitemap(config, max_pages=None):
    """Fetch a sitemap XML and extract URLs matching the configured pattern."""
    url = config["discovery_url"]
    print(f"  Fetching sitemap: {url}")
    r = fetch(url)
    if not r:
        return []

    root = ET.fromstring(r.content)
    ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    locs = [el.text for el in root.findall(".//s:loc", ns)]

    pattern = config.get("sitemap", {}).get("url_pattern", "")
    if pattern:
        locs = [u for u in locs if pattern in u]

    print(f"  Found {len(locs)} URLs matching '{pattern}'")
    items = [{"url": u, "title": "", "type": "", "blurb": ""} for u in locs]
    return items


def extract_cards(soup, config):
    """Extract items from HTML using CSS selectors. Shared by pagination and single_page."""
    sel = config["selectors"]
    url_prefix = config.get("url_prefix", "")
    cards = soup.select(sel["item"])
    items = []

    for card in cards:
        title_el = card.select_one(sel["title"])
        url_el = card.select_one(sel["url"])
        type_el = card.select_one(sel.get("type", "NONE"))

        # Blurb extraction: three strategies
        blurb = ""
        if sel.get("blurb_bare_text"):
            # Bare text node: get card text minus all child element text
            blurb = card.get_text(" ", strip=True)
            for fragment in [el.get_text(" ", strip=True) for el in card.find_all(True) if el.get_text(" ", strip=True)]:
                blurb = blurb.replace(fragment, "", 1)
            blurb = " ".join(blurb.split()).strip()
        elif "blurb_parent" in sel:
            parent_el = card.select_one(sel["blurb_parent"])
            if parent_el and parent_el.parent:
                container = parent_el.parent
                for child in container.find_all("span"):
                    child.decompose()
                blurb = container.get_text(" ", strip=True).lstrip("| ").strip()
        else:
            blurb_el = card.select_one(sel.get("blurb", "NONE"))
            blurb = blurb_el.get_text(" ", strip=True) if blurb_el else ""

        # get_text(" ") keeps a space between adjacent inline elements
        # (e.g. <em>ThinkerTools</em>is); clean_text collapses the doubles.
        title = title_el.get_text(" ", strip=True) if title_el else ""
        # Strip trailing date in parens, e.g. "Good Behavior Game (October 2024)"
        title = re.sub(r'\s*\([A-Z][a-z]+ \d{4}\)\s*$', '', title)

        item_url = url_el["href"] if url_el and url_el.has_attr("href") else ""
        if item_url and not item_url.startswith("http"):
            item_url = url_prefix + item_url

        item = {
            "title": clean_text(title),
            "url": item_url,
            "type": clean_text(type_el.get_text(" ", strip=True)) if type_el else "",
            "blurb": clean_text(blurb),
        }

        # Extra fields (grade_level, evidence_tier, authors, date)
        for extra in ("grade_level", "evidence_tier", "authors", "date"):
            if extra in sel:
                el = card.select_one(sel[extra])
                if el:
                    if extra == "date" and el.has_attr("datetime"):
                        item[extra] = el["datetime"]
                    else:
                        item[extra] = clean_text(el.get_text(" ", strip=True))

        # Authors as list (multiple elements)
        if "authors" in sel:
            author_els = card.select(sel["authors"])
            if author_els:
                item["authors"] = [clean_text(a.get_text(" ", strip=True)) for a in author_els]

        items.append(item)

    return items


def scrape_single_page(config, max_pages=None):
    """Fetch a single page with all results and extract via CSS selectors."""
    url = config["discovery_url"]
    print(f"  Fetching: {url}")
    r = fetch(url)
    if not r:
        return []
    soup = BeautifulSoup(r.text, "html.parser")
    items = extract_cards(soup, config)
    print(f"  Extracted {len(items)} items")
    return items


def early_stop_hit(items, existing_urls, max_consecutive=EARLY_STOP_CONSECUTIVE,
                   max_total=EARLY_STOP_TOTAL):
    """True if a page's items contain enough already-indexed URLs to stop paginating.

    Triggers on either `max_consecutive` known URLs in a row or `max_total`
    known URLs anywhere on the page. `existing_urls` must be normalized
    (rstrip('/'), lowercase) as produced by load_existing_urls(). Returns
    False when existing_urls is None (diffing disabled).
    """
    if not existing_urls:
        return False
    consecutive = total = 0
    for item in items:
        if item.get("url", "").rstrip("/").lower() in existing_urls:
            consecutive += 1
            total += 1
            if consecutive >= max_consecutive or total >= max_total:
                return True
        else:
            consecutive = 0
    return False


def scrape_pagination(config, max_pages=None, existing_urls=None):
    """Paginate through HTML listing pages and extract items via CSS selectors.

    Supports two URL patterns:
      - Query string (default): {base_url}?{param}={page_num}
      - Path-based: set pagination.url_pattern, e.g. "{base}page/{page}/"
        where {base} is discovery_url and {page} is the page number.
        Page 1 uses discovery_url directly (no /page/1/).

    Stops early once a page contains enough already-indexed URLs (see
    early_stop_hit) -- only when the config sets "early_stop": true;
    max_pages remains a hard cap.
    """
    if not config.get("early_stop"):
        existing_urls = None
    base_url = config["discovery_url"]
    pag = config["pagination"]
    param = pag.get("param")
    start = pag["start"]
    url_pattern = pag.get("url_pattern")

    page_num = start
    all_items = []

    while True:
        if max_pages is not None and (page_num - start) >= max_pages:
            break

        if url_pattern:
            if page_num == start:
                url = base_url
            else:
                url = url_pattern.replace("{base}", base_url).replace("{page}", str(page_num))
        else:
            url = f"{base_url}?{param}={page_num}"
        print(f"  Fetching page {page_num}: {url}")
        r = fetch(url)
        if not r:
            if CONSECUTIVE_FAILURES >= MAX_CONSECUTIVE_FAILURES:
                break
            page_num += 1
            continue

        soup = BeautifulSoup(r.text, "html.parser")
        items = extract_cards(soup, config)

        if not items:
            print(f"  No items on page {page_num} — reached end.")
            break

        all_items.extend(items)
        print(f"  Extracted {len(items)} items from page {page_num}")
        if early_stop_hit(items, existing_urls):
            print(f"  Early stop: page {page_num} is mostly already indexed.")
            break
        page_num += 1

    return all_items


def resolve_json_path(obj, path):
    """Navigate a slash-separated JSON path. Supports /* for arrays.

    Uses / as separator so keys with dots (like 'dc.title') work.
    Example: 'metadata/dc.title/0/value'
    """
    parts = path.split("/")
    current = obj
    for i, part in enumerate(parts):
        if current is None:
            return None
        if part == "*":
            if isinstance(current, list):
                remaining = "/".join(parts[i + 1:])
                if remaining:
                    return [resolve_json_path(item, remaining) for item in current]
                return current
            return None
        if isinstance(current, dict):
            current = current.get(part)
        elif isinstance(current, list):
            try:
                current = current[int(part)]
            except (ValueError, IndexError):
                return None
        else:
            return None
    return current


def strip_html(text):
    """Remove HTML tags, leaving a space where each tag was so adjacent
    elements don't fuse ("</p><p>" -> " "). Callers pass the result through
    clean_text(), which collapses the extra spaces and decodes entities."""
    if not text:
        return ""
    return re.sub(r'<[^>]+>', ' ', text).strip()


def clean_text(text):
    """Normalize scraped text: decode HTML entities ("&reg;", "&#8217;" --
    WWC and WP REST sources ship them double-encoded), turn NBSP and other
    Unicode spaces into plain spaces, drop BOM / zero-width / soft-hyphen
    characters, and collapse tabs, newlines and runs of spaces to one."""
    if not text:
        return ""
    if not isinstance(text, str):
        text = str(text)
    text = html.unescape(text)
    for ch in ("\u00a0", "\u2009", "\u202f"):  # NBSP, thin space, narrow NBSP
        text = text.replace(ch, " ")
    for ch in ("\ufeff", "\u200b", "\u00ad"):  # BOM, zero-width space, soft hyphen
        text = text.replace(ch, "")
    text = re.sub(r"\s+", " ", text)
    # get_text(" ") separates inline elements, which also puts spaces around
    # <sup>®</sup> and before closing punctuation; tighten those back.
    text = re.sub(r"\s+([\u00ae\u2122\u00a9,.;:!?)\]])", r"\1", text)
    text = re.sub(r"([(\[])\s+", r"\1", text)
    return text.strip()


def _load_url_filter(config):
    """Fetch a listing page and extract allowed URL slugs for filtering API results."""
    filt = config.get("url_filter")
    if not filt:
        return None
    page_url = filt["url"]
    slug_prefix = filt["slug_prefix"]
    print(f"  Fetching URL filter list: {page_url}")
    r = fetch(page_url)
    if not r:
        print("  WARNING: could not fetch URL filter page — no filtering applied",
              file=sys.stderr)
        return None
    soup = BeautifulSoup(r.text, "html.parser")
    slugs = set()
    for a in soup.find_all("a", href=lambda h: h and slug_prefix in h):
        href = a.get("href", "").rstrip("/")
        slug = href.split(slug_prefix)[-1] if slug_prefix in href else ""
        if slug:
            slugs.add(slug)
    print(f"  URL filter: {len(slugs)} allowed slugs from {page_url}")
    return slugs


def scrape_api(config, max_pages=None, existing_urls=None):
    """Fetch from a REST/search API and extract items via JSON paths.

    Stops early once a page contains enough already-indexed URLs (see
    early_stop_hit) -- only when the config sets "early_stop": true;
    max_pages / pagination.pages remain hard caps.
    """
    if not config.get("early_stop"):
        existing_urls = None
    api = config["api"]
    paths = api["json_paths"]
    items_path = paths.get("items", "")
    allowed_slugs = _load_url_filter(config)

    method = api.get("method", "GET").upper()
    pag = api.get("pagination", {})
    page_param = pag.get("param", "page")
    page_start = pag.get("start", 0)
    page_step = pag.get("step", 1)
    total_pages = pag.get("pages")
    if max_pages is not None:
        total_pages = max_pages

    url_transform = config.get("url_transform")

    all_items = []
    page_num = page_start
    pages_fetched = 0

    while True:
        if total_pages is not None and pages_fetched >= total_pages:
            break

        if method == "POST":
            body = dict(api.get("body", {}))
            body[page_param] = page_num
            hdrs = api.get("headers", {})
            print(f"  POST {page_param}={page_num}: {config['discovery_url']}")
            r = fetch_post(config["discovery_url"], headers=hdrs, json_body=body)
        else:
            params = dict(api.get("params", {}))
            params[page_param] = page_num
            url = config["discovery_url"]
            print(f"  GET {page_param}={page_num}: {url}")
            r = fetch(url, params=params)

        if not r:
            if CONSECUTIVE_FAILURES >= MAX_CONSECUTIVE_FAILURES:
                break
            page_num += page_step
            pages_fetched += 1
            continue

        data = r.json()
        raw_items = resolve_json_path(data, items_path) if items_path else data
        if not raw_items or (isinstance(raw_items, list) and len(raw_items) == 0):
            print(f"  No items at {page_param}={page_num} — reached end.")
            break

        per_page = params.get("per_page") if method != "POST" else None
        page_items = []
        for raw in raw_items:
            item_root = paths.get("item_root")
            obj = resolve_json_path(raw, item_root) if item_root else raw

            title = resolve_json_path(obj, paths.get("title", "")) or ""
            item_url = resolve_json_path(obj, paths.get("url", "")) or ""
            date = resolve_json_path(obj, paths.get("date", "")) or ""
            desc = resolve_json_path(obj, paths.get("description", "")) or ""
            if not desc:
                fallback_path = paths.get("description_fallback")
                if fallback_path:
                    desc = resolve_json_path(obj, fallback_path) or ""
            item_type = resolve_json_path(obj, paths.get("type", "")) or ""
            authors = resolve_json_path(obj, paths.get("authors", "")) or []
            tags = resolve_json_path(obj, paths.get("tags", "")) or []

            if isinstance(item_type, list):
                item_type = item_type[0] if item_type else ""

            # Strip HTML and normalize whitespace
            desc = clean_text(strip_html(desc) if isinstance(desc, str) else str(desc))
            title = clean_text(strip_html(title) if isinstance(title, str) else str(title))

            url_str = item_url if isinstance(item_url, str) else str(item_url)
            url_template = config.get("url_template")
            if url_template:
                url_str = url_template.replace("{url}", url_str)
            if url_transform:
                url_str = url_str.replace(url_transform["replace"], url_transform["with"])

            item_dict = {
                "title": title,
                "url": url_str,
                "date": date if isinstance(date, str) else str(date),
                "blurb": desc,
                "type": item_type if isinstance(item_type, str) else str(item_type),
                "authors": authors if isinstance(authors, list) else [authors],
                "tags": tags if isinstance(tags, list) else [tags],
            }

            # Extra fields from config
            for field_name, field_path in api.get("extra_fields", {}).items():
                val = resolve_json_path(obj, field_path)
                if val:
                    if field_name == "page_text" and isinstance(val, str):
                        # an API that returns the article body: keep it as text, capped
                        val = clean_text(strip_html(val))[:PAGE_TEXT_MAX_CHARS]
                    item_dict[field_name] = val

            page_items.append(item_dict)

        all_items.extend(page_items)
        print(f"  Extracted {len(raw_items)} items at {page_param}={page_num}")
        if per_page and isinstance(raw_items, list) and len(raw_items) < int(per_page):
            print(f"  Short page ({len(raw_items)} < {per_page}) — last page.")
            break
        if early_stop_hit(page_items, existing_urls):
            print(f"  Early stop: {page_param}={page_num} is mostly already indexed.")
            break
        page_num += page_step
        pages_fetched += 1

    if allowed_slugs is not None:
        slug_prefix = config["url_filter"]["slug_prefix"]
        before = len(all_items)
        all_items = [
            item for item in all_items
            if item["url"].rstrip("/").split(slug_prefix)[-1] in allowed_slugs
        ]
        print(f"  URL filter applied: {before} -> {len(all_items)} items")

    return all_items


# ── Diff against existing entries ──


DB_PATH = REPO_ROOT / "data" / "hub.db"


def load_existing_urls():
    """Load all URLs from hub.db (includes excluded entries to prevent re-scraping)."""
    import sqlite3
    if DB_PATH.exists():
        conn = sqlite3.connect(DB_PATH)
        urls = {row[0].rstrip("/").lower() for row in conn.execute("SELECT url FROM entries")}
        conn.close()
        return urls
    if not LLMS_FULL.exists():
        return set()
    urls = set()
    with open(LLMS_FULL, encoding="utf-8") as f:
        for line in f:
            m = re.match(r'^url:\s*"(.+)"', line.strip())
            if m:
                urls.add(m.group(1).rstrip("/").lower())
    return urls


def diff_items(items, existing_urls):
    """Split items into new vs. already-indexed."""
    new = []
    existing = []
    for item in items:
        normalized = item["url"].rstrip("/").lower()
        if normalized in existing_urls:
            existing.append(item)
        else:
            new.append(item)
    return new, existing


# ── Test mode ──


def run_test(config, source):
    """Test the config against one page/request and report results."""
    test = config.get("test")
    if not test:
        print("  No test config defined.")
        return False

    discovery = config["discovery"]
    print(f"\n  Testing {source} ({discovery})...")

    if discovery == "sitemap":
        url = test["url"]
        r = fetch(url)
        if not r:
            print("  FAIL: could not fetch sitemap")
            return False
        root = ET.fromstring(r.content)
        ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        locs = [el.text for el in root.findall(".//s:loc", ns)]
        pattern = test.get("expected_url_contains", "")
        matching = [u for u in locs if pattern in u] if pattern else locs
        min_urls = test.get("expected_min_urls", 1)
        if len(matching) >= min_urls:
            print(f"  PASS: {len(matching)} URLs found (expected >= {min_urls})")
            return True
        else:
            print(f"  FAIL: {len(matching)} URLs found (expected >= {min_urls})")
            return False

    elif discovery == "pagination":
        url = test["url"]
        r = fetch(url)
        if not r:
            print("  FAIL: could not fetch test page")
            return False
        soup = BeautifulSoup(r.text, "html.parser")
        sel = config["selectors"]
        cards = soup.select(sel["item"])
        expected = test.get("expected_item_count")
        if expected and len(cards) != expected:
            print(f"  FAIL: found {len(cards)} items, expected {expected}")
            return False
        if not cards:
            print("  FAIL: no items found with selector")
            return False
        # Verify first card has extractable fields
        card = cards[0]
        title_el = card.select_one(sel["title"])
        if not title_el:
            print("  FAIL: title selector returned nothing on first card")
            return False
        title_text = title_el.get_text(strip=True)
        expected_title = test.get("expected_first_title_contains", "")
        if expected_title and expected_title not in title_text:
            print(f"  FAIL: first title '{title_text}' doesn't contain '{expected_title}'")
            return False
        print(f"  PASS: {len(cards)} items, first title: '{title_text[:60]}'")
        return True

    elif discovery == "single_page":
        url = test.get("url", config["discovery_url"])
        r = fetch(url)
        if not r:
            print("  FAIL: could not fetch page")
            return False
        soup = BeautifulSoup(r.text, "html.parser")
        items = extract_cards(soup, config)
        min_items = test.get("expected_min_items", 1)
        if len(items) < min_items:
            print(f"  FAIL: found {len(items)} items, expected >= {min_items}")
            return False
        if not items:
            print("  FAIL: no items found with selectors")
            return False
        print(f"  PASS: {len(items)} items, first: '{items[0]['title'][:60]}'")
        return True

    elif discovery == "api":
        print("  API test: sending one request...")
        items = scrape_api(config, max_pages=1)
        min_results = test.get("expected_min_results", 1)
        expected_count = test.get("expected_item_count")
        if expected_count and len(items) != expected_count:
            print(f"  FAIL: got {len(items)} items, expected {expected_count}")
            return False
        if len(items) < min_results:
            print(f"  FAIL: got {len(items)} items, expected >= {min_results}")
            return False
        print(f"  PASS: {len(items)} items from first page, first: '{items[0]['title'][:60]}'")
        return True

    print(f"  Unknown discovery type: {discovery}")
    return False


# ── Detail fetch (individual page descriptions) ──


PROGRESS_DIR = STAGING_DIR


def _save_progress(source, items):
    """Save current items to a progress file for resume on interruption."""
    PROGRESS_DIR.mkdir(parents=True, exist_ok=True)
    path = PROGRESS_DIR / f"{source}-progress.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2, ensure_ascii=False)


def _load_progress(source):
    """Load saved progress. Returns list of items or None."""
    path = PROGRESS_DIR / f"{source}-progress.json"
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return None


def _clear_progress(source):
    """Remove progress file after successful completion."""
    path = PROGRESS_DIR / f"{source}-progress.json"
    if path.exists():
        path.unlink()


def fetch_detail_descriptions(items, config, source):
    """Fetch individual pages to fill in missing descriptions.

    Uses the 'detail_fetch' config block:
        "detail_fetch": {
            "selector": "meta[property='og:description']",
            "attr": "content",
            "description_source": "page-abstract"
        }
    If selector matches an element, extracts text via 'attr' (if set) or
    get_text(). Only fetches items with empty/short blurbs. Each filled item
    gets blurb_source = the config's description_source ('page-meta' for a
    one-sentence teaser, 'page-abstract' for a full abstract); without it,
    meta tags count as page-meta and anything else as page-abstract.

    Optional "extra_fields": {"type": {"selector": ..., "attr": ...}, ...}
    fills other item fields from the same page (a page-only publication type,
    a date). Optional "text_selector" scopes page_text to one container. Every fetched page also yields item["page_meta"] (common meta
    tags: description, og:*, article:published_time, canonical), item["page_text"]
    (readable main text, capped at PAGE_TEXT_MAX_CHARS) and
    item["fetched_status"] / item["fetched_at"], so the row records that the
    URL was live and what the page said, without a second request later.
    """
    detail = config.get("detail_fetch")
    if not detail:
        return items

    selector = detail["selector"]
    attr = detail.get("attr")
    label = detail.get("description_source") or (
        "page-meta" if selector.lstrip().startswith("meta") else "page-abstract")

    need_fetch = [(i, item) for i, item in enumerate(items)
                  if len(item.get("blurb", "")) < MIN_BLURB_LENGTH]

    if not need_fetch:
        print("[scrape] detail_fetch: all items already have descriptions, skipping")
        return items

    est_minutes = len(need_fetch) * _request_delay // 60
    print(f"[scrape] detail_fetch: {len(need_fetch)} items need descriptions (est. ~{est_minutes} min)...")

    for count, (i, item) in enumerate(need_fetch):
        if CONSECUTIVE_FAILURES >= MAX_CONSECUTIVE_FAILURES:
            print(f"[scrape] detail_fetch: stopping due to {MAX_CONSECUTIVE_FAILURES} consecutive failures.")
            print(f"[scrape] detail_fetch: {count}/{len(need_fetch)} fetched. Progress saved — rerun to resume.")
            _save_progress(source, items)
            break
        print(f"  [{count+1}/{len(need_fetch)}] {item['title'][:70]}")
        r = fetch(item["url"])
        if r:
            soup = BeautifulSoup(r.text, "html.parser")
            items[i]["fetched_status"] = getattr(r, "status_code", None)
            items[i]["fetched_at"] = time.strftime("%Y-%m-%d")
            items[i]["page_meta"] = extract_page_meta(soup)
            items[i]["page_text"] = extract_page_text(soup, selector=detail.get("text_selector"))
            for field, spec in (detail.get("extra_fields") or {}).items():
                fel = soup.select_one(spec["selector"])
                if fel:
                    val = clean_text(fel.get(spec.get("attr")) if spec.get("attr") else fel.get_text(" ", strip=True))
                    if val:
                        items[i][field] = val
            el = soup.select_one(selector)
            if el:
                desc = clean_text(el.get(attr) if attr else el.get_text(" ", strip=True))
                items[i]["blurb"] = desc
                items[i]["blurb_source"] = label
                print(f"    OK ({len(desc)} chars)")
            else:
                print(f"    No match for selector: {selector}")
        else:
            print("    Fetch failed")
        _save_progress(source, items)

    return items


PAGE_META_TAGS = {
    "description": "meta[name='description']",
    "og:title": "meta[property='og:title']",
    "og:description": "meta[property='og:description']",
    "og:type": "meta[property='og:type']",
    "article:published_time": "meta[property='article:published_time']",
    "citation_title": "meta[name='citation_title']",
    "citation_publication_date": "meta[name='citation_publication_date']",
    "citation_doi": "meta[name='citation_doi']",
    "dc.date": "meta[name='dc.date' i]",
}


PAGE_TEXT_MAX_CHARS = 20_000


def extract_page_text(soup, max_chars=PAGE_TEXT_MAX_CHARS, selector=None):
    """The page's readable main text (the config's text_selector if given, else
    article/main/role=main, else body) with scripts, styles, navigation,
    headers and footers removed; whitespace collapsed; capped. Stored on the
    row so later passes (description upgrades, tagging) never need to fetch
    the page again."""
    root = soup.select_one(selector) if selector else None
    if root is None:
        root = soup.select_one("article") or soup.select_one("main") or soup.select_one("[role='main']") or soup.body
    if root is None:
        return ""
    for tag in root.select("script, style, noscript, nav, header, footer, aside, form, iframe, svg"):
        tag.decompose()
    text = clean_text(root.get_text(" ", strip=True))
    return text[:max_chars]


def extract_page_meta(soup):
    """Common page-level metadata worth keeping from a detail fetch."""
    meta = {}
    for key, sel in PAGE_META_TAGS.items():
        el = soup.select_one(sel)
        if el and el.get("content"):
            meta[key] = clean_text(el.get("content"))
    canon = soup.select_one("link[rel='canonical']")
    if canon and canon.get("href"):
        meta["canonical"] = canon.get("href").strip()
    t = soup.find("title")
    if t and t.get_text(strip=True):
        meta["title"] = clean_text(t.get_text(" ", strip=True))
    return meta


def resolve_lookups(items, config):
    """For each entry in the config's "lookups" list — {field, url, id_path?,
    name_path?, items_path?} — fetch the taxonomy once and replace the ids in
    item[field] (a value or a list) with their names. The ids are kept as
    item[field + "_ids"]; for "type", the first name becomes the type and all
    names go to type_labels."""
    lookups = config.get("lookups")
    if not lookups or not items:
        return items
    for look in lookups:
        field = look.get("field", "type")
        r = fetch(look["url"], headers={"Accept": "application/json"})
        if not r:
            print(f"  WARNING: lookup for {field} failed — ids left as-is", file=sys.stderr)
            continue
        data = r.json()
        terms = resolve_json_path(data, look["items_path"]) if look.get("items_path") else data
        names = {}
        for t in terms or []:
            tid = resolve_json_path(t, look.get("id_path", "id"))
            name = resolve_json_path(t, look.get("name_path", "name"))
            if tid is not None and name:
                names[str(tid)] = clean_text(strip_html(str(name)))
        print(f"  lookup {field}: {len(names)} terms from {look['url']}")
        for item in items:
            raw_val = item.get(field)
            ids = raw_val if isinstance(raw_val, list) else ([raw_val] if raw_val not in ("", None, []) else [])
            ids = [str(i) for i in ids]
            if not ids or not all(i in names for i in ids):
                continue
            item[field + "_ids"] = ids
            labels = [names[i] for i in ids]
            if field == "type":
                item["type"] = labels[0]
                if len(labels) > 1:
                    item["type_labels"] = labels
            else:
                item[field] = labels
    return items


def apply_type_filter(items, config):
    """Split items by the config's "type_allow" list (source type labels,
    case-insensitive). Items with no type yet are kept — a later detail fetch
    may supply one. Rejected items carry filter_reason = "type_filtered:<label>"
    and are staged (not dropped) so the call can be reversed without re-scraping."""
    allow = config.get("type_allow")
    if not allow:
        return items, []
    allowed = {a.strip().lower() for a in allow}
    kept, filtered = [], []
    for item in items:
        label = (item.get("type") or "").strip()
        if not label or label.lower() in allowed:
            kept.append(item)
        else:
            item["filter_reason"] = f"type_filtered:{label}"
            filtered.append(item)
    return kept, filtered


# ── Main ──


def split_by_blurb(items, threshold=MIN_BLURB_LENGTH):
    """Split items into ready (blurb >= threshold) and backlog (blurb < threshold)."""
    ready, backlog = [], []
    for item in items:
        if len(item.get("blurb", "")) >= threshold:
            ready.append(item)
        else:
            item["backlog_reason"] = f"blurb too short ({len(item.get('blurb', ''))} chars)"
            backlog.append(item)
    return ready, backlog


def write_backlog(source, backlog_items):
    """Append backlog items to sources/{source}-backlog.txt, skipping URLs
    already present so repeated runs don't accumulate duplicate lines."""
    if not backlog_items:
        return
    path = SOURCES_DIR / f"{source}-backlog.txt"
    existing = set()
    if path.exists():
        with open(path, encoding="utf-8") as f:
            existing = {line.split("\t", 1)[0] for line in f if line.strip()}
    new_items = [i for i in backlog_items if i["url"] not in existing]
    if not new_items:
        print(f"[scrape] Backlog: 0 new items ({len(backlog_items)} already present in {path})")
        return
    with open(path, "a", encoding="utf-8") as f:
        for item in new_items:
            title = item.get("title", "").replace("\t", " ")
            reason = item.get("backlog_reason", "unknown")
            f.write(f"{item['url']}\t{title}\t{reason}\n")
    print(f"[scrape] Backlog: {len(new_items)} new items written to {path} "
          f"({len(backlog_items) - len(new_items)} already present)")


def main():
    parser = argparse.ArgumentParser(description="Scrape a source for the Renaissance Hub")
    parser.add_argument("source", help="Source slug (e.g., wested, tntp, digital-promise)")
    parser.add_argument("--pages", type=int, default=None, help="Limit pagination to N pages")
    parser.add_argument("--test", action="store_true", help="Test selectors against one page")
    parser.add_argument("--no-diff", action="store_true", help="Skip diff — include already-indexed items")
    parser.add_argument("--backfill", action="store_true",
                        help="Scan every page (early-stop off) but still skip already-indexed URLs; use with --pages for a bounded catch-up")
    parser.add_argument("--limit", type=int, default=None,
                        help="Keep only the first N new items (after the diff) — bounds detail fetches for a pilot run")
    parser.add_argument("--audit", action="store_true",
                        help="Print the request audit (repeated URLs, throttle gaps) for this source's request log and exit; no fetching")
    parser.add_argument("--stdout", action="store_true", help="Output to stdout instead of file")
    parser.add_argument("--fresh", action="store_true", help="Ignore progress file, start from scratch")
    args = parser.parse_args()

    source = resolve_source(args.source)
    config = load_config(source)
    discovery = config["discovery"]

    # Per-source delay override, never below MIN_DELAY (robots.txt may raise it)
    global _request_delay
    _request_delay = effective_delay(config)

    print(f"[scrape] Source: {source} ({discovery}, {_request_delay}s delay)")

    if args.audit:
        log_path = LOGS_DIR / f"{source}-requests.log"
        if not log_path.exists():
            print(f"[scrape] No request log at {log_path}")
            sys.exit(1)
        print_request_audit(audit_request_log(read_request_log(log_path), _request_delay), _request_delay)
        sys.exit(0)

    _start_request_log(source)
    check_robots(config)

    if args.test:
        ok = run_test(config, source)
        sys.exit(0 if ok else 1)

    # Check for saved progress (from interrupted detail_fetch)
    items = None
    if not args.fresh:
        items = _load_progress(source)
    if items is not None:
        already_done = sum(1 for i in items if len(i.get("blurb", "")) >= MIN_BLURB_LENGTH)
        print(f"[scrape] RESUMING from progress file: {len(items)} items, {already_done} with descriptions")
    else:
        # Known URLs drive both early-stop during pagination and the post-scrape diff.
        # --backfill keeps the diff (known pages are never re-fetched) but turns
        # early-stop off so every listing page up to --pages is scanned.
        existing = None if args.no_diff else load_existing_urls()
        stop_urls = None if args.backfill else existing

        # Run scrape
        if discovery == "sitemap":
            items = scrape_sitemap(config, args.pages)
        elif discovery == "pagination":
            items = scrape_pagination(config, args.pages, existing_urls=stop_urls)
        elif discovery == "single_page":
            items = scrape_single_page(config, args.pages)
        elif discovery == "api":
            items = scrape_api(config, args.pages, existing_urls=stop_urls)
        else:
            print(f"Error: unknown discovery type '{discovery}'", file=sys.stderr)
            sys.exit(1)

        # Deduplicate by URL
        seen_urls = set()
        deduped = []
        for item in items:
            key = item["url"].rstrip("/").lower()
            if key not in seen_urls:
                seen_urls.add(key)
                deduped.append(item)
        if len(deduped) < len(items):
            print(f"[scrape] Deduplicated: {len(items)} -> {len(deduped)}")
        items = deduped

        print(f"[scrape] Total items extracted: {len(items)}")

        # Diff (on by default)
        if existing is not None:
            new_items, already = diff_items(items, existing)
            print(f"[scrape] Already indexed: {len(already)}, New: {len(new_items)}")
            items = new_items

    # Provenance: text from the listing/API is 'listing' unless the config says
    # otherwise (an API that hands back a page's meta description is
    # 'page-meta'); detail_fetch relabels the items it fills. process_staged.py
    # stores it as description_source.
    listing_label = config.get("description_source", "listing")
    for item in items:
        if item.get("blurb") and not item.get("blurb_source"):
            item["blurb_source"] = listing_label

    # Taxonomy ids -> names (WordPress-style APIs return term ids)
    items = resolve_lookups(items, config)

    if args.limit is not None and len(items) > args.limit:
        print(f"[scrape] --limit {args.limit}: keeping the first {args.limit} of {len(items)} new items")
        items = items[:args.limit]

    # Type filter, pass 1: items whose listing type is out of scope are set
    # aside before any page is fetched for them.
    items, filtered = apply_type_filter(items, config)

    # Detail fetch: fill in descriptions from individual pages if configured
    if config.get("detail_fetch"):
        items = fetch_detail_descriptions(items, config, source)

    # Type filter, pass 2: types that only the page supplied (extra_fields)
    items, filtered_late = apply_type_filter(items, config)
    filtered.extend(filtered_late)
    if filtered:
        print(f"[scrape] Type filter: {len(filtered)} items set aside (kept in staging as filtered_items)")

    # Split by blurb quality
    ready, backlog = split_by_blurb(items)
    print(f"[scrape] Ready: {len(ready)}, Backlog: {len(backlog)}")

    # Write backlog
    write_backlog(source, backlog)

    # Clean up progress file on successful completion
    _clear_progress(source)

    # Output ready items
    output = {
        "source": source,
        "discovery": discovery,
        "total_ready": len(ready),
        "total_backlog": len(backlog),
        "items": ready,
        # Backlog and filtered items travel with the staging file, as full
        # item dicts, so process_staged.py can record them as excluded rows
        # (dedup, honest "new" counts, and nothing fetched is thrown away).
        "backlog_items": [dict(i, reason=i.get("backlog_reason", "")) for i in backlog],
        "total_filtered": len(filtered),
        "filtered_items": filtered,
    }

    if args.stdout:
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        STAGING_DIR.mkdir(parents=True, exist_ok=True)
        out_path = STAGING_DIR / f"{source}.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        print(f"[scrape] Written to {out_path}")

    if _run_requests:
        print_request_audit(audit_request_log(_run_requests, _request_delay), _request_delay)


if __name__ == "__main__":
    main()
