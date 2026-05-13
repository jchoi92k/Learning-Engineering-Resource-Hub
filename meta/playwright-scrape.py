#!/usr/bin/env python3
"""
Renaissance AI and Education Resource Hub — Playwright / API Scraper

Handles JS-rendered and JS-paginated sources that static WebFetch can't reach.

    tntp             TNTP Publications (4 JS-paginated pages, 36 total)
    digital-promise  Digital Promise Research Library (DSpace 7 REST API, 252+ items)

Usage:
    python meta/playwright-scrape.py tntp
    python meta/playwright-scrape.py tntp --headed        # visible browser, for debugging
    python meta/playwright-scrape.py digital-promise
    python meta/playwright-scrape.py digital-promise --max 50

First-time setup (TNTP only — Playwright already installed):
    playwright install chromium
"""

import re
import sys
import json
import time
import argparse
import urllib.request
import urllib.error
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent.parent
FULL_FILE = ROOT / "docs" / "llms-full.txt"
STAGING_DIR = ROOT / "docs" / "staging"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}

# ── Tag inference ─────────────────────────────────────────────────────────────

TAG_KEYWORDS = {
    "k-12":                     ["k-12", "school", "teacher", "student", "classroom", "district", "principal"],
    "higher-ed":                ["college", "university", "higher education", "postsecondary"],
    "literacy":                 ["literacy", "reading", "writing"],
    "math-education":           ["math", "algebra", "numeracy"],
    "early-childhood":          ["early childhood", "preschool", "pre-k", "kindergarten"],
    "english-learners":         ["english learner", "ell ", "english language learner", "multilingual"],
    "professional-development": ["professional development", "teacher effectiveness", "coaching", "pd "],
    "rct":                      ["randomized", "rct", "controlled trial"],
    "longitudinal":             ["longitudinal", "multi-year", "over time"],
    "meta-analysis":            ["meta-analysis", "systematic review"],
    "coaching":                 ["instructional coach", "coaching"],
    "sel":                      ["social-emotional", "sel ", "belonging", "well-being"],
    "school-discipline":        ["discipline", "suspension", "expulsion"],
    "attendance":               ["attendance", "chronic absence", "absenteeism"],
    "college-access":           ["college access", "college-going", "first-generation"],
    "career-readiness":         ["career readiness", "workforce"],
    "dropout-prevention":       ["dropout", "graduation rate"],
    "formative-assessment":     ["assessment", "evaluation", "feedback"],
    "personalized-learning":    ["personalized", "differentiated"],
}


def clean_text(text):
    """Strip invisible Unicode characters (zero-width spaces, soft hyphens, etc.)."""
    invisible = ["​", "‌", "‍", "⁠", "﻿", "­"]
    for ch in invisible:
        text = text.replace(ch, "")
    return " ".join(text.split())  # also collapse whitespace


def infer_tags(text, base_tags=None):
    text_lower = text.lower()
    tags = set(base_tags or [])
    for tag, keywords in TAG_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            tags.add(tag)
    return sorted(tags)


# ── Corpus helpers ────────────────────────────────────────────────────────────

def load_existing_urls():
    content = FULL_FILE.read_text(encoding="utf-8")
    return set(re.findall(r'url: "([^"]+)"', content))


# ── Staging writer ────────────────────────────────────────────────────────────

def write_staging(slug, source_name, entries, summary_lines):
    today = date.today().isoformat()
    STAGING_DIR.mkdir(exist_ok=True)
    out = STAGING_DIR / f"backlog-{slug}-{today}.txt"

    header = [
        f"# Staging: Backlog expansion — {source_name}",
        f"# Date: {today}",
        *[f"# {line}" for line in summary_lines],
        "# Instructions: Review entries, then append to docs/llms-full.txt.",
        "#   Run: python docs/build_tags.py from docs/ after merging.",
        "",
    ]
    body = []
    for i, e in enumerate(entries, 1):
        tags_str = ", ".join(e["tags"])
        body += [
            f"### {i}. {e['title']}",
            "",
            "```yaml",
            f'url: "{e["url"]}"',
            f"type: {e['type']}",
            f'source: "{source_name}"',
            f"url_confirmed: {str(e['url_confirmed']).lower()}",
            "description_inferred: false",
            f"date_added: {today}",
            f"tags: [{tags_str}]",
            "```",
            "",
            e["desc"],
            "",
            "---",
            "",
        ]

    out.write_text("\n".join(header + body), encoding="utf-8")
    print(f"\n[playwright-scrape] Written: {out}")
    return out


