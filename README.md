# Walmart collector 1.5.2: correction delivery for review

This is a correction delivery for the client's review. It is not a final release, and it has not been accepted.

**Target:** Walmart #3891, 3900 Fountain Square Pl, Waukegan, IL 60085, **PICKUP**.

**Collector:** release 1.5.2, commit `627c804d66aa33fc423fd2296c8896c5d5c2c3d4` (2026-11-01). That commit is the
frozen tree in `source/`. The tag `review-1.5.2-20261103` points to this repository's publication commit, which is a different
commit: it adds the layout, guides and manifests around the tree and changes no collector file.

## Status

- **What 1.5.2 corrects** ([correction map](review/CORRECTION_MAP.md)):
  - The provenance files name the real capture of each recovered size and UPC.
  - Sizes and packs: five carried sizes ("30 lb" became "2 pack, 30 lb"), a pack stated twice ("2 pack"), and both
    sizes of a set of two.
  - `blocked` and `request_failed` replace one failure class, and a page that was never read is never "absent".
  - An interrupted replay resumes as a replay.
  - A row carried from a replay names the live run that read it.
  - Six private-label brands are confirmed from USPTO records.
- **The last live data** comes from S6 (`01M6A2VQAA5VXJHJHMZPCTZTD4`, 2026-10-31), which ran on release **1.5.1**:
  - **580 valid, distinct fresh** products from 15 Pickup result pages, and 706 retained rows;
  - it was a capped pilot, rejected by the coverage gate G3, so nothing was published.
- **1.5.2 has made no live request.**
  - Its corrections are verified offline, by tests and by replays of the stored pages.
  - Its Docker image, recovery and walkthrough ran on the owner's Azure test VM, with no provider request.
- **Still open:**
  - a live run of 1.5.2, including S6's 226 unread UPCs and 9 unread sizes;
  - the 275 sponsored and variant items that need their own page read;
  - full category coverage;
  - Scrape.do on the final version (credits);
  - a live offer example;
  - a run in the client's Azure;
  - paid Classic, whose live mode stays disabled;
  - the client's own acceptance.
- Schedules are **off**. A successful package verification is not final client acceptance.

## Contents

| Path | What it holds |
|---|---|
| [`source/`](source/) | Collector 1.5.2 in two editions, Oxylabs Web API and Scrape.do ([about](source/README.md), [operations](source/walmart-oxylabs-1.5.2/docs/OPERATIONS.md), [verification report](source/walmart-oxylabs-1.5.2/docs/VERIFICATION.md)) |
| [`classic-probe/`](classic-probe/) | The frozen offline Classic probe 1.5.2, with its offline results ([start here](classic-probe/README_FIRST.md)) |
| [`review/`](review/) | [Correction map](review/CORRECTION_MAP.md), [acceptance matrix](review/ACCEPTANCE_MATRIX.csv), [technical report](review/TECHNICAL_REPORT.md), [runbook](review/ACCEPTANCE_RUNBOOK.md), [cost and runtime](review/COST_AND_RUNTIME_REPORT.md), [test plan](review/TEST_PLAN.md), [delivery index](review/DELIVERY_INDEX.md) |
| [`data/`](data/) | The live product files: [S6 on 1.5.1](data/S6-1.5.1/), [S7 on 1.5.1](data/S7-1.5.1/), [S4 on 1.5.0](data/S4-1.5.0/) ([description](data/README.md)) |
| [`evidence/`](evidence/) | Live runs, offline replays, tests, the owner's Azure test and the reconciliations ([index](evidence/README.md)) |
| [`walkthrough/`](walkthrough/) | A recorded walkthrough on the owner's Azure test VM, with no live run ([description](walkthrough/README.md)) |
| [`manifests/`](manifests/) | Checksums, file map, corrections, redactions, exclusions and the publication record |
| [`CHANGELOG.md`](CHANGELOG.md) | One entry per delivery, and how this repository is updated |

## Verify (offline, no request sent)

```
git clone https://github.com/lonadonia/walmart-azure-scraper.git && cd walmart-azure-scraper
git checkout review-1.5.2-20261103
sha256sum --quiet -c manifests/SHA256SUMS.txt && echo "checksums OK"
python3 manifests/check_frozen_trees.py   # source/ and classic-probe/: the delivered archives, file for file
python3 manifests/check_data.py           # data/: the runs' own exports, 22 fields, counts and lineage
cp -r source ../walmart-source-1.5.2 && cd ../walmart-source-1.5.2/walmart-oxylabs-1.5.2
uv sync --frozen && uv run --frozen walmart-collector --version   # walmart-azure-headless 1.5.2
uv run --frozen python -m pytest -q tests/unit
```

- Each check ends with `PASS`.
- Copy `source/` out of the clone before installing, so that the checks stay true.
- The [acceptance runbook](review/ACCEPTANCE_RUNBOOK.md) has the PowerShell form (section 1), the integration suite
  and its Windows notes (section 2), how to trace a row to its page (section 4), and the Classic probe (section 6).

## What was changed for this publication

`source/` and `classic-probe/` hold the delivered archives' files, unchanged. Everywhere else, paths are rewritten to
this layout, and [`manifests/`](manifests/) records every other change:

| File | What it records |
|---|---|
| [`FILE_MAP.csv`](manifests/FILE_MAP.csv) | each file's origin and both SHA-256 values |
| [`DOC_CORRECTIONS.md`](manifests/DOC_CORRECTIONS.md) | the corrections made to the review documents, including one erratum on the set of two sizes |
| [`REDACTIONS.csv`](manifests/REDACTIONS.csv) | the redactions: workstation paths and names, and an account identifier |
| [`EXCLUDED.csv`](manifests/EXCLUDED.csv) | what was left out: drafts, internal tools, redundant copies and the all-in-one archive |
| [`PUBLICATION.json`](manifests/PUBLICATION.json) | the checks run before publication |
