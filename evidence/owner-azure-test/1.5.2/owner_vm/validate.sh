#!/usr/bin/env bash
# Owner Azure VM validation of the Walmart collector, release 1.5.2. Offline for the retailer and every provider:
# no key is on this path, no provider is called, nothing is scheduled, and nothing existing is modified.
#   bash validate.sh env|backup|tests|docker|replay|counts
# Everything lives under ~/v152. Each step writes logs/<name>.log and one row of commands.csv.
set -u
V="$HOME/v152"
LOGS="$V/logs"
REL=1.5.2
PROBE=1.5.2
ED=walmart-oxylabs-$REL
IMG=walmart-collector:$REL-oxylabs
IMG2=walmart-collector:$REL-scrapedo
NET=v152net
PG=v152pg
DBURL=postgresql+psycopg://postgres@v152pg/walmart_live150
export PATH="$HOME/.local/bin:/usr/local/bin:$PATH"
mkdir -p "$LOGS" "$V/junit" "$V/load" "$V/publication" "$V/backup" "$V/replay"
[ -f "$V/commands.csv" ] || echo "step,utc_start,utc_end,seconds,exit_code" > "$V/commands.csv"

step() {
  local name=$1; shift
  local start t0 rc
  start=$(date -u +%FT%TZ); t0=$(date +%s)
  "$@" > "$LOGS/$name.log" 2>&1
  rc=$?
  echo "$name,$start,$(date -u +%FT%TZ),$(( $(date +%s) - t0 )),$rc" >> "$V/commands.csv"
  echo "$(date -u +%TZ) $name exit $rc"
  return $rc
}

DBS="walmart_collector walmart_oxylabs walmart_pubtest walmart_pubtest_oxylabs walmart_pubtest_scrapedo walmart_scrapedo"

env_report() {
  date -u +%FT%TZ; uname -srm; lsb_release -ds; nproc; free -m; df -h /
  uv --version; docker version --format 'docker {{.Server.Version}}' 2>/dev/null || sudo docker version --format 'docker {{.Server.Version}}'
  psql --version
  echo "--- timers naming the collector (none expected)"; systemctl list-timers --all --no-pager | grep -i -E 'walmart|collector' || echo none
  echo "--- cron naming the collector (none expected)"; (sudo crontab -l 2>/dev/null; crontab -l 2>/dev/null) | grep -i -E 'walmart|collector' || echo none
}

row_counts() {
  for d in $DBS; do
    echo "== $d"
    sudo -u postgres psql -At -d "$d" -c "select table_name, (xpath('/row/c/text()', query_to_xml(format('select count(*) as c from %I.%I', table_schema, table_name), false, true, '')))[1]::text from information_schema.tables where table_schema='public' order by 1"
  done
}

backup() {
  for d in $DBS; do
    sudo -u postgres pg_dump -Fc "$d" > "$V/backup/$d.dump" || return 1
  done
  ( cd "$V/backup" && sha256sum *.dump > SHA256SUMS.txt && cat SHA256SUMS.txt )
  ls -la "$V/backup"
}

prepare() {
  rm -rf "$V/src"; mkdir -p "$V/src"
  ( cd "$V/pkg" && sha256sum -c PKG_SHA256.txt ) || return 1
  ( cd "$V/src" && python3 -m zipfile -e "$V/pkg/WALMART_SOURCE_$REL.zip" . ) || return 1
  ls "$V/src"/walmart-source-$REL
}

in_ed() { ( cd "$V/src/walmart-source-$REL/$ED" && "$@" ); }

pgpath() { echo "$V/src/walmart-source-$REL/$ED/.venv/lib/python3.12/site-packages/pgserver/pginstall/bin"; }

