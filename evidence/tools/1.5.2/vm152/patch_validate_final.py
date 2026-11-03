from pathlib import Path

p = Path("C:/w7/tools/vm152/validate.sh")
t = p.read_bytes().decode("utf-8")


def sub(a, b):
    global t
    assert t.count(a) == 1, (a[:70], t.count(a))
    t = t.replace(a, b)


# 1. The replay chain: a graceful stop in S4, a forced kill in S6, each at a real point of the run.
sub(
    """  for stage in S1 S2 S3 S4 S5b_serial S5b_parallel S5a; do
    src=$(python3 -c "import json;print(json.load(open('$V/pkg/runs.json'))['$stage'])")
    step "c_replay_$stage" cli replay --run "$src"
    rp=$(grep -oE '"run(_id)?": ?"01[0-9A-Z]{24}"' "$LOGS/c_replay_$stage.log" | grep -oE '01[0-9A-Z]{24}' | grep -v "$src" | head -1)
    echo "$stage $rp" >> "$V/replay/replay_runs.txt"
  done
  kill_and_resume S6
  stage=S7
  src=$(python3 -c "import json;print(json.load(open('$V/pkg/runs.json'))['$stage'])")
  step "c_replay_$stage" cli replay --run "$src"
  rp=$(grep -oE '"run(_id)?": ?"01[0-9A-Z]{24}"' "$LOGS/c_replay_$stage.log" | grep -oE '01[0-9A-Z]{24}' | grep -v "$src" | head -1)
  echo "$stage $rp" >> "$V/replay/replay_runs.txt"
""",
    """  for stage in S1 S2 S3 S4 S5b_serial S5b_parallel S5a S6 S7; do
    case "$stage" in
      S4) interrupt_and_resume S4 TERM 6; continue ;;
      S6) interrupt_and_resume S6 KILL 6; continue ;;
    esac
    src=$(python3 -c "import json;print(json.load(open('$V/pkg/runs.json'))['$stage'])")
    step "c_replay_$stage" cli replay --run "$src"
    rp=$(grep -oE '"run(_id)?": ?"01[0-9A-Z]{24}"' "$LOGS/c_replay_$stage.log" | grep -oE '01[0-9A-Z]{24}' | grep -v "$src" | head -1)
    echo "$stage $rp" >> "$V/replay/replay_runs.txt"
  done
""",
)
# 2. The interruption itself.
start = t.index("# A forced kill in the middle of a replay")
end = t.index("# The frozen Classic probe from its ZIP alone")
new = r"""# A signal in the middle of a replay, then the real recovery commands: a resume refused while the dead worker's lease
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

"""
t = t[:start] + new + t[end:]
# 3. A reset of what the earlier revision left: its containers, volumes and network. The VM's own databases are not touched.
sub(
    """case "${1:-}" in
  prep) step prepare0 prepare ;;
""",
    """reset_docker() {
  sudo docker rm -f v152replay "$PG" 2>/dev/null
  sudo docker network rm "$NET" 2>/dev/null
  sudo docker volume rm v152pgdata v152data 2>/dev/null
  sudo docker ps -a --format '{{.Names}}'; sudo docker volume ls -q; sudo docker network ls --format '{{.Name}}'
}

case "${1:-}" in
  reset) step reset_docker reset_docker ;;
  prep) step prepare0 prepare ;;
""",
)
sub(
    """  chain) replay_chain ;;
""",
    "",
)
p.write_bytes(t.encode("utf-8"))
print("patched")