# ── TNTP scraper (Playwright — JS-paginated listing) ─────────────────────────

def scrape_tntp(headless=True, max_pages=10):
    try:
        from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
    except ImportError:
        sys.exit("Playwright not found. Run: pip install playwright && playwright install chromium")

    existing = load_existing_urls()
    all_pub_urls = []
    entries = []
    skipped = 0
    failed = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        ctx = browser.new_context(user_agent=HEADERS["User-Agent"])

        # Phase 1: paginate the listing, collecting URLs from the ajax-list section only.
        # Scoping to .ajax-list-item avoids carousel and featured-section duplicates.
        listing = ctx.new_page()
        listing.goto("https://tntp.org/publications/", wait_until="networkidle", timeout=30000)

        for page_num in range(1, max_pages + 1):
            try:
                listing.wait_for_selector(".ajax-list-item a[href*='/publication/']", timeout=10000)
            except PWTimeout:
                print(f"[tntp] Timeout waiting for listing on page {page_num}.")
                break

            links = listing.eval_on_selector_all(
                ".ajax-list-item a[href*='/publication/']",
                "els => [...new Set(els.map(e => e.href))]"
            )
            new_on_page = [l for l in links if l not in all_pub_urls]
            all_pub_urls.extend(new_on_page)
            print(f"[tntp] Listing page {page_num}: {len(new_on_page)} new URLs "
                  f"(running total: {len(all_pub_urls)})")

            next_btn = listing.query_selector("a.next.page-numbers")
            if not next_btn:
                print(f"[tntp] No next-page button — reached last listing page.")
                break
            next_btn.click()
            listing.wait_for_load_state("networkidle")
            time.sleep(0.4)

        # Phase 2: fetch each publication page for title + description.
        print(f"\n[tntp] Fetching details for {len(all_pub_urls)} publications...")
        detail = ctx.new_page()

        for url in all_pub_urls:
            if url in existing:
                skipped += 1
                print(f"  SKIP (indexed): {url.split('/')[-2]}")
                continue

            try:
                detail.goto(url, wait_until="domcontentloaded", timeout=15000)

                title = ""
                for sel in ["h1.publication__title", "h1.entry-title", ".publication-title", "h1"]:
                    el = detail.query_selector(sel)
                    if el:
                        title = el.inner_text().strip()
                        if title:
                            break

                TNTP_GENERIC = "Explore our publications shaping America"

                # Primary: body paragraphs from the publication content section.
                # Take first 2–3 paragraphs and join into a single description.
                desc = ""
                body_paras = detail.eval_on_selector_all(
                    ".single-publication-content p",
                    "els => els.map(e => e.innerText.trim()).filter(t => t.length > 40)"
                )
                if body_paras:
                    combined = " ".join(body_paras[:3])
                    desc = clean_text(combined)[:700]

                # Fallback: meta description (skip if it's the generic site tagline).
                if len(desc) < 80:
                    meta_el = detail.query_selector("meta[name='description']")
                    if meta_el:
                        candidate = (meta_el.get_attribute("content") or "").strip()
                        if TNTP_GENERIC not in candidate:
                            desc = clean_text(candidate)

                title = clean_text(title)
                desc = clean_text(desc)

                if not title or len(desc) < 30:
                    print(f"  FAIL (no content): {url}")
                    failed.append(url)
                    continue

                tags = infer_tags(title + " " + desc, base_tags=["k-12"])
                entries.append({
                    "title": title,
                    "url": url,
                    "type": "report",
                    "url_confirmed": True,
                    "desc": desc[:700].strip(),
                    "tags": tags,
                })
                print(f"  OK: {title[:70]}")
                time.sleep(0.3)

            except PWTimeout:
                print(f"  TIMEOUT: {url}")
                failed.append(url)

        browser.close()

    summary = [
        f"New: {len(entries)} | Skipped (already indexed): {skipped} | Failed: {len(failed)}",
        "Discovery: https://tntp.org/publications/ (4 pages, 36 total)",
    ]
    if failed:
        summary.append(f"Failed URLs: {'; '.join(f.split('/')[-2] for f in failed)}")

    if entries:
        write_staging("tntp", "TNTP", entries, summary)
    else:
        print("[tntp] No new entries to stage.")
        print(f"  {skipped} already indexed, {len(failed)} failed.")

    print(f"\n[tntp] Done. {len(entries)} new, {skipped} skipped, {len(failed)} failed.")


