#!/usr/bin/env python3
"""
Embed published hub entries and upsert them into the Cloudflare Vectorize
index that powers the MCP worker's semantic search.

Usage (from repo root):
    python scripts/embed_corpus.py            # embed new/changed entries only
    python scripts/embed_corpus.py --full     # re-embed everything
    python scripts/embed_corpus.py --dry-run  # show what would be embedded

Requires in .env (or the environment):
    CLOUDFLARE_API_TOKEN   - token with Workers AI (read/run) + Vectorize (edit) permissions
    CLOUDFLARE_ACCOUNT_ID  - the account id shown in the Cloudflare dashboard

Model: @cf/baai/bge-base-en-v1.5 (768 dims, cosine) — must match the index
created with `wrangler vectorize create renaissance-hub-entries
--dimensions=768 --metric=cosine` and the model the worker uses for queries.

Incremental behavior: a local cache (data/embed-cache.json, gitignored)
stores a hash of each entry's embedded text. Unchanged entries are skipped.
Entries excluded or de-published since the last run are deleted from the index.
"""
import argparse
import hashlib
import json
import sqlite3
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "hub.db"
CACHE_PATH = ROOT / "data" / "embed-cache.json"
ENV_PATH = ROOT / ".env"

MODEL = "@cf/baai/bge-base-en-v1.5"
INDEX = "renaissance-hub-entries"
BATCH = 90          # bge batch limit is 100 texts per request; stay under it
REQUEST_DELAY = 1.0  # gentle pacing between API calls


def load_env():
    env = {}
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    import os
    token = os.environ.get("CLOUDFLARE_API_TOKEN") or env.get("CLOUDFLARE_API_TOKEN")
    account = os.environ.get("CLOUDFLARE_ACCOUNT_ID") or env.get("CLOUDFLARE_ACCOUNT_ID")
    if not token or not account:
        print("[embed] Error: CLOUDFLARE_API_TOKEN and CLOUDFLARE_ACCOUNT_ID must be set "
              "in .env or the environment. Token needs Workers AI + Vectorize permissions.")
        sys.exit(1)
    return token, account


def load_entries():
    # Reader (WAL mode: never blocked by a writer); the timeout only matters if a writer holds a checkpoint.
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("""
        SELECT num, title, description, type, source
        FROM entries WHERE excluded = 0 AND url_status != 'broken' ORDER BY num
    """).fetchall()
    tags = {}
    for r in conn.execute("SELECT entry_num, tag FROM entry_tags ORDER BY tag"):
        tags.setdefault(r["entry_num"], []).append(r["tag"])
    conn.close()
    entries = []
    for r in rows:
        text = f"{r['title']}\n{r['description']}\nTags: {', '.join(tags.get(r['num'], []))}"
        entries.append({"num": r["num"], "text": text})
    return entries


def embed_batch(session, account, texts):
    url = f"https://api.cloudflare.com/client/v4/accounts/{account}/ai/run/{MODEL}"
    r = session.post(url, json={"text": texts}, timeout=60)
    r.raise_for_status()
    body = r.json()
    if not body.get("success"):
        raise RuntimeError(f"Workers AI error: {body.get('errors')}")
    return body["result"]["data"]


def upsert_vectors(session, account, vectors):
    """Upsert via the Vectorize v2 REST API (ndjson body)."""
    url = f"https://api.cloudflare.com/client/v4/accounts/{account}/vectorize/v2/indexes/{INDEX}/upsert"
    ndjson = "\n".join(json.dumps(v) for v in vectors)
    r = session.post(url, data=ndjson.encode("utf-8"),
                     headers={"Content-Type": "application/x-ndjson"}, timeout=120)
    r.raise_for_status()
    body = r.json()
    if not body.get("success"):
        raise RuntimeError(f"Vectorize upsert error: {body.get('errors')}")
    return body["result"]


