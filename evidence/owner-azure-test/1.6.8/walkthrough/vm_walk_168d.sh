#!/usr/bin/env bash
# Owner VM, Walmart release 1.6.8 (commit 85c29e7): the walkthrough recorded in a session of its own, after the
# container gate (vm_docker_168d.sh). The gate's own recording failed: asciinema starts the recorded command through
# sh (dash), which does not pass exported bash functions on, and the walkthrough found none of the gate's helpers.
# This script is vm_docker_168d.sh with the same helpers and stages, but for: its own steps and logs
# (docker/walk_session/), the stage wprep (the database password file again, the inputs checked; nothing
# downloaded), build166 (the published 1.6.6 Oxylabs edition built as an image, as the gate's rollback stage does),
# and walk, which writes the helpers to a file the walkthrough sources and judges the recording by its output.
# The images are built again from the same ZIPs: their ids are those this session's image report gives.
#   bash vm_walk_168d.sh wprep|start|build|build166|image|walk|stop|after
BASE="$HOME/q168d"
IN="$HOME/q167"  # inputs uploaded for the 1.6.7 gate, read only
D="$BASE/docker"
EXEC=/run/q168ddocker
LOGS="$D/walk_session/logs"
PKG="$D/pkg"
SRC="$D/src"
COMMIT=85c29e7b2404500299056973f50c84b84e187a5a
REL=1.6.8
L12=01M6MC7YE4PBXV88G3PJ5ENW4B
L10=01M6KA3CKYJSD6WDY4TDAAV73Y
DUMP_SHA=2986596171776e90289b44eb911f7f73459b9d5c7055eba2abb6f39a739662a1
TAR_SHA=02d66177c9bd873061042567d0afdd0def90bbbfa1e345fbc5d321ae4fbe7178
TAR2_SHA=0ff0b87cf4b4e0f1e6c26f1dd065f84721899f322bd6ec2993345e67be5184db  # the other 22 runs' stored pages
OLD_ZIP_SHA=0859a2f693527bab073252edf941928bb4f118ea4a63d581078d96ddd2324e22  # the published 1.6.6 Oxylabs ZIP
OLD_COMMIT=cbea802891d4e66b74a0abc33e0af0af74c89708  # the commit 1.6.6's archives were built at (its BUILD_INFO)
# the 15 live runs of the 1.6.x campaign the W4 tables of 1.6.6 read, by their W4 labels
LIVE_RUNS="L1=01M6H5TX7R4ZWV8W3NTH0QN6HF L2=01M6H72J86K5TF7A1874N7BJ2R L3=01M6HA74X4QYMW45SVD62JQDSQ L2b=01M6HAXEP6495EGWT91JQS09SS L4r=01M6HCF2YSD7N18W7JMH6EHK23 L4=01M6HCZXM0WGMRCFDTCNZ7218K L5=01M6K1HG154683NAAFXQZX33C6 L6=01M6K25T57WW4BJBJ3RQGWN26G L8=01M6K6P21BW509BMRTN1FSB9H7 L9=01M6K7AB85824HHKD17VNEHASS L7=01M6K7HT3XVV8R8CX79P31KMB4 L10=01M6KA3CKYJSD6WDY4TDAAV73Y L11=01M6KF4RDC2MKR5Q26ZY5D727P L11b=01M6KFRFEX31W014SW9ZTT4Y54 L12=01M6MC7YE4PBXV88G3PJ5ENW4B"
declare -A ZIP=( [oxylabs]="$BASE/WALMART_OXYLABS_SOURCE_1.6.8.zip" [scrapedo]="$BASE/WALMART_SCRAPEDO_SOURCE_1.6.8.zip" )
declare -A WANT=( [oxylabs]=eacf76e90320dbb1e1795913c4e0736d6297ca54645653764fae212eec6093ea
                  [scrapedo]=18642dd6fd1de8db6d43eea16bc11e11ffa780cc791a67dd75b4ce316d63db52 )
mkdir -p "$LOGS" "$D/out"
STEPS="$D/walk_session/steps.jsonl"
PGPASSWORD=$(cat "$IN/pg.secret"); export PGPASSWORD
DBHOST=127.0.0.1

step() {  # step NAME EXPECT -- command...   (EXPECT: an exit code, or "any" for a step judged by its output)
  local name=$1 expect=$2; shift 3
  local log="$LOGS/$name.log" t0 t1 rc at
  at=$(date -u +%Y-%m-%dT%H:%M:%SZ); t0=$(date +%s.%N)
  "$@" > "$log" 2>&1; rc=$?
  t1=$(date +%s.%N)
  python3 - "$name" "$rc" "$expect" "$at" "$t0" "$t1" "$log" "$*" >> "$STEPS" <<'PY'
import json, sys
name, rc, expect, at, t0, t1, log, cmd = sys.argv[1:]
print(json.dumps({"step": name, "exit": int(rc), "expected_exit": expect if expect == "any" else int(expect),
                  "pass_by_exit": True if expect == "any" else int(rc) == int(expect), "started_at": at,
                  "seconds": round(float(t1) - float(t0), 1), "log": "logs/" + log.rsplit("/", 1)[1],
                  "command": cmd[:600]}))
PY
  tail -n 1 "$STEPS" | cut -c1-220
  return 0
}

