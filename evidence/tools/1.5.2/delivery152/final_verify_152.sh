#!/usr/bin/env bash
# The final verification of the Walmart 1.5.2 delivery: every step in the verifier's order, one at a time.
#   bash final_verify_152.sh [FIRST_STEP]
# FIRST_STEP resumes after an interruption: the verifier keeps an earlier attempt's log, and its report counts the last.
D="<repository>/deliverables/20261102_walmart_1.5.2"
W='C:/w7/v2'
P=/c/w7/v2_progress.txt
FIRST=${1:-}
STEPS=/c/w7/v2_steps.txt
export UV_PYTHON='C:\w6\py312\pkg\tools\python.exe'
"<home>/.local/bin/uv.exe" run --no-project --with tzdata python -I -X utf8 -c "
import sys
sys.path.insert(0, r'C:\w7\wt\scripts')
import verify_walmart_152_delivery as v
print('\n'.join(v.ORDER))
" > "$STEPS" 2>/dev/null
n=$(wc -l < "$STEPS")
echo "$(date -u +%H:%M:%SZ) driver start: $n steps${FIRST:+, from $FIRST}" >> "$P"
[ "$n" -gt 80 ] || { echo "$(date -u +%H:%M:%SZ) FAILED: step list has $n lines" >> "$P"; exit 1; }
go=${FIRST:+0}; go=${go:-1}
while IFS= read -r s; do
  s=${s%$'\r'}
  [ "$s" = "$FIRST" ] && go=1
  [ "$go" = 1 ] || continue
  echo "$(date -u +%H:%M:%SZ) start $s" >> "$P"
  bash /c/w7/tools/delivery152/vstep152.sh "$D" "$W" "$s" >> "$P" 2>&1
done < "$STEPS"
echo "$(date -u +%H:%M:%SZ) steps finished" >> "$P"
echo "$(date -u +%H:%M:%SZ) DONE" >> "$P"
