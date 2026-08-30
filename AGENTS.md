# AGENTS.md — Renaissance AI and Education Resource Hub

Instructions for any coding agent (Claude Code, GitHub Actions agents, or others) working in this repository. Humans: start at `index.md`.

## What this is

A referatory of evidence-based K-12 and higher-education research links: metadata plus a description per entry, published for humans (GitHub Pages) and for LLM agents (`docs/llms.txt`, `docs/llms-full.txt`, an MCP server). `data/hub.db` (SQLite, committed) is the single source of truth; everything under `docs/` is generated from it.

## Setup

```bash
pip install -r requirements.txt      # Python 3.12 (see .python-version)
python -m pytest tests/ -q           # 30+ fast unit tests
ruff check scripts/ tests/
```

## The pipeline (all mechanics live in scripts; never re-implement them in prose)

```bash
bash scripts/update.sh [--dry-run] [--sources "lpi wwc"]   # weekly wrapper: scrape → insert → verify new URLs → build → docs/staging/run-summary.md
python scripts/scrape.py <source>            # one source; config in sources/<source>.json; output docs/staging/<source>.json
python scripts/process_staged.py <source>    # insert staged items into hub.db (auto-tagging; backlog items become pending rows)
python scripts/verify_urls.py --min-num N    # verify rows added this run (num > N)
python scripts/build_from_db.py              # regenerate docs/ from hub.db; --check verifies docs/ match hub.db
python scripts/embed_corpus.py               # sync embeddings to Cloudflare Vectorize (needs CLOUDFLARE_* env)
```

## Rules

- **Descriptions come from the source.** Listing blurbs, page abstracts or meta descriptions — never written from a title alone. If a page cannot be fetched, drop the entry. Each row's `description_source` (`listing` / `page-meta` / `page-abstract` / `llm-summary` / `manual`) records which kind of text it holds; see `docs/schema.md`.
- **Only scripts write `hub.db`.** Do not hand-edit `docs/` (it is regenerated) and do not edit `data/hub.db` outside `process_staged.py` / `verify_urls.py` / a reviewed one-off script.
- **UTF-8 everywhere**; always pass `encoding="utf-8"`.
- **Throttle.** `scrape.py` and `verify_urls.py` already wait ≥ 5 s between requests and honour robots.txt `Crawl-delay`; do not add ad-hoc HTTP calls elsewhere.
- **Edit surface for automated runs:** `sources/*.json` (scraper configs) and, through the scripts, `hub.db` and `docs/`. Do not modify `scripts/`, `.github/`, `.claude/`, `AGENTS.md` or `CLAUDE.md` in an unattended run; propose those changes in the PR body instead.
- **Never push to `main` or merge.** Automated runs open a pull request; a maintainer merges.
- Run the tests before proposing a code change; run `build_from_db.py --check` before proposing a data change.

## Where to read more

- `index.md` — repo map and common operations
- `meta/agent-guide.md` — entry format, tag vocabulary, source URL patterns, no-inference policy
- `sources/README.md` — scraping conventions, backlog format, per-source profiles (`sources/<source>.md`)
- `docs/schema.md` — field definitions and the controlled tag vocabulary
- `meta/operator-guide.md` — deployment surfaces (Pages, MCP worker, Gem) and what needs a manual step