bin() { find "$PKG/root/usr/bin" "$PKG/root/usr/sbin" "$PKG/root/usr/libexec" -maxdepth 3 -type f -perm -u+x -name "$1" 2>/dev/null | head -1; }
dk() { sudo -n env DOCKER_CONFIG="$D/cli" DOCKER_BUILDKIT=0 "$(bin docker)" -H "unix://$EXEC/docker.sock" "$@"; }
img() { echo "walmart-collector-q168d:$REL-$1"; }
url() { echo "postgresql://walmart_q167@$DBHOST:5432/$1"; }
# A collector command in the edition's image, through the host network (the VM's PostgreSQL on 127.0.0.1), with
# no provider key and HTTP(S) sent to a closed local port.
cdb() {  # cdb EDITION VOLUME DB -- collector args...
  local e=$1 vol=$2 db=$3; shift 4
  dk run --rm --network host --read-only --tmpfs /tmp -v "$vol:/app/data" --env-file "$D/pg.env" \
    -e "WALMART_COLLECTOR_DATABASE_URL=$(url "$db")" -e HTTP_PROXY=http://127.0.0.1:9 -e HTTPS_PROXY=http://127.0.0.1:9 \
    -e NO_PROXY=127.0.0.1,localhost "$(img "$e")" "$@"
}
psqlq() { psql -h "$DBHOST" -U walmart_q167 -d "$1" -Atc "$2"; }
cdbi() {  # cdbi IMAGE VOLUME DB -- collector args...   (cdb with any image)
  local image=$1 vol=$2 db=$3; shift 4
  dk run --rm --network host --read-only --tmpfs /tmp -v "$vol:/app/data" --env-file "$D/pg.env" \
    -e "WALMART_COLLECTOR_DATABASE_URL=$(url "$db")" -e HTTP_PROXY=http://127.0.0.1:9 -e HTTPS_PROXY=http://127.0.0.1:9 \
    -e NO_PROXY=127.0.0.1,localhost "$image" "$@"
}

host_state() {  # what this gate could change on the host, with counters left out
  echo "== packages"; dpkg-query -W -f '${Package} ${Version}\n' | sha256sum; dpkg-query -W | wc -l
  echo "== links"; ip -br link | awk '{print $1, $2}'
  echo "== addresses"; ip -br addr | awk '{print $1, $3, $4}'
  echo "== iptables (filter, nat)"; sudo -n iptables -S | sha256sum; sudo -n iptables -t nat -S | sha256sum
  echo "== ip6tables"; sudo -n ip6tables -S | sha256sum
  echo "== nft ruleset, counters removed"; sudo -n nft list ruleset | sed -E 's/counter packets [0-9]+ bytes [0-9]+/counter/' | sha256sum
  echo "== sysctl"; sysctl net.ipv4.ip_forward net.ipv6.conf.all.forwarding net.bridge.bridge-nf-call-iptables 2>&1
  echo "== apparmor profiles"; sudo -n aa-status 2>/dev/null | sed -n '/profiles are loaded/,/profiles are in complain/p' | sha256sum
  echo "== mounts naming docker, containerd, q167 or q168"; findmnt -rn -o TARGET | grep -E "docker|containerd|q16[78]" || echo none
  echo "== /etc/docker, /var/lib/docker, /var/lib/containerd"; ls -d /etc/docker /var/lib/docker /var/lib/containerd 2>&1
  echo "== /run entries"; sudo -n ls -A /run | sort | tr '\n' ' '; echo
  echo "== /run/containerd, /run/docker (left by the 2026-11-01 test)"; sudo -n ls -A /run/containerd /run/docker 2>&1 | tr '\n' ' '; echo
  echo "== /opt"; ls -A /opt | tr '\n' ' '; echo; sudo -n find /opt/containerd | sort | sha256sum
  echo "== units naming docker or containerd"; systemctl list-units --all --no-pager --plain 2>/dev/null | grep -E "docker|containerd" || echo none
  echo "== processes naming dockerd or containerd"; pgrep -a -f "dockerd|containerd" | grep -v pgrep || echo none
  echo "== groups"; getent group docker || echo "no docker group"
  echo "== databases"; sudo -n -u postgres psql -Atc "select datname||' '||pg_get_userbyid(datdba) from pg_database order by 1"
  echo "== listening sockets"; ss -ltnH | awk '{print $4}' | sort
}

