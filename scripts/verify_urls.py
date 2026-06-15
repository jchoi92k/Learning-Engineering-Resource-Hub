#!/usr/bin/env python3
"""
Verify entry URLs in the Renaissance AI and Education Resource Hub.

Domain-aware throttling: round-robins across domains so same-domain
requests are naturally spaced. Uses browser-like User-Agent to avoid
false 403s from bot-blocking sites.

Usage:
    python scripts/verify_urls.py                # verify all unverified entries
    python scripts/verify_urls.py --sample 100   # random sample of 100
    python scripts/verify_urls.py --source WWC   # verify one source only
    python scripts/verify_urls.py --recheck      # re-verify previously broken
    python scripts/verify_urls.py --stale 30     # re-verify entries not checked in 30 days
    python scripts/verify_urls.py --all          # verify everything
    python scripts/verify_urls.py --auto-exclude # auto-exclude confirmed-broken (404/410) URLs

Results written directly to data/hub.db.
"""
import argparse
import json
import random
import sqlite3
import sys
import time
from collections import defaultdict
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

import requests

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
DB_PATH = REPO_ROOT / "data" / "hub.db"
BROKEN_FILE = REPO_ROOT / "data" / "broken-urls.json"

DOMAIN_DELAY = 5
REQUEST_TIMEOUT = 15

# Browser-like UA to avoid false 403s from bot-blocking sites
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

TODAY = date.today().isoformat()

# 404/410 = truly gone. 403 = possibly bot-blocked (flag but don't auto-exclude).
CONFIRMED_BROKEN_CODES = {"404", "410"}


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def check_url(url):
    """HEAD then GET fallback. Returns (http_status_str, is_ok, method_used)."""
    try:
        r = SESSION.head(url, timeout=REQUEST_TIMEOUT, allow_redirects=True)
        if r.status_code == 405 or r.status_code == 403:
            r = SESSION.get(url, timeout=REQUEST_TIMEOUT, allow_redirects=True, stream=True)
            r.close()
            return str(r.status_code), r.status_code < 400, "GET"
        return str(r.status_code), r.status_code < 400, "HEAD"
    except requests.exceptions.Timeout:
        return "timeout", False, "HEAD"
    except requests.exceptions.ConnectionError as e:
        reason = str(e)[:40]
        return f"conn_err({reason})", False, "HEAD"
    except Exception as e:
        return str(e)[:40], False, "HEAD"


def round_robin_check(entries, conn, auto_exclude=False):
    by_domain = defaultdict(list)
    for e in entries:
        domain = urlparse(e["url"]).netloc
        by_domain[domain].append(e)

    domain_last_request = {}
    domain_403_count = defaultdict(int)
    domain_skipped = {}  # domain -> count of URLs skipped
    total = len(entries)
    checked = 0
    ok_count = 0
    broken_count = 0
    flagged_count = 0

    DOMAIN_403_THRESHOLD = 3

    # Show domain distribution
    print(f"\n  Domain distribution:")
    for domain, items in sorted(by_domain.items(), key=lambda x: -len(x[1])):
        print(f"    {domain}: {len(items)} URLs")
    print()

    start_time = time.time()

    while any(by_domain.values()):
        # Remove empty domains and domains that hit the 403 threshold
        for d in list(by_domain.keys()):
            if not by_domain[d]:
                del by_domain[d]
            elif domain_403_count[d] >= DOMAIN_403_THRESHOLD:
                skipped_count = len(by_domain[d])
                domain_skipped[d] = skipped_count
                print(f"  !! Skipping {skipped_count} remaining URLs from {d} (403 x{domain_403_count[d]})")
                del by_domain[d]
        if not by_domain:
            break

        now = time.time()

        # Pick the domain that has waited the longest (most idle time)
        best_domain = None
        best_idle = -1
        shortest_wait = float("inf")

        for domain in by_domain:
            last = domain_last_request.get(domain, 0)
            idle = now - last
            remaining = DOMAIN_DELAY - idle
            if idle >= DOMAIN_DELAY and idle > best_idle:
                best_domain = domain
                best_idle = idle
            if remaining < shortest_wait:
                shortest_wait = remaining
                if best_domain is None:
                    best_domain = domain

        if best_domain is None:
            break

        # Wait if the chosen domain is still on cooldown
        last = domain_last_request.get(best_domain, 0)
        remaining = DOMAIN_DELAY - (time.time() - last)
        if remaining > 0:
            time.sleep(remaining)

        entry = by_domain[best_domain].pop(0)
        http_status, ok, method = check_url(entry["url"])
        actual_delay = time.time() - domain_last_request.get(best_domain, 0) if best_domain in domain_last_request else 0
        domain_last_request[best_domain] = time.time()
        checked += 1

        elapsed = time.time() - start_time
        rate = checked / elapsed if elapsed > 0 else 0

        if ok:
            url_status = "verified"
            symbol = "+"
            ok_count += 1
        elif http_status in CONFIRMED_BROKEN_CODES:
            url_status = "broken"
            symbol = "X"
            broken_count += 1
        else:
            url_status = "flagged"
            symbol = "?"
            flagged_count += 1
            if http_status == "403":
                domain_403_count[best_domain] += 1

        excluded = 0
        exclude_reason = None
        if url_status == "broken" and auto_exclude:
            excluded = 1
            exclude_reason = f"broken_url_{http_status}"

        conn.execute("""
            UPDATE entries SET url_status = ?, url_http_status = ?, last_verified = ?,
                excluded = CASE WHEN ? = 1 THEN 1 ELSE excluded END,
                exclude_reason = CASE WHEN ? = 1 THEN ? ELSE exclude_reason END,
                updated_at = strftime('%Y-%m-%dT%H:%M:%SZ', 'now')
            WHERE num = ?
        """, (url_status, http_status, TODAY, excluded, excluded, exclude_reason, entry["num"]))

        delay_str = f"{actual_delay:.1f}s" if actual_delay > 0 else "first"
        print(f"  [{checked}/{total}] {symbol} {http_status:>4s} ({method}) [{best_domain}] {delay_str} | {entry['title'][:40]}  ({rate:.1f}/min)")

        if checked % 50 == 0:
            conn.commit()
            print(f"  --- checkpoint: {ok_count} OK, {broken_count} broken, {flagged_count} flagged ---")

    conn.commit()

    if domain_skipped:
        print(f"\n  Domains blocked (403 x{DOMAIN_403_THRESHOLD}+, remaining URLs skipped):")
        for domain, count in sorted(domain_skipped.items()):
            print(f"    {domain}: {count} URLs skipped")

    return ok_count, broken_count, flagged_count


