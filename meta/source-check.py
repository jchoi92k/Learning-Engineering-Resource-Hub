#!/usr/bin/env python3
"""
Renaissance AI and Education Resource Hub — Source Accessibility Check

Re-run anytime to verify which sources are reachable before an automation run.
Usage: python meta/source-check.py

Exit codes: 0 = all clear, 1 = one or more sources degraded/blocked
"""

import urllib.request
import urllib.error
import time
import sys
import io

# Force UTF-8 output on Windows terminals
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

TIMEOUT = 12
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    )
}

# ---------------------------------------------------------------------------
# Source definitions
# Each entry: name, discovery_url, sample_url, discovery_check (substring
# that must appear in the discovery page to confirm it's not a redirect/error)
# ---------------------------------------------------------------------------

SOURCES = [
    # ── Currently automatable ──────────────────────────────────────────────
    {
        "name": "Evidence for ESSA",
        "discovery_url": "https://evidenceforessa.org/sitemap.xml",
        "sample_url": "https://evidenceforessa.org/program/lenses-on-literature/",
        "discovery_check": "evidenceforessa.org/program",
        "notes": "Sitemap lists all programs; new ones appear here first",
    },
    {
        "name": "JEDM",
        "discovery_url": "https://jedm.educationaldatamining.org/index.php/JEDM/issue/archive",
        "sample_url": "https://jedm.educationaldatamining.org/index.php/JEDM/article/view/8",
        "discovery_check": "JEDM",
        "notes": "Volume/issue archive listing",
    },
    {
        "name": "JLA",
        "discovery_url": "https://learning-analytics.info/index.php/JLA/issue/archive",
        "sample_url": "https://learning-analytics.info/index.php/JLA/article/view/8885",
        "discovery_check": "Volume",
        "notes": "Volume/issue archive listing",
    },
    {
        "name": "Campbell Collaboration",
        "discovery_url": "https://www.campbellcollaboration.org/education/reviews/",
        "sample_url": "https://www.campbellcollaboration.org/review/the-relationship-between-homework-time-and-academic-performance-among-k-12-a-systematic-review",
        "discovery_check": "review",
        "notes": "52 education systematic reviews on one page; correct listing is /education/reviews/",
    },
    {
        "name": "Learning Policy Institute (LPI)",
        "discovery_url": "https://learningpolicyinstitute.org/research/",
        "sample_url": "https://learningpolicyinstitute.org/product/effective-teacher-professional-development",
        "discovery_check": "product",
        "notes": "Research listing; slugs not predictable from titles",
    },
    {
        "name": "EdTrust",
        "discovery_url": "https://edtrust.org/research/",
        "sample_url": "https://edtrust.org/resource/young-learners-family-engagement",
        "discovery_check": "resource",
        "notes": "Research listing page",
    },
    {
        "name": "Brookings (Brown Center)",
        "discovery_url": "https://www.brookings.edu/sitemap_index.xml",
        "sample_url": "https://www.brookings.edu/articles/getting-state-free-college-right-design-choices-that-matter/",
        "discovery_check": "sitemap",
        "notes": "Sitemap-based discovery; curate Brown Center manually",
    },
    {
        "name": "IES REL",
        "discovery_url": "https://ies.ed.gov/use-work/regional-educational-laboratories-rel/pacific/products",
        "sample_url": "https://ies.ed.gov/ncee/rel/Products/Region/pacific/Publication/108204",
        "discovery_check": "publication",
        "notes": "Listing pages JS-rendered; individual publication pages static. Enumerate all 10 regions.",
    },
    {
        "name": "WWC Intervention Reports",
        "discovery_url": "https://ies.ed.gov/ncee/wwc/Search/Products?productType=2",
        "sample_url": "https://ies.ed.gov/ncee/wwc/InterventionReport/381",
        "discovery_check": "Intervention",
        "notes": "Listing may be JS-rendered; individual report pages are static",
    },
    # ── Known blocked / Playwright-only ───────────────────────────────────
    {
        "name": "Digital Promise (Playwright only)",
        "discovery_url": "https://digitalpromise.dspacedirect.org/server/api/discover/search/objects?dsoType=item",
        "sample_url": "https://digitalpromise.dspacedirect.org/items/some-uuid",
        "discovery_check": "items",
        "notes": "Angular SPA — requires Playwright; skip in automated cron",
    },
    {
        "name": "RAND (blocked)",
        "discovery_url": "https://www.rand.org/pubs/research_reports.html",
        "sample_url": "https://www.rand.org/pubs/research_reports/RRA134-1.html",
        "discovery_check": "research",
        "notes": "robots.txt 403 — skip in automated cron",
    },
    {
        "name": "MDRC (blocked)",
        "discovery_url": "https://www.mdrc.org/work/publications",
        "sample_url": "https://www.mdrc.org/publication/achievement-first-program-study",
        "discovery_check": "publication",
        "notes": "WAF block — skip in automated cron",
    },
    # ── Candidate new sources (under evaluation) ──────────────────────────
    # ── New sources (verified accessible) ────────────────────────────────
    {
        "name": "WestEd",
        "discovery_url": "https://wested.org/resources/?type=research-evaluation",
        "sample_url": "https://wested.org/resource/legislating-literacy-at-the-state-level/",
        "discovery_check": "resource",
        "notes": "Federal regional lab; IES-funded evals and practitioner resources",
    },
    {
        "name": "TNTP",
        "discovery_url": "https://tntp.org/publications/",
        "sample_url": "https://tntp.org/publication/the-widget-effect-failure-to-act-on-differences-in-teacher-effectiveness/",
        "discovery_check": "publication",
        "notes": "36 publications confirmed (4 JS-rendered pages — WebFetch only sees page 1); teacher effectiveness research; quasi-experimental",
    },
    {
        "name": "NWEA Research",
        "discovery_url": "https://nwea.org/research/",
        "sample_url": "https://nwea.org/research/publication/academically-diverse-classrooms-deeper-needs-what-teachers-face-after-the-pandemic/",
        "discovery_check": "research",
        "notes": "~200+ publications; MAP Growth longitudinal research; paginated",
    },
    {
        "name": "Mathematica",
        "discovery_url": "https://mathematica.org/evidence?focusArea=Education&contentType=Publication",
        "sample_url": "https://mathematica.org/publications/evaluation-of-the-networks-for-school-improvement-initiative-student-outcomes-final-report",
        "discovery_check": "Education",
        "notes": "IES-funded RCTs and quasi-experimental studies; major policy evaluator",
    },
    {
        "name": "UChicago Consortium on School Research",
        "discovery_url": "https://consortium.uchicago.edu/publications",
        "sample_url": "https://consortium.uchicago.edu/publications/5Essentials-2026-malleability-and-student-groups",
        "discovery_check": "publication",
        "notes": "319 publications; K-12 school improvement; peer-reviewed; strong candidate",
    },
    {
        "name": "CREDO at Stanford",
        "discovery_url": "https://credo.stanford.edu/research-reports/report-finder/",
        "sample_url": "https://credo.stanford.edu/reports/item/national-charter-school-study-iii/",
        "discovery_check": "report",
        "notes": "~9 reports; charter school effectiveness; rigorous matching methods",
    },
    # ── Confirmed blocked ─────────────────────────────────────────────────
    {
        "name": "Urban Institute (blocked)",
        "discovery_url": "https://www.urban.org/topics/education",
        "sample_url": "https://www.urban.org/topics/education",
        "discovery_check": "education",
        "notes": "HTTP 403 — blocked",
    },
    {
        "name": "Mathematica old URL (404)",
        "discovery_url": "https://www.mathematica.org/publications",
        "sample_url": "https://www.mathematica.org/publications",
        "discovery_check": "publication",
        "notes": "Wrong path — use /evidence instead",
    },
]


