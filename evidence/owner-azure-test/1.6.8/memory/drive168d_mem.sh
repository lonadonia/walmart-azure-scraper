#!/usr/bin/env bash
# Owner VM: after the walkthrough session (drive168d_walk.sh) ends, the memory measurement (vm_mem_168d.sh).
cd "$HOME/q168d" || exit 2
echo "waiting for the walkthrough session $(date -u +%FT%TZ)"
while pgrep -f "[b]ash drive168d_walk.sh" > /dev/null; do sleep 20; done
echo "walk session ended $(date -u +%FT%TZ); memory measurement starts"
bash "$HOME/q168d/vm_mem_168d.sh"
echo "MEM DONE exit $? $(date -u +%FT%TZ)"
