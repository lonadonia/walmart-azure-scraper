#!/usr/bin/env bash
# The final build of the Walmart 1.5.2 delivery, 2026-11-02: evidence tree and ZIP, the packaging commit after a clean scan
# of the staged scripts, manifest, index, spec, assembly. Commits locally; pushes nothing. Offline.
set -u
H=/c/w7/pack152g
P=$H/build_progress.txt
VPY=/c/w7/wt/headless/walmart-azure-headless/.venv/Scripts/python.exe
PY=/c/w6/py312/pkg/tools/python.exe
export UV_PYTHON='C:\w6\py312\pkg\tools\python.exe'
FOLDER=20261102_walmart_1.5.2
D="<repository>/deliverables/$FOLDER"
OLD="<repository>/deliverables/20261101_walmart_1.5.1"
EVZ=C:/w7/pack152f/evidence/WALMART_EVIDENCE_1.5.2.zip
step() { echo "$(date -u +%TZ) $*" | tee -a "$P"; }
fail() { step "FAILED: $*"; exit 1; }
[ -e "$D" ] && fail "the delivery folder exists"
step "evidence tree"
$VPY -I -X utf8 C:/w7/tools/delivery152/assemble_evidence_152.py C:/w7/pack152f/ev_tree > $H/assemble_evidence.log 2>&1 || fail "evidence tree"
step "evidence zip"
(cd /c/w7/wt && $PY -I -X utf8 scripts/build_walmart_152_delivery.py zip-evidence C:/w7/pack152f/ev_tree C:/w7/pack152f/evidence) > $H/zip.log 2>&1 || fail "zip"
tail -1 $H/zip.log | cut -c1-160
step "scan of the staged scripts"
rm -rf C:/w7/plan152/staged_scan
$PY -I -X utf8 C:/w7/tools/delivery151/staged_scan.py C:/w7/plan152/staged_scan > $H/staged_scan.log 2>&1 || fail "staged scan"
(cd /c/w7/wt && $PY -I -X utf8 C:/w6/tools/secret_scan.py --staged) > $H/secret_scan.log 2>&1 || fail "secret scan"
tail -1 $H/staged_scan.log; tail -1 $H/secret_scan.log
step "packaging commit"
git -C /c/w7/wt commit -q -F C:/w7/plan152/commit_msg_152.txt || fail "commit"
REV=$(git -C /c/w7/wt rev-parse HEAD)
step "packaging commit $REV"
step "manifest"
$PY -I -X utf8 C:/w7/tools/docs152/source_run_manifest_152.py C:/w7/pack152f/src/WALMART_SOURCE_1.5.2.zip $EVZ \
  C:/w7/pack152g/probe/OXYLABS_CLASSIC_OFFLINE_PROBE_1.5.2.zip "$OLD/live/RUN_SUMMARY.json" \
  C:/w7/wt "$REV" C:/w7/stage152/SOURCE_AND_RUN_MANIFEST.json > $H/manifest.log 2>&1 || fail "manifest"
step "index"
$PY -I -X utf8 C:/w7/tools/docs152/fill_index_152.py $EVZ $FOLDER 2026-11-02 C:/w7/plan152/vm_milestones.json \
  C:/w7/stage152/DELIVERY_INDEX.md > $H/index.log 2>&1 || fail "index"
cat $H/index.log
step "spec"
$PY -I -X utf8 C:/w7/tools/delivery152/assemble_spec_152.py "$D" C:/w7/pack152g/spec.json > $H/spec.log 2>&1 || fail "spec"
cat $H/spec.log | cut -c1-160
step "assemble"
(cd /c/w7/wt && $PY -I -X utf8 scripts/build_walmart_152_delivery.py assemble C:/w7/pack152g/spec.json) > $H/assemble.log 2>&1 || fail "assemble"
tail -2 $H/assemble.log | cut -c1-200
step "BUILD DONE"
