#!/usr/bin/env bash
# Weekly corpus update: scrape every automated source, insert new entries into
# hub.db, rebuild the published files, and write a run summary for the PR body.
# URL verification is OFF by default (2026-09-06): repeated per-URL checks from
# this machine's IP got it edge-blocked by digitalpromise.dspacedirect.org, and
# that host signals the block with a soft 202 that the verifier reads as a pass,
# so its 403 circuit-breaker never trips. Opt back in per-run with --verify.
#
# Usage (from repo root; Git Bash on Windows, bash on Linux/CI):
#   scripts/update.sh                       # full run over WEEKLY_SOURCES (no verify)
#   scripts/update.sh --dry-run             # scrape only: no DB writes, no build
#   scripts/update.sh --sources "wwc lpi"   # limit to given source slugs
#   scripts/update.sh --verify              # re-enable verify_urls.py on the new rows
#   scripts/update.sh --scrape-args "--pages 1 --limit 2"   # extra scrape.py flags for every source (pilot runs)
#
# Env: PYTHON (default: python), RUN_SUMMARY (default: docs/staging/run-summary.md),
#      SOURCE_GAP (seconds to pause between sources, default 5).
#
# Not in the weekly list on purpose (see meta/operator-guide.md and sources/*.md):
#   brookings (selected set; its Research label mixes reports with commentary),
#   casel (60s crawl-delay + detail fetch, run manually), jedm/jla (frozen
#   selective set), ies-rel (no config), aims/rand/mdrc/nap (blocked or manual).
#
# digital-promise is back in the list (2026-09-20) for cloud runs: dspacedirect
# edge-blocked the maintainer's home IP on 2026-09-06 after per-URL verification,
# but answers GitHub-hosted runners normally. From a blocked IP the scrape stops
# after two refusals. Never run --verify against it.
# campbell-collaboration opts out of cloud runners in its config
# (skip_on_cloud_runner): it is scraped from a laptop only.
#
# The script never aborts on a single failing source: each source's outcome is
# recorded in the summary and the run continues. Exit code is non-zero only if
# a pipeline step (process/verify/build) fails.

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

PY="${PYTHON:-python}"
WEEKLY_SOURCES=(
  campbell-collaboration
  credo
  digital-promise
  edtrust
  evidence-for-essa
  lpi
  lpi-briefs
  lpi-fact-sheets
  mathematica
  nwea-research
  tntp
  uchicago-consortium
  wested
  wwc
  wwc-practice-guides
)

DRY_RUN=0
SKIP_VERIFY=1  # verification off by default since 2026-09-06 (see header); --verify to opt in
SCRAPE_ARGS=()  # extra flags appended to every scrape.py call (--scrape-args)
SOURCE_GAP="${SOURCE_GAP:-5}"  # back-to-back configs can share a host (the three LPI ones)
SOURCES=("${WEEKLY_SOURCES[@]}")
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=1 ;;
    --skip-verify) SKIP_VERIFY=1 ;;  # no-op now (verify already off by default); kept for compatibility
    --verify) SKIP_VERIFY=0 ;;
    --sources) shift; read -r -a SOURCES <<< "$1" ;;
    --scrape-args) shift; read -r -a SCRAPE_ARGS <<< "$1" ;;
    -h|--help) sed -n '2,23p' "$0"; exit 0 ;;
    *) echo "Unknown option: $1" >&2; exit 2 ;;
  esac
  shift
done

STAGING="docs/staging"
LOG_DIR="$STAGING/logs"
SUMMARY="${RUN_SUMMARY:-$STAGING/run-summary.md}"
mkdir -p "$LOG_DIR"
TODAY="$(date +%Y-%m-%d)"

# One pipeline run at a time: a second run would race this one for the staging
# files and for hub.db's single writer slot. The lock is a directory because
# mkdir is atomic everywhere we run (flock is not available in Git Bash).
LOCK_DIR="$STAGING/update.lock"
if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  other_pid="$(cat "$LOCK_DIR/pid" 2>/dev/null || echo '?')"
  other_start="$(cat "$LOCK_DIR/started" 2>/dev/null || echo '?')"
  if [[ "$other_pid" =~ ^[0-9]+$ ]] && kill -0 "$other_pid" 2>/dev/null; then
    echo "[update] another run is active (pid $other_pid, started $other_start); aborting."\
         "If that run is dead, remove $LOCK_DIR and retry." >&2
    exit 3
  fi
  echo "[update] removing stale lock left by pid $other_pid (started $other_start)"
  rm -rf "$LOCK_DIR" && mkdir "$LOCK_DIR"
