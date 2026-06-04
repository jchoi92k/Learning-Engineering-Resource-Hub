#!/usr/bin/env python3
"""
Generic scraper for the Renaissance AI and Education Resource Hub.

Reads per-source configs from meta/sources/{source}.json, fetches listing
data (sitemap, API, or paginated HTML), and outputs structured JSON.
The LLM agent never sees raw HTML — only the extracted fields.

Usage:
    python meta/scrape.py wested                  # full scrape
    python meta/scrape.py wested --pages 3        # limit pagination to 3 pages
    python meta/scrape.py wested --test           # test selectors against one page
    python meta/scrape.py wested --diff           # show only items not in llms-full.txt

Output goes to docs/staging/{source}.json (or stdout with --stdout).
"""
import argparse
import json
import os
import re
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
SOURCES_DIR = SCRIPT_DIR / "sources"
STAGING_DIR = REPO_ROOT / "docs" / "staging"
LLMS_FULL = REPO_ROOT / "docs" / "llms-full.txt"

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 (compatible; RenaissanceHub/1.0)"
})

CONSECUTIVE_FAILURES = 0
MAX_CONSECUTIVE_FAILURES = 3
MIN_BLURB_LENGTH = 30
DEFAULT_DELAY = 5  # seconds between requests (no-policy default)
_request_delay = DEFAULT_DELAY
_last_fetch_time = 0
BACKOFF_SCHEDULE = [5, 10, 20]  # seconds on 429/503, then give up


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


def check_robots(config):
    """Fetch robots.txt. Parse crawl-delay if present and use it as the request delay."""
    global _request_delay
    url = config.get("robots_txt")
    if not url:
        return True
    try:
        r = SESSION.get(url, timeout=15)
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


def _throttle():
    """Wait to respect the request delay between fetches."""
    global _last_fetch_time
    elapsed = time.time() - _last_fetch_time
    if _last_fetch_time > 0 and elapsed < _request_delay:
        time.sleep(_request_delay - elapsed)
    _last_fetch_time = time.time()


def _handle_rate_limit(status_code, url):
    """Retry with exponential backoff on 429/503. Returns response or None."""
    for attempt, wait in enumerate(BACKOFF_SCHEDULE):
        print(f"  HTTP {status_code} — backing off {wait}s (attempt {attempt + 1}/{len(BACKOFF_SCHEDULE)})...",
              file=sys.stderr)
        time.sleep(wait)
        try:
            r = SESSION.get(url, timeout=30)
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
    _throttle()
    try:
        r = SESSION.get(url, timeout=30, **kwargs)
        if r.status_code == 200:
            CONSECUTIVE_FAILURES = 0
            return r
        if r.status_code in (429, 503):
            result = _handle_rate_limit(r.status_code, url)
            if result:
                CONSECUTIVE_FAILURES = 0
                return result
        CONSECUTIVE_FAILURES += 1
        print(f"  HTTP {r.status_code}: {url}", file=sys.stderr)
        if CONSECUTIVE_FAILURES >= MAX_CONSECUTIVE_FAILURES:
            print(f"  {MAX_CONSECUTIVE_FAILURES} consecutive failures — stopping.", file=sys.stderr)
        return None
    except Exception as e:
        CONSECUTIVE_FAILURES += 1
        print(f"  Fetch error: {e} — {url}", file=sys.stderr)
        if CONSECUTIVE_FAILURES >= MAX_CONSECUTIVE_FAILURES:
            print(f"  {MAX_CONSECUTIVE_FAILURES} consecutive failures — stopping.", file=sys.stderr)
        return None


def fetch_post(url, headers=None, json_body=None):
    """POST request for API sources, with throttling and backoff."""
    global CONSECUTIVE_FAILURES
    _throttle()
    try:
        r = SESSION.post(url, headers=headers, json=json_body, timeout=30)
        if r.status_code == 200:
            CONSECUTIVE_FAILURES = 0
            return r
        if r.status_code in (429, 503):
            result = _handle_rate_limit(r.status_code, url)
            if result:
                CONSECUTIVE_FAILURES = 0
                return result
        CONSECUTIVE_FAILURES += 1
        print(f"  HTTP {r.status_code}: {url}", file=sys.stderr)
        return None
    except Exception as e:
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
            all_text = card.get_text(" ", strip=True)
            child_text = " ".join(el.get_text(" ", strip=True) for el in card.find_all(True))
            blurb = all_text
            for ct in [child_text]:
                for fragment in [el.get_text(strip=True) for el in card.find_all(True) if el.get_text(strip=True)]:
                    blurb = blurb.replace(fragment, "", 1)
            blurb = " ".join(blurb.split()).strip()
        elif "blurb_parent" in sel:
            parent_el = card.select_one(sel["blurb_parent"])
            if parent_el and parent_el.parent:
                container = parent_el.parent
                for child in container.find_all("span"):
                    child.decompose()
                blurb = container.get_text(strip=True).lstrip("| ").strip()
        else:
            blurb_el = card.select_one(sel.get("blurb", "NONE"))
            blurb = blurb_el.get_text(strip=True) if blurb_el else ""

        title = title_el.get_text(strip=True) if title_el else ""
        # Strip trailing date in parens, e.g. "Good Behavior Game (October 2024)"
        title = re.sub(r'\s*\([A-Z][a-z]+ \d{4}\)\s*$', '', title)

        item_url = url_el["href"] if url_el and url_el.has_attr("href") else ""
        if item_url and not item_url.startswith("http"):
            item_url = url_prefix + item_url

        item = {
            "title": title,
            "url": item_url,
            "type": type_el.get_text(strip=True) if type_el else "",
            "blurb": blurb,
        }

        # Extra fields (grade_level, evidence_tier, authors, date)
        for extra in ("grade_level", "evidence_tier", "authors", "date"):
            if extra in sel:
                el = card.select_one(sel[extra])
                if el:
                    if extra == "date" and el.has_attr("datetime"):
                        item[extra] = el["datetime"]
                    else:
                        item[extra] = el.get_text(strip=True)

        # Authors as list (multiple elements)
        if "authors" in sel:
            author_els = card.select(sel["authors"])
            if author_els:
                item["authors"] = [a.get_text(strip=True) for a in author_els]

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


