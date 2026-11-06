#!/usr/bin/env bash
# Owner VM, release 1.6.8, fourth candidate (commit 85c29e7): the Linux suite and the two fail-befores
# (vm_full_168d.sh); only if every suite step exited 0, the container gate's stages one after the other (the
# walkthrough is recorded while the gate's daemon runs, before collect and after), then the qualification of the two
# edition ZIPs (vm_qual_168d.sh), then the delivered Classic probe 1.7.2 from a clean extraction (vm_probe_172.sh).
# One heavy job at a time: the VM has 3.9 GB of RAM. Refuses to start while a job of the second candidate's run
# (~/q168: drive168b.sh, its suite, gate, daemon or qualification) is still running.
cd "$HOME/q168d" || exit 1
if pgrep -a -f "drive168b.sh|vm_full_168b.sh|vm_docker_168.sh|vm_qual_168.sh|vm_full_168.sh|/run/q168docker/" ; then
  echo "!! a job of the second candidate's run is still running: nothing started"
  exit 1
fi
echo "== suite $(date -u +%H:%M:%SZ)"
bash vm_full_168d.sh > vm_full_168d.out 2>&1
echo "suite script exit $? $(date -u +%H:%M:%SZ)"
if ! grep -q "^ALL DONE" FULL_1.6.8d_LINUX.log || grep -qE "^(sync )?exit [1-9]" FULL_1.6.8d_LINUX.log; then
  echo "!! the suite of 85c29e7 did not pass: the gate, the qualification and the probe run are not started"
  exit 1
fi
gate_ok=1
for st in prep start build image smoke fresh campaign killresume pages_all rollback persist coverage_live walk collect after; do
  if [ "$gate_ok" = 0 ] && [ "$st" != after ]; then echo "== $st skipped: an earlier stage did not pass"; continue; fi
  echo "== $st $(date -u +%H:%M:%SZ)"
  n0=$(wc -l < docker/steps.jsonl 2>/dev/null || echo 0)
  bash vm_docker_168d.sh "$st"
  case "$st" in
    prep|start|build|image)  # the stages the rest needs: stop the gate when one of their steps did not pass
      if tail -n +"$((n0 + 1))" docker/steps.jsonl | grep -q '"pass_by_exit": false'; then gate_ok=0; echo "!! $st did not pass"; fi ;;
  esac
done
echo "gate done $(date -u +%H:%M:%SZ)"
echo "== qual $(date -u +%H:%M:%SZ)"
bash vm_qual_168d.sh > qual_driver.log 2>&1
echo "qual exit $? done $(date -u +%H:%M:%SZ)"
echo "== probe 1.7.2 $(date -u +%H:%M:%SZ)"
bash vm_probe_172.sh > probe172_driver.log 2>&1
echo "probe exit $? done $(date -u +%H:%M:%SZ)"
