# Walmart collector 1.6.8: correction delivery for review

This is a correction delivery for the client's review. It is not a final release, and it has not been accepted.

**Target:** Walmart #3891, 3900 Fountain Square Pl, Waukegan, IL 60085, **PICKUP**.

**Collector:** release 1.6.8, commit `85c29e7b2404500299056973f50c84b84e187a5a` (2026-11-05T20:51:52Z), unchanged in this revision. That tree is in `source/`, in two provider editions, built by
`scripts/build_walmart_168_delivery.py` of the same commit. **Shared Classic probe:** 1.7.4, commit `a1def53747dfabcb2ad9ca97efc421c1e70f0ac6`, live mode disabled.

The tag `review-1.6.8-probe174-20261111` points to this revision's publication commit. It corrects the probe's process supervision on
Windows (probe 1.7.4) and two statements of the 1.6.8 publication, and changes no collector file. The 1.6.8 delivery stays at its tag,
`review-1.6.8-20261106`, and the earlier deliveries at theirs, `review-1.6.6-20261105`, `review-1.6.5-20261104` and `review-1.5.2-20261103`.

## This revision: probe 1.7.4 and two corrected statements (2026-11-11)

The client's review of the 1.6.8 delivery found that probe 1.7.2 did not hold a session's processes on Windows in every case.
- **What was wrong (reproduced on the frozen 1.7.2 code, on Windows).** When no job object could be made, or the session's process could not join one,
  1.7.2 ran the session anyway and fell back to `taskkill /T`. That cannot reach a child whose parent has exited. In the reproduction the child kept
  running, and connected to a local stub, after the supervisor had returned and reported nothing left running and no problem. When the job's count could not be read,
  1.7.2 also reported nothing left running.
- **What 1.7.4 does.** A session runs only once a job object with kill-on-close and no breakaway holds it. The process is created suspended, assigned,
  confirmed in the job and counted alone there before it runs. If any step fails, the suspended process is ended and reaped and the session is refused:
  no command, no descendant, no request. There is no `taskkill` fallback. The tree counts as gone only when the job's own count says so (the process group
  on Linux). A cleanup that cannot be verified is reported as `cleanup-unknown` or `cleanup-failed`; the session's evidence is not used, and a recovery runs and records that outcome.
  Live mode stays disabled.
- **Tested offline, on Windows 11 and on Linux** (a full description is in [`1.7.4-classic-probe/`](evidence/offline-tests/1.7.4-classic-probe/)). On the 1.7.2 code, five new tests fail on Windows and show the
  defect in their output; two control tests pass. On 1.7.4 all seven pass, and the whole suite gives 229 passed, 5 skipped, 0 failed. Ruff, format and mypy (for Windows and for Linux) are clean.
  On Linux, the owner's test VM, from the archive: 227 passed, 7 skipped, 0 failed; the three review tests that run there pass, and two of them fail on the 1.7.2 code. The archive's first build failed mypy on Linux and was not published; `a1def53` corrects it.
- **Corrected statements.** "1.7.2 completes C2" did not hold on Windows (above). Also, 59 of the 275 sponsored and variant products had been counted
  as excluded with "0 unresolved", but nothing in their sources supports exclusion. Four have no category path, and 55 have no proof of local
  eligibility, so they are **unresolved** ([W3 recount](evidence/reconciliation/1.6.8-probe174/w3/)); settling them needs 59 paid page reads. Two acceptance
  rows, A25 and P4-02, become BLOCKED_BUDGET for that reason. The 44 products whose UPC has no read are a separate queue, unchanged.
  Each corrected sentence is in [`DOC_CORRECTIONS.md`](manifests/DOC_CORRECTIONS.md).
- **Unchanged:** the collector and its data. There is no live run and no new live collection. 7,055 fresh products are from 1.6.4 (L10). L12 on 1.6.6
  had 40 fresh and 10,261 carried forward. 0 of 11 CSV rows are complete. No provider request was made, nothing ran in the client's environment, and no schedule is on.
  The shared trial ledger was read again for the probe 1.7.4 revision on 2026-11-09 (read-only): Walmart's part is the same, 1,513 reservations and USD 2.2470 committed, its last reservation on 2026-11-04, and this revision made no request. The database's SHA-256 has changed since 2026-11-06 because Mariano's own stages have drawn on Mariano's envelope, outside this revision.

## Status (the 1.6.8 delivery, with this revision's corrections marked)

**Corrections verified offline and on the owner's Azure test VM. No live run on this release. Named milestones still pending.**