DELETE_BATCH = 100  # Vectorize refuses more ids per delete call (VECTOR_DELETE_ERROR 40007)


def delete_vectors(session, account, ids):
    url = f"https://api.cloudflare.com/client/v4/accounts/{account}/vectorize/v2/indexes/{INDEX}/delete_by_ids"
    for i in range(0, len(ids), DELETE_BATCH):
        r = session.post(url, json={"ids": ids[i:i + DELETE_BATCH]}, timeout=60)
        r.raise_for_status()


def main():
    parser = argparse.ArgumentParser(description="Embed hub entries into Vectorize")
    parser.add_argument("--full", action="store_true", help="Re-embed everything, ignore cache")
    parser.add_argument("--dry-run", action="store_true", help="Report work without calling the API")
    parser.add_argument("--endpoint", help="Use a local populate worker (wrangler dev --remote --config populate.toml) "
                                           "instead of the REST API — no API token needed")
    args = parser.parse_args()

    token = account = None
    if not args.endpoint and not args.dry_run:
        token, account = load_env()
    entries = load_entries()
    print(f"[embed] {len(entries)} published entries in hub.db")

    cache = {}
    if CACHE_PATH.exists() and not args.full:
        cache = json.loads(CACHE_PATH.read_text(encoding="utf-8"))

    todo = []
    for e in entries:
        h = hashlib.sha256(e["text"].encode("utf-8")).hexdigest()[:16]
        e["hash"] = h
        if cache.get(str(e["num"])) != h:
            todo.append(e)

    current_ids = {str(e["num"]) for e in entries}
    stale = [k for k in cache if k not in current_ids]

    print(f"[embed] To embed: {len(todo)} new/changed | unchanged: {len(entries) - len(todo)} | stale to delete: {len(stale)}")
    if args.dry_run:
        return
    if not todo and not stale:
        print("[embed] Nothing to do.")
        return

    session = requests.Session()
    if not args.endpoint:
        session.headers.update({"Authorization": f"Bearer {token}"})

    done = 0
    for i in range(0, len(todo), BATCH):
        batch = todo[i:i + BATCH]
        if args.endpoint:
            r = session.post(args.endpoint, timeout=120,
                             json={"items": [{"num": e["num"], "text": e["text"]} for e in batch]})
            r.raise_for_status()
            body = r.json()
            if not body.get("ok"):
                raise RuntimeError(f"populate worker error: {body.get('error')}")
        else:
            vectors = embed_batch(session, account, [e["text"] for e in batch])
            upsert_vectors(session, account, [
                {"id": str(e["num"]), "values": vec, "metadata": {"num": e["num"]}}
                for e, vec in zip(batch, vectors)
            ])
        for e in batch:
            cache[str(e["num"])] = e["hash"]
        done += len(batch)
        print(f"[embed] {done}/{len(todo)} embedded + upserted")
        CACHE_PATH.write_text(json.dumps(cache, indent=0), encoding="utf-8")
        time.sleep(REQUEST_DELAY)

    if stale:
        if args.endpoint:
            for i in range(0, len(stale), DELETE_BATCH):
                r = session.post(args.endpoint, json={"deleteIds": stale[i:i + DELETE_BATCH]}, timeout=60)
                if r.status_code != 200 or not r.json().get("ok"):
                    raise RuntimeError(f"populate worker delete error ({r.status_code}): {r.text[:300]}")
                time.sleep(REQUEST_DELAY)
        else:
            delete_vectors(session, account, stale)
        for k in stale:
            cache.pop(k, None)
        CACHE_PATH.write_text(json.dumps(cache, indent=0), encoding="utf-8")
        print(f"[embed] Deleted {len(stale)} stale vectors")

    print(f"[embed] Done. Index '{INDEX}' now reflects {len(entries)} published entries.")
    print("[embed] Note: Vectorize mutations can take a short time to become queryable.")


if __name__ == "__main__":
    main()
