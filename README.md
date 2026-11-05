# Walmart collector 1.6.6: correction delivery for review

This is a correction delivery for the client's review. It is not a final release, and it has not been accepted.

**Target:** Walmart #3891, 3900 Fountain Square Pl, Waukegan, IL 60085, **PICKUP**.

**Collector:** release 1.6.6, commit `39cc61f61ee694c0659a611310605bee6ed42d6b` (2026-11-04T22:34:53Z). The
delivered archives were built at `cbea802891d4e66b74a0abc33e0af0af74c89708` (22:38:53Z). That commit adds only their
builder (`scripts/`), so the collector and probe trees are those of `39cc61f`. That tree is in `source/`, in two
provider editions.

The tag `review-1.6.6-20261105` points to this repository's publication commit. That is a different commit: it adds
the layout, guides and manifests around the tree and changes no collector file. The earlier deliveries stay at their
own tags, `review-1.6.5-20261104` and `review-1.5.2-20261103`.

## Status

**Corrections verified; named milestones still pending.**

- **What 1.6.6 corrects from the client's review of 1.6.5:**
  - **Classic C2 and C4** are completed in the shared probe 1.7.1 (live mode disabled). The 1.6.5 publication said probe 1.7.0 corrected C1 to C5. That was true of C1, C3 and C5 only: C2 and C4 were partly corrected. Seven reproduction tests fail on 1.7.0 and pass on 1.7.1. [What changed](review/CLASSIC_PROBE_CORRECTIONS.md).
  - **A refused automatic publication is an alert.** It is logged and recorded as an `ERROR` (`PUBLICATION_REFUSED`), and the execution, and Azure's retry of it, exits 6. Release 1.6.5 logged a `WARN` and exited 0.
  - **The 1.6.5 statements that were not accurate are corrected** and listed in [`DOC_CORRECTIONS.md`](manifests/DOC_CORRECTIONS.md).

  The other points of the earlier reviews stay as 1.6.5 corrected them: the four deal fields always `""`, UPC and size provenance, the sponsored and variant decisions, coverage and partitions, retention and recovery. See the [correction map](review/CORRECTION_MAP.md) and the [requirement matrix](review/REQUIREMENT_MATRIX.md).
- **Verified from clean extractions of both 1.6.6 editions:** 533 unit and 202 integration tests passed in each, with
  ruff, format and mypy clean ([`evidence/verification/1.6.6/`](evidence/verification/1.6.6/)). From its own clean
  export, the probe 1.7.1 ran 173 tests: 171 passed, and the 2 vendored-file checks were skipped, because a
  probe-only extraction has no collector beside it.
- **Live, in the developer environment** (the user's Oxylabs Web API trial, from the workstation): fifteen runs on
  releases 1.6.0 to 1.6.6, each attributed to the release that ran it. L12, on the final 1.6.6, read with
  product-page collection on:
  - 40 fresh valid products and 10 product pages;
  - UPC 27 of 40, size 39 of 40;
  - three UPCs that had never been read;
  - its whole export, 10,301 records, verified against the stored pages.

  The census L10 on 1.6.4 gave 7,055 fresh valid products with detail reading off. The last demonstration of 500
  or more with detail on is L8 on 1.6.3 (675).
- **Still pending:**
  - a demonstration of 500 or more products with detail on, on 1.6.6 (about USD 0.07, more than the USD 0.003 left);
  - the full catalogue (no CSV row is complete; the listing pages left are priced at about USD 4.07, product pages
    not included);
  - anything in the client's Azure environment (the VM is deallocated; access waits for the client);
  - a container build;
  - an observed schedule;
  - Scrape.do live;
  - a live Classic successor.

  The [test plan](review/TEST_PLAN.md) and the [milestones](review/MILESTONES.md) give each with its condition.
- **Spending:** Walmart's share of the trial allowance is used: USD 2.247 committed of USD 2.25, and USD 0.003 left.
  The Oxylabs ceiling is 0. Nothing ran in the client's environment, and no schedule is on.

## Contents

| Path | What it holds |
|---|---|
| [`source/`](source/) | Collector 1.6.6 in two editions, Oxylabs Web API and Scrape.do ([about](source/README.md), [operations](source/walmart-oxylabs-1.6.6/docs/OPERATIONS.md), [verification report](source/walmart-oxylabs-1.6.6/docs/VERIFICATION.md)) |
| [`classic-probe-1.7.1/`](classic-probe-1.7.1/) | The shared offline Classic probe 1.7.1: the client's findings C1 to C5, with C2 and C4 completed in this version ([start here](classic-probe-1.7.1/README_FIRST.md), [what changed](review/CLASSIC_PROBE_CORRECTIONS.md)) |
| [`classic-probe-1.7.0/`](classic-probe-1.7.0/) | The probe 1.7.0 of the 1.6.5 delivery, unchanged; superseded by 1.7.1 |
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
git checkout review-1.6.6-20261105
sha256sum --quiet -c manifests/SHA256SUMS.txt && echo "checksums OK"
python3 manifests/check_frozen_trees.py   # source/ and the probes: the delivered archives, file for file
python3 manifests/check_data.py           # data/: the runs' own exports, 22 fields, deal fields, counts, lineage
cp -r source ../walmart-source-1.6.6 && cd ../walmart-source-1.6.6/walmart-oxylabs-1.6.6
uv sync --frozen && uv run --frozen walmart-collector --version   # walmart-azure-headless 1.6.6
uv run --frozen python -m pytest -q tests/unit
```

- Each check ends with `PASS`.
- Copy `source/` out of the clone before installing, so that the checks stay true.
- The [acceptance runbook](review/ACCEPTANCE_RUNBOOK.md) has the PowerShell form, the integration suite, the
  database migration, a container build, a run with its status, pause, resume, export and rollback, and where the
  data and the published dataset live.

## What was changed for this publication

`source/`, `classic-probe/`, `classic-probe-1.7.0/` and `classic-probe-1.7.1/` hold the delivered archives' files,
unchanged. Everywhere else, paths are rewritten to this layout, and [`manifests/`](manifests/) records every other
change:

| File | What it records |
|---|---|
| [`FILE_MAP.csv`](manifests/FILE_MAP.csv) | each file's origin, state and both SHA-256 values; a file carried unchanged from an earlier publication keeps the origin and state recorded there |
| [`DOC_CORRECTIONS.md`](manifests/DOC_CORRECTIONS.md) | the corrections made to the review documents and evidence notes, including the 1.6.5 statements this delivery corrects |
| [`REDACTIONS.csv`](manifests/REDACTIONS.csv) | the redactions: workstation paths and names, and the credential's fingerprint |
| [`EXCLUDED.csv`](manifests/EXCLUDED.csv) | what was left out: the provider's unsanitized answers, internal drafts and redundant copies |
| [`PUBLICATION.json`](manifests/PUBLICATION.json) | the checks run before publication |