- **What 1.6.8 and probe 1.7.2 correct from the client's review of 1.6.6:**
  - **Classic C4, incomplete bodies.** A server that declares `Content-Length: 100`, sends the two bytes `{}` and closes got `ok=True` on 1.7.1. On 1.7.2 such a body, zero bytes included, is kept as partial with its declared and received lengths and hash, is never parsed, and its money stays held.
  - **Classic C2, the whole-session deadline and stale evidence.** On Linux 1.7.1 waited 1.10 s for a FIFO manifest past a 0.30 s deadline, and accepted an earlier campaign's `complete=true` file. On 1.7.2 one monotonic deadline bounds the manifest, the processing, the export, the cleanup and the recovery, and only evidence of the current execution counts. *(This revision: on Windows the session's process tree was held only when a job object could be made and the process joined it. Corrected in probe 1.7.4, above.)*
  - **The Linux test discrepancy.** The drip test no longer demands a forced kill when the worker ended by itself; a separate test forces a hung worker and checks a real kill and reap. [What changed](review/CLASSIC_PROBE_CORRECTIONS.md).
  - **What "complete" means.** A partition is complete only when each child ended complete; a row read in part is never complete; a read of a filtered view never completes a listing. 252 of 1,104 listings are complete under these rules, against the 244 published, and no CSV row is (0 of 11). [Tables](evidence/reconciliation/1.6.8/w4/).
  - **Scope that was skipped.** A subcategory that is a category page of its own is now read for the listings it names; a link that shows a listing filtered has the listing itself read, once, in full; two shelves that share listing ID 0 are two listings.
  - **The category mapping.** "Fabric Softeners" is the name the Household Essentials page gives listing `1115193_1071967_1630538`. A listing takes the name its category page gives that exact view, on fresh and carried rows, and the earlier name stays in the row's lineage.
  - **UPC and size are decided apart**, so a size conflict no longer withholds a UPC the same read verifies. The queue of unread UPCs is 44, not 45. The 275 sponsored and variant decisions are reconciled at row level. [Tables](evidence/reconciliation/1.6.8/). *(This revision: 59 of the 275 are unresolved, not excluded; the 44 unread UPCs are a separate queue. See above.)*
  - **The 1.6.6 statements that were not accurate** are corrected, with dated errata, in [`DOC_CORRECTIONS.md`](manifests/DOC_CORRECTIONS.md). The earlier tags are not moved.
- **Verified from the delivered archives:**
  - on Linux, the owner's Azure test VM: both editions, 554 unit and 222 integration tests each, ruff, format and mypy clean, migrations on PostgreSQL 16 ([qualification](evidence/owner-azure-test/1.6.8/qualification/));
  - in Docker on the same VM: both images built from the delivered source, with digests, a replay of the stored pages, a kill and resume, a rollback to 1.6.6 and forward, and data checked across a restart ([container](evidence/owner-azure-test/1.6.8/container/));
  - on Windows: both editions from clean extractions, 554 unit tests and the integration files the change touches, each in its own process ([`evidence/verification/1.6.8/`](evidence/verification/1.6.8/)). A full Windows integration pass of an earlier candidate's ZIP (`7a96218`) was stopped by the workstation's low-memory protection after 56 tests passed, and was not forced;
  - probe 1.7.2: 201 passed and 3 skipped on Linux, 199 passed and 5 skipped on Windows, each skip explained ([`1.7.2-classic-probe/`](evidence/offline-tests/1.7.2-classic-probe/)); probe 1.7.4 (this revision): 229 passed and 5 skipped on Windows, 227 passed and 7 skipped on Linux ([`1.7.4-classic-probe/`](evidence/offline-tests/1.7.4-classic-probe/));
  - the Bicep build and lint of both editions, no deployment.
- **Live, in the developer environment** (the owner's Oxylabs Web API trial, free credit at the documented rate, from the workstation): fifteen runs on releases 1.6.0 to 1.6.6, each attributed to the release that ran it. **None on 1.6.7 or 1.6.8.**
  - L12 on 1.6.6 proves 40 fresh valid products and 10 product pages. Its 10,301 exported records include 10,261 carried.
  - The census L10 on 1.6.4 gave 7,055 fresh valid products with detail reading off, and L8 on 1.6.3 gave 675 with detail on.
- **Still pending:**
  - a demonstration of 500 or more products with detail on, on 1.6.8 (at most 45 submissions, USD 0.0675; USD 0.003 is left and the ceiling is 0);
  - the full catalogue: no CSV row is complete. The known listing pages left are priced at about USD 4.63, the 95 category pages of their own at USD 0.14, the product pages of the products known today at USD 13.96 and, as an estimate, those of products not yet seen at USD 75.48 to 152.93; the listings the category pages name are not known until they are read ([test plan](review/TEST_PLAN.md));
  - anything in the client's Azure environment (access waits for the client: the VM's restart, the new public key installed and the old one revoked);
  - an observed schedule and a natural unavailable transition;
  - Scrape.do live;
  - a live Classic successor.

  The [test plan](review/TEST_PLAN.md) and the [milestones](review/MILESTONES.md) give each with its condition.
- **Spending:** Walmart's share of the trial allowance is used: USD 2.247 committed of USD 2.25, and USD 0.003 left. The Oxylabs ceiling is 0. This delivery made no provider request. Nothing ran in the client's environment, and no schedule is on.

## Contents

