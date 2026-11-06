#!/usr/bin/env bash
# Owner Azure VM: qualification of the two release 1.6.8 editions exactly as the builder made them
# (scripts/build_walmart_168_delivery.py source 85c29e7), against the VM's PostgreSQL 16 with an isolated role
# and isolated databases (created here; no existing database or role is read or changed). No provider request:
# after the installs every step runs with HTTP(S) sent to a closed local port and no provider key.
# Each step: one JSON line in $QUAL/steps.jsonl and its own log in $QUAL/logs/.
# usage: vm_qual_168d.sh            (the ZIPs and their expected SHA-256 are below)
set -u
BASE="$HOME/q168d"
PGSECRET="$HOME/q167/pg.secret"  # the isolated role walmart_q167 this work created for 1.6.7
QUAL="$BASE/qual"
COMMIT=85c29e7b2404500299056973f50c84b84e187a5a
declare -A ZIP=( [oxylabs]="$BASE/WALMART_OXYLABS_SOURCE_1.6.8.zip" [scrapedo]="$BASE/WALMART_SCRAPEDO_SOURCE_1.6.8.zip" )
declare -A WANT=( [oxylabs]=eacf76e90320dbb1e1795913c4e0736d6297ca54645653764fae212eec6093ea
                  [scrapedo]=18642dd6fd1de8db6d43eea16bc11e11ffa780cc791a67dd75b4ce316d63db52 )
OLD_ZIP="$HOME/q167/WALMART_OXYLABS_SOURCE_1.6.6.zip"
OLD_WANT=0859a2f693527bab073252edf941928bb4f118ea4a63d581078d96ddd2324e22
[ ! -e "$QUAL" ] || { echo "exists: $QUAL"; exit 2; }
mkdir -p "$QUAL/logs"

step() {  # step NAME EXPECT CWD -- command...
  local name=$1 expect=$2 cwd=$3; shift 4
  local log="$QUAL/logs/$name.log" t0 t1 rc at
  at=$(date -u +%Y-%m-%dT%H:%M:%SZ); t0=$(date +%s.%N)
  ( cd "$cwd" && "$@" ) > "$log" 2>&1; rc=$?
  t1=$(date +%s.%N)
  python3 - "$name" "$rc" "$expect" "$at" "$t0" "$t1" "$log" "$*" >> "$QUAL/steps.jsonl" <<'PY'
import json, sys
name, rc, expect, at, t0, t1, log, cmd = sys.argv[1:]
print(json.dumps({"step": name, "exit": int(rc), "expected_exit": int(expect), "pass_by_exit": int(rc) == int(expect),
                  "started_at": at, "seconds": round(float(t1) - float(t0), 1), "log": "logs/" + log.rsplit("/", 1)[1],
                  "command": cmd}))
PY
  tail -n 1 "$QUAL/steps.jsonl"
  return 0
}

offline() {
  export HTTP_PROXY=http://127.0.0.1:9 HTTPS_PROXY=http://127.0.0.1:9 http_proxy=http://127.0.0.1:9 https_proxy=http://127.0.0.1:9
  export ALL_PROXY=http://127.0.0.1:9 NO_PROXY=localhost,127.0.0.1 no_proxy=localhost,127.0.0.1 UV_OFFLINE=1
  unset OXYLABS_API OXYLABS_API_KEY OXYLABS_WEB_API_KEY OXYLABS_WEB_API_KEY_FILE SCRAPEDO_API_KEY SCRAPEDO_API_KEY_FILE
  unset WALMART_COLLECTOR_CONFIG WALMART_COLLECTOR_STORAGE WALMART_COLLECTOR_DATABASE_AUTH 2>/dev/null
}

{
  echo "owner Azure VM qualification of release 1.6.8 (commit $COMMIT); host: $(. /etc/os-release; echo "$PRETTY_NAME"), kernel $(uname -r), $(uname -m), $(nproc) vCPU, $(free -m | awk '/Mem:/{print $2}') MB RAM"
  echo "started $(date -u +%Y-%m-%dT%H:%M:%SZ); uv $(uv --version | cut -d' ' -f2); PostgreSQL $(sudo -n -u postgres psql -Atc 'show server_version')"
} > "$QUAL/HOST.txt"

