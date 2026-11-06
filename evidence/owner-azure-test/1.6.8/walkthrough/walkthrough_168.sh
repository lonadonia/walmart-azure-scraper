#!/usr/bin/env bash
# The recorded terminal walkthrough of Walmart release 1.6.8 (commit 85c29e7) on Hamza's Azure test VM.
# Every command shown is run as shown. Offline: no provider, retailer or Classic request is made (the containers get
# no provider key, and their HTTP(S) goes to a closed local port). Recorded with asciinema by "vm_walk_168d.sh walk"
# and rendered to MP4 by render_cast.py; no audio. Lines starting with # are the narration.
# The helpers are those of vm_docker_168d.sh, which vm_walk_168d.sh writes to walk_helpers.sh (asciinema starts this
# script through sh, which does not pass exported bash functions on):
#   dk ...                          the docker client of this gate's own daemon (Ubuntu's packages, unpacked; no install)
#   cdb EDITION VOLUME DB -- ARGS   the collector in that edition's image: host network (the VM's PostgreSQL), read-only
#                                   root, the data volume, no provider key, HTTP(S) to a closed local port
#   cdbi IMAGE VOLUME DB -- ARGS    the same with any image
#   psqlq DB SQL                    a query of this work's isolated databases
set -u
cd "$BASE" || exit 1
. "$BASE/walk_helpers.sh" || exit 1
WDB=walmart_q168d_walk
VOL=q168dwalk
IMG=walmart-collector-q168d:1.6.8-oxylabs
OLD=walmart-collector-q168d:1.6.6-oxylabs
L10=01M6KA3CKYJSD6WDY4TDAAV73Y
L12=01M6MC7YE4PBXV88G3PJ5ENW4B
say() { printf '\n\033[1;36m# %s\033[0m\n' "$*"; sleep 2.5; }
run() { printf '\033[1;32m$\033[0m %s\n' "$*"; sleep 1; eval "$*"; sleep 2; }
newest() { psqlq "$WDB" "select id from runs where mode = 'REPLAY' and config_snapshot->'replay'->>'source_run' = '$1' order by created_at desc limit 1"; }

say "Walmart collector, release 1.6.8 (commit 85c29e7): a correction update, verified offline."
say "Recorded on Hamza's Azure test VM: an owner test, not the client's environment. No provider, retailer or Classic request is made here."
run "date -u +%FT%TZ; uname -srm"
run "sha256sum WALMART_OXYLABS_SOURCE_1.6.8.zip WALMART_SCRAPEDO_SOURCE_1.6.8.zip"

say "Both editions, built with docker build from those ZIPs"
run "dk version --format 'Docker {{.Server.Version}} (Ubuntu packages unpacked for this test; nothing installed on the VM)'"
run "dk image ls --format '{{.Repository}}:{{.Tag}}  {{.ID}}  {{.Size}}' | grep q168d"
run "dk run --rm --network none $IMG --version"
run "dk run --rm --network none walmart-collector-q168d:1.6.8-scrapedo --version"
run "dk run --rm --network none --entrypoint cat $IMG /app/BUILD_INFO.json; echo"

say "The store and the fulfillment: Walmart #3891, 3900 Fountain Square Pl, Waukegan, IL 60085, Pickup"
run "dk run --rm --network none --entrypoint cat $IMG /app/config/stores.yaml"
say "The schedule is off in the configuration, and nothing on this VM starts the collector"
run "dk run --rm --network none --entrypoint grep $IMG -n -A2 'schedule:' /app/config/collector.yaml"
run "systemctl list-timers --all --no-pager | grep -i -E 'walmart|collector' || echo 'no timer names the collector'"
run "(crontab -l; sudo -n crontab -l) 2>/dev/null | grep -i -E 'walmart|collector' || echo 'no cron entry names the collector'"

say "Without a provider key, a run is refused before any request (exit 3: CREDENTIALS)"
run "dk run --rm --network none $IMG validate-config --require-credentials | python3 walkview.py environment.oxylabs_key"

say "A copy of the campaign database and of the stored pages of live runs L10 and L12, for this recording only (removed at the end)"
run "sudo -n -u postgres createdb -O walmart_q167 $WDB && pg_restore -h 127.0.0.1 -U walmart_q167 -d $WDB --no-owner --no-privileges --exit-on-error ~/q167/campaign_live150.dump && echo restored: $WDB"
run "dk volume create $VOL && dk run --rm --network none -v $VOL:/app/data -v \"\$D/in:/in:ro\" --entrypoint tar $IMG -xf /in/stored_live_L10_L12.tar -C /app/data && echo loaded"
say "The schema: checked, and brought to the release's head (an upgrade that has nothing to do changes nothing)"
run "cdb oxylabs $VOL $WDB -- db-upgrade | python3 walkview.py"
run "cdb oxylabs $VOL $WDB -- validate-config --check-db | python3 walkview.py database"

