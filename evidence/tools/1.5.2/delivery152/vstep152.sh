#!/usr/bin/env bash
# Run verification steps of the Walmart 1.5.2 delivery one at a time, kept awake, in order; offline.
#   bash vstep152.sh DELIVERY WORK STEP [STEP ...]
#   STEP: a verifier step (data, source.extract, oxylabs.*, scrapedo.*, probe.*), or
#     collect  copies the record into DELIVERY/verification/;
#     report   writes DELIVERY/PACKAGE_VERIFICATION.txt, with the final secret scan.
#   NO_SECRET_VALUES=1 leaves out the local credential files (for a rehearsal only).
# The verifier runs on the signed CPython through uv with tzdata; extracted editions build from the signed CPython.
R="<repository>"
D=$1; W=$2; shift 2
export UV_PYTHON='C:\w6\py312\pkg\tools\python.exe'
export PSYCOPG_IMPL=python
UV="<home>/.local/bin/uv.exe"
L="$R/data/local"
SECRETS=""
for n in <local credential files>; do
  [ -f "$L/$n.env" ] && SECRETS="$SECRETS${SECRETS:+,}$L/$n.env"
done
BICEP='<home>\AppData\Local\Temp\<temp>\bicep\bicep.exe'
VERIFY="C:/w7/wt/scripts/verify_walmart_152_delivery.py"
awake() { /c/w6/py312/pkg/tools/python.exe -I C:/w6/tools/keep_awake.py "$UV" run --no-project --with tzdata python "$VERIFY" "$@"; }
for step in "$@"; do
  case "$step" in
    collect)
      awake collect "$D" "$W" 2>&1 | grep -v '^keep_awake:' | tail -3
      continue ;;
    report)
      awake "$D" "$W" report "--report=$D/PACKAGE_VERIFICATION.txt" \
        "--scanner=C:/w6/tools/secret_scan.py" 2>&1 | grep -v '^keep_awake:' | tail -3 | cut -c1-300
      continue ;;
  esac
  extra=()
  case "$step" in
    data)
      extra=("--scanner=C:/w6/tools/secret_scan.py" "--scanner2=C:/m5/tools170/keyscan170.py"
             "--rules=<local file>" "--personal=<local file>"
             "--earlier=$R/deliverables" "--other-deliveries=<local file>" "--outside-changes=<local file>"
             "--task-start=2026-11-01T18:20:00Z" "--pdf-renderer=C:/w6/tools/pdf_pages_png.ps1" "--repo=C:/w7/wt")
      [ -z "$NO_SECRET_VALUES" ] && extra+=("--secrets=<local credential files>") ;;
    *.bicep-build|*.bicep-lint|*bicep*) extra=("--bicep=$BICEP") ;;
  esac
  awake "$D" "$W" "$step" "${extra[@]}" 2>&1 | grep -v '^keep_awake:' | tail -1 | cut -c1-300
done
