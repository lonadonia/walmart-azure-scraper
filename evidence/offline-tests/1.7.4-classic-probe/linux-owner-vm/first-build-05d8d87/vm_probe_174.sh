#!/usr/bin/env bash
# Owner VM: the Classic probe package 1.7.4 (OXYLABS_CLASSIC_OFFLINE_PROBE_1.7.4.zip) run on Linux from a clean
# extraction, with the commands of its README_FIRST.md and of its own offline_results (made on Windows), the run that
# evidence/offline-tests/1.7.4-classic-probe/README.md names as missing; then the reproduction on the reviewed 1.7.2
# (its delivered package, with the 1.7.4 review tests added), as REPRODUCE.md does on Windows. No request: after the
# installs, HTTP(S) goes to a closed local port; the tests close the network themselves; the live command must be
# refused (exit 3). Each command's output goes to out/NN_*.txt and a line to out/commands.csv. A step expected to
# fail passes only if its output says so (output_must_say).
set -u
BASE="$HOME/q174/run"
ZIP="$HOME/q174/OXYLABS_CLASSIC_OFFLINE_PROBE_1.7.4.zip"
WANT=d689e62091a68acc4f716e9a0bd1fe3cc81073a5136f2934fe4232a4a267df98
ZIP172="$HOME/q174/OXYLABS_CLASSIC_OFFLINE_PROBE_1.7.2.zip"
WANT172=fe25579154b9cac70628fa8b7e3a61a85858b01f6900ff0aded04b3d6da76e1e
[ ! -e "$BASE" ] || { echo "exists: $BASE"; exit 2; }
mkdir -p "$BASE/out"
OUT="$BASE/out"
got=$(sha256sum "$ZIP" | cut -d' ' -f1)
got172=$(sha256sum "$ZIP172" | cut -d' ' -f1)
echo "1.7.4 zip sha256 $got (expected $WANT)" > "$OUT/HOST.txt"
echo "1.7.2 zip sha256 $got172 (expected $WANT172)" >> "$OUT/HOST.txt"
[ "$got" = "$WANT" ] && [ "$got172" = "$WANT172" ] || { echo "zip sha mismatch"; exit 2; }
echo "host: $(. /etc/os-release; echo "$PRETTY_NAME"), kernel $(uname -r), $(uname -m); python3 $(python3 -c 'import platform; print(platform.python_version())'); uv $(uv --version | cut -d' ' -f2); started $(date -u +%FT%TZ)" >> "$OUT/HOST.txt"
python3 -m zipfile -e "$ZIP" "$BASE/x" || exit 2
python3 -m zipfile -e "$ZIP172" "$BASE/x172" || exit 2
P="$BASE/x/oxylabs-classic-offline-probe-1.7.4"
P172="$BASE/x172/oxylabs-classic-offline-probe-1.7.2"
( cd "$P" && sha256sum -c --quiet FILE_SHA256.txt ) > "$OUT/file_sha256_check.txt" 2>&1
echo "1.7.4: sha256sum -c exit $? over $(wc -l < "$P/FILE_SHA256.txt") files" >> "$OUT/file_sha256_check.txt"
( cd "$P172" && sha256sum -c --quiet FILE_SHA256.txt ) >> "$OUT/file_sha256_check.txt" 2>&1
echo "1.7.2: sha256sum -c exit $? over $(wc -l < "$P172/FILE_SHA256.txt") files" >> "$OUT/file_sha256_check.txt"
echo "output_file,command,exit_code,expected_exit_code,output_must_say,said,started_at,ended_at" > "$OUT/commands.csv"

step() {  # step OUTPUT_FILE EXPECTED MUST_SAY -- command...
  local f=$1 expect=$2 must=$3 at rc said; shift 4
  at=$(date -u +%FT%TZ)
  "$@" > "$OUT/$f" 2>&1; rc=$?
  said=yes
  if [ -n "$must" ] && ! grep -qF -- "$must" "$OUT/$f"; then said=no; fi
  echo "$f,\"$*\",$rc,$expect,\"$must\",$said,$at,$(date -u +%FT%TZ)" >> "$OUT/commands.csv"
  echo "$f exit $rc (expected $expect)${must:+; must say \"$must\": $said}"
}

# installs first (the only steps that may reach the package index); the 1.7.2 copy gets the 1.7.4 review test file
cd "$P/oxylabs-classic-probe" || exit 2
step 00_uv_sync_frozen.txt 0 "" -- uv sync --frozen
cp "$P/oxylabs-classic-probe/tests/test_review_of_172.py" "$P172/oxylabs-classic-probe/tests/" || exit 2
sha256sum "$P/oxylabs-classic-probe/tests/test_review_of_172.py" "$P172/oxylabs-classic-probe/tests/test_review_of_172.py" > "$OUT/16_test_file_copied.txt"
( cd "$P172/oxylabs-classic-probe" && step 16a_uv_sync_frozen_1.7.2.txt 0 "" -- uv sync --frozen )

