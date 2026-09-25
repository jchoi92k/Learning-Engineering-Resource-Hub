# Operator Guide

> How the hub is connected, deployed, and updated.
> Audience: whoever maintains the hub day-to-day (currently the user; eventually a handoff target).
> Read after `meta/agent-guide.md` if you're an agent; read this first if you're a human picking up operations.

---

## The four surfaces

The same underlying corpus (`data/hub.db`) feeds four consumer surfaces. **Updates do not propagate to all of them automatically.** You need to know which ones require manual action.

| Surface | URL | Data source | Auto-updates on `main` push? |
|---|---|---|---|
| **GitHub Pages web UI** | https://jchoi92k.github.io/Learning-Engineering-Resource-Hub | `docs/` directory on `main` | ✅ Yes — within ~1 min of push |
| **`llms.txt` / `llms-full.txt`** (for LLM agents) | Same Pages URL + `/llms.txt` or `/llms-full.txt` | `docs/llms.txt`, `docs/llms-full.txt` on `main` | ✅ Yes — via GitHub Pages |
| **MCP server** (Cloudflare Worker) | https://renaissance-hub.joon-96a.workers.dev/mcp | `docs/data.json` (bundled at deploy time) | ❌ **No** — requires `npx wrangler deploy` |
| **Gemini Gem** | gemini.google.com (the maintainer's account) | `docs/gem-knowledge.txt` uploaded into the Gem | ❌ **No** — requires manual re-upload |

---

## Data pipeline (canonical → derived)

```
data/hub.db          ← canonical source of truth (SQLite). Written by process_staged.py / verify_urls.py / curate.py.
        |
        | `python scripts/build_from_db.py`  (run by `scripts/update.sh`; also runnable manually)
        ↓
docs/llms-full.txt     ← full index with descriptions
docs/data.json         ← consumed by web UI; bundled into the MCP worker at deploy time
docs/llms.txt          ← compact index for LLM agents
docs/tags/*.md         ← per-tag pages for the web UI
docs/gem-knowledge.txt ← knowledge file uploaded to the Gemini Gem
```

`build_from_db.py` is the only build step. It validates UTF-8 encoding and regenerates every published file in `docs/` from hub.db. Entries with `url_status='broken'` are held out of published outputs (they stay in hub.db for re-checking). **Always run it after any change to hub.db**, commit the result, and remember the MCP worker needs a redeploy afterward (next section).

---

## Maintenance flows per surface

### 1. GitHub Pages web UI — automatic

Hosting: GitHub Pages, sourced from `docs/` on `main`.

Update flow:
- Merge anything to `main` (weekly update PR, manual commit, new-source PR, etc.).
- GitHub rebuilds the Pages site within ~1 minute.
- No action needed.

**Watch for:** GitHub Pages is *case-sensitive* on paths after the repo name. If you rename a file or directory, links break silently.

### 2. MCP server (Cloudflare Worker) — manual deploy

Hosted at: `https://renaissance-hub.joon-96a.workers.dev`. Code in `worker/`. Config in `worker/wrangler.toml` (name: `renaissance-hub`).

The worker **bundles `docs/data.json` at deploy time** (via `import rawData from "../../docs/data.json"` in `worker/src/index.js` — no copy step needed). This means the worker serves a frozen snapshot of data.json from whenever it was last deployed — it does *not* fetch live from GitHub Pages.

**After a weekly update PR or any corpus change merges to `main`, the MCP server returns stale data until you redeploy.**

Update flow:

```bash
cd worker
npx wrangler deploy
cd ..
python scripts/embed_corpus.py --endpoint http://localhost:8788   # after starting: npx wrangler dev --remote --config worker/populate.toml --port 8788
```

Semantic search: the search tool embeds queries via Workers AI (`@cf/baai/bge-base-en-v1.5`) and ranks against the `renaissance-hub-entries` Vectorize index (768d, cosine). `embed_corpus.py` keeps that index in sync with hub.db — run it after any corpus change (incremental: unchanged entries are skipped via `data/embed-cache.json`). Two auth options: the local populate worker (`worker/populate.toml`, uses wrangler's OAuth — no token needed) or a `CLOUDFLARE_API_TOKEN` + `CLOUDFLARE_ACCOUNT_ID` in `.env` for direct REST calls. If the index is empty or a binding fails, the worker silently falls back to keyword search — check the `search_mode` field in responses to confirm which path served a query.

Recommended cadence:
- After every weekly update PR merge (or batch a couple of weeks together if you're not under demo pressure).
- Before any presentation, demo, or external stakeholder check-in.
- After adding a new source (so MCP clients see the new entries).

You can verify the deployed entry count quickly:

```bash
curl -s https://renaissance-hub.joon-96a.workers.dev/ | grep "curated"
# or: curl -s -X POST https://renaissance-hub.joon-96a.workers.dev/mcp \
#   -H "Content-Type: application/json" \
#   -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"list_tags","arguments":{}}}' | jq .
```

The worker's tool descriptions use dynamic interpolation (`data.entries.length`), so they always reflect whatever is in the bundled `data.json`. No hardcoded counts to maintain.

### 3. Gemini Gem — manual upload

The hub is also exposed as a custom Gem at gemini.google.com. The Gem has two parts:

- **Instructions** (system prompt) — content lives in `meta/gem-instructions.md`. Rarely changes.
- **Knowledge file** — `docs/gem-knowledge.txt`. Regenerated by `build_from_db.py` on every build.

Update flow when the corpus changes:

1. Go to gemini.google.com → Gems (left sidebar) → your hub Gem → Edit.
2. Replace the existing knowledge file with the updated `docs/gem-knowledge.txt`.
3. Save.

Recommended cadence: same as the MCP worker, or whenever you want the Gem to know about recent entries.

If you also updated `meta/gem-instructions.md` (you changed how the Gem should respond), paste the new instructions into the Gem's Instructions field too.

### 4. `llms.txt` / `llms-full.txt` for agents — automatic via Pages

External LLM agents fetch these directly from the GitHub Pages URL:
- https://jchoi92k.github.io/Learning-Engineering-Resource-Hub/llms.txt
- https://jchoi92k.github.io/Learning-Engineering-Resource-Hub/llms-full.txt

Updates flow with GitHub Pages — same as the web UI. No action needed.

---

## The weekly update (GitHub Actions)

Workflow: `.github/workflows/weekly-update.yml`. Since 2026-09-20 it replaces the claude.ai routine (its prompt, `meta/automation-prompt.md`, is kept for history only). Everything it runs is read from the repo at run time, so there is no separate copy of the instructions to keep in sync.

Trigger: manual only for now (Actions tab → Weekly update → Run workflow). `dry_run` defaults to on: a dry run scrapes and reviews but writes nothing and opens no PR. A schedule has not been added yet.

What a run does:

1. **Job `update`** (read-only GitHub token):
   - `scripts/update.sh` scrapes the weekly source list (`WEEKLY_SOURCES` in the script), inserts new rows into `data/hub.db` and rebuilds `docs/`.
   - The `/weekly-update` skill (`.claude/skills/weekly-update/SKILL.md`) runs through `anthropics/claude-code-action` with `--already-run`: it triages failed sources, reviews the new rows with `scripts/curate.py` and writes the PR text to `docs/staging/pr-body.md`.
   - A guard step discards any change outside `data/hub.db`, `docs/`, `meta/processing-log.md` and `sources/*.json`, re-runs the checks (`build_from_db.py --check`, pytest, ruff) and writes a job summary. Nothing is published from a dry run, after a failed check, or when the review left no `pr-body.md`; the fix for a missing summary is to run again.
2. **Job `publish`**: commits the changes to the fixed branch `auto/weekly` as the GitHub App `renaissance-hub-updater` (force-push) and opens or updates the pull request. A maintainer reviews and merges; nothing reaches `main` without that. Weekly PRs are squash-merged by convention.

The job summary also reports the size of the review step (turns, refused tool calls, and an API-price equivalent in dollars). The review runs on a subscription token, so that dollar figure is an estimate and is not billed.

Related workflows:

- `.github/workflows/ci.yml` — pytest, ruff and `build_from_db.py --check` on every push to `main` and every PR.
- `.github/workflows/deploy.yml` — deploys `main` to the MCP worker and Vectorize (see the after-merge checklist).
- `.github/workflows/runner-access-check.yml` — manual, read-only dry run (`sources` input) to test whether a GitHub-hosted runner can reach a source.

Sources that cannot run from GitHub-hosted runners carry `skip_on_cloud_runner` in their `sources/*.json` config (see `sources/README.md`). Campbell Collaboration is one: it answered runners with HTTP 202 and no content, so it is off the weekly list and scraped by hand from a local run (`bash scripts/update.sh --sources "campbell-collaboration"`).

Update flow for the workflow itself:

| If you change… | You need to… |
|---|---|
| The skill, `update.sh`, a source config | Commit to `main`; the next run picks it up |
| The source list | Edit `WEEKLY_SOURCES` in `scripts/update.sh` |
| The Claude token or the App key | Replace the repo secret (see Accounts and access) |

---

## After-merge checklist (for weekly update PRs and new-source PRs)

When a corpus-changing PR merges to `main`, run through this:

1. ✅ **GitHub Pages** — auto-updates in ~1 minute. Verify by loading the Pages URL and checking the entry count on the home page.
2. ⚠️ **Local copy** — `git pull` (the PR changes `data/hub.db`, which the next two steps read).
3. ⚠️ **Vectorize + MCP worker** — run the **Deploy** workflow (Actions tab → Deploy → Run workflow, untick dry run). It re-embeds every published entry, deletes vectors of unpublished ones, runs `wrangler deploy` and then `scripts/check_deploy.py`, which fails the run if the live worker or the index does not match `docs/data.json`. It uses the repo secrets `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID`; a full re-embed is roughly 3,000 Workers AI neurons (estimate) against a free allowance of 10,000 per day.
4. **By hand instead** (no workflow): `python scripts/embed_corpus.py --endpoint http://localhost:8788` with the populate worker running (see section 2 above), then `cd worker && npx wrangler deploy`, then `python scripts/check_deploy.py --skip-index`. The worker imports `docs/data.json` directly; no copy step.
5. ⚠️ **Gemini Gem** — upload the new `docs/gem-knowledge.txt` to the Gem on gemini.google.com.

Steps 2, 3 and 5 are started by hand (step 4 is the fallback for step 3). If you skip them, downstream consumers stay on stale data without warning.

---

## Accounts and access

| Service | Account / Location | What's needed |
|---|---|---|
| GitHub | github.com/jchoi92k | Repo write access |
| GitHub Pages | (Repo settings) | Already configured to serve `docs/` from `main` |
| Cloudflare Workers | Cloudflare account that deployed `renaissance-hub` | `npx wrangler login` from `worker/` directory |
| Claude Code token for the weekly run | Maintainer's Claude subscription | Repo secret `CLAUDE_CODE_OAUTH_TOKEN`, created with `claude setup-token`; lasts one year |
| Updater GitHub App (`renaissance-hub-updater`) | Installed on the repo; Contents and Pull requests write | Repo secret `APP_PRIVATE_KEY`, repo variable `APP_CLIENT_ID` |
| Gemini Gem | gemini.google.com | The account that owns the Gem |

Secrets:
- **Never commit a token or key to the repo.** `.env` is gitignored.
- List repo secrets and variables by name only: `gh secret list --json name`, `gh variable list --json name`. A bare `gh variable list` prints values.
- If a secret leaks, revoke or rotate it at the issuer first (a new App private key in the App settings, a new `claude setup-token`), then replace the repo secret.

---

## Things that can drift (and how to detect)

The hub has four data surfaces. They can each drift from the canonical `data/hub.db`:

| Drift | How to detect | Fix |
|---|---|---|
| MCP worker behind `docs/data.json` | Compare `get_stats` total with `meta.total` in `docs/data.json` | `cd worker && npx wrangler deploy` |
| Vectorize behind the corpus | `python scripts/embed_corpus.py --dry-run --prune` reports pending upserts or deletes; `python scripts/check_deploy.py` compares the vector count | Run the Deploy workflow (after-merge step 3) |
| Gem knowledge file out of date | Ask the Gem a question whose answer requires a recent entry — if it whiffs, the knowledge is stale | Re-upload `docs/gem-knowledge.txt` |
| `meta/agent-guide.md` Current state count vs. actual | Compare to `meta.total` in `docs/data.json` | Update `agent-guide.md` per the hygiene rule |

The first one — worker drift — is the most easily forgotten and the most user-visible (LLM agents querying the MCP get wrong counts and miss entries). Make it a habit to redeploy after each weekly update PR.

---

## Common operations

### "I just merged a weekly update PR — what do I do?"

Run the after-merge checklist above: pull, embed, deploy the worker, re-upload the Gem file. GitHub Pages updates on its own.

### "I want to add a new source"

1. File a GitHub issue using the `[New source]` template.
2. After scope-check, run `meta/new-source-prompt.md` (interactive in Claude Code).
3. Review and merge the resulting PR.
4. Add the source's slug to `WEEKLY_SOURCES` in `scripts/update.sh` so the weekly run includes it. If the host refuses GitHub-hosted runners, test with `runner-access-check.yml` first; a source that cannot run there gets `skip_on_cloud_runner` in its config and a local run instead.
5. Run the after-merge checklist.

### "Want to check source accessibility before a run"

```bash
python scripts/source_check.py
```

Probes each source's discovery URL + a sample publication URL. Classifies each as OK / PARTIAL / DEGRADED / JS-RENDERED / BLOCKED. For reachability from GitHub-hosted runners specifically, run the `runner-access-check.yml` workflow instead.

The script reads its source list from `data/source-targets.json`, so it stays in sync automatically when sources are added or removed.

### "The weekly run failed or opened no PR"

- Open the run in the Actions tab and read the job summary: it lists the pipeline and review outcomes, whether `pr-body.md` was written, the checks, and any changes the guard discarded.
- No PR after a green run usually means nothing new was found, or it was a dry run.
- "Review summary: missing" means the review step did not finish its write-up; run the workflow again.
- A single source failing does not fail the run; it is reported in the PR text for a human.
- The `weekly-update-logs` artifact holds `run-summary.md` and the per-source logs.

### "The Claude token expired or was rotated"

1. Run `claude setup-token` locally.
2. Replace the repo secret `CLAUDE_CODE_OAUTH_TOKEN` (Settings → Secrets and variables → Actions).
3. Start a dry run of the weekly workflow to confirm.

### "Worker deploy is failing"

- `npx wrangler whoami` — confirm you're logged in. If not, `npx wrangler login`.
- Check `worker/wrangler.toml` — `name = "renaissance-hub"`.
- Check Cloudflare dashboard for any quota/billing flags on the account.
- If the worker URL changed for some reason, update `worker/src/index.js`'s help page text and re-publish.

---

## Handoff notes (if someone else takes over)

A new operator needs:
- Write access to github.com/jchoi92k/Learning-Engineering-Resource-Hub
- Cloudflare account access (so they can `wrangler deploy` to the existing worker — or accept moving the worker to their account)
- Their own Claude subscription token in `CLAUDE_CODE_OAUTH_TOKEN` for the weekly run
- Admin access to the `renaissance-hub-updater` GitHub App (or a replacement App with Contents and Pull requests write)
- The Gemini Gem (transferable or recreate-able — instructions in `meta/gem-instructions.md`)
- This file + `meta/agent-guide.md` + `index.md` to onboard

---

## Related docs

- `index.md` — public repo navigation
- `meta/agent-guide.md` — operational reference for indexing work
- `.claude/skills/weekly-update/SKILL.md` — the review step of the weekly run
- `meta/automation-prompt.md` — the retired routine prompt (history)
- `meta/backlog-prompt.md` — single-source backlog expansion
- `meta/new-source-prompt.md` — onboarding a brand-new source
- `meta/source-audit.md` — per-source access matrix