tests() {
  step prepare prepare || return 1
  step uv_sync in_ed uv sync --frozen
  step version in_ed uv run --frozen walmart-collector --version
  step validate_config in_ed uv run --frozen walmart-collector validate-config
  step ruff_check in_ed uv run --frozen ruff check .
  step ruff_format in_ed uv run --frozen ruff format --check .
  step mypy in_ed uv run --frozen mypy src
  step unit in_ed env PSYCOPG_IMPL=python uv run --frozen pytest tests/unit -q --no-header --junitxml="$V/junit/unit.xml"
  local f n
  for f in "$V/src/walmart-source-$REL/$ED"/tests/integration/test_*.py; do
    n=$(basename "$f" .py)
    case "$n" in
      test_concurrency_load|test_publication_safety) continue ;;
    esac
    step "int_$n" in_ed env PSYCOPG_IMPL=python uv run --frozen pytest "tests/integration/$n.py" -q --no-header --tb=short --junitxml="$V/junit/$n.xml"
  done
  step publication_faults in_ed env PSYCOPG_IMPL=python PUBLICATION_EVIDENCE_DIR="$V/publication" uv run --frozen pytest tests/integration/test_publication_safety.py -q --no-header --tb=short --junitxml="$V/junit/test_publication_safety.xml"
  step concurrency_load in_ed env PSYCOPG_IMPL=python LOAD_EVIDENCE_DIR="$V/load" LOAD_PAGES=6 uv run --frozen pytest tests/integration/test_concurrency_load.py -q --no-header --tb=short --junitxml="$V/junit/test_concurrency_load.xml"
}

build_one() {
  local dir=$1 tag=$2 commit built
  commit=$(python3 -c "import json;print(json.load(open('$V/src/walmart-source-$REL/$dir/BUILD_INFO.json'))['commit'])")
  built=$(date -u +%FT%TZ)
  ( cd "$V/src/walmart-source-$REL/$dir" && sudo docker build --pull --build-arg SOURCE_COMMIT="$commit" --build-arg BUILT_AT="$built" -t "$tag" . )
}

image_report() {
  sudo docker image inspect "$IMG" --format 'id {{.Id}} size {{.Size}} user {{.Config.User}} entrypoint {{.Config.Entrypoint}} created {{.Created}}'
  sudo docker image inspect "$IMG2" --format 'id {{.Id}} size {{.Size}} user {{.Config.User}} entrypoint {{.Config.Entrypoint}} created {{.Created}}'
  sudo docker image history "$IMG" --format '{{.Size}} {{.CreatedBy}}' | cut -c1-120 | grep -v -i -E 'key|secret' | head -30
  echo "--- no key or data file in the image:"
  sudo docker run --rm --network none --entrypoint sh "$IMG" -c 'find /app -name "*.env" -o -name ".env*" | grep -v -E "\.venv|example" || echo none; ls -la /app /app/config | head -24; cat /app/BUILD_INFO.json; id'
}

smoke() {
  local c="sudo docker run --rm --network none --read-only --tmpfs /tmp"
  $c "$IMG" --version
  $c "$IMG" --help | head -40
  $c "$IMG" validate-config
  echo "--- the default command"; $c "$IMG"
  echo "--- Scrape.do edition"
  $c "$IMG2" --version
  $c "$IMG2" validate-config
  echo "--- refused without a key (exit 3 expected: CREDENTIALS)"
  $c "$IMG" validate-config --require-credentials; echo "exit $?"
}

cli() { sudo docker run --rm --network "$NET" -v v152data:/app/data -e WALMART_COLLECTOR_DATABASE_URL="$DBURL" "$IMG" "$@"; }

net_up() {
  sudo docker network create --internal "$NET"
  sudo docker volume create v152pgdata
  sudo docker volume create v152data
  sudo docker run -d --name "$PG" --network "$NET" -e POSTGRES_HOST_AUTH_METHOD=trust -v v152pgdata:/var/lib/postgresql/data postgres:16
  for _ in $(seq 1 60); do sudo docker exec "$PG" pg_isready -U postgres && break; sleep 1; done
  sudo docker exec "$PG" createdb -U postgres walmart_live150
  sudo docker exec -i "$PG" pg_restore -U postgres --no-owner --no-privileges -d walmart_live150 < "$V/pkg/campaign_copy.dump"
  sudo docker run --rm -v v152data:/data -v "$V/pkg:/pkg:ro" alpine:3.20 sh -c 'tar -xzf /pkg/campaign_data.tar.gz -C /data && chown -R 10001:10001 /data && du -sh /data'
  echo "--- no route out of this network (the attempt must fail):"
  sudo docker run --rm --network "$NET" --entrypoint python "$IMG" -c "
import socket
try:
    socket.create_connection(('1.1.1.1', 443), 5)
    print('CONNECTED')
except OSError as exc:
    print('refused as intended:', exc)"
}