export HTTP_PROXY=http://127.0.0.1:9 HTTPS_PROXY=http://127.0.0.1:9 http_proxy=http://127.0.0.1:9 https_proxy=http://127.0.0.1:9
export ALL_PROXY=http://127.0.0.1:9 NO_PROXY=localhost,127.0.0.1 no_proxy=localhost,127.0.0.1 UV_OFFLINE=1
unset OXYLABS_USERNAME OXYLABS_PASSWORD OXYLABS_API_KEY OXYLABS_WEB_API_KEY 2>/dev/null
PY=.venv/bin/python
step 01_pytest_standalone.txt 0 "" -- $PY -m pytest -q -p no:cacheprovider -rs "--junitxml=$OUT/junit_standalone_linux.xml"
step 02_ruff_check.txt 0 "" -- $PY -m ruff check src tests
step 03_ruff_format_check.txt 0 "" -- $PY -m ruff format --check src tests
step 04_mypy.txt 0 "" -- $PY -m mypy
step 05_version.txt 0 "1.7.4" -- $PY -m classic_probe --version
step 06_help.txt 0 "" -- $PY -m classic_probe --help
step 07_plan.txt 0 "" -- $PY -m classic_probe plan --targets config/targets.json
step 08_plan_with_placeholder_rates.txt 0 "" -- $PY -m classic_probe plan --targets config/targets.json --rates config/rates.example.json
step 09_validate.txt 0 "" -- $PY -m classic_probe validate --targets config/targets.json --rates config/rates.example.json
step 11_replay_synthetic_responses.txt 0 "" -- $PY -m classic_probe replay --retailer walmart --targets config/targets.json --fixtures ../offline_results/synthetic_inputs_of_the_replay/fixtures --rates ../offline_results/synthetic_inputs_of_the_replay/synthetic_rates.json --out offline_out/replay
step 11c_replay_marianos_saved_pages.txt 0 "" -- $PY -m classic_probe replay --retailer marianos --targets config/targets.json --fixtures ../offline_results/inputs_of_the_marianos_replay/fixtures --rates ../offline_results/inputs_of_the_marianos_replay/synthetic_rates.json --out offline_out/replay_marianos
step 12_campaign_init_offline.txt 0 "" -- $PY -m classic_probe campaign-init --manifest offline_out/manifest.json --ledger offline_out/ledger.sqlite3 --campaign-id offline-check --offline
step 13_status.txt 0 "" -- $PY -m classic_probe status --manifest offline_out/manifest.json
step 14_export.txt 0 "" -- $PY -m classic_probe export --manifest offline_out/manifest.json --out offline_out/export
step 15_live_is_refused.txt 3 "" -- $PY -m classic_probe live --manifest offline_out/manifest.json
# the reviewed 1.7.2 with the 1.7.4 review tests: on Linux 3 of the 7 run (4 are Windows-only); the 2 test_w_ ones
# are expected to fail by their output, the control to pass
( cd "$P172/oxylabs-classic-probe" && step 16b_review_tests_on_1.7.2.txt 1 "2 failed, 1 passed, 4 skipped" -- $PY -m pytest -p no:cacheprovider -rA --tb=short tests/test_review_of_172.py )
step 17_review_tests_on_1.7.4.txt 0 "3 passed, 4 skipped" -- $PY -m pytest -p no:cacheprovider -rA --tb=short tests/test_review_of_172.py
# an independent check that no test process was left running
sleep 2
ps -eo pid,etimes,args | grep -E "[c]hild\.py|[s]ession\.py|[d]escendant" > "$OUT/18_leftover_processes.txt"
echo "leftover test processes: $(grep -c . "$OUT/18_leftover_processes.txt")" >> "$OUT/18_leftover_processes.txt"
echo "ended $(date -u +%FT%TZ)" >> "$OUT/HOST.txt"
python3 - "$OUT" <<'PY'
import csv, sys, xml.etree.ElementTree as ET
from pathlib import Path
out = Path(sys.argv[1])
rows = list(csv.DictReader((out / "commands.csv").open(encoding="utf-8")))
bad = [r["output_file"] for r in rows if r["exit_code"] != r["expected_exit_code"] or r["said"] != "yes"]
s = ET.parse(out / "junit_standalone_linux.xml").getroot()
s = s if s.tag == "testsuite" else s.find("testsuite")
print("junit:", {k: s.get(k) for k in ("tests", "failures", "errors", "skipped")})
live = (out / "15_live_is_refused.txt").read_text(encoding="utf-8", errors="strict")
print("live refused output (last line):", live.strip().splitlines()[-1][:200] if live.strip() else "(empty)")
print(f"{len(rows)} commands, {len(bad)} not as expected: {bad}")
print((out / "18_leftover_processes.txt").read_text(encoding="utf-8").strip().splitlines()[-1])
PY
grep -E "SKIPPED" "$OUT/01_pytest_standalone.txt" | head -12
tail -n 1 "$OUT/01_pytest_standalone.txt"
tail -n 1 "$OUT/16b_review_tests_on_1.7.2.txt"
tail -n 1 "$OUT/17_review_tests_on_1.7.4.txt"
echo "VM RUN DONE"
