#!/usr/bin/env bash
# Windows workstation: WALMART_SOURCE_1.6.8.zip of commit 85c29e7 from a clean extraction (the steps after extract and
# the Bicep checks): each check in its own process, one after the other. Output to C:/w9/v168d.
set -u
PY=/c/w6/py312/pkg/tools/python.exe
V="$PY -I -X utf8 /c/w9/scratch/c168d/tools/verify168d_clean.py /c/w9/delivery168d/source/WALMART_SOURCE_1.6.8.zip C:/w9/v168d"
export UV_PYTHON='C:\w6\py312\pkg\tools\python.exe'
{
  echo "$(date -u +%FT%TZ) verify168d_clean.py on 85c29e7 source ZIP"
  for ed in oxylabs scrapedo; do
    for c in tree lock install ruff format mypy-m version-m help-m validate-config-m unit integration-affected; do
      echo "== $ed.$c $(date -u +%H:%M:%SZ)"
      $V "$ed.$c" 2>&1 | tail -2 | cut -c1-240
    done
  done
  $V report 2>&1 | tail -8 | cut -c1-240
  echo "ended $(date -u +%FT%TZ)"
} >> /c/w9/v168d/driver.log 2>&1