say "Start: live run L12 (2026-11-04, release 1.6.6) replayed from its stored pages by 1.6.8. A replay makes no request and is never published"
run "cdb oxylabs $VOL $WDB -- replay --run $L12 | python3 walkview.py"
RP=$(newest "$L12")
say "Status of that run: its outcome, its records, and where its files are kept"
run "cdb oxylabs $VOL $WDB -- status --run $RP | python3 walkview.py run.status run.records_by_status run.collection_complete run.lineage.basis"
run "dk run --rm --network none -v $VOL:/app/data --entrypoint sh $IMG -c 'find /app/data/runs -maxdepth 2 | head -5'"
say "Export: the files of the run, and the 22 columns in the agreed order"
run "cdb oxylabs $VOL $WDB -- export --run $RP --out /app/data/walk/export | python3 walkview.py out files verified"
run "dk run --rm --network none -v $VOL:/app/data --entrypoint sh $IMG -c 'head -1 /app/data/walk/export/products.csv | tr , \"\\n\" | nl | paste - - - -'"

say "Coverage under 1.6.8 of live run L10 as it was collected (2026-11-04, release 1.6.4, a pilot with page limits)"
say "A row is complete only when every listing of it is; a /cp/ subcategory page an earlier release skipped keeps its row open"
run "cdb oxylabs $VOL $WDB -- coverage-report --run $L10 --out /app/data/walk/coverage_L10 | python3 walkview.py coverage_complete csv_rows_complete csv_rows"

say "Pause and resume: a new replay of L10 from its stored pages, killed with SIGKILL partway through, then resumed by the ordinary command"
before=$(newest "$L10")
run "dk run -d --name q168dwalkreplay --network host --read-only --tmpfs /tmp -v $VOL:/app/data --env-file \"\$D/pg.env\" -e WALMART_COLLECTOR_DATABASE_URL=\$(url $WDB) -e HTTP_PROXY=http://127.0.0.1:9 -e HTTPS_PROXY=http://127.0.0.1:9 -e NO_PROXY=127.0.0.1,localhost $IMG replay --run $L10 | cut -c1-12"
KP=""; n=0
for _ in $(seq 1 1200); do
  KP=$(newest "$L10")
  if [ -n "$KP" ] && [ "$KP" != "$before" ]; then
    n=$(psqlq "$WDB" "select count(*) from page_fetches where run_id = '$KP'")
    [ "${n:-0}" -ge 60 ] && break
  fi
  sleep 0.1
done
run "dk kill --signal=KILL q168dwalkreplay > /dev/null; psqlq $WDB \"select 'pages read when killed: ' || count(*) from page_fetches where run_id = '$KP'\""
run "dk inspect q168dwalkreplay --format 'container exit code {{.State.ExitCode}} (137: killed)' && dk rm q168dwalkreplay > /dev/null"
run "psqlq $WDB \"select status from runs where id = '$KP'\"; psqlq $WDB \"select state, count(*) from tasks where run_id = '$KP' group by 1 order by 1\""
for i in $(seq 1 30); do
  run "cdb oxylabs $VOL $WDB -- resume --run $KP | python3 walkview.py"
  [ "$(psqlq "$WDB" "select count(*) from tasks where run_id = '$KP' and state in ('pending', 'running')")" = 0 ] && break
  say "refused while the killed worker's lease holds (exit 9: BUSY); tried again after 15 s"
  sleep 15
done
run "psqlq $WDB \"select status from runs where id = '$KP'\"; psqlq $WDB \"select state, count(*) from tasks where run_id = '$KP' group by 1 order by 1\""
say "Every task finished. 'rejected' means not publishable, like its source run L10, a pilot; a replay is never published"
run "psqlq $WDB \"select 'pages: ' || count(*) || ', read twice: ' || count(*) - count(distinct (url, purpose)) from page_fetches where run_id = '$KP'\""
run "psqlq $WDB \"select url, purpose, count(*) from page_fetches where run_id = '$KP' group by 1, 2 having count(*) > 1\""

say "Rollback: the published release 1.6.6, built as an image from its ZIP, on the same database; then 1.6.8 again"
run "dk run --rm --network none $OLD --version"
run "cdbi $OLD $VOL $WDB -- validate-config --check-db | python3 walkview.py database"
run "cdbi $OLD $VOL $WDB -- status --run $RP | python3 walkview.py run.status run.records_by_status"
run "cdb oxylabs $VOL $WDB -- validate-config --check-db | python3 walkview.py database"

say "Removing this recording's database copy and volume"
run "sudo -n -u postgres dropdb $WDB && echo dropped: $WDB; dk volume rm $VOL"
say "End of the walkthrough. It shows no live provider run: L10 and L12 were collected on 2026-11-04 and are only replayed here."