| Path | What it holds |
|---|---|
| [`source/`](source/) | Collector 1.6.8 in two editions, Oxylabs Web API and Scrape.do ([about](source/README.md), [operations](source/walmart-oxylabs-1.6.8/docs/OPERATIONS.md), [verification report](source/walmart-oxylabs-1.6.8/docs/VERIFICATION.md)) |
| [`classic-probe-1.7.4/`](classic-probe-1.7.4/) | The shared offline Classic probe 1.7.4, this revision's ([start here](classic-probe-1.7.4/README_FIRST.md), [what changed](review/CLASSIC_PROBE_CORRECTIONS.md)) |
| [`classic-probe-1.7.2/`](classic-probe-1.7.2/) | The shared offline Classic probe 1.7.2 of the 1.6.8 delivery, unchanged; superseded by 1.7.4 |
| [`classic-probe-1.7.1/`](classic-probe-1.7.1/), [`classic-probe-1.7.0/`](classic-probe-1.7.0/) | The probes of the 1.6.6 and 1.6.5 deliveries, unchanged; superseded |
| [`classic-probe/`](classic-probe/) | The Walmart probe 1.5.2 the client reviewed, unchanged |
| [`review/`](review/) | [Technical report](review/TECHNICAL_REPORT.md), [summary PDF](review/WALMART_1.6.8_SUMMARY.pdf), [requirement matrix](review/REQUIREMENT_MATRIX.md), [correction map](review/CORRECTION_MAP.md), [milestones](review/MILESTONES.md), [acceptance matrix](review/ACCEPTANCE_MATRIX.csv), [runbook](review/ACCEPTANCE_RUNBOOK.md), [recovery and operations](review/RECOVERY_AND_OPERATIONS.md), [cost and runtime](review/COST_AND_RUNTIME_REPORT.md), [test plan and next live proposal](review/TEST_PLAN.md), [delivery index](review/DELIVERY_INDEX.md) |
| [`data/`](data/) | The live product files, one folder per run (`<stage>-<release that collected it>`) ([description](data/README.md)) |
| [`evidence/`](evidence/) | Live runs, the shared trial ledger, reconciliations, offline tests, owner-VM tests and verifications ([index](evidence/README.md)) |
| [`walkthrough/`](walkthrough/) | The walkthrough of 1.6.8 on the owner's Azure test VM (no live run), and that of 1.5.2, unchanged |
| [`manifests/`](manifests/) | Checksums, file map, corrections, redactions, exclusions and the publication record |
| [`CHANGELOG.md`](CHANGELOG.md) | One entry per delivery, and how this repository is updated |

## Verify (offline, no request sent)

```
git clone https://github.com/lonadonia/walmart-azure-scraper.git && cd walmart-azure-scraper
git checkout review-1.6.8-probe174-20261111
sha256sum --quiet -c manifests/SHA256SUMS.txt && echo "checksums OK"
python3 manifests/check_frozen_trees.py   # source/ and the probes: the delivered archives, file for file
python3 manifests/check_data.py           # data/: the runs' own exports, 22 fields, deal fields, counts, lineage
cp -r source ../walmart-source-1.6.8 && cd ../walmart-source-1.6.8/walmart-oxylabs-1.6.8
uv sync --frozen && uv run --frozen walmart-collector --version   # walmart-azure-headless 1.6.8
uv run --frozen python -m pytest -q tests/unit
```

- Each check ends with `PASS`.
- Copy `source/` out of the clone before installing, so that the checks stay true.
- The probe's Windows finding, reproduced on the 1.7.2 code and then run on 1.7.4: [`REPRODUCE.md`](evidence/offline-tests/1.7.4-classic-probe/REPRODUCE.md)
  gives the exact commands (Windows, Python 3.12, uv; offline).
- The [acceptance runbook](review/ACCEPTANCE_RUNBOOK.md) has the PowerShell form, the integration suite, the
  database migration, a container build, a run with its status, pause, resume, export and rollback, and where the
  data and the published dataset live.

## What was changed for this publication

`source/` and the `classic-probe*` folders hold the delivered archives' files, unchanged. Everywhere else, paths are rewritten to
this layout, and [`manifests/`](manifests/) records every other change:

| File | What it records |
|---|---|
| [`FILE_MAP.csv`](manifests/FILE_MAP.csv) | each file's origin, state and both SHA-256 values; a file carried unchanged from an earlier publication keeps the origin and state recorded there |
| [`DOC_CORRECTIONS.md`](manifests/DOC_CORRECTIONS.md) | the corrections made to the review documents and evidence notes, including the 1.6.6 statements this delivery corrects |
| [`REDACTIONS.csv`](manifests/REDACTIONS.csv) | the redactions: workstation and owner-VM paths, names and addresses, and the credential's fingerprint |
| [`EXCLUDED.csv`](manifests/EXCLUDED.csv) | what was left out: the provider's unsanitized answers, internal drafts and redundant copies |
| [`PUBLICATION.json`](manifests/PUBLICATION.json) | the checks run before publication |
