#!/usr/bin/env bash
# Owner VM: wall time and memory of a replay of L10 (the census of release 1.6.4, its stored pages) by the delivered
# release 1.6.8, Oxylabs edition, run on the host from a clean extraction of its ZIP (not in Docker), in a fresh copy
# of the campaign database (walmart_q168d_mem). REPLAY, no request: HTTP(S) goes to a closed local port and no
# provider key is set. measure_tree.py samples the resident memory of the collector's whole process tree.
# Run once, after the walkthrough session; refuses to run twice.
set -u
BASE="$HOME/q168d"
IN="$HOME/q167"
M="$BASE/mem"
ZIP="$BASE/WALMART_OXYLABS_SOURCE_1.6.8.zip"
WANT=eacf76e90320dbb1e1795913c4e0736d6297ca54645653764fae212eec6093ea
DUMP_SHA=2986596171776e90289b44eb911f7f73459b9d5c7055eba2abb6f39a739662a1
TAR_SHA=02d66177c9bd873061042567d0afdd0def90bbbfa1e345fbc5d321ae4fbe7178
L10=01M6KA3CKYJSD6WDY4TDAAV73Y
DB=walmart_q168d_mem
[ ! -e "$M/x" ] || { echo "exists: $M/x"; exit 2; }
mkdir -p "$M/out"
OUT="$M/out"
LOG="$OUT/mem.log"
exec >> "$LOG" 2>&1
PGPASSWORD=$(cat "$IN/pg.secret"); export PGPASSWORD
echo "host: $(. /etc/os-release; echo "$PRETTY_NAME"), kernel $(uname -r), $(uname -m), $(nproc) vCPU; started $(date -u +%FT%TZ)"
free -m
for pair in "$ZIP $WANT" "$IN/campaign_live150.dump $DUMP_SHA" "$IN/stored_live_L10_L12.tar $TAR_SHA"; do
  set -- $pair
  got=$(sha256sum "$1" | cut -d' ' -f1); echo "sha256 $(basename "$1") $got"
  [ "$got" = "$2" ] || { echo "SHA MISMATCH $1"; exit 2; }
done
python3 -m zipfile -e "$ZIP" "$M/x" || exit 2
E=$(find "$M/x" -maxdepth 2 -name pyproject.toml -printf '%h\n' | head -1)
echo "edition folder: ${E#$M/}"; cat "$E/BUILD_INFO.json"; echo
cd "$E" || exit 2
UV_OFFLINE=1 uv sync --frozen 2>&1 | tail -2; echo "sync exit ${PIPESTATUS[0]}"
.venv/bin/python --version
if [ "$(sudo -n -u postgres psql -Atc "select count(*) from pg_database where datname = '$DB'")" != 0 ]; then
  echo "database $DB exists: refusing"; exit 2
fi
sudo -n -u postgres createdb -O walmart_q167 "$DB" || exit 2
pg_restore -h 127.0.0.1 -U walmart_q167 -d "$DB" --no-owner --no-privileges --exit-on-error "$IN/campaign_live150.dump"
echo "restore exit $?"
mkdir -p "$M/data"
tar -xf "$IN/stored_live_L10_L12.tar" -C "$M/data"; echo "pages loaded: exit $? ($(find "$M/data" -type f | wc -l) files)"
export WALMART_COLLECTOR_DATABASE_URL="postgresql://walmart_q167@127.0.0.1:5432/$DB"
export WALMART_COLLECTOR_DATA_DIR="$M/data"
export HTTP_PROXY=http://127.0.0.1:9 HTTPS_PROXY=http://127.0.0.1:9 http_proxy=http://127.0.0.1:9 https_proxy=http://127.0.0.1:9
export NO_PROXY=127.0.0.1,localhost no_proxy=127.0.0.1,localhost
for v in $(env | cut -d= -f1 | grep -E '^(OXYLABS|SCRAPEDO|SCRAPE_DO)' || true); do unset "$v"; done
.venv/bin/walmart-collector --version; echo "exit $?"
.venv/bin/walmart-collector validate-config --check-db > "$OUT/check_db.json" 2>&1; echo "check-db exit $?"
echo "== the measured replay $(date -u +%FT%TZ)"
python3 "$BASE/measure_tree.py" "$OUT/measure.json" -- .venv/bin/walmart-collector replay --run "$L10" > "$OUT/replay.log" 2>&1
echo "replay exit $? $(date -u +%FT%TZ)"
cat "$OUT/measure.json"
RP=$(psql -h 127.0.0.1 -U walmart_q167 -d "$DB" -Atc "select id from runs where mode = 'REPLAY' and config_snapshot->'replay'->>'source_run' = '$L10' order by created_at desc limit 1")
echo "replay run $RP"
.venv/bin/walmart-collector status --run "$RP" > "$OUT/status.json" 2>&1; echo "status exit $?"
psql -h 127.0.0.1 -U walmart_q167 -d "$DB" -Atc "select jsonb_build_object('collection_parallel', config_snapshot->'collection'->'parallel', 'overrides', config_snapshot->'overrides', 'replay', config_snapshot->'replay') from runs where id = '$RP'" > "$OUT/workers.json"
psql -h 127.0.0.1 -U walmart_q167 -d "$DB" -Atc "select count(*) from page_fetches where run_id = '$RP'" > "$OUT/pages.txt"
free -m
echo "ended $(date -u +%FT%TZ)"