# -- an isolated PostgreSQL role and databases (the password stays in a mode-600 file of this folder) ------------
umask 077
[ -s "$PGSECRET" ] || { echo "no $PGSECRET"; exit 2; }
umask 022
PGPASSWORD=$(cat "$PGSECRET"); export PGPASSWORD
sudo -n -u postgres psql -v ON_ERROR_STOP=1 -q > "$QUAL/logs/pg_setup.log" 2>&1 <<SQL
DO \$\$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'walmart_q167') THEN
    CREATE ROLE walmart_q167 LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE PASSWORD '$PGPASSWORD';
  END IF;
END \$\$;
SQL
echo "pg role exit $?" >> "$QUAL/logs/pg_setup.log"
for db in walmart_q168d_oxylabs walmart_q168d_scrapedo walmart_q168d_oxylabs_test walmart_q168d_scrapedo_test; do
  if [ "$(sudo -n -u postgres psql -Atc "select count(*) from pg_database where datname = '$db'")" = 0 ]; then
    sudo -n -u postgres createdb -O walmart_q167 "$db" >> "$QUAL/logs/pg_setup.log" 2>&1
    echo "created $db exit $?" >> "$QUAL/logs/pg_setup.log"
  else
    echo "exists $db" >> "$QUAL/logs/pg_setup.log"
  fi
done
sudo -n -u postgres psql -Atc "select datname||' owner='||pg_get_userbyid(datdba) from pg_database where datname like 'walmart%' order by 1" >> "$QUAL/logs/pg_setup.log" 2>&1

for e in oxylabs scrapedo; do
  dir="$QUAL/$e"; mkdir -p "$dir"
  got=$(sha256sum "${ZIP[$e]}" | cut -d' ' -f1)
  echo "{\"step\": \"$e.zip\", \"sha256\": \"$got\", \"expected\": \"${WANT[$e]}\", \"pass\": $([ "$got" = "${WANT[$e]}" ] && echo true || echo false)}" >> "$QUAL/steps.jsonl"
  [ "$got" = "${WANT[$e]}" ] || { echo "zip sha mismatch $e"; exit 2; }
  python3 -m zipfile -e "${ZIP[$e]}" "$dir" || { echo "extract failed: $e"; exit 2; }
  tree="$dir/walmart-$e-1.6.8"
  [ -f "$tree/pyproject.toml" ] || { echo "not extracted: $tree"; exit 2; }
  step "$e.build_info" 0 "$tree" -- grep -q "\"commit\": \"$COMMIT\"" BUILD_INFO.json
  unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy ALL_PROXY UV_OFFLINE
  step "$e.install" 0 "$tree" -- uv sync --frozen
  offline
  export WALMART_COLLECTOR_DATA_DIR="$dir/data"
  step "$e.lock" 0 "$tree" -- uv lock --check --offline
  step "$e.ruff" 0 "$tree" -- uv run --frozen ruff check src tests
  step "$e.format" 0 "$tree" -- uv run --frozen ruff format --check src tests
  step "$e.mypy" 0 "$tree" -- uv run --frozen mypy
  step "$e.version" 0 "$tree" -- uv run --frozen walmart-collector --version
  step "$e.help" 0 "$tree" -- uv run --frozen walmart-collector --help
  step "$e.validate-config" 0 "$tree" -- uv run --frozen walmart-collector validate-config
  export WALMART_COLLECTOR_DATABASE_URL="postgresql://walmart_q167@127.0.0.1:5432/walmart_q168d_$e"
  # A new database: the schema check must fail (exit 2, revision null) before db-upgrade; then pass.
  step "$e.check-db-before" 2 "$tree" -- uv run --frozen walmart-collector validate-config --check-db
  step "$e.db-upgrade" 0 "$tree" -- uv run --frozen walmart-collector db-upgrade
  step "$e.check-db-after" 0 "$tree" -- uv run --frozen walmart-collector validate-config --check-db
  step "$e.db-upgrade-again" 0 "$tree" -- uv run --frozen walmart-collector db-upgrade
  step "$e.status" 0 "$tree" -- uv run --frozen walmart-collector status
  unset WALMART_COLLECTOR_DATABASE_URL
  step "$e.unit" 0 "$tree" -- uv run --frozen python -m pytest -p no:cacheprovider -q -rfEs tests/unit
  export WALMART_COLLECTOR_TEST_DATABASE_URL="postgresql://walmart_q167@127.0.0.1:5432/walmart_q168d_${e}_test"
  step "$e.integration" 0 "$tree" -- uv run --frozen python -m pytest -p no:cacheprovider -q -rfEs tests/integration
  # The owner's operator drill (not part of the release): copied beside the edition's tests, run, removed.
  cp "$BASE/test_operator_drill_owner.py" "$tree/tests/integration/"
  echo "{\"step\": \"$e.drill_file\", \"sha256\": \"$(sha256sum "$BASE/test_operator_drill_owner.py" | cut -d' ' -f1)\", \"pass\": true, \"info\": \"the drill file run\"}" >> "$QUAL/steps.jsonl"
  export DRILL_TRANSCRIPT="$QUAL/logs/$e.drill.jsonl"
  step "$e.drill" 0 "$tree" -- uv run --frozen python -m pytest -p no:cacheprovider -q -rfEs tests/integration/test_operator_drill_owner.py
  rm -f "$tree/tests/integration/test_operator_drill_owner.py"
  unset DRILL_TRANSCRIPT WALMART_COLLECTOR_TEST_DATABASE_URL
