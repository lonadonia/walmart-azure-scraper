#!/usr/bin/env bash
# The recorded terminal walkthrough of Walmart release 1.5.2 (commit 627c804) on Hamza's Azure test VM, 2026-11-01.
# Every command shown is run as shown. Offline: no provider, retailer or Classic request is made. Recorded with asciinema
# and rendered to MP4 by render_cast.py; no audio. Lines starting with # are the narration.
set -u
cd ~/v152 || exit 1
export PATH="/usr/local/bin:$PATH"
X=/tmp/walkthrough_exports
S6=01M6A2VQAA5VXJHJHMZPCTZTD4
DBURL=postgresql+psycopg://postgres@v152pg/walmart_live150
say() { printf '\n\033[1;36m# %s\033[0m\n' "$*"; sleep 2.5; }
run() { printf '\033[1;32m$\033[0m %s\n' "$*"; sleep 1; eval "$*"; sleep 2; }
sql() { sudo docker exec v152pg psql -U postgres -d "${DB:-walmart_live150}" -At -c "$1"; }

say "Walmart collector, release 1.5.2 (commit 627c804): a correction update, verified offline."
say "Recorded on Hamza's Azure test VM. No provider, retailer or Classic request is made here."
run "date -u +%FT%TZ"
run "sha256sum pkg/WALMART_SOURCE_1.5.2.zip pkg/OXYLABS_CLASSIC_OFFLINE_PROBE_1.5.2.zip"

say "Both editions, built in Docker from that source ZIP"
run "sudo docker image ls walmart-collector 2>/dev/null"
run "sudo docker run --rm --network none walmart-collector:1.5.2-oxylabs --version"
run "sudo docker run --rm --network none walmart-collector:1.5.2-scrapedo --version"
run "sudo docker run --rm --network none --entrypoint cat walmart-collector:1.5.2-oxylabs /app/BUILD_INFO.json; echo"

say "The store and the fulfillment: Walmart #3891, Waukegan, IL 60085, Pickup"
run "sudo docker run --rm --network none --entrypoint cat walmart-collector:1.5.2-oxylabs /app/config/stores.yaml"
say "The schedule is off in the configuration, and nothing on this VM starts the collector"
run "sudo docker run --rm --network none --entrypoint grep walmart-collector:1.5.2-oxylabs -n -A2 'schedule:' /app/config/collector.yaml"
run "systemctl list-timers --all --no-pager | grep -i -E 'walmart|collector' || echo 'no timer names the collector'"
run "(crontab -l; sudo crontab -l) 2>/dev/null | grep -i -E 'walmart|collector' || echo 'no cron entry names the collector'"

say "Without a key, a run is refused before any request (exit 3: CREDENTIALS)"
run "sudo docker run --rm --network none walmart-collector:1.5.2-oxylabs validate-config --require-credentials > /tmp/walkthrough_vc.out 2>&1; echo exit \$?"
run "grep '\"event\": \"RESULT\"' /tmp/walkthrough_vc.out | python3 -c \"import json, sys; d=json.load(sys.stdin); print('exit_code', d['exit_code'], '| oxylabs key:', json.dumps(d['result']['environment']['oxylabs_key']))\"; rm -f /tmp/walkthrough_vc.out"
say "The containers' network is internal: it reaches the test database and nothing else"
run "sudo docker network inspect v152net --format 'internal network: {{.Internal}}'"
run "sudo docker run --rm --network v152net --entrypoint python walmart-collector:1.5.2-oxylabs -c \"import socket; socket.create_connection(('1.1.1.1', 443), 5)\" 2>&1 | tail -1"

say "The nine runs of 2026-10-31 were replayed from their stored pages in the container at 19:56Z to 19:59Z"
run "cut -d, -f1,2,5 commands.csv | grep -E 'docker_build|c_replay|c_export_S6'"
run "rm -rf $X; mkdir -p $X && tar -xzf replay/exports_container.tar.gz -C $X && ls $X && ls $X/S6"
run "python3 -c \"import json; d='$X/S6/'; print(len(json.load(open(d+'products_fresh.json'))), 'rows observed by S6;', len(json.load(open(d+'products.json'))), 'retained rows')\""

say "Each row names the page it was read from, and the store check in that page's own data"
run "python3 -c \"import json; r=[x for x in json.load(open('$X/S6/record_map.json'))['rows'] if x['observation_kind']=='replayed'][0]; print(json.dumps({'item': r['item_id'], 'page': r['page']['url'], 'fetched_at': r['page']['fetched_at'], 'store_check': r['fields']['_store_check']['selector_or_path']}, indent=1))\""

say "A corrected carried row: run S3 read it at 21:33:20Z; 1.5.2 keeps the pack beside the size"
run "python3 -c \"import json; p=[x for x in json.load(open('$X/S6/products.json')) if '/18472720019?' in x['url']][0]; print(p['product_title'], '->', repr(p['weight']), p['crawl_date'])\""
run "python3 -c \"import json; r=[x for x in json.load(open('$X/S6/record_map.json'))['rows'] if x['item_id']=='18472720019'][0]; print(json.dumps({k: r[k] for k in ('observation_kind', 'observed_by_run', 'observed_at', 'read_again_by_run')}, indent=1)); print(r['fields']['weight']['selector_or_path'])\""

