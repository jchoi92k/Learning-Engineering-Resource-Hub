#!/usr/bin/env python3
"""
Check that the live MCP worker and the Vectorize index match docs/data.json.
Run after a deploy; exits non-zero on any mismatch so a workflow fails loudly.

Usage (from repo root):
    python scripts/check_deploy.py
    python scripts/check_deploy.py --skip-index   # worker checks only (no Cloudflare token)

Checks:
  1. get_stats on the worker reports the same entry count as docs/data.json.
  2. A search_resources query is served by semantic search and returns results
     (the worker falls back to keyword search silently when Vectorize fails).
  3. The Vectorize index holds exactly as many vectors as there are published
     entries (needs CLOUDFLARE_API_TOKEN + CLOUDFLARE_ACCOUNT_ID).
Each check is retried for a while: a new worker version and Vectorize
mutations take a short time to become visible.
"""
import argparse
import json
import sys
import time
from pathlib import Path

import requests

from embed_corpus import INDEX, load_env

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "docs" / "data.json"
MCP_URL = "https://renaissance-hub.joon-96a.workers.dev/mcp"
SEARCH_QUERY = "tutoring programs for middle school math"
ATTEMPTS = 12
WAIT = 15  # seconds between attempts: up to about 3 minutes per check


def call_tool(name, arguments):
    body = {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": name, "arguments": arguments}}
    r = requests.post(MCP_URL, json=body, timeout=60, headers={"Accept": "application/json, text/event-stream"})
    r.raise_for_status()
    result = r.json()["result"]
    if result.get("isError"):
        raise RuntimeError(result["content"][0]["text"])
    return result.get("structuredContent") or json.loads(result["content"][0]["text"])


def index_count(session, account):
    url = f"https://api.cloudflare.com/client/v4/accounts/{account}/vectorize/v2/indexes/{INDEX}/list"
    r = session.get(url, params={"count": 1}, timeout=60)
    r.raise_for_status()
    return r.json()["result"]["totalCount"]


def retry(label, check):
    """Run check() until it returns (ok, detail) with ok True, or give up."""
    detail = ""
    for attempt in range(1, ATTEMPTS + 1):
        try:
            ok, detail = check()
        except Exception as e:  # network blips count as a failed attempt
            ok, detail = False, f"error: {e}"
        if ok:
            print(f"[check] OK   {label}: {detail}")
            return True
        if attempt < ATTEMPTS:
            time.sleep(WAIT)
    print(f"[check] FAIL {label}: {detail} (after {ATTEMPTS} attempts)")
    return False


def main():
    parser = argparse.ArgumentParser(description="Check the live worker and index against docs/data.json")
    parser.add_argument("--skip-index", action="store_true", help="Skip the Vectorize count check")
    args = parser.parse_args()

    expected = json.loads(DATA_PATH.read_text(encoding="utf-8"))["meta"]["total"]
    print(f"[check] docs/data.json: {expected} published entries")

    def stats():
        total = call_tool("get_stats", {})["total_entries"]
        return total == expected, f"worker reports {total}"

    def search():
        res = call_tool("search_resources", {"query": SEARCH_QUERY, "limit": 5})
        mode, shown = res.get("search_mode"), res.get("showing", 0)
        return mode == "semantic" and shown > 0, f"search_mode={mode}, {shown} results"

    results = [retry("worker entry count", stats), retry("semantic search", search)]

    if not args.skip_index:
        token, account = load_env()
        session = requests.Session()
        session.headers.update({"Authorization": f"Bearer {token}"})

        def vectors():
            n = index_count(session, account)
            return n == expected, f"index holds {n}"

        results.append(retry("Vectorize vector count", vectors))

    if not all(results):
        sys.exit(1)
    print("[check] All checks passed.")


if __name__ == "__main__":
    main()