done

# -- a rollback of the code: the 1.6.6 edition against the database 1.6.8 migrated (one schema head, 0006) -------
dir="$QUAL/rollback166"; mkdir -p "$dir"
got=$(sha256sum "$OLD_ZIP" | cut -d' ' -f1)
echo "{\"step\": \"rollback166.zip\", \"sha256\": \"$got\", \"expected\": \"$OLD_WANT\", \"pass\": $([ "$got" = "$OLD_WANT" ] && echo true || echo false)}" >> "$QUAL/steps.jsonl"
if [ "$got" = "$OLD_WANT" ]; then
  python3 -m zipfile -e "$OLD_ZIP" "$dir" || { echo "extract failed: 1.6.6"; exit 2; }
  tree="$dir/walmart-oxylabs-1.6.6"
  [ -f "$tree/pyproject.toml" ] || { echo "not extracted: $tree"; exit 2; }
  unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy ALL_PROXY UV_OFFLINE
  step "rollback166.install" 0 "$tree" -- uv sync --frozen
  offline
  export WALMART_COLLECTOR_DATA_DIR="$QUAL/oxylabs/data"
  export WALMART_COLLECTOR_DATABASE_URL="postgresql://walmart_q167@127.0.0.1:5432/walmart_q168d_oxylabs"
  step "rollback166.version" 0 "$tree" -- uv run --frozen walmart-collector --version
  step "rollback166.check-db" 0 "$tree" -- uv run --frozen walmart-collector validate-config --check-db
  step "rollback166.status" 0 "$tree" -- uv run --frozen walmart-collector status
  # And forward again: 1.6.8 on the same database.
  step "rollforward168.check-db" 0 "$QUAL/oxylabs/walmart-oxylabs-1.6.8" -- uv run --frozen walmart-collector validate-config --check-db
  unset WALMART_COLLECTOR_DATABASE_URL
fi
echo "ended $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$QUAL/HOST.txt"
python3 - "$QUAL" <<'PY'
import json, sys
from pathlib import Path
qual = Path(sys.argv[1])
rows = [json.loads(l) for l in (qual / "steps.jsonl").open(encoding="utf-8")]
# An expected failure passes only when its output shows the failure, never by its exit code alone.
for r in rows:
    if r.get("expected_exit", 0) != 0:
        text = (qual / r["log"]).read_text(encoding="utf-8", errors="strict")
        r["failure_shown"] = '"current": false' in text and '"revision": null' in text
        r["pass_by_exit"] = r["pass_by_exit"] and r["failure_shown"]
bad = [r for r in rows if not r.get("pass_by_exit", r.get("pass"))]
(qual / "steps_checked.json").write_text(json.dumps(rows, indent=1) + "\n", encoding="utf-8")
print(f"{len(rows)} steps, {len(bad)} not as expected:", [r["step"] for r in bad])
PY
