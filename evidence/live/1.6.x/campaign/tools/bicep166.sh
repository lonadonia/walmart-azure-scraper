#!/usr/bin/env bash
# The Bicep build and lint of both 1.6.6 editions' azure/main.bicep, from the clean extraction of
# WALMART_SOURCE_1.6.6.zip (C:/w9/v166/src), as for 1.6.5 (BICEP_CHECKS.txt). No deployment: build and lint only.
# usage: bicep166.sh BICEP_EXE OUT_DIR
set -uo pipefail
BICEP=$1 OUT=$2
SRC=/c/w9/v166/src/walmart-source-1.6.6
WANT=398af294cf16ac4becdbd008a77d148d0e8e91492309a6b60ec911b7e1cab082
[ "$(sha256sum "$BICEP" | cut -d' ' -f1)" = "$WANT" ] || { echo "bicep sha mismatch"; exit 2; }
mkdir -p "$OUT/logs"
VER=$("$BICEP" --version 2>&1 | tr -d '\r')
{
  echo "Bicep checks of the azure/ templates of both 1.6.6 editions, from the clean extraction of WALMART_SOURCE_1.6.6.zip (C:/w9/v166/src), run beside the verifier (its Scrape.do integration suite was still running; the templates are only read); $VER, signed (Authenticode: Valid), sha256 $WANT. No deployment: build and lint only."
  for ed in oxylabs scrapedo; do
    cd "$SRC/walmart-$ed-1.6.6" || exit 2
    for step in build lint; do
      log="$OUT/logs/$ed.bicep-$step.log"
      at=$(date -u +%Y-%m-%dT%H:%M:%SZ)
      if [ $step = build ]; then cmd="bicep build azure/main.bicep --stdout"; "$BICEP" build azure/main.bicep --stdout > "$log" 2>&1; rc=$?
      else cmd="bicep lint azure/main.bicep"; "$BICEP" lint azure/main.bicep > "$log" 2>&1; rc=$?; fi
      echo "$ed.bicep-$step: \$ $cmd; started $at; exit $rc; log logs/$ed.bicep-$step.log ($(wc -c < "$log") bytes)"
    done
  done
} > "$OUT/BICEP_CHECKS.txt"
cat "$OUT/BICEP_CHECKS.txt"
