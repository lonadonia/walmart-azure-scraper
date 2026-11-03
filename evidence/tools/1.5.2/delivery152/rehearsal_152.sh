#!/usr/bin/env bash
# A REHEARSAL of the 1.5.2 delivery build, in C:/w7/rh152 only: evidence tree and ZIP, manifest, index, spec, assemble,
# then the verifier's data step. Second form (21:30Z): the owner VM's real files are in C:/w7/stage152 now, so the overlay
# holds only the generated manifest and index. Nothing here goes into deliverables/ or C:/w7/stage152.
set -u
H=/c/w7/rh152
P=$H/progress.txt
VPY=/c/w7/wt/headless/walmart-azure-headless/.venv/Scripts/python.exe
PY=/c/w6/py312/pkg/tools/python.exe
export UV_PYTHON='C:\w6\py312\pkg\tools\python.exe'
D="C:/w7/rh152/del/20261102_walmart_1.5.2"
step() { echo "$(date -u +%TZ) $*" >> "$P"; }
fail() { step "FAILED: $*"; exit 1; }
mkdir -p $H/overlay
step "start (second form: real VM files)"
step "evidence tree"
$VPY -I -X utf8 C:/w7/tools/delivery152/assemble_evidence_152.py C:/w7/rh152/ev_tree > $H/assemble_evidence.log 2>&1 || fail "evidence tree (assemble_evidence.log)"
step "evidence zip"
(cd /c/w7/wt && $PY -I -X utf8 scripts/build_walmart_152_delivery.py zip-evidence C:/w7/rh152/ev_tree C:/w7/rh152/pack_ev) > $H/zip.log 2>&1 || fail "zip (zip.log)"
EVZ=C:/w7/rh152/pack_ev/WALMART_EVIDENCE_1.5.2.zip
step "manifest"
$PY -I -X utf8 C:/w7/tools/docs152/source_run_manifest_152.py C:/w7/pack152f/src/WALMART_SOURCE_1.5.2.zip $EVZ \
  C:/w7/pack152g/probe/OXYLABS_CLASSIC_OFFLINE_PROBE_1.5.2.zip \
  "<repository>/deliverables/20261101_walmart_1.5.1/live/RUN_SUMMARY.json" \
  C:/w7/wt pending C:/w7/rh152/overlay/SOURCE_AND_RUN_MANIFEST.json > $H/manifest.log 2>&1 || fail "manifest (manifest.log)"
step "index"
$PY -I -X utf8 C:/w7/tools/docs152/fill_index_152.py $EVZ 20261102_walmart_1.5.2 2026-11-02 C:/w7/plan152/vm_milestones.json \
  C:/w7/rh152/overlay/DELIVERY_INDEX.md > $H/index.log 2>&1 || fail "index (index.log)"
step "spec"
OVERLAY152='C:\w7\rh152\overlay' EVZIP152="$EVZ" $PY -I -X utf8 C:/w7/tools/delivery152/assemble_spec_152.py "$D" C:/w7/rh152/spec.json > $H/spec.log 2>&1 || fail "spec (spec.log)"
step "assemble"
(cd /c/w7/wt && $PY -I -X utf8 scripts/build_walmart_152_delivery.py assemble C:/w7/rh152/spec.json) > $H/assemble.log 2>&1 || fail "assemble (assemble.log)"
step "verifier data step"
bash /c/w7/tools/delivery152/vstep152.sh "$D" C:/w7/rh152/v data >> $H/data_step.log 2>&1
step "DONE"