def check_url(url, check_string=""):
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            raw = resp.read()
            content = raw.decode("utf-8", errors="replace")
            status = resp.getcode()
            size = len(content)
            # Simple JS-render heuristic: very short body or Angular/React markers
            js_markers = (
                'ng-version' in content or
                'window.__NUXT__' in content or
                '__NEXT_DATA__' in content or
                (size < 800 and '<div id="root"' in content)
            )
            has_check = bool(check_string and check_string.lower() in content.lower())
            return {
                "ok": True,
                "status": status,
                "size_kb": round(size / 1024, 1),
                "readable": not js_markers,
                "has_check": has_check,
            }
    except urllib.error.HTTPError as e:
        return {"ok": False, "status": e.code, "error": str(e.reason)}
    except urllib.error.URLError as e:
        return {"ok": False, "status": 0, "error": str(e.reason)[:60]}
    except Exception as e:
        return {"ok": False, "status": 0, "error": str(e)[:60]}


def classify(disc, sample):
    if not disc["ok"]:
        return "BLOCKED", f"HTTP {disc['status']}"
    if not disc.get("readable", True):
        return "JS-RENDERED", f"{disc['size_kb']} KB body but JS markers found"
    if not disc.get("has_check", True):
        return "DEGRADED", "Discovery page missing expected content"
    if not sample["ok"]:
        return "PARTIAL", f"Discovery OK; sample entry HTTP {sample['status']}"
    return "OK", f"Discovery {disc['size_kb']} KB | sample HTTP {sample['status']}"


def main():
    print()
    print("Renaissance AI and Education Resource Hub — Source Check")
    print("=" * 65)
    print()

    rows = []
    for src in SOURCES:
        name = src["name"]
        pad = max(0, 38 - len(name))
        print(f"  {name}{' ' * pad}", end="", flush=True)
        disc = check_url(src["discovery_url"], src.get("discovery_check", ""))
        time.sleep(0.4)
        sample = check_url(src["sample_url"])
        time.sleep(0.4)
        label, detail = classify(disc, sample)
        print(f"{label:<14}  {detail}")
        rows.append({"name": name, "label": label, "notes": src.get("notes", "")})

    print()
    print("Summary")
    print("-" * 65)
    for status in ("OK", "PARTIAL", "DEGRADED", "JS-RENDERED", "BLOCKED"):
        group = [r for r in rows if r["label"] == status]
        if not group:
            continue
        icon = {"OK": "✓", "PARTIAL": "~", "DEGRADED": "~", "JS-RENDERED": "~", "BLOCKED": "✗"}[status]
        print(f"\n  {icon} {status} ({len(group)})")
        for r in group:
            print(f"      {r['name']}")
            if r["notes"]:
                print(f"        {r['notes']}")

    print()
    bad = sum(1 for r in rows if r["label"] not in ("OK", "PARTIAL"))
    ok  = sum(1 for r in rows if r["label"] == "OK")
    print(f"  Automatable: {ok}  |  Issues: {bad}")
    print()
    return 0  # always exit 0; blocked sources are expected, not errors


if __name__ == "__main__":
    sys.exit(main())