replay_chain() {
  local stage src rp out
  step c_db_upgrade cli db-upgrade || return 1
  step c_validate cli validate-config --check-db || return 1
  : > "$V/replay/replay_runs.txt"
  for stage in S1 S2 S3 S4 S5b_serial S5b_parallel S5a S6 S7; do
    case "$stage" in
      S4) interrupt_and_resume S4 TERM 6; continue ;;
      S6) interrupt_and_resume S6 KILL 6; continue ;;
    esac
    src=$(python3 -c "import json;print(json.load(open('$V/pkg/runs.json'))['$stage'])")
    step "c_replay_$stage" cli replay --run "$src"
    rp=$(grep -oE '"run(_id)?": ?"01[0-9A-Z]{24}"' "$LOGS/c_replay_$stage.log" | grep -oE '01[0-9A-Z]{24}' | grep -v "$src" | head -1)
    echo "$stage $rp" >> "$V/replay/replay_runs.txt"
  done
  while read -r stage rp; do
    step "c_export_$stage" cli export --run "$rp" --out "/app/data/exports_container/$stage"
  done < "$V/replay/replay_runs.txt"
  step c_status cli status --limit 30
  sudo docker run --rm -v v152data:/data alpine:3.20 sh -c 'cd /data/exports_container && tar -czf - .' > "$V/replay/exports_container.tar.gz"
  ls -la "$V/replay"
}

sql() { sudo docker exec "$PG" psql -U postgres -At -d walmart_live150 -c "$1"; }

# A signal in the middle of a replay, then the real recovery commands: a resume refused while the dead worker's lease
# holds, the resume, the result. TERM is a graceful stop, KILL a forced one that gives the process no chance to clean up.
interrupt_and_resume() {
  local stage=$1 sig=$2 pages=$3
  local src rp="" n=0 rc=9 i
  local out="$LOGS/interrupt_${sig}_$stage.log"
  src=$(python3 -c "import json;print(json.load(open('$V/pkg/runs.json'))['$stage'])")
  {
    echo "$(date -u +%FT%TZ) start the replay of $stage ($src), detached"
    sudo docker run -d --name v152replay --network "$NET" -v v152data:/app/data -e WALMART_COLLECTOR_DATABASE_URL="$DBURL" "$IMG" replay --run "$src"
    for _ in $(seq 1 600); do
      rp=$(sql "select id from runs where mode='REPLAY' and config_snapshot->'replay'->>'source_run'='$src' limit 1")
      [ -n "$rp" ] && n=$(sql "select count(*) from page_fetches where run_id='$rp'")
      [ "${n:-0}" -ge "$pages" ] && break
      sleep 0.1
    done
    echo "$(date -u +%FT%TZ) replay run $rp has $n pages read: $sig"
    echo "running: $(sudo docker inspect v152replay --format '{{.State.Running}}')"
    if [ "$sig" = KILL ]; then
      sudo docker kill --signal=KILL v152replay
    else
      sudo docker stop --time 90 v152replay
    fi
    sudo docker inspect v152replay --format 'exit code {{.State.ExitCode}} oom {{.State.OOMKilled}}'
    sudo docker logs v152replay 2>&1 | tail -3 | cut -c1-260
    sudo docker rm v152replay
    echo "--- the state after the signal"
    sql "select status, stop_code from runs where id='$rp'"
    sql "select state, count(*) from tasks where run_id='$rp' group by 1 order by 1"
    echo "pages read $(sql "select count(*) from page_fetches where run_id='$rp'") records $(sql "select count(*) from records where run_id='$rp'")"
    echo "--- resume: repeated only while it is refused because the dead worker's lease holds (exit 9)"
    for i in $(seq 1 40); do
      cli resume --run "$rp" > "$LOGS/interrupt_${sig}_${stage}_attempt_$i.log" 2>&1
      rc=$?
      echo "$(date -u +%FT%TZ) resume attempt $i: exit $rc"
      tail -1 "$LOGS/interrupt_${sig}_${stage}_attempt_$i.log" | cut -c1-300
      [ "$rc" -eq 9 ] || break
      sleep 15
    done
    echo "--- the state after the resume"
    sql "select status, stop_code from runs where id='$rp'"
    sql "select state, count(*) from tasks where run_id='$rp' group by 1 order by 1"
    echo "pages read $(sql "select count(*) from page_fetches where run_id='$rp'") records $(sql "select count(*) from records where run_id='$rp'")"
    echo "pages read twice: $(sql "select count(*) from (select url, purpose from page_fetches where run_id='$rp' group by 1,2 having count(*) > 1) d")"
    echo "$stage $rp" >> "$V/replay/replay_runs.txt"
  } > "$out" 2>&1
  echo "$(date -u +%TZ) interrupt_and_resume $stage $sig: resume exit $rc"
}

