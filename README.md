# Walmart collector 1.6.5: correction delivery for review

This is a correction delivery for the client's review. It is not a final release, and it has not been accepted.

**Target:** Walmart #3891, 3900 Fountain Square Pl, Waukegan, IL 60085, **PICKUP**.

**Collector:** release 1.6.5, commit `67d216eb8ee2ec839a437b0b5bf2d594324b6982` (2026-11-04T14:15:19Z). That commit is
the frozen tree in `source/`, in two provider editions. The tag `review-1.6.5-20261104` points to this repository's
publication commit, which is a different commit: it adds the layout, guides and manifests around the tree and
changes no collector file. The earlier delivery stays at its own tag, `review-1.5.2-20261103`.

## Status

**Corrections verified; named milestones still pending.**

- **Every point of the client's two latest reviews is corrected**, with its tests and evidence: the four deal fields
  always `""`, UPC and size provenance, the sponsored and variant decisions, coverage and partitions, retention and
  recovery, and the Classic findings C1 to C5 (probe 1.7.0, live mode disabled). See the
  [correction map](review/CORRECTION_MAP.md) and the [requirement matrix](review/REQUIREMENT_MATRIX.md).
- **The final release 1.6.5 is verified from clean extractions of both editions:** 533 unit and 200 integration
  tests passed in each, with ruff, format and mypy clean, and the last-good publication check passed.
- **Live, in the developer environment** (the user's Oxylabs Web API trial, from the workstation): fourteen runs on
  releases 1.6.0 to 1.6.5, each attributed to the release that ran it. The census L10 on 1.6.4 gave 7,055 fresh valid
  products with detail reading off; its export passes the final release's check, and 1.6.5's live canary passed.
  The last detail-on demonstration is L8 on 1.6.3 (675 fresh valid).
- **Still pending:** the full catalogue (no CSV row is complete; the rest is priced at about USD 4.07 of listing
  pages plus product pages), a detail-on run of 1.6.5 (at most about USD 0.07), anything in the client's Azure
  environment (the VM is deallocated; access waits for the client), an observed schedule, Scrape.do live, and a live
  Classic successor. The [test plan](review/TEST_PLAN.md) and the [milestones](review/MILESTONES.md) give each with
  its condition.
- **Spending:** Walmart's share of the trial allowance is used (USD 2.2275 committed of USD 2.25), and the Oxylabs
  ceiling is 0. Nothing ran in the client's environment, and no schedule is on.

## Contents

| Path | What it holds |
|---|---|
| [`source/`](source/) | Collector 1.6.5 in two editions, Oxylabs Web API and Scrape.do ([about](source/README.md), [operations](source/walmart-oxylabs-1.6.5/docs/OPERATIONS.md), [verification report](source/walmart-oxylabs-1.6.5/docs/VERIFICATION.md)) |
| [`classic-probe-1.7.0/`](classic-probe-1.7.0/) | The shared offline Classic probe 1.7.0: the client's findings C1 to C5 corrected ([start here](classic-probe-1.7.0/README_FIRST.md), [what changed](review/CLASSIC_PROBE_CORRECTIONS.md)) |
| [`classic-probe/`](classic-probe/) | The Walmart probe 1.5.2 the client reviewed, unchanged |
| [`review/`](review/) | [Technical report](review/TECHNICAL_REPORT.md), [requirement matrix](review/REQUIREMENT_MATRIX.md), [correction map](review/CORRECTION_MAP.md), [milestones](review/MILESTONES.md), [acceptance matrix](review/ACCEPTANCE_MATRIX.csv), [runbook](review/ACCEPTANCE_RUNBOOK.md), [recovery and operations](review/RECOVERY_AND_OPERATIONS.md), [cost and runtime](review/COST_AND_RUNTIME_REPORT.md), [test plan and next live proposal](review/TEST_PLAN.md), [delivery index](review/DELIVERY_INDEX.md) |
| [`data/`](data/) | The live product files, one folder per run (`<stage>-<release that collected it>`) ([description](data/README.md)) |
| [`evidence/`](evidence/) | Live runs, the shared trial ledger, reconciliations, offline tests and verifications ([index](evidence/README.md)) |
| [`walkthrough/`](walkthrough/) | The 1.5.2 walkthrough on the owner's Azure test VM (no live run), unchanged |
| [`manifests/`](manifests/) | Checksums, file map, corrections, redactions, exclusions and the publication record |
| [`CHANGELOG.md`](CHANGELOG.md) | One entry per delivery, and how this repository is updated |

## Verify (offline, no request sent)

```
git clone https://github.com/lonadonia/walmart-azure-scraper.git && cd walmart-azure-scraper
git checkout review-1.6.5-20261104
sha256sum --quiet -c manifests/SHA256SUMS.txt && echo "checksums OK"
python3 manifests/check_frozen_trees.py   # source/ and both probes: the delivered archives, file for file
python3 manifests/check_data.py           # data/: the runs' own exports, 22 fields, deal fields, counts, lineage
cp -r source ../walmart-source-1.6.5 && cd ../walmart-source-1.6.5/walmart-oxylabs-1.6.5
uv sync --frozen && uv run --frozen walmart-collector --version   # walmart-azure-headless 1.6.5
uv run --frozen python -m pytest -q tests/unit
```

- Each check ends with `PASS`.
- Copy `source/` out of the clone before installing, so that the checks stay true.
- The [acceptance runbook](review/ACCEPTANCE_RUNBOOK.md) has the PowerShell form, the integration suite, the
  database migration, a container build, a run with its status, pause, resume, export and rollback, and where the
  data and the published dataset live.

## What was changed for this publication

`source/`, `classic-probe/` and `classic-probe-1.7.0/` hold the delivered archives' files, unchanged. Everywhere
else, paths are rewritten to this layout, and [`manifests/`](manifests/) records every other change:

| File | What it records |
|---|---|
| [`FILE_MAP.csv`](manifests/FILE_MAP.csv) | each file's origin, state and both SHA-256 values; a file carried unchanged from the 1.5.2 publication keeps the origin and state recorded there |
| [`DOC_CORRECTIONS.md`](manifests/DOC_CORRECTIONS.md) | the corrections made to the review documents and evidence notes |
| [`REDACTIONS.csv`](manifests/REDACTIONS.csv) | the redactions: workstation paths and names, and the credential's fingerprint |
| [`EXCLUDED.csv`](manifests/EXCLUDED.csv) | what was left out: the provider's unsanitized answers, internal drafts and redundant copies |
| [`PUBLICATION.json`](manifests/PUBLICATION.json) | the checks run before publication |
