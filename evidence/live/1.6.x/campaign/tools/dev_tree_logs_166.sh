#!/usr/bin/env bash
# The development-tree records of collector 1.6.6 for evidence/offline-tests/1.6.6-collector/: static checks, the unit
# suite, and the three publication tests of test_operations.py (the two new ones and the unchanged one), on the
# committed tree (it must be clean). Offline: HTTP(S) to a closed local port, no provider key.
# usage: dev_tree_logs_166.sh OUTDIR
set -uo pipefail
OUT=$1
mkdir -p "$OUT"
cd /c/w9/wt/headless/walmart-azure-headless
export UV_PYTHON='C:/w6/py312/pkg/tools/python.exe' PYTHONUTF8=1
export HTTP_PROXY=http://127.0.0.1:9 HTTPS_PROXY=http://127.0.0.1:9 http_proxy=http://127.0.0.1:9 https_proxy=http://127.0.0.1:9 NO_PROXY=localhost,127.0.0.1 no_proxy=localhost,127.0.0.1
unset OXYLABS_API OXYLABS_WEB_API_KEY_FILE SCRAPEDO_TOKEN WALMART_COLLECTOR_DATABASE_URL WALMART_COLLECTOR_CONFIG 2>/dev/null
head() {
  local changed
  changed=$(git -C /c/w9/wt status --porcelain -- headless/walmart-azure-headless | wc -l)
  echo "release 1.6.6, commit $(git -C /c/w9/wt rev-parse HEAD), $(date -u +%Y-%m-%dT%H:%M:%SZ), development tree (clean: $changed changed files)"
}
run() { echo "\$ $*"; "$@"; echo "exit=$?"; }
{ head; run uv run --frozen python -m ruff check src tests deploy; run uv run --frozen python -m ruff format --check src tests deploy; run uv run --frozen python -m mypy; } > "$OUT/STATIC_1.6.6.log" 2>&1
{ head; run uv run --frozen python -m pytest -q -p no:cacheprovider tests/unit; } > "$OUT/UNIT_1.6.6.log" 2>&1
{ head; run uv run --frozen python -m pytest -p no:cacheprovider -rA --tb=short tests/integration/test_operations.py -k "refused or a_complete_run_is_published_and_a_partial_run_never_replaces_it"; } > "$OUT/TESTS_ON_1.6.6.log" 2>&1
tail -n 2 "$OUT/STATIC_1.6.6.log" "$OUT/UNIT_1.6.6.log" "$OUT/TESTS_ON_1.6.6.log"
