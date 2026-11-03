#!/usr/bin/env bash
# The final revision's offline replays on the PC: new copies, B3, then the campaign twice.
P=/c/w7/wt/headless/walmart-azure-headless
PY=$P/.venv/Scripts/python.exe
cd "$P" || exit 1
L=/c/w7/ev152/logs
git -C /c/w7/wt rev-parse HEAD
git -C /c/w7/wt status --short | head -3
$PY -I -X utf8 /c/w7/tools/fresh_copy_152.py C:/w7/r152c > $L/fresh_copy_c.log 2>&1 || { echo "copy c failed"; exit 1; }
$PY -I -X utf8 /c/w7/tools/fresh_copy_152.py C:/w7/r152d > $L/fresh_copy_d.log 2>&1 || { echo "copy d failed"; exit 1; }
echo "copies done $(date -u +%TZ)"
export REPROC_DB=walmart_reproc152_a5 REPROC_OUT='C:\w7\ev152\final_b3' REPROC_EXPORT_NAME=export_replay_1_5_2
$PY -I -X utf8 /c/w7/tools/reproc150_setup.py start > $L/final_b3_setup.log 2>&1; echo "b3 setup exit $? $(date -u +%TZ)"
$PY -I -X utf8 /c/w7/tools/reproc150_run.py 1 7 > $L/final_b3_1.log 2>&1
$PY -I -X utf8 /c/w7/tools/reproc150_run.py 8 18 > $L/final_b3_2.log 2>&1; echo "b3 exit $? $(date -u +%TZ)"
unset REPROC_DB REPROC_OUT REPROC_EXPORT_NAME
$PY -I -X utf8 /c/w7/tools/reproc152_run.py C:/w7/r152c C:/w7/ev152/final_a1 > $L/final_a1.log 2>&1; echo "a1 exit $? $(date -u +%TZ)"
$PY -I -X utf8 /c/w7/tools/reproc152_run.py C:/w7/r152d C:/w7/ev152/final_a2 > $L/final_a2.log 2>&1; echo "a2 exit $? $(date -u +%TZ)"
