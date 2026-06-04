#!/usr/bin/env python3
"""
Renaissance AI and Education Resource Hub — Source Accessibility Check

Probes each source's discovery URL and a sample publication URL, then
classifies accessibility as OK / PARTIAL / DEGRADED / JS-RENDERED / BLOCKED.

Source list is read from meta/source-targets.json — no hardcoded list to drift.
Sources without both sample_url and discovery_check fields are skipped.

Usage: python meta/source-check.py
"""

import json
import urllib.request
import urllib.error
import time
import sys
import io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

TIMEOUT = 12
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    )
}

ROOT = Path(__file__).parent.parent
TARGETS_FILE = ROOT / "meta" / "source-targets.json"


def load_sources():
    with open(TARGETS_FILE, encoding="utf-8") as f:
        raw = json.load(f)

    sources = []
    for name, cfg in raw.items():
        if name.startswith("_"):
            continue
        discovery_url = cfg.get("discovery_url", "")
        sample_url = cfg.get("sample_url", "")
        discovery_check = cfg.get("discovery_check", "")
        if not discovery_url or not sample_url or not discovery_check:
            continue
        if not discovery_url.startswith("http"):
            continue
        sources.append({
            "name": name,
            "discovery_url": discovery_url,
            "sample_url": sample_url,
            "discovery_check": discovery_check,
            "notes": cfg.get("notes", ""),
        })
    return sources


def check_url(url, check_string=""):
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            raw = resp.read()
            content = raw.decode("utf-8", errors="replace")
            status = resp.getcode()
            size = len(content)
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
    sources = load_sources()
    if not sources:
        print("No checkable sources found in", TARGETS_FILE)
        return 1

    print()
    print("Renaissance AI and Education Resource Hub — Source Check")
    print(f"Reading from: {TARGETS_FILE}")
    print("=" * 65)
    print()

    rows = []
    for src in sources:
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
    ok = sum(1 for r in rows if r["label"] == "OK")
    print(f"  Automatable: {ok}  |  Issues: {bad}")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
