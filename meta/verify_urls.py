#!/usr/bin/env python3
"""
Verify entry URLs in the Renaissance AI and Education Resource Hub.

Domain-aware throttling: round-robins across domains so same-domain
requests are naturally spaced. Falls back to a per-domain delay when
only one domain remains.

Usage:
    python meta/verify_urls.py                # verify all entries
    python meta/verify_urls.py --sample 100   # random sample of 100
    python meta/verify_urls.py --source WWC   # verify one source only
    python meta/verify_urls.py --recheck      # only re-verify previously broken

Results saved to meta/url-verification.json (merged with existing).
Broken entries saved to meta/broken-urls.json.
"""
import argparse
import json
import random
import sys
import time
from collections import defaultdict
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

import requests

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
DATA_JSON = REPO_ROOT / "docs" / "data.json"
VERIFICATION_FILE = SCRIPT_DIR / "url-verification.json"
BROKEN_FILE = SCRIPT_DIR / "broken-urls.json"

DOMAIN_DELAY = 3  # seconds between requests to the same domain
REQUEST_TIMEOUT = 15

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 (compatible; RenaissanceHub/1.0)"
})

TODAY = date.today().isoformat()


def load_verification():
    if VERIFICATION_FILE.exists():
        with open(VERIFICATION_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_verification(data):
    with open(VERIFICATION_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def check_url(url):
    """HEAD request with GET fallback. Returns (status_code, ok)."""
    try:
        r = SESSION.head(url, timeout=REQUEST_TIMEOUT, allow_redirects=True)
        if r.status_code == 405:
            r = SESSION.get(url, timeout=REQUEST_TIMEOUT, allow_redirects=True, stream=True)
            r.close()
        return r.status_code, r.status_code < 400
    except requests.exceptions.Timeout:
        return "timeout", False
    except requests.exceptions.ConnectionError:
        return "connection_error", False
    except Exception as e:
        return str(e)[:50], False


def round_robin_check(entries):
    """Check URLs by round-robining across domains for natural spacing."""
    by_domain = defaultdict(list)
    for e in entries:
        domain = urlparse(e["url"]).netloc
        by_domain[domain].append(e)

    domain_last_request = {}
    results = {}
    total = len(entries)
    checked = 0

    while any(by_domain.values()):
        # Clean empty domains
        by_domain = {d: q for d, q in by_domain.items() if q}
        if not by_domain:
            break

        # Find a domain that's ready (off cooldown)
        ready_domain = None
        min_wait = float("inf")
        now = time.time()

        for domain in by_domain:
            last = domain_last_request.get(domain, 0)
            remaining = DOMAIN_DELAY - (now - last)
            if remaining <= 0:
                ready_domain = domain
                break
            if remaining < min_wait:
                min_wait = remaining
                ready_domain = domain

        if ready_domain is None:
            break

        # Wait if needed
        last = domain_last_request.get(ready_domain, 0)
        remaining = DOMAIN_DELAY - (time.time() - last)
        if remaining > 0:
            time.sleep(remaining)

        entry = by_domain[ready_domain].pop(0)
        status, ok = check_url(entry["url"])
        domain_last_request[ready_domain] = time.time()
        checked += 1

        url_key = entry["url"].rstrip("/")
        results[url_key] = {
            "num": entry["num"],
            "status": status,
            "ok": ok,
            "last_verified": TODAY,
        }

        symbol = "+" if ok else "X"
        print(f"  [{checked}/{total}] {symbol} {status} {entry['title'][:50]}")

    return results


def main():
    parser = argparse.ArgumentParser(description="Verify entry URLs")
    parser.add_argument("--sample", type=int, help="Random sample size")
    parser.add_argument("--source", type=str, help="Verify only this source (partial match)")
    parser.add_argument("--recheck", action="store_true", help="Only re-verify previously broken URLs")
    args = parser.parse_args()

    with open(DATA_JSON, encoding="utf-8") as f:
        data = json.load(f)

    entries = data["entries"]

    if args.source:
        entries = [e for e in entries if args.source.lower() in e["source"].lower()]
        print(f"[verify] Filtered to {len(entries)} entries from '{args.source}'")

    if args.recheck:
        existing = load_verification()
        broken_urls = {k for k, v in existing.items() if not v.get("ok", True)}
        entries = [e for e in entries if e["url"].rstrip("/") in broken_urls]
        print(f"[verify] Re-checking {len(entries)} previously broken URLs")

    if args.sample and len(entries) > args.sample:
        random.seed(42)
        entries = random.sample(entries, args.sample)

    print(f"[verify] Checking {len(entries)} URLs across {len(set(urlparse(e['url']).netloc for e in entries))} domains")

    results = round_robin_check(entries)

    # Merge with existing verification data
    existing = load_verification()
    existing.update({k: v for k, v in results.items()})
    save_verification(existing)

    # Count results
    ok_count = sum(1 for v in results.values() if v["ok"])
    broken_count = sum(1 for v in results.values() if not v["ok"])
    print(f"\n[verify] Results: {ok_count} OK, {broken_count} broken")

    # Write broken entries
    all_broken = {k: v for k, v in existing.items() if not v.get("ok", True)}
    broken_entries = []
    for e in data["entries"]:
        url_key = e["url"].rstrip("/")
        if url_key in all_broken:
            broken_entries.append({
                "num": e["num"],
                "title": e["title"],
                "url": e["url"],
                "source": e["source"],
                "status": all_broken[url_key]["status"],
                "last_verified": all_broken[url_key]["last_verified"],
            })

    with open(BROKEN_FILE, "w", encoding="utf-8") as f:
        json.dump({"total_broken": len(broken_entries), "entries": broken_entries}, f, indent=2, ensure_ascii=False)
    print(f"[verify] Broken URLs written to {BROKEN_FILE}")

    # Summary by domain
    broken_by_domain = defaultdict(int)
    for e in broken_entries:
        broken_by_domain[urlparse(e["url"]).netloc] += 1
    if broken_by_domain:
        print("\n[verify] Broken by domain:")
        for domain, count in sorted(broken_by_domain.items(), key=lambda x: -x[1]):
            print(f"  {domain}: {count}")


if __name__ == "__main__":
    main()