prep() {
  date -u +%FT%TZ > "$D/started_at.txt"
  host_state > "$LOGS/host_before.txt" 2>&1
  rm -rf "$PKG" "$SRC"; mkdir -p "$PKG/debs" "$PKG/root" "$SRC"
  ( cd "$PKG/debs" && apt-get download docker.io containerd runc ) || return 1
  ( cd "$PKG/debs" && sha256sum ./*.deb )
  for p in docker.io containerd runc; do apt-cache show --no-all-versions "$p" | grep -E "^(Package|Version|SHA256|Filename):"; done
  for f in "$PKG"/debs/*.deb; do dpkg-deb -x "$f" "$PKG/root" || return 1; done
  for b in docker dockerd containerd containerd-shim-runc-v2 runc; do
    echo "$b: $(bin "$b")"; "$(bin "$b")" --version 2>&1 | head -1
    ldd "$(bin "$b")" 2>&1 | grep -E "not found" && return 1
  done
  [ "$(sha256sum "$IN/campaign_live150.dump" | cut -d' ' -f1)" = "$DUMP_SHA" ] || { echo "dump sha"; return 1; }
  [ "$(sha256sum "$IN/stored_live_L10_L12.tar" | cut -d' ' -f1)" = "$TAR_SHA" ] || { echo "tar sha"; return 1; }
  for e in oxylabs scrapedo; do
    [ "$(sha256sum "${ZIP[$e]}" | cut -d' ' -f1)" = "${WANT[$e]}" ] || { echo "zip sha $e"; return 1; }
    python3 -m zipfile -e "${ZIP[$e]}" "$SRC" || return 1
    grep -q "\"commit\": \"$COMMIT\"" "$SRC/walmart-$e-$REL/BUILD_INFO.json" || { echo "build info $e"; return 1; }
  done
  umask 077; printf 'PGPASSWORD=%s\n' "$PGPASSWORD" > "$D/pg.env"; umask 022
  cat > "$D/containerd.toml" <<EOF
version = 3
root = "$D/containerd-root"
state = "$EXEC/containerd-state"
disabled_plugins = ["io.containerd.grpc.v1.cri", "io.containerd.cri.v1.images", "io.containerd.cri.v1.runtime", "io.containerd.nri.v1.nri", "io.containerd.podsandbox.controller.v1.podsandbox"]

[grpc]
  address = "$EXEC/containerd/containerd.sock"

[ttrpc]
  address = "$EXEC/containerd/containerd.sock.ttrpc"

[debug]
  address = ""

[metrics]
  address = ""

[plugins]
  [plugins."io.containerd.internal.v1.opt"]
    path = "$D/containerd-opt"
EOF
  cat > "$D/daemon.json" <<EOF
{
  "data-root": "$D/root",
  "exec-root": "$EXEC/exec",
  "pidfile": "$EXEC/dockerd.pid",
  "hosts": ["unix://$EXEC/docker.sock"],
  "containerd": "$EXEC/containerd/containerd.sock",
  "bridge": "none",
  "iptables": false,
  "ip6tables": false,
  "ip-forward": false,
  "ip-masq": false,
  "userland-proxy": false,
  "features": {"containerd-snapshotter": false},
  "storage-driver": "overlay2",
  "log-driver": "json-file",
  "log-opts": {"max-size": "10m"}
}
EOF
  cat "$D/containerd.toml" "$D/daemon.json"
}

start() {
  local path="$(dirname "$(bin runc)"):$(dirname "$(bin containerd)"):$(dirname "$(bin dockerd)"):/usr/sbin:/usr/bin:/sbin:/bin"
  sudo -n mkdir -p "$EXEC/containerd" && sudo -n chmod 711 "$EXEC"
  echo "$(date -u +%FT%TZ) containerd"
  sudo -n env PATH="$path" "$(bin containerd)" --config "$D/containerd.toml" >> "$LOGS/containerd.out" 2>&1 &
  for _ in $(seq 1 60); do sudo -n test -S "$EXEC/containerd/containerd.sock" && break; sleep 0.5; done
  sudo -n test -S "$EXEC/containerd/containerd.sock" || { echo "containerd did not start"; tail -20 "$LOGS/containerd.out"; return 1; }
  echo "$(date -u +%FT%TZ) dockerd"
  sudo -n env PATH="$path" "$(bin dockerd)" --config-file "$D/daemon.json" >> "$LOGS/dockerd.out" 2>&1 &
  for _ in $(seq 1 120); do dk version > /dev/null 2>&1 && break; sleep 0.5; done
  dk version || { tail -30 "$LOGS/dockerd.out"; return 1; }
  dk info --format 'driver {{.Driver}} cgroup {{.CgroupDriver}} v{{.CgroupVersion}} root {{.DockerRootDir}} security {{.SecurityOptions}}'
  dk network ls
}

stop() {
  local pid
  dk ps -a
  pid=$(sudo -n cat "$EXEC/dockerd.pid" 2>/dev/null)
  [ -n "$pid" ] && sudo -n kill -TERM "$pid"
  for _ in $(seq 1 60); do [ -n "$pid" ] && sudo -n kill -0 "$pid" 2>/dev/null || break; sleep 0.5; done
  pid=$(pgrep -f "$D/containerd.toml" | head -1)
  [ -n "$pid" ] && sudo -n kill -TERM "$pid"
  for _ in $(seq 1 60); do [ -n "$pid" ] && sudo -n kill -0 "$pid" 2>/dev/null || break; sleep 0.5; done
  pgrep -a -f "$D/containerd.toml|$D/daemon.json|containerd-shim" || echo "no daemon of this gate is running"
  findmnt -rn -o TARGET | grep -E "q168d" || echo "no mount of this gate"
}

build() {
  for e in oxylabs scrapedo; do
    step "build_$e" 0 -- bash -c "cd '$SRC/walmart-$e-$REL' && sudo -n env DOCKER_CONFIG='$D/cli' DOCKER_BUILDKIT=0 '$(bin docker)' -H 'unix://$EXEC/docker.sock' build --network host --pull --build-arg SOURCE_COMMIT=$COMMIT --build-arg BUILT_AT=\$(date -u +%FT%TZ) -t '$(img "$e")' ."
  done
}

image_report() {
  local e
  for e in oxylabs scrapedo; do
    echo "== $(img "$e")"
    dk image inspect "$(img "$e")" --format 'id {{.Id}} size {{.Size}} user {{.Config.User}} entrypoint {{.Config.Entrypoint}} cmd {{.Config.Cmd}} created {{.Created}}'
    dk image inspect "$(img "$e")" --format '{{json .RootFS.Layers}}'
    dk image inspect "$(img "$e")" --format '{{json .Config.Env}}'
    dk image history --no-trunc "$(img "$e")" --format '{{.Size}} {{.CreatedBy}}' | cut -c1-200
    echo "docker save sha256: $(dk save "$(img "$e")" | sha256sum | cut -d' ' -f1)"
    echo "-- inside: BUILD_INFO, user, no key file, version"
    dk run --rm --network none --entrypoint sh "$(img "$e")" -c 'cat /app/BUILD_INFO.json; id; find / -xdev \( -name "*.env" -o -name ".env*" -o -name "*.pem" -o -name "*.key" \) 2>/dev/null | grep -v -E "^/proc|/\.venv/|example|/usr/(lib|share)/" || echo "no key or env file"; python -c "import walmart_headless as w; print(w.__version__)"'
    echo "-- the image's src and config against the delivered ZIP's (SHA-256 of every file)"
    dk run --rm --network none --entrypoint sh "$(img "$e")" -c 'cd /app && find src config -type f ! -name "*.pyc" ! -path "*/__pycache__/*" | LC_ALL=C sort | xargs sha256sum' > "$LOGS/image_files_$e.txt"
    ( cd "$SRC/walmart-$e-$REL" && find src config -type f ! -name "*.pyc" ! -path "*/__pycache__/*" | LC_ALL=C sort | xargs sha256sum ) > "$LOGS/zip_files_$e.txt"
    if cmp -s "$LOGS/image_files_$e.txt" "$LOGS/zip_files_$e.txt"; then
      echo "identical: $(wc -l < "$LOGS/zip_files_$e.txt") files"
    else
      echo "DIFFERENT"; diff "$LOGS/zip_files_$e.txt" "$LOGS/image_files_$e.txt" | head -20
    fi
  done
  echo "== base images"
  dk image inspect python:3.12-slim-bookworm --format '{{.Id}} {{json .RepoDigests}}'
  dk image inspect ghcr.io/astral-sh/uv:0.13.1 --format '{{.Id}} {{json .RepoDigests}}'
  dk image ls --no-trunc
}

smoke() {
  local e c
  for e in oxylabs scrapedo; do
    c=(dk run --rm --network none --read-only --tmpfs /tmp "$(img "$e")")
    step "smoke_${e}_version" 0 -- "${c[@]}" --version
    step "smoke_${e}_help" 0 -- "${c[@]}" --help
    step "smoke_${e}_default_command" 0 -- dk run --rm --network none --read-only --tmpfs /tmp "$(img "$e")"
    # No key in the container: refused with exit 3 (CREDENTIALS), the output saying the key is not configured.
    step "smoke_${e}_require_credentials" 3 -- "${c[@]}" validate-config --require-credentials
  done
}

fresh() {  # a new isolated database per edition: the schema check fails, db-upgrade, then everything passes
  local e db
  for e in oxylabs scrapedo; do
    db="walmart_q168d_c_$e"
    if [ "$(sudo -n -u postgres psql -Atc "select count(*) from pg_database where datname = '$db'")" = 0 ]; then
      sudo -n -u postgres createdb -O walmart_q167 "$db"
    fi
    dk volume create "q168ddata_$e"
    step "c_${e}_check_db_before" 2 -- cdb "$e" "q168ddata_$e" "$db" -- validate-config --check-db
    step "c_${e}_db_upgrade" 0 -- cdb "$e" "q168ddata_$e" "$db" -- db-upgrade
    step "c_${e}_check_db" 0 -- cdb "$e" "q168ddata_$e" "$db" -- validate-config --check-db
    step "c_${e}_db_upgrade_again" 0 -- cdb "$e" "q168ddata_$e" "$db" -- db-upgrade
    step "c_${e}_sync_config" 0 -- cdb "$e" "q168ddata_$e" "$db" -- sync-config
    step "c_${e}_status" 0 -- cdb "$e" "q168ddata_$e" "$db" -- status
    psqlq "$db" "select version_num from alembic_version" > "$LOGS/c_${e}_alembic.txt" 2>&1
    psqlq "$db" "select key, enabled from stores order by 1" >> "$LOGS/c_${e}_alembic.txt" 2>&1
  done
}

replay_id() {  # the newest replay of a source run, in the campaign database or the one named second
  psqlq "${2:-walmart_q168d_c_campaign}" "select id from runs where mode = 'REPLAY' and config_snapshot->'replay'->>'source_run' = '$1' order by created_at desc limit 1"
}

campaign() {  # the private campaign copy: two stored live runs replayed by the Oxylabs image
  local db=walmart_q168d_c_campaign src rp
  if [ "$(sudo -n -u postgres psql -Atc "select count(*) from pg_database where datname = '$db'")" = 0 ]; then
    sudo -n -u postgres createdb -O walmart_q167 "$db"
    step campaign_restore 0 -- pg_restore -h "$DBHOST" -U walmart_q167 -d "$db" --no-owner --no-privileges --exit-on-error "$IN/campaign_live150.dump"
  fi
  dk volume create q168dcampaign
  # a copy the image's user (uid 10001) can read: the uploaded file is mode 600 (attempt 1 of this stage failed on it)
  mkdir -p "$D/in" && rm -f "$D/in/stored_live_L10_L12.tar" && install -m 644 "$IN/stored_live_L10_L12.tar" "$D/in/stored_live_L10_L12.tar" || return 1
  [ "$(sha256sum "$D/in/stored_live_L10_L12.tar" | cut -d" " -f1)" = "$TAR_SHA" ] || { echo "tar sha"; return 1; }
  step campaign_load_pages 0 -- dk run --rm --network none -v q168dcampaign:/app/data -v "$D/in:/in:ro" --entrypoint tar "$(img oxylabs)" -xf /in/stored_live_L10_L12.tar -C /app/data
  psqlq "$db" "select mode, status, count(*) from runs group by 1, 2 order by 1, 2" > "$LOGS/campaign_runs_before.txt"
  step campaign_check_db 0 -- cdb oxylabs q168dcampaign "$db" -- validate-config --check-db
  step campaign_db_upgrade 0 -- cdb oxylabs q168dcampaign "$db" -- db-upgrade
  for src in "$L12" "$L10"; do
    step "replay_$src" any -- cdb oxylabs q168dcampaign "$db" -- replay --run "$src"
    rp=$(replay_id "$src"); echo "$src $rp" >> "$D/replays.txt"
    step "status_$rp" 0 -- cdb oxylabs q168dcampaign "$db" -- status --run "$rp"
    step "coverage_$rp" 0 -- cdb oxylabs q168dcampaign "$db" -- coverage-report --run "$rp" --out "/app/data/q168/coverage/$rp"
    step "coverage_source_$src" 0 -- cdb oxylabs q168dcampaign "$db" -- coverage-report --run "$src" --out "/app/data/q168/coverage/$src"
    step "export_$rp" 0 -- cdb oxylabs q168dcampaign "$db" -- export --run "$rp" --out "/app/data/q168/export/$rp"
    step "validate_export_$rp" any -- cdb oxylabs q168dcampaign "$db" -- validate-export --run "$rp"
  done
}

killresume() {  # L10 replayed in a fresh copy of the campaign database (a run is replayed once per database),
  # killed (SIGKILL) after some pages, then resumed by the ordinary command
  local db=walmart_q168d_c_killresume rp="" n=0 rc=9 i before
  local out="$LOGS/killresume.log"
  if [ "$(sudo -n -u postgres psql -Atc "select count(*) from pg_database where datname = '$db'")" = 0 ]; then
    sudo -n -u postgres createdb -O walmart_q167 "$db"
    step killresume_restore 0 -- pg_restore -h "$DBHOST" -U walmart_q167 -d "$db" --no-owner --no-privileges --exit-on-error "$IN/campaign_live150.dump"
  fi
  step killresume_check_db 0 -- cdb oxylabs q168dcampaign "$db" -- validate-config --check-db
  before=$(replay_id "$L10" "$db")
  {
    echo "$(date -u +%FT%TZ) start a replay of L10 ($L10), detached"
    dk run -d --name q168dreplay --network host --read-only --tmpfs /tmp -v q168dcampaign:/app/data --env-file "$D/pg.env" \
      -e "WALMART_COLLECTOR_DATABASE_URL=$(url "$db")" -e HTTP_PROXY=http://127.0.0.1:9 -e HTTPS_PROXY=http://127.0.0.1:9 \
      -e NO_PROXY=127.0.0.1,localhost "$(img oxylabs)" replay --run "$L10"
    for _ in $(seq 1 1200); do
      rp=$(replay_id "$L10" "$db")
      if [ -n "$rp" ] && [ "$rp" != "$before" ]; then
        n=$(psqlq "$db" "select count(*) from page_fetches where run_id = '$rp'")
        [ "${n:-0}" -ge 120 ] && break
      fi
      sleep 0.1
    done
    echo "$(date -u +%FT%TZ) replay run $rp has $n pages read: SIGKILL"
    echo "running: $(dk inspect q168dreplay --format '{{.State.Running}}')"
    dk kill --signal=KILL q168dreplay
    dk inspect q168dreplay --format 'exit code {{.State.ExitCode}} oom {{.State.OOMKilled}}'
    dk logs q168dreplay 2>&1 | tail -3 | cut -c1-300
    dk rm q168dreplay
    echo "--- the state after the kill"
    psqlq "$db" "select status, stop_code from runs where id = '$rp'"
    psqlq "$db" "select state, count(*) from tasks where run_id = '$rp' group by 1 order by 1"
    echo "pages read $(psqlq "$db" "select count(*) from page_fetches where run_id = '$rp'") records $(psqlq "$db" "select count(*) from records where run_id = '$rp'")"
    echo "--- resume: repeated only while it is refused because the dead worker's lease holds (exit 9)"
    for i in $(seq 1 40); do
      cdb oxylabs q168dcampaign "$db" -- resume --run "$rp" > "$LOGS/killresume_attempt_$i.log" 2>&1
      rc=$?
      echo "$(date -u +%FT%TZ) resume attempt $i: exit $rc"
      tail -1 "$LOGS/killresume_attempt_$i.log" | cut -c1-400
      [ "$rc" -eq 9 ] || break
      sleep 15
    done
    echo "--- the state after the resume"
    psqlq "$db" "select status, stop_code from runs where id = '$rp'"
    psqlq "$db" "select state, count(*) from tasks where run_id = '$rp' group by 1 order by 1"
    echo "pages read $(psqlq "$db" "select count(*) from page_fetches where run_id = '$rp'") records $(psqlq "$db" "select count(*) from records where run_id = '$rp'")"
    echo "pages read twice: $(psqlq "$db" "select count(*) from (select url, purpose from page_fetches where run_id = '$rp' group by 1, 2 having count(*) > 1) d")"
    echo "L10-killed $rp $db" >> "$D/replays_killresume.txt"
  } > "$out" 2>&1
  step "export_killed_$rp" 0 -- cdb oxylabs q168dcampaign "$db" -- export --run "$rp" --out "/app/data/q168/export/$rp"
  step "coverage_killed_$rp" 0 -- cdb oxylabs q168dcampaign "$db" -- coverage-report --run "$rp" --out "/app/data/q168/coverage/$rp"
  echo "$(date -u +%TZ) killresume: last resume exit $rc"
}

pages_all() {  # the other 22 runs' stored pages: validate-export checks every record against its own page
  local db=walmart_q168d_c_campaign rp
  [ "$(sha256sum "$IN/stored_live_other22.tar" | cut -d' ' -f1)" = "$TAR2_SHA" ] || { echo "tar2 sha"; return 1; }
  rm -f "$D/in/stored_live_other22.tar" && install -m 644 "$IN/stored_live_other22.tar" "$D/in/stored_live_other22.tar" || return 1
  step campaign_load_pages_other22 0 -- dk run --rm --network none -v q168dcampaign:/app/data -v "$D/in:/in:ro" --entrypoint tar "$(img oxylabs)" -xf /in/stored_live_other22.tar -C /app/data
  for rp in $(awk '{print $2}' "$D/replays.txt"); do
    step "validate_export_all_pages_$rp" 0 -- cdb oxylabs q168dcampaign "$db" -- validate-export --run "$rp"
  done
  if [ -s "$D/replays_killresume.txt" ]; then
    rp=$(awk 'NR==1 {print $2}' "$D/replays_killresume.txt"); local kdb; kdb=$(awk 'NR==1 {print $3}' "$D/replays_killresume.txt")
    step "validate_export_all_pages_$rp" 0 -- cdb oxylabs q168dcampaign "$kdb" -- validate-export --run "$rp"
  fi
}

rollback() {  # the published 1.6.6 edition, built as an image, against the database 1.6.8 migrated; then 1.6.8
  local db=walmart_q168d_c_campaign old="$SRC/walmart-oxylabs-1.6.6" image=walmart-collector-q168d:1.6.6-oxylabs rp
  rp=$(awk 'NR==1 {print $2}' "$D/replays.txt")
  [ "$(sha256sum "$IN/WALMART_OXYLABS_SOURCE_1.6.6.zip" | cut -d' ' -f1)" = "$OLD_ZIP_SHA" ] || { echo "1.6.6 zip sha"; return 1; }
  [ -d "$old" ] || python3 -m zipfile -e "$IN/WALMART_OXYLABS_SOURCE_1.6.6.zip" "$SRC" || return 1
  grep -q "\"commit\": \"$OLD_COMMIT\"" "$old/BUILD_INFO.json" || { echo "1.6.6 build info"; return 1; }
  step build_rollback166 0 -- bash -c "cd '$old' && sudo -n env DOCKER_CONFIG='$D/cli' DOCKER_BUILDKIT=0 '$(bin docker)' -H 'unix://$EXEC/docker.sock' build --network host --build-arg SOURCE_COMMIT=$OLD_COMMIT --build-arg BUILT_AT=\$(date -u +%FT%TZ) -t '$image' ."
  step rollback166_image 0 -- dk image inspect "$image" --format 'id {{.Id}} created {{.Created}}'
  step rollback166_version 0 -- dk run --rm --network none --read-only --tmpfs /tmp "$image" --version
  step rollback166_check_db 0 -- cdbi "$image" q168dcampaign "$db" -- validate-config --check-db
  step rollback166_status 0 -- cdbi "$image" q168dcampaign "$db" -- status --store walmart-3891-pickup
  step "rollback166_status_$rp" 0 -- cdbi "$image" q168dcampaign "$db" -- status --run "$rp"
  step "rollback166_export_$rp" 0 -- cdbi "$image" q168dcampaign "$db" -- export --run "$rp" --out "/app/data/q168/export_rollback166/$rp"
  step rollforward168_check_db 0 -- cdb oxylabs q168dcampaign "$db" -- validate-config --check-db
  step rollforward168_status 0 -- cdb oxylabs q168dcampaign "$db" -- status --store walmart-3891-pickup
}

coverage_live() {  # 1.6.8's coverage report of each live run of the 1.6.x campaign: the 1.6.8 W4 tables' inputs
  local db=walmart_q168d_c_campaign x label id
  psqlq "$db" "select id, mode, status, created_at from runs order by created_at" > "$LOGS/campaign_all_runs.txt"
  for x in $LIVE_RUNS; do
    label=${x%%=*}; id=${x#*=}
    step "coverage_live_$label" 0 -- cdb oxylabs q168dcampaign "$db" -- coverage-report --run "$id" --out "/app/data/q168/coverage_live/$id"
  done
}

volume_sums() {  # SHA-256 of every file this gate's replays wrote (exports and coverage), from the volume
  dk run --rm --network none -v q168dcampaign:/app/data --entrypoint sh "$(img oxylabs)" -c 'cd /app/data/q168 && find . -type f | LC_ALL=C sort | xargs sha256sum'
}

persist() {  # the daemon restarted: images, volumes, the database and the files written before are still there
  local db=walmart_q168d_c_campaign rp
  volume_sums > "$LOGS/volume_before_restart.txt"
  local kdb krp
  krp=$(awk 'NR==1 {print $2}' "$D/replays_killresume.txt" 2>/dev/null); kdb=$(awk 'NR==1 {print $3}' "$D/replays_killresume.txt" 2>/dev/null)
  for rp in $(awk '{print $2}' "$D/replays.txt"); do
    cdb oxylabs q168dcampaign "$db" -- status --run "$rp" > "$LOGS/status_before_restart_$rp.json" 2>&1
  done
  [ -n "$krp" ] && cdb oxylabs q168dcampaign "$kdb" -- status --run "$krp" > "$LOGS/status_before_restart_$krp.json" 2>&1
  step daemon_stop 0 -- stop
  step daemon_start_again 0 -- start
  step after_restart_images 0 -- dk image ls
  step after_restart_volumes 0 -- dk volume ls
  volume_sums > "$LOGS/volume_after_restart.txt"
  step after_restart_volume_unchanged 0 -- cmp "$LOGS/volume_before_restart.txt" "$LOGS/volume_after_restart.txt"
  for rp in $(awk '{print $2}' "$D/replays.txt"); do
    step "after_restart_status_$rp" 0 -- cdb oxylabs q168dcampaign "$db" -- status --run "$rp"
    step "after_restart_export_$rp" 0 -- cdb oxylabs q168dcampaign "$db" -- export --run "$rp" --out "/app/data/q168/export_after_restart/$rp"
  done
  if [ -n "$krp" ]; then
    step "after_restart_status_$krp" 0 -- cdb oxylabs q168dcampaign "$kdb" -- status --run "$krp"
    step "after_restart_export_$krp" 0 -- cdb oxylabs q168dcampaign "$kdb" -- export --run "$krp" --out "/app/data/q168/export_after_restart/$krp"
  fi
  step after_restart_fresh_status_oxylabs 0 -- cdb oxylabs q168ddata_oxylabs walmart_q168d_c_oxylabs -- status
  step after_restart_fresh_status_scrapedo 0 -- cdb scrapedo q168ddata_scrapedo walmart_q168d_c_scrapedo -- status
  volume_sums > "$LOGS/volume_final.txt"
}

collect() {  # the evidence of the volumes, to the host
  dk run --rm --network none -v q168dcampaign:/app/data --entrypoint sh "$(img oxylabs)" -c 'cd /app/data && tar -czf - q168' > "$D/out/campaign_volume_q168.tar.gz"
  sha256sum "$D/out/campaign_volume_q168.tar.gz"
  dk system df
  dk image ls --no-trunc > "$LOGS/images_final.txt"
  dk volume ls > "$LOGS/volumes_final.txt"
  psqlq walmart_q168d_c_campaign "select mode, status, count(*) from runs group by 1, 2 order by 1, 2" > "$LOGS/campaign_runs_after.txt"
  psqlq walmart_q168d_c_killresume "select mode, status, count(*) from runs group by 1, 2 order by 1, 2" > "$LOGS/killresume_runs_after.txt"
}

after() {  # stop, remove what the gate made, compare the host with its state before
  stop
  # the gate dockerd's bind mount of the host network namespace (containers run with --network host) outlives it
  findmnt -rn -o TARGET | grep "^$EXEC/" | sort -r | while read -r m; do echo "unmount $m"; sudo -n umount "$m"; done
  sudo -n rm -rf "$D/root" "$D/containerd-root" "$D/containerd-opt" "$D/cli" "$EXEC"
  rm -f "$D/pg.env"
  host_state > "$LOGS/host_after.txt" 2>&1
  diff "$LOGS/host_before.txt" "$LOGS/host_after.txt" && echo "host state unchanged"
}

wprep() {  # the session's own start: the gate's daemon gone, the inputs as the gate checked them, the password file
  date -u +%FT%TZ > "$D/walk_session/started_at.txt"
  if pgrep -a -f "$D/daemon.json|$D/containerd.toml"; then echo "a daemon of the gate is still running"; return 1; fi
  host_state > "$LOGS/host_before.txt" 2>&1
  for e in oxylabs scrapedo; do
    [ "$(sha256sum "${ZIP[$e]}" | cut -d' ' -f1)" = "${WANT[$e]}" ] || { echo "zip sha $e"; return 1; }
    grep -q "\"commit\": \"$COMMIT\"" "$SRC/walmart-$e-$REL/BUILD_INFO.json" || { echo "build info $e"; return 1; }
  done
  [ "$(sha256sum "$IN/campaign_live150.dump" | cut -d' ' -f1)" = "$DUMP_SHA" ] || { echo "dump sha"; return 1; }
  [ "$(sha256sum "$D/in/stored_live_L10_L12.tar" | cut -d' ' -f1)" = "$TAR_SHA" ] || { echo "tar sha"; return 1; }
  [ "$(sha256sum "$IN/WALMART_OXYLABS_SOURCE_1.6.6.zip" | cut -d' ' -f1)" = "$OLD_ZIP_SHA" ] || { echo "1.6.6 zip sha"; return 1; }
  grep -q "\"commit\": \"$OLD_COMMIT\"" "$SRC/walmart-oxylabs-1.6.6/BUILD_INFO.json" || { echo "1.6.6 build info"; return 1; }
  umask 077; printf 'PGPASSWORD=%s\n' "$PGPASSWORD" > "$D/pg.env"; umask 022
  echo "inputs as the gate checked them; the gate's daemon is not running"
}

build166() {  # the published 1.6.6 Oxylabs edition, built as the gate's rollback stage built it
  local old="$SRC/walmart-oxylabs-1.6.6" image=walmart-collector-q168d:1.6.6-oxylabs
  step build_rollback166 0 -- bash -c "cd '$old' && sudo -n env DOCKER_CONFIG='$D/cli' DOCKER_BUILDKIT=0 '$(bin docker)' -H 'unix://$EXEC/docker.sock' build --network host --build-arg SOURCE_COMMIT=$OLD_COMMIT --build-arg BUILT_AT=\$(date -u +%FT%TZ) -t '$image' ."
  step rollback166_image 0 -- dk image inspect "$image" --format 'id {{.Id}} created {{.Created}}'
}

walk() {  # the recorded English walkthrough (asciinema; walkthrough_168.sh is the script recorded)
  local W="$IN/walk" cast="$D/out/WALKTHROUGH_1.6.8.cast"
  # the gate's failed recording is kept, under another name
  [ -f "$cast" ] && [ ! -f "$D/out/WALKTHROUGH_1.6.8_GATE_FAILED.cast" ] && mv "$cast" "$D/out/WALKTHROUGH_1.6.8_GATE_FAILED.cast"
  export D EXEC IN BASE REL COMMIT L12 L10 DBHOST PKG
  # asciinema runs the command through sh (dash), which drops exported bash functions: the walkthrough sources them
  declare -f bin dk img url psqlq cdbi cdb replay_id > "$BASE/walk_helpers.sh"
  bash -c ". '$BASE/walk_helpers.sh' && type bin dk img url psqlq cdbi cdb > /dev/null && echo 'helpers usable'" || return 1
  "$W/venv/bin/asciinema" rec --overwrite -q -i 2 --cols 120 --rows 36 -c "bash $BASE/walkthrough_168.sh" "$cast"
  echo "rec-exit $?"
  sha256sum "$cast"
  # judged by its output: a command or a file the recording could not find fails the step
  if grep -q -E "command not found|No such file or directory" "$cast"; then
    echo "the recording shows a failure:"
    grep -o -E ".{0,100}(command not found|No such file or directory).{0,40}" "$cast" | head -20
    return 1
  fi
  echo "no 'command not found' and no 'No such file or directory' in the recording"
}

case "${1:-}" in
  wprep) step wprep 0 -- wprep ;;
  start) step daemon_start 0 -- start ;;
  build) build ;;
  build166) build166 ;;
  image) step image_report 0 -- image_report ;;
  walk) step walk 0 -- walk ;;
  stop) step daemon_stop_final 0 -- stop ;;
  after) step after 0 -- after ;;
  *) echo "usage: $0 wprep|start|build|build166|image|walk|stop|after"; exit 2 ;;
esac
