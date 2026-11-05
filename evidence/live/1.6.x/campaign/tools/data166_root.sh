#!/usr/bin/env bash
# A slim root for assemble_data_166.py: the files it reads from each 1.6.x run folder (the published 1.6.5 folders of
# /c/w9/repo, and L12 from the staged publication /c/w9/pub166) and the regenerated shared-ledger reservations.
# usage: data166_root.sh OUT_ROOT
set -euo pipefail
OUT=$1
[ ! -e "$OUT" ] || { echo "exists: $OUT"; exit 2; }
NEED="db/runs.csv db/collection_segments.csv db/provider_usage.csv db/node_coverage.csv db/page_fetches.csv
exports/manifest.json exports/validation_report.json exports/products_fresh.json exports/products_fresh.csv
exports/products.json exports/products.csv"
copy_run() {
  local src=$1 name
  name=$(basename "$src")
  for f in $NEED; do
    if [ -f "$src/$f" ]; then
      mkdir -p "$OUT/evidence/live/1.6.x/runs/$name/$(dirname "$f")"
      cp -p "$src/$f" "$OUT/evidence/live/1.6.x/runs/$name/$f"
    fi
  done
}
for d in /c/w9/repo/evidence/live/1.6.x/runs/*/; do copy_run "${d%/}"; done
copy_run /c/w9/pub166/evidence/live/1.6.x/runs/L12_01M6MC7YE4PBXV88G3PJ5ENW4B
mkdir -p "$OUT/evidence/live/1.6.x/campaign/shared_ledger"
cp -p /c/w9/scratch/campaign166/shared_ledger/reservations.csv "$OUT/evidence/live/1.6.x/campaign/shared_ledger/"
find "$OUT" -type f | wc -l