def scrape_pagination(config, max_pages=None):
    """Paginate through HTML listing pages and extract items via CSS selectors."""
    base_url = config["discovery_url"]
    pag = config["pagination"]
    param = pag["param"]
    start = pag["start"]

    page_num = start
    all_items = []

    while True:
        if max_pages is not None and (page_num - start) >= max_pages:
            break

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
    """Remove HTML tags from a string."""
    if not text:
        return ""
    return re.sub(r'<[^>]+>', '', text).strip()


def scrape_api(config, max_pages=None):
    """Fetch from a REST/search API and extract items via JSON paths."""
    api = config["api"]
    paths = api["json_paths"]
    items_path = paths.get("items", "")

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

            # Strip HTML from descriptions
            desc = strip_html(desc) if isinstance(desc, str) else str(desc)
            title = strip_html(title) if isinstance(title, str) else str(title)

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
                "blurb": desc[:500],
                "type": item_type if isinstance(item_type, str) else str(item_type),
                "authors": authors if isinstance(authors, list) else [authors],
                "tags": tags if isinstance(tags, list) else [tags],
            }

            # Extra fields from config
            for field_name, field_path in api.get("extra_fields", {}).items():
                val = resolve_json_path(obj, field_path)
                if val:
                    item_dict[field_name] = val

            all_items.append(item_dict)

        print(f"  Extracted {len(raw_items)} items at {page_param}={page_num}")
        page_num += page_step
        pages_fetched += 1

    return all_items


# ── Diff against existing entries ──


DB_PATH = SCRIPT_DIR / "hub.db"


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
    """Append backlog items to meta/sources/{source}-backlog.txt."""
    if not backlog_items:
        return
    path = SOURCES_DIR / f"{source}-backlog.txt"
    with open(path, "a", encoding="utf-8") as f:
        for item in backlog_items:
            title = item.get("title", "").replace("\t", " ")
            reason = item.get("backlog_reason", "unknown")
            f.write(f"{item['url']}\t{title}\t{reason}\n")
    print(f"[scrape] Backlog: {len(backlog_items)} items written to {path}")


def main():
    parser = argparse.ArgumentParser(description="Scrape a source for the Renaissance Hub")
    parser.add_argument("source", help="Source slug (e.g., wested, tntp, digital-promise)")
    parser.add_argument("--pages", type=int, default=None, help="Limit pagination to N pages")
    parser.add_argument("--test", action="store_true", help="Test selectors against one page")
    parser.add_argument("--no-diff", action="store_true", help="Skip diff — include already-indexed items")
    parser.add_argument("--stdout", action="store_true", help="Output to stdout instead of file")
    args = parser.parse_args()

    source = resolve_source(args.source)
    config = load_config(source)
    discovery = config["discovery"]

    # Per-source delay override (default 3s)
    global _request_delay
    _request_delay = config.get("request_delay", DEFAULT_DELAY)

    print(f"[scrape] Source: {source} ({discovery}, {_request_delay}s delay)")

    check_robots(config)

    if args.test:
        ok = run_test(config, source)
        sys.exit(0 if ok else 1)

    # Run scrape
    if discovery == "sitemap":
        items = scrape_sitemap(config, args.pages)
    elif discovery == "pagination":
        items = scrape_pagination(config, args.pages)
    elif discovery == "single_page":
        items = scrape_single_page(config, args.pages)
    elif discovery == "api":
        items = scrape_api(config, args.pages)
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
    if not args.no_diff:
        existing = load_existing_urls()
        new_items, already = diff_items(items, existing)
        print(f"[scrape] Already indexed: {len(already)}, New: {len(new_items)}")
        items = new_items

    # Split by blurb quality
    ready, backlog = split_by_blurb(items)
    print(f"[scrape] Ready: {len(ready)}, Backlog: {len(backlog)}")

    # Write backlog
    write_backlog(source, backlog)

    # Output ready items
    output = {
        "source": source,
        "discovery": discovery,
        "total_ready": len(ready),
        "total_backlog": len(backlog),
        "items": ready,
    }

    if args.stdout:
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        STAGING_DIR.mkdir(parents=True, exist_ok=True)
        out_path = STAGING_DIR / f"{source}.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        print(f"[scrape] Written to {out_path}")


if __name__ == "__main__":
    main()