fi
echo $$ > "$LOCK_DIR/pid"
date -u +%Y-%m-%dT%H:%M:%SZ > "$LOCK_DIR/started"
trap 'rm -rf "$LOCK_DIR"' EXIT

db_max_num() {
  "$PY" -c "import sqlite3; print(sqlite3.connect('data/hub.db').execute('SELECT COALESCE(MAX(num),0) FROM entries').fetchone()[0])"
}

START_MAX="$(db_max_num)"
echo "[update] $TODAY | ${#SOURCES[@]} sources | dry-run=$DRY_RUN | scrape-args: ${SCRAPE_ARGS[*]:-none} | max(num) before run: $START_MAX"

# Per-source results: slug|status|scraped|new|ready|backlog|inserted|pending|filtered|range
RESULTS=()
FAILED_SOURCES=()
PIPELINE_FAILED=0
TOTAL_INSERTED=0
TOTAL_PENDING=0
TOTAL_FILTERED=0
CLOUD_SKIPPED=()   # sources whose config opts out of cloud runners (skip_on_cloud_runner)
RECON_WARNINGS=()  # per-source counts that do not add up (see the reconciliation checks below)

for src in "${SOURCES[@]}"; do
  echo
  echo "===== $src ====="
  log="$LOG_DIR/$src.log"
  status="ok"
  scraped=0; new=0; ready=0; backlog=0; filtered=0; inserted=0; pending=0; held=0; range="-"

  # A config can opt out of cloud runners ("skip_on_cloud_runner": "<reason>"):
  # some hosts answer datacenter IPs with a challenge page. On GitHub Actions the
  # source is listed as skipped, with no request made; anywhere else it runs.
  if [[ "${GITHUB_ACTIONS:-}" == "true" && -f "sources/$src.json" ]]; then
    skip_reason="$("$PY" -c 'import json,sys; print(json.load(open(sys.argv[1], encoding="utf-8")).get("skip_on_cloud_runner") or "")' "sources/$src.json" 2>/dev/null)"
    if [[ -n "$skip_reason" ]]; then
      echo "  skipped on this cloud runner: $skip_reason"
      CLOUD_SKIPPED+=("$src")
      RESULTS+=("$src|skipped (laptop only)|0|0|0|0|0|0|0|-")
      continue
    fi
  fi

  # Remove any stale staging file so a failed scrape can't feed last run's items
  # to process_staged. --fresh: ignore a leftover progress file from an
  # interrupted detail_fetch.
  rm -f "$STAGING/$src.json"
  if "$PY" scripts/scrape.py "$src" --fresh "${SCRAPE_ARGS[@]}" > "$log" 2>&1; then
    scraped="$(sed -n 's/^\[scrape\] Total items extracted: \([0-9]*\).*/\1/p' "$log" | tail -1)"
    new="$(sed -n 's/^\[scrape\] Already indexed: [0-9]*, New: \([0-9]*\).*/\1/p' "$log" | tail -1)"
    ready="$(sed -n 's/^\[scrape\] Ready: \([0-9]*\), Backlog: \([0-9]*\).*/\1/p' "$log" | tail -1)"
    backlog="$(sed -n 's/^\[scrape\] Ready: \([0-9]*\), Backlog: \([0-9]*\).*/\2/p' "$log" | tail -1)"
    # Items set aside by a config rule (type_allow / exclude_when) are recorded as
    # excluded rows so next week's dedup knows them, so they must reach process_staged.
    filtered="$(sed -n 's/^\[scrape\] Filters: \([0-9]*\) items set aside.*/\1/p' "$log" | tail -1)"
    if grep -q "consecutive failures" "$log"; then
      status="partial (fetch failures)"
    elif [[ "${scraped:-0}" == "0" ]]; then
      status="empty (0 items extracted — selector drift or block?)"
    fi
  else
    status="scrape failed (exit $?)"
  fi
  scraped="${scraped:-0}"; new="${new:-0}"; ready="${ready:-0}"; backlog="${backlog:-0}"; filtered="${filtered:-0}"
  grep -E "^\[scrape\]|Early stop|HTTP [0-9]{3}|consecutive failures|Error" "$log" | sed 's/^/  /'

  if [[ "$status" != "ok" && "$status" != partial* ]]; then
    FAILED_SOURCES+=("$src")
  fi

  # Reconciliation, scrape side: every item not in the DB must land in one of
  # the three piles. A remainder means items were dropped without a record, so
  # next week's run would find them again (the 2026-09-14 filtered-items gap).
  # --limit cuts the new items before they are sorted, so compare against the cut.
  if [[ "$status" == "ok" || "$status" == partial* ]]; then
    expected="$new"
    limited="$(sed -n 's/^\[scrape\] --limit [0-9]*: keeping the first \([0-9]*\) of.*/\1/p' "$log" | tail -1)"
    if [[ -n "$limited" ]]; then expected="$limited"; fi
    if [[ $(( ready + backlog + filtered )) -ne $expected ]]; then
      RECON_WARNINGS+=("$src: scrape found $expected items not in the DB but sorted $(( ready + backlog + filtered )) (ready $ready + backlog $backlog + filtered $filtered)")
    fi
  fi

  if [[ $DRY_RUN -eq 0 && ( "$ready" != "0" || "$backlog" != "0" || "$filtered" != "0" ) && -f "$STAGING/$src.json" ]]; then
    if "$PY" scripts/process_staged.py "$src" >> "$log" 2>&1; then
      inserted="$(sed -n 's/^\[process\] Inserted \([0-9]*\) entries (\([0-9-]*\)).*/\1/p' "$log" | tail -1)"
      range="$(sed -n 's/^\[process\] Inserted \([0-9]*\) entries (\([0-9-]*\)).*/\2/p' "$log" | tail -1)"
      pending="$(sed -n 's/^\[process\] Backlog: \([0-9]*\) pending rows.*/\1/p' "$log" | tail -1)"
      held="$(sed -n 's/^\[process\] Type filter: \([0-9]*\) rows (\([0-9-]*\)).*/\1/p' "$log" | tail -1)"
      held_range="$(sed -n 's/^\[process\] Type filter: \([0-9]*\) rows (\([0-9-]*\)).*/\2/p' "$log" | tail -1)"
      inserted="${inserted:-0}"; range="${range:--}"; pending="${pending:-0}"; held="${held:-0}"
      if [[ "$range" == "-" && -n "$held_range" ]]; then range="$held_range"; fi
      TOTAL_INSERTED=$(( TOTAL_INSERTED + inserted ))
      TOTAL_PENDING=$(( TOTAL_PENDING + pending ))
      TOTAL_FILTERED=$(( TOTAL_FILTERED + held ))
      echo "  [process] inserted $inserted ($range), pending backlog rows $pending, config-filtered rows recorded $held"
      # Reconciliation, DB side: every sorted item must become a row or be a
      # logged duplicate skip.
      dupes="$(sed -n 's/^\[process\] Skipped \([0-9]*\) duplicate URLs.*/\1/p' "$log" | tail -1)"
      dupes="${dupes:-0}"
      if [[ $(( inserted + pending + held + dupes )) -ne $(( ready + backlog + filtered )) ]]; then
        RECON_WARNINGS+=("$src: $(( ready + backlog + filtered )) items staged but $(( inserted + pending + held + dupes )) recorded (inserted $inserted + pending $pending + filtered $held + duplicate skips $dupes)")
      fi
    else
      status="process_staged failed"
      PIPELINE_FAILED=1
      echo "  [process] FAILED — see $log"
    fi
  fi

  RESULTS+=("$src|$status|$scraped|$new|$ready|$backlog|$inserted|$pending|$held|$range")
  sleep "$SOURCE_GAP"
