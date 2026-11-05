#!/usr/bin/env bash
# The last-good publication check (W6) on release 1.6.6, as on 1.6.1, 1.6.4 and 1.6.5: a clean extraction of the
# Oxylabs edition ZIP, its own frozen publication tests, and the corrupt-evidence test of 1.6.4/1.6.5 (the same file,
# sha256 5da68a03...) copied beside them. Offline: HTTP(S) to a closed local port, no provider key.
# usage: lastgood166.sh WORK_DIR EVIDENCE_DIR LOG JUNIT
set -uo pipefail
WORK=$1 EVID=$2 LOG=$3 JUNIT=$4
ZIP=/c/w9/delivery166/source/editions/WALMART_OXYLABS_SOURCE_1.6.6.zip
WANT=0859a2f693527bab073252edf941928bb4f118ea4a63d581078d96ddd2324e22
TEST=/c/w9/live/tools/lastgood164/test_last_good_corrupt_evidence.py
TEST_SHA=5da68a0345de86288d976d6b72243478929aa3f638d014b452ab4012a83b9675
[ ! -e "$WORK" ] || { echo "exists: $WORK"; exit 2; }
[ ! -e "$EVID" ] || { echo "exists: $EVID"; exit 2; }
[ "$(sha256sum "$ZIP" | cut -d' ' -f1)" = "$WANT" ] || { echo "zip sha mismatch"; exit 2; }
[ "$(sha256sum "$TEST" | cut -d' ' -f1)" = "$TEST_SHA" ] || { echo "test sha mismatch"; exit 2; }
mkdir -p "$WORK" && unzip -q "$ZIP" -d "$WORK" || exit 2
cd "$WORK/walmart-oxylabs-1.6.6" || exit 2
[ ! -e tests/integration/test_last_good_corrupt_evidence.py ] || { echo "the frozen tree already has the file"; exit 2; }
cp "$TEST" tests/integration/
export UV_PYTHON='C:/w6/py312/pkg/tools/python.exe' PYTHONUTF8=1
export UV_OFFLINE=1  # as the clean verifier: uv uses its cache only (attempt 1, without it, failed at uv sync: uv tried PyPI for hatchling and the closed proxy refused)
export HTTP_PROXY=http://127.0.0.1:9 HTTPS_PROXY=http://127.0.0.1:9 http_proxy=http://127.0.0.1:9 https_proxy=http://127.0.0.1:9 NO_PROXY=localhost,127.0.0.1 no_proxy=localhost,127.0.0.1
unset OXYLABS_API OXYLABS_WEB_API_KEY_FILE SCRAPEDO_TOKEN WALMART_COLLECTOR_DATABASE_URL WALMART_COLLECTOR_CONFIG 2>/dev/null
{
  echo "LAST GOOD PUBLICATION on release 1.6.6: clean extraction of WALMART_OXYLABS_SOURCE_1.6.6.zip (sha256 $WANT), $(tr -d '\r\n' < BUILD_INFO.json)"
  echo "start $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "\$ uv sync --frozen"
  uv sync --frozen 2>&1 | grep -E '^ \+ (tzdata|urllib3|walmart-azure-headless)==' ; echo "uv sync exit=${PIPESTATUS[0]}"
  echo "\$ PUBLICATION_EVIDENCE_DIR=<evidence folder> uv run --frozen python -m pytest -q -p no:cacheprovider tests/integration/test_publication_safety.py tests/integration/test_publish.py tests/integration/test_last_good_corrupt_evidence.py"
  PUBLICATION_EVIDENCE_DIR="$(cygpath -w "$EVID")" uv run --frozen python -m pytest -q -p no:cacheprovider \
    tests/integration/test_publication_safety.py tests/integration/test_publish.py \
    tests/integration/test_last_good_corrupt_evidence.py --junitxml="$(cygpath -w "$JUNIT")" 2>&1
  echo "exit=$?"
  echo "end $(date -u +%Y-%m-%dT%H:%M:%SZ)"
} > "$LOG"
tail -n 4 "$LOG"