def export_broken(conn):
    rows = conn.execute("""
        SELECT num, title, url, source, url_status, url_http_status, last_verified
        FROM entries WHERE url_status IN ('broken', 'flagged')
        ORDER BY url_status, num
    """).fetchall()

    entries = [dict(r) for r in rows]
    with open(BROKEN_FILE, "w", encoding="utf-8") as f:
        json.dump({"total": len(entries), "entries": entries}, f, indent=2, ensure_ascii=False)
    print(f"[verify] Broken/flagged URLs written to {BROKEN_FILE}")


def main():
    parser = argparse.ArgumentParser(description="Verify entry URLs")
    parser.add_argument("--sample", type=int, help="Random sample size")
    parser.add_argument("--source", type=str, help="Verify only this source (partial match)")
    parser.add_argument("--recheck", action="store_true", help="Re-verify previously broken URLs")
    parser.add_argument("--stale", type=int, metavar="DAYS", help="Re-verify entries not checked in the last N days")
    parser.add_argument("--all", action="store_true", help="Verify everything including already verified")
    parser.add_argument("--auto-exclude", action="store_true", help="Auto-exclude confirmed-broken (404/410) URLs")
    args = parser.parse_args()

    conn = get_db()

    if args.recheck:
        rows = conn.execute("SELECT num, url, title, source FROM entries WHERE url_status IN ('broken', 'flagged')").fetchall()
    elif args.all:
        rows = conn.execute("SELECT num, url, title, source FROM entries").fetchall()
    elif args.stale:
        cutoff = TODAY
        rows = conn.execute("""
            SELECT num, url, title, source FROM entries
            WHERE url_status = 'unverified'
               OR last_verified IS NULL
               OR last_verified <= date(?, '-' || ? || ' days')
        """, (cutoff, args.stale)).fetchall()
    else:
        rows = conn.execute("SELECT num, url, title, source FROM entries WHERE url_status = 'unverified'").fetchall()

    entries = [dict(r) for r in rows]

    if args.source:
        entries = [e for e in entries if args.source.lower() in e["source"].lower()]
        print(f"[verify] Filtered to {len(entries)} entries from '{args.source}'")

    if args.sample and len(entries) > args.sample:
        random.seed(42)
        entries = random.sample(entries, args.sample)

    if not entries:
        print("[verify] No entries to check.")
        conn.close()
        return

    domains = len(set(urlparse(e["url"]).netloc for e in entries))
    print(f"[verify] Checking {len(entries)} URLs across {domains} domains")
    print(f"[verify] Domain delay: {DOMAIN_DELAY}s | Timeout: {REQUEST_TIMEOUT}s")
    print(f"[verify] Status codes: + = verified, X = broken (404/410), ? = flagged (403/timeout/other)")

    ok_count, broken_count, flagged_count = round_robin_check(entries, conn, args.auto_exclude)

    print(f"\n[verify] Results: {ok_count} OK, {broken_count} broken, {flagged_count} flagged")

    if flagged_count > 0:
        print(f"[verify] Note: {flagged_count} 'flagged' entries may be bot-blocked (403) or temporarily unavailable.")
        print(f"[verify] These are NOT auto-excluded. Review manually or retry with --recheck.")

    export_broken(conn)

    # Summary by domain
    problem_domains = defaultdict(lambda: {"broken": 0, "flagged": 0})
    for row in conn.execute("SELECT url, url_status FROM entries WHERE url_status IN ('broken', 'flagged')"):
        domain = urlparse(row["url"]).netloc
        problem_domains[domain][row["url_status"]] += 1
    if problem_domains:
        print("\n[verify] Problem domains:")
        for domain, counts in sorted(problem_domains.items(), key=lambda x: -(x[1]["broken"] + x[1]["flagged"])):
            parts = []
            if counts["broken"]: parts.append(f"{counts['broken']} broken")
            if counts["flagged"]: parts.append(f"{counts['flagged']} flagged")
            print(f"  {domain}: {', '.join(parts)}")

    conn.close()


if __name__ == "__main__":
    main()
