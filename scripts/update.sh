#!/usr/bin/env bash
# Weekly corpus update: scrape every automated source, insert new entries into
# hub.db, verify only the new URLs, rebuild the published files, and write a
# run summary for the PR body.
#
# Usage (from repo root; Git Bash on Windows, bash on Linux/CI):
#   scripts/update.sh                       # full run over WEEKLY_SOURCES
#   scripts/update.sh --dry-run             # scrape only: no DB writes, no build
#   scripts/update.sh --sources "wwc lpi"   # limit to given source slugs
#   scripts/update.sh --skip-verify         # skip verify_urls.py (faster local runs)
#
# Env: PYTHON (default: python), RUN_SUMMARY (default: docs/staging/run-summary.md),
#      SOURCE_GAP (seconds to pause between sources, default 5).
#
# Not in the weekly list on purpose (see meta/operator-guide.md and sources/*.md):
#   casel (60s crawl-delay + detail fetch, run manually), jedm/jla (frozen
#   selective set), ies-rel (no config), aims/rand/mdrc/nap (blocked or manual).
#
# The script never aborts on a single failing source: each source's outcome is
# recorded in the summary and the run continues. Exit code is non-zero only if
# a pipeline step (process/verify/build) fails.

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

PY="${PYTHON:-python}"
WEEKLY_SOURCES=(
  brookings
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
)

DRY_RUN=0
SKIP_VERIFY=0
SOURCE_GAP="${SOURCE_GAP:-5}"  # back-to-back configs can share a host (the three LPI ones)
SOURCES=("${WEEKLY_SOURCES[@]}")
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=1 ;;
    --skip-verify) SKIP_VERIFY=1 ;;
    --sources) shift; read -r -a SOURCES <<< "$1" ;;
    -h|--help) sed -n '2,20p' "$0"; exit 0 ;;
    *) echo "Unknown option: $1" >&2; exit 2 ;;
  esac
  shift
done

STAGING="docs/staging"
LOG_DIR="$STAGING/logs"
SUMMARY="${RUN_SUMMARY:-$STAGING/run-summary.md}"
mkdir -p "$LOG_DIR"
TODAY="$(date +%Y-%m-%d)"

db_max_num() {
  "$PY" -c "import sqlite3; print(sqlite3.connect('data/hub.db').execute('SELECT COALESCE(MAX(num),0) FROM entries').fetchone()[0])"
}

START_MAX="$(db_max_num)"
echo "[update] $TODAY | ${#SOURCES[@]} sources | dry-run=$DRY_RUN | max(num) before run: $START_MAX"

# Per-source results: slug|status|scraped|new|ready|backlog|inserted|pending|range
RESULTS=()
FAILED_SOURCES=()
PIPELINE_FAILED=0
TOTAL_INSERTED=0
TOTAL_PENDING=0

for src in "${SOURCES[@]}"; do
  echo
  echo "===== $src ====="
  log="$LOG_DIR/$src.log"
  status="ok"
  scraped=0; new=0; ready=0; backlog=0; inserted=0; pending=0; range="-"

  # Remove any stale staging file so a failed scrape can't feed last run's items
  # to process_staged. --fresh: ignore a leftover progress file from an
  # interrupted detail_fetch.
  rm -f "$STAGING/$src.json"
  if "$PY" scripts/scrape.py "$src" --fresh > "$log" 2>&1; then
    scraped="$(sed -n 's/^\[scrape\] Total items extracted: \([0-9]*\).*/\1/p' "$log" | tail -1)"
    new="$(sed -n 's/^\[scrape\] Already indexed: [0-9]*, New: \([0-9]*\).*/\1/p' "$log" | tail -1)"
    ready="$(sed -n 's/^\[scrape\] Ready: \([0-9]*\), Backlog: \([0-9]*\).*/\1/p' "$log" | tail -1)"
    backlog="$(sed -n 's/^\[scrape\] Ready: \([0-9]*\), Backlog: \([0-9]*\).*/\2/p' "$log" | tail -1)"
    if grep -q "consecutive failures" "$log"; then
      status="partial (fetch failures)"
    elif [[ "${scraped:-0}" == "0" ]]; then
      status="empty (0 items extracted — selector drift or block?)"
    fi
  else
    status="scrape failed (exit $?)"
  fi
  scraped="${scraped:-0}"; new="${new:-0}"; ready="${ready:-0}"; backlog="${backlog:-0}"
  grep -E "^\[scrape\]|Early stop|HTTP [0-9]{3}|consecutive failures|Error" "$log" | sed 's/^/  /'

  if [[ "$status" != "ok" && "$status" != partial* ]]; then
    FAILED_SOURCES+=("$src")
  fi

  if [[ $DRY_RUN -eq 0 && ( "$ready" != "0" || "$backlog" != "0" ) && -f "$STAGING/$src.json" ]]; then
    if "$PY" scripts/process_staged.py "$src" >> "$log" 2>&1; then
      inserted="$(sed -n 's/^\[process\] Inserted \([0-9]*\) entries (\([0-9-]*\)).*/\1/p' "$log" | tail -1)"
      range="$(sed -n 's/^\[process\] Inserted \([0-9]*\) entries (\([0-9-]*\)).*/\2/p' "$log" | tail -1)"
      pending="$(sed -n 's/^\[process\] Backlog: \([0-9]*\) pending rows.*/\1/p' "$log" | tail -1)"
      inserted="${inserted:-0}"; range="${range:--}"; pending="${pending:-0}"
      TOTAL_INSERTED=$(( TOTAL_INSERTED + inserted ))
      TOTAL_PENDING=$(( TOTAL_PENDING + pending ))
      echo "  [process] inserted $inserted ($range), pending backlog rows $pending"
    else
      status="process_staged failed"
      PIPELINE_FAILED=1
      echo "  [process] FAILED — see $log"
    fi
  fi

  RESULTS+=("$src|$status|$scraped|$new|$ready|$backlog|$inserted|$pending|$range")
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
  if [[ $END_MAX -gt $START_MAX ]]; then echo "**Rows added:** num $((START_MAX + 1))–$END_MAX"; fi
  echo "**URL verification (new rows only):** $VERIFY_LINE"
  echo "**Build:** $BUILD_LINE"
  echo
  echo "| Source | Status | Fetched | Not in DB | Ready | Backlog | Inserted | Pending | Nums |"
  echo "|---|---|---|---|---|---|---|---|---|"
  for r in "${RESULTS[@]}"; do
    IFS='|' read -r s st sc nw rd bl ins pd rg <<< "$r"
    echo "| $s | $st | $sc | $nw | $rd | $bl | $ins | $pd | $rg |"
  done
  if [[ ${#FAILED_SOURCES[@]} -gt 0 ]]; then
    echo
    echo "**Sources needing attention:** ${FAILED_SOURCES[*]}"
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