done

END_MAX="$(db_max_num)"

# ── Verify only the rows added in this run ──
VERIFY_LINE="skipped"
if [[ $DRY_RUN -eq 0 && $SKIP_VERIFY -eq 0 && $TOTAL_INSERTED -gt 0 ]]; then
  echo
  echo "===== verify_urls (num > $START_MAX) ====="
  if "$PY" scripts/verify_urls.py --min-num "$START_MAX" > "$LOG_DIR/verify.log" 2>&1; then
    VERIFY_LINE="$(sed -n 's/^\[verify\] Results: //p' "$LOG_DIR/verify.log" | tail -1)"
    echo "  $VERIFY_LINE"
  else
    VERIFY_LINE="FAILED (see logs/verify.log)"
    PIPELINE_FAILED=1
    echo "  FAILED — see $LOG_DIR/verify.log"
  fi
elif [[ $DRY_RUN -eq 0 && $TOTAL_INSERTED -eq 0 ]]; then
  VERIFY_LINE="nothing new to verify"
fi

# ── Rebuild published outputs ──
BUILD_LINE="skipped (dry run)"
if [[ $DRY_RUN -eq 0 ]]; then
  echo
  echo "===== build_from_db ====="
  if "$PY" scripts/build_from_db.py > "$LOG_DIR/build.log" 2>&1; then
    BUILD_LINE="$(grep -E "published|entries" "$LOG_DIR/build.log" | tail -1 | sed 's/^ *//')"
    echo "  ${BUILD_LINE:-ok}"
  else
    BUILD_LINE="FAILED (see logs/build.log)"
    PIPELINE_FAILED=1
    echo "  FAILED — see $LOG_DIR/build.log"
  fi
