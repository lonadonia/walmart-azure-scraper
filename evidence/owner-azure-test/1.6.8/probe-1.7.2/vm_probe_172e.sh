#!/usr/bin/env bash
# Owner VM: the delivered Classic probe package 1.7.2 (OXYLABS_CLASSIC_OFFLINE_PROBE_1.7.2.zip, rebuilt 2026-11-06 with
# the workstation user name replaced in one offline-results log; the probe tree unchanged) run on Linux from a
# clean extraction, with the commands of its README_FIRST.md and of its own offline_results (made on Windows). No
# request: after the install, HTTP(S) goes to a closed local port; the tests close the network themselves; the live
# command must be refused (exit 3). Each command's output goes to out/NN_*.txt and a line to out/commands.csv.
set -u
BASE="$HOME/q168e/probe172"
ZIP="$HOME/q168e/OXYLABS_CLASSIC_OFFLINE_PROBE_1.7.2.zip"
WANT=fe25579154b9cac70628fa8b7e3a61a85858b01f6900ff0aded04b3d6da76e1e
[ ! -e "$BASE" ] || { echo "exists: $BASE"; exit 2; }
mkdir -p "$BASE/out"
OUT="$BASE/out"
got=$(sha256sum "$ZIP" | cut -d' ' -f1)
echo "zip sha256 $got (expected $WANT)" > "$OUT/HOST.txt"
[ "$got" = "$WANT" ] || { echo "zip sha mismatch"; exit 2; }
echo "host: $(. /etc/os-release; echo "$PRETTY_NAME"), kernel $(uname -r), $(uname -m); uv $(uv --version | cut -d' ' -f2); started $(date -u +%FT%TZ)" >> "$OUT/HOST.txt"
python3 -m zipfile -e "$ZIP" "$BASE/x" || exit 2
P="$BASE/x/oxylabs-classic-offline-probe-1.7.2"
( cd "$P" && sha256sum -c --quiet FILE_SHA256.txt ) > "$OUT/file_sha256_check.txt" 2>&1
echo "sha256sum -c exit $? over $(wc -l < "$P/FILE_SHA256.txt") files" >> "$OUT/file_sha256_check.txt"
echo "output_file,command,exit_code,expected_exit_code,started_at,ended_at" > "$OUT/commands.csv"
cd "$P/oxylabs-classic-probe" || exit 2

step() {  # step OUTPUT_FILE EXPECTED -- command...
  local f=$1 expect=$2 at rc; shift 3
  at=$(date -u +%FT%TZ)
  "$@" > "$OUT/$f" 2>&1; rc=$?
  echo "$f,\"$*\",$rc,$expect,$at,$(date -u +%FT%TZ)" >> "$OUT/commands.csv"
  echo "$f exit $rc (expected $expect)"
}

step 00_uv_sync_frozen.txt 0 -- uv sync --frozen
export HTTP_PROXY=http://127.0.0.1:9 HTTPS_PROXY=http://127.0.0.1:9 http_proxy=http://127.0.0.1:9 https_proxy=http://127.0.0.1:9
export ALL_PROXY=http://127.0.0.1:9 NO_PROXY=localhost,127.0.0.1 no_proxy=localhost,127.0.0.1 UV_OFFLINE=1
unset OXYLABS_USERNAME OXYLABS_PASSWORD OXYLABS_API_KEY OXYLABS_WEB_API_KEY 2>/dev/null
PY=.venv/bin/python
step 01_pytest_standalone.txt 0 -- $PY -m pytest -q -p no:cacheprovider -rs "--junitxml=$OUT/junit_standalone_linux.xml"
step 02_ruff_check.txt 0 -- $PY -m ruff check src tests
step 03_ruff_format_check.txt 0 -- $PY -m ruff format --check src tests
step 04_mypy.txt 0 -- $PY -m mypy
step 05_version.txt 0 -- $PY -m classic_probe --version
step 06_help.txt 0 -- $PY -m classic_probe --help
step 07_plan.txt 0 -- $PY -m classic_probe plan --targets config/targets.json
step 08_plan_with_placeholder_rates.txt 0 -- $PY -m classic_probe plan --targets config/targets.json --rates config/rates.example.json
step 09_validate.txt 0 -- $PY -m classic_probe validate --targets config/targets.json --rates config/rates.example.json
# Steps 10 and 11b of the package's own offline_results wrote the replay inputs with helpers of the tool that made
# those results; the helpers are not in the package, the inputs are (offline_results/*_inputs*). The second candidate's
# run of this script called the helpers, so its steps 10 to 11c exited 2 on "can't open file" and proved nothing about
# the probe. These replays read the packaged inputs.
step 11_replay_synthetic_responses.txt 0 -- $PY -m classic_probe replay --retailer walmart --targets config/targets.json --fixtures ../offline_results/synthetic_inputs_of_the_replay/fixtures --rates ../offline_results/synthetic_inputs_of_the_replay/synthetic_rates.json --out offline_out/replay
step 11c_replay_marianos_saved_pages.txt 0 -- $PY -m classic_probe replay --retailer marianos --targets config/targets.json --fixtures ../offline_results/inputs_of_the_marianos_replay/fixtures --rates ../offline_results/inputs_of_the_marianos_replay/synthetic_rates.json --out offline_out/replay_marianos
step 12_campaign_init_offline.txt 0 -- $PY -m classic_probe campaign-init --manifest offline_out/manifest.json --ledger offline_out/ledger.sqlite3 --campaign-id offline-check --offline
step 13_status.txt 0 -- $PY -m classic_probe status --manifest offline_out/manifest.json
step 14_export.txt 0 -- $PY -m classic_probe export --manifest offline_out/manifest.json --out offline_out/export
step 15_live_is_refused.txt 3 -- $PY -m classic_probe live --manifest offline_out/manifest.json
step 17_review_tests_on_1.7.2.txt 0 -- $PY -m pytest -p no:cacheprovider -rA --tb=short tests/test_review_of_171.py
echo "ended $(date -u +%FT%TZ)" >> "$OUT/HOST.txt"
python3 - "$OUT" <<'PY'
import csv, sys, xml.etree.ElementTree as ET
from pathlib import Path
out = Path(sys.argv[1])
rows = list(csv.DictReader((out / "commands.csv").open(encoding="utf-8")))
bad = [r["output_file"] for r in rows if r["exit_code"] != r["expected_exit_code"]]
s = ET.parse(out / "junit_standalone_linux.xml").getroot()
s = s if s.tag == "testsuite" else s.find("testsuite")
print("junit:", {k: s.get(k) for k in ("tests", "failures", "errors", "skipped")})
live = (out / "15_live_is_refused.txt").read_text(encoding="utf-8", errors="strict")
print("live refused output (last line):", live.strip().splitlines()[-1][:200] if live.strip() else "(empty)")
print(f"{len(rows)} commands, {len(bad)} not as expected: {bad}")
PY
grep -E "skipped|SKIPPED" "$OUT/01_pytest_standalone.txt" | head -10
tail -2 "$OUT/17_review_tests_on_1.7.2.txt"