say "A size recovered from a saved product page: both files name the same page, run, time and revision"
run "python3 -c \"import json; w=[x for x in json.load(open('$X/S6/field_dispositions.json')) if x['item_id']=='10402650'][0]['weight']; print(json.dumps({k: w[k] for k in ('disposition', 'value', 'source_run', 'page_fetch_id', 'observed_at', 'source_revision')}, indent=1))\""
run "python3 -c \"import json; f=[x for x in json.load(open('$X/S6/record_map.json'))['rows'] if x['item_id']=='10402650'][0]['fields']['weight']; print(json.dumps({k: f[k] for k in ('source', 'fetch_id', 'observed_at', 'body_sha256')}, indent=1))\""

say "Kill and resume, now: a new replay of S6's stored pages, killed with SIGKILL partway through, then resumed"
say "A run already replayed is not replayed again, so this uses a fresh copy of the campaign database, dropped afterwards"
run "sudo docker exec v152pg createdb -U postgres walmart_walk && sudo docker exec -i v152pg pg_restore -U postgres --no-owner --no-privileges -d walmart_walk < pkg/campaign_copy.dump && echo 'restored: walmart_walk'"
DB=walmart_walk
DBURL=postgresql+psycopg://postgres@v152pg/walmart_walk
before=$(sql "select coalesce(string_agg(id, ','), '') from runs where mode='REPLAY' and config_snapshot->'replay'->>'source_run'='$S6'")
run "sudo docker run -d --name v152walk --network v152net -v v152data:/app/data -e WALMART_COLLECTOR_DATABASE_URL=$DBURL walmart-collector:1.5.2-oxylabs replay --run $S6"
rp=""; n=0
for _ in $(seq 1 900); do
  rp=$(sql "select id from runs where mode='REPLAY' and config_snapshot->'replay'->>'source_run'='$S6' and position(id in '$before') = 0 limit 1")
  [ -n "$rp" ] && n=$(sql "select count(*) from page_fetches where run_id='$rp'")
  [ "${n:-0}" -ge 6 ] && break
  sleep 0.1
done
run "sql \"select count(*) from page_fetches where run_id='$rp'\""
run "sudo docker kill --signal=KILL v152walk"
run "sudo docker inspect v152walk --format 'exit code {{.State.ExitCode}}' && sudo docker rm v152walk"
run "sql \"select state, count(*) from tasks where run_id='$rp' group by 1 order by 1\""
for i in $(seq 1 20); do
  run "sudo docker run --rm --network v152net -v v152data:/app/data -e WALMART_COLLECTOR_DATABASE_URL=$DBURL walmart-collector:1.5.2-oxylabs resume --run $rp | tail -1 | cut -c1-150; echo exit \${PIPESTATUS[0]}"
  [ "$(sql "select count(*) from tasks where run_id='$rp' and state in ('pending', 'running')")" = 0 ] && break
  say "refused while the killed worker's lease holds: retried after 15 s"
  sleep 15
done
run "sql \"select status from runs where id='$rp'\"; sql \"select state, count(*) from tasks where run_id='$rp' group by 1 order by 1\""
say "Every task finished. 'rejected' means not publishable, as for its source run S6, a pilot: only the coverage check G3 failed, the one a pilot is expected to fail, so the exit is 0. A replay is never published."
run "sql \"select purpose, count(*) from page_fetches where run_id='$rp' group by 1 order by 1\""
say "Read twice after the resume: only robots.txt and the store page, the resumed session's own setup"
run "sql \"select url, purpose, count(*) from page_fetches where run_id='$rp' group by 1, 2 having count(*) > 1\""
run "sudo docker exec v152pg dropdb -U postgres walmart_walk && echo 'dropped: walmart_walk'"
unset DB

say "Publication faults: a SYNTHETIC test against a fixture, run here at 20:14Z to 20:16Z; not a retailer run"
run "sed -n 1,24p publication/README.txt"

say "The Oxylabs Classic offline probe 1.5.2: its plan, and the live command, which is refused; nothing is sent"
run "cd probe/oxylabs-classic-offline-probe-1.5.2/oxylabs-classic-probe"
run "uv run --frozen classic-probe plan --targets config/targets.json | head -20"
run "uv run --frozen classic-probe live --manifest ../../campaign.json | tail -12; echo exit \${PIPESTATUS[0]}"
run "cd ~/v152"

say "The record of every step on this VM: commands.csv, one log per step, the JUnit XML and the load tests"
run "cut -d, -f1,5 commands.csv | tail -28 | paste -sd ' '"
run "ls junit load publication"
say "In the delivery: azure_docker_recovery/README.txt, and WALMART_EVIDENCE_1.5.2.zip: 7_release_1_5_2/owner_vm/"
say "End of the walkthrough."
rm -rf "$X"