# The frozen Classic probe from its ZIP alone: what a clean Linux host needs, and its peak memory. Offline.
probe_check() {
  rm -rf "$V/probe"; mkdir -p "$V/probe"
  ( cd "$V/probe" && python3 -m zipfile -e "$V/pkg/OXYLABS_CLASSIC_OFFLINE_PROBE_$PROBE.zip" . ) || return 1
  local d="$V/probe/oxylabs-classic-offline-probe-$PROBE/oxylabs-classic-probe"
  ( cd "$d"     && uv sync --frozen     && /usr/bin/time -v uv run --frozen pytest -q --no-header 2>&1 | tail -30     && /usr/bin/time -v uv run --frozen classic-probe plan --targets config/targets.json 2>&1 | grep -E 'Maximum resident|walmart-search-p1' | cut -c1-160     && uv run --frozen classic-probe validate --targets config/targets.json --rates config/rates.example.json | tail -3 | cut -c1-200 ;
    uv run --frozen classic-probe campaign-init --manifest "$V/probe/campaign.json" --ledger "$V/probe/ledger.sqlite" --campaign-id vm-offline-check --offline | tail -3 | cut -c1-200 ;
    uv run --frozen classic-probe live --manifest "$V/probe/campaign.json" | tail -12 | cut -c1-200; echo "live exit ${PIPESTATUS[0]} (3 expected: refused)" ;
    du -sh "$d" "$d/.venv" )
}

reset_docker() {
  sudo docker rm -f v152replay "$PG" 2>/dev/null
  sudo docker network rm "$NET" 2>/dev/null
  sudo docker volume rm v152pgdata v152data 2>/dev/null
  sudo docker ps -a --format '{{.Names}}'; sudo docker volume ls -q; sudo docker network ls --format '{{.Name}}'
}

case "${1:-}" in
  reset) step reset_docker reset_docker ;;
  prep) step prepare0 prepare ;;
  probe) step probe probe_check ;;
  env) step env env_report; step counts_before row_counts ;;
  backup) step backup backup ;;
  tests) tests ;;
  docker)
    step docker_build_oxylabs build_one "$ED" "$IMG"
    step docker_build_scrapedo build_one "walmart-scrapedo-$REL" "$IMG2"
    step docker_image image_report
    step docker_smoke smoke
    ;;
  replay)
    step docker_net net_up || exit 1
    replay_chain
    ;;
  counts) step counts_after row_counts; diff "$LOGS/counts_before.log" "$LOGS/counts_after.log" && echo "row counts unchanged" ;;
  *) echo "usage"; exit 2 ;;
esac