fi

# ── Held-out / flagged rows among the new ones ──
HELD_OUT=""
if [[ $DRY_RUN -eq 0 && $TOTAL_INSERTED -gt 0 ]]; then
  HELD_OUT="$("$PY" - "$START_MAX" <<'EOF'
import sqlite3, sys
start = int(sys.argv[1])
conn = sqlite3.connect("data/hub.db")
rows = conn.execute("""SELECT num, url_status, url_http_status, source, title FROM entries
                       WHERE num > ? AND url_status IN ('broken', 'flagged') ORDER BY num""", (start,)).fetchall()
for num, st, http, src, title in rows:
    print(f"| {num} | {st} | {http or '-'} | {src} | {title[:70]} |")
EOF
)"
fi

# ── Summary ──
{
  echo "## Weekly update — $TODAY"
  echo
  if [[ $DRY_RUN -eq 1 ]]; then echo "_Dry run: scrape only, nothing written to hub.db._"; echo; fi
  echo "**New entries:** $TOTAL_INSERTED"
  echo "**Backlog rows recorded as pending (excluded, not published):** $TOTAL_PENDING"
  echo "**Rows set aside by a config rule (excluded, not published):** $TOTAL_FILTERED"
  if [[ $END_MAX -gt $START_MAX ]]; then echo "**Rows added:** num $((START_MAX + 1))–$END_MAX"; fi
  echo "**URL verification (new rows only):** $VERIFY_LINE"
  echo "**Build:** $BUILD_LINE"
  echo
  echo "| Source | Status | Fetched | Not in DB | Ready | Backlog | Inserted | Pending | Filtered | Nums |"
  echo "|---|---|---|---|---|---|---|---|---|---|"
  for r in "${RESULTS[@]}"; do
    IFS='|' read -r s st sc nw rd bl ins pd fl rg <<< "$r"
    echo "| $s | $st | $sc | $nw | $rd | $bl | $ins | $pd | $fl | $rg |"
  done
  if [[ ${#FAILED_SOURCES[@]} -gt 0 ]]; then
    echo
    echo "**Sources needing attention:** ${FAILED_SOURCES[*]}"
  fi
  if [[ ${#CLOUD_SKIPPED[@]} -gt 0 ]]; then
    echo
    echo "**Skipped on this cloud runner (run from a laptop: \`bash scripts/update.sh --sources \"${CLOUD_SKIPPED[*]}\"\`):** ${CLOUD_SKIPPED[*]}"
  fi
  if [[ ${#RECON_WARNINGS[@]} -gt 0 ]]; then
    echo
    echo "**Counts that do not add up (items may have been dropped without a record — see the source's log):**"
    echo
    for w in "${RECON_WARNINGS[@]}"; do echo "- $w"; done
  fi
  if [[ -n "$HELD_OUT" ]]; then
    echo
    echo "**New rows held out of published outputs (broken) or flagged:**"
    echo
    echo "| Num | Status | HTTP | Source | Title |"
    echo "|---|---|---|---|---|"
    echo "$HELD_OUT"
  fi
  echo
  echo "Per-source logs: \`$LOG_DIR/\` (not committed)."
} > "$SUMMARY"

echo
echo "[update] Summary written to $SUMMARY"
cat "$SUMMARY"

exit $PIPELINE_FAILED