# ── Digital Promise scraper (DSpace 7 REST API — no browser needed) ───────────

def scrape_digital_promise(max_items=100):
    """
    Uses the DSpace 7 REST API directly — no browser required.
    Individual item pages at /items/{uuid} are human-readable and url_confirmed.
    """
    existing = load_existing_urls()
    entries = []
    skipped = 0
    failed = 0

    API_BASE = "https://digitalpromise.dspacedirect.org/server/api"
    SITE_BASE = "https://digitalpromise.dspacedirect.org"
    PAGE_SIZE = 20
    api_page = 0
    total_elements = None

    print(f"[digital-promise] Querying DSpace REST API (max {max_items} items)...")

    while (len(entries) + skipped) < max_items:
        api_url = (
            f"{API_BASE}/discover/search/objects"
            f"?dsoType=item&size={PAGE_SIZE}&page={api_page}"
        )
        try:
            req = urllib.request.Request(
                api_url,
                headers={**HEADERS, "Accept": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            print(f"[digital-promise] API error on page {api_page}: {e}")
            break

        try:
            result = data["_embedded"]["searchResult"]
            objects = result["_embedded"]["objects"]
            page_meta = result["page"]
            if total_elements is None:
                total_elements = page_meta["totalElements"]
                print(f"[digital-promise] {total_elements} total items in DSpace.")
        except (KeyError, TypeError) as e:
            print(f"[digital-promise] Unexpected API response structure: {e}")
            break

        if not objects:
            print(f"[digital-promise] No more results.")
            break

        print(f"[digital-promise] API page {api_page}: {len(objects)} items")

        for obj in objects:
            try:
                item = obj["_embedded"]["indexableObject"]
                uuid = item["uuid"]
                item_url = f"{SITE_BASE}/items/{uuid}"

                if item_url in existing:
                    skipped += 1
                    continue

                metadata = item.get("metadata", {})

                title_meta = metadata.get("dc.title", [])
                title = title_meta[0].get("value", "").strip() if title_meta else ""

                desc_meta = (metadata.get("dc.description.abstract", [])
                             or metadata.get("dc.description", []))
                desc = desc_meta[0].get("value", "").strip() if desc_meta else ""

                subjects = " ".join(
                    s.get("value", "") for s in metadata.get("dc.subject", [])
                )

                title = clean_text(title)
                desc = clean_text(desc)

                if not title or not desc:
                    failed += 1
                    continue

                tags = infer_tags(title + " " + desc + " " + subjects,
                                  base_tags=["digital-promise"])
                entries.append({
                    "title": title,
                    "url": item_url,
                    "type": "report",
                    "url_confirmed": True,
                    "desc": desc[:700].strip(),
                    "tags": tags,
                })
                print(f"  OK: {title[:70]}")

            except (KeyError, TypeError, IndexError):
                failed += 1
                continue

        api_page += 1
        time.sleep(0.4)

        if total_elements and (api_page * PAGE_SIZE) >= total_elements:
            print(f"[digital-promise] All {total_elements} API items processed.")
            break

    summary = [
        f"New: {len(entries)} | Skipped (already indexed): {skipped} | No-content drops: {failed}",
        f"API: {API_BASE}/discover/search/objects?dsoType=item",
    ]
    if entries:
        write_staging("digital-promise", "Digital Promise", entries, summary)
    else:
        print("[digital-promise] No new entries to stage.")

    print(f"\n[digital-promise] Done. {len(entries)} new, {skipped} skipped, {failed} dropped.")


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Scrape JS-rendered/paginated sources for the Renaissance Hub."
    )
    parser.add_argument(
        "source", choices=["tntp", "digital-promise"],
        help="Source to scrape"
    )
    parser.add_argument(
        "--headed", action="store_true",
        help="(TNTP only) Launch browser in headed mode — useful for debugging selectors"
    )
    parser.add_argument(
        "--max", type=int, default=None,
        help="Max pages to paginate (TNTP) or max items to fetch (Digital Promise)"
    )
    args = parser.parse_args()

    if args.source == "tntp":
        scrape_tntp(headless=not args.headed, max_pages=args.max or 10)
    elif args.source == "digital-promise":
        scrape_digital_promise(max_items=args.max or 252)


if __name__ == "__main__":
    main()
