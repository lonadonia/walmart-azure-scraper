# Evidence

Grouped by class. Paths are rewritten to this repository's layout; contents are not, except for the redactions
listed in [`../manifests/REDACTIONS.csv`](../manifests/REDACTIONS.csv).
[`../manifests/FILE_MAP.csv`](../manifests/FILE_MAP.csv) gives each file's origin and both SHA-256 values.

## The evidence of release 1.6.8 (this delivery)

**Read the class before the number.** No provider or retailer request was made for this delivery: everything below is offline, on stored pages or on synthetic pages. Nothing ran in the client's environment.

| Folder | Class | What it holds |
|---|---|---|
| [`owner-azure-test/1.6.8/`](owner-azure-test/1.6.8/) | OWNER AZURE TEST, with no provider request | on Hamza's Azure test VM (Linux): `qualification/` (both edition ZIPs, the suites, migrations, the operator drill, a rollback), `container/` (the images with their digests, replays of stored pages, a kill and resume, a rollback, a restart), `linux-suite/` (the suite on the commit, and the fail-befores), `probe-1.7.2/`, `walkthrough/` (the recording's script, cast and renderer), `memory/` (a replay of L10 timed and its memory measured, on the host), `HOST_STATE.md` |
| [`offline-tests/1.6.8-collector/`](offline-tests/1.6.8-collector/) | OFFLINE TEST | release 1.6.8: its diffs from 1.6.6, 1.6.7 and 1.5.2, each new test's failure on the commit before it, the candidates that were replaced, and 1.6.7's own logs |
| [`offline-tests/1.7.4-classic-probe/`](offline-tests/1.7.4-classic-probe/) | OFFLINE TEST | the shared Classic probe 1.7.4 (the probe 1.7.4 revision): the client's case on Windows, reproduced on the 1.7.2 code (5 failed by their output, 2 controls passed) and passing on 1.7.4 (7 passed); the whole suite on Windows (229 passed, 5 skipped), lint and types; the two refusal tests run 15 times; on Linux, the owner's test VM, the archive's suite (227 passed, 7 skipped) and the review tests on 1.7.4 and on 1.7.2, with the first build's failed type check kept; the pinned diffs from 1.7.2; the exact commands |
| [`reconciliation/1.6.8-probe174/w3/`](reconciliation/1.6.8-probe174/w3/) | RECONCILIATION (offline, no request) | the 275 sponsored and variant decisions recounted from the published 1.6.8 rows with missing evidence counted as unresolved: 48 included, 165 excluded, 3 duplicates, 59 unresolved |
| [`offline-tests/1.7.2-classic-probe/`](offline-tests/1.7.2-classic-probe/) | OFFLINE TEST | the shared Classic probe 1.7.2: its diff from 1.7.1, the review's tests on 1.7.1 (where they fail) and on 1.7.2, on Windows and Linux, the published 1.7.1 on Linux, each skip explained, and the package built again before publication with the workstation's user name replaced in one of its offline results (`PACKAGE_REBUILD.txt`) |
| [`verification/1.6.8/`](verification/1.6.8/) | the delivery's verification | `package/`: both editions from clean extractions of the source ZIP on Windows, and the Bicep build and lint; `last_good_publication/`: the synthetic publication faults |
| [`reconciliation/1.6.8/`](reconciliation/1.6.8/) | OFFLINE REPROCESSING of the live evidence | W2, S6's blanks rechecked against every saved read; W3, the 275 at row level; W4, coverage under 1.6.8 from its own reports of the live runs, each listing's change from 1.6.6, and the continuation estimate |

## The evidence of releases 1.6.0 to 1.6.6 (the earlier deliveries of this work)

**Read the class before the number.** Every 1.6.x live request was made on 2026-11-03 or 2026-11-04, from the
workstation, with the owner's Oxylabs Web API trial account (free credit), by the release named for its run. Nothing ran in the
client's environment.

| Folder | Class | What it holds |
|---|---|---|
| [`live/1.6.x/runs/`](live/1.6.x/runs/) | LIVE, releases 1.6.0 to 1.6.6 | the fifteen runs (L12, on 1.6.6, is the last), one folder each (`<stage>_<run id>/`): the collector database's rows of the run, its stored pages (sanitized, with `PAGE_LINEAGE.csv` and the SHA-256 of each private original in `RAW_ORIGINALS_MANIFEST.csv`), its exports, coverage and field dispositions |
| [`live/1.6.x/campaign/`](live/1.6.x/campaign/) | LIVE, the campaign record | the harness that launched the collector's commands, the step definitions, `commands.csv` (every command with its start, end and exit code), each command's log, the checks, and the shared trial ledger's Walmart extract (`shared_ledger/`) |
| [`live/1.6.x/builds/`](live/1.6.x/builds/) | BUILD | the Oxylabs edition ZIP of each release that ran live, 1.6.0 to 1.6.6, as built |
| [`offline-tests/1.6.0-collector/`](offline-tests/1.6.0-collector/) to [`1.6.6-collector/`](offline-tests/1.6.6-collector/) | OFFLINE TEST | each release's diff from the one before, its new tests run against the release before (where they fail), and its suites on its commit; `1.6.6-collector/` also holds the pinned diff from 1.5.2, and `1.6.5-collector/` the scan of every stored page's price layout |
| [`offline-tests/1.7.0-classic-probe/`](offline-tests/1.7.0-classic-probe/) | OFFLINE TEST | the shared Classic probe 1.7.0: its diff from 1.6.0 and its tests |
| [`offline-tests/1.7.1-classic-probe/`](offline-tests/1.7.1-classic-probe/) | OFFLINE TEST | the shared Classic probe 1.7.1: its diff from 1.7.0, the reproductions of C2 and C4 on 1.7.0 (where they fail) and on 1.7.1, and its development-tree tests |
| [`verification/1.6.6/`](verification/1.6.6/) | the delivery's verification | `package/`: both editions from clean extractions of the source ZIP, and the Bicep build and lint; `last_good_publication/`: the synthetic publication faults |
| [`verification/1.6.5/`](verification/1.6.5/) | the 1.6.5 delivery's verification, kept | the same two records for 1.6.5, and `source_check_l10/`: the live L10 and L8 exports checked with 1.6.5's source check, and the record of the 1.6.4 check's defect |
| [`verification/1.6.1/`](verification/1.6.1/), [`verification/1.6.4/`](verification/1.6.4/) | SYNTHETIC TEST | the same last-good publication check on releases 1.6.1 and 1.6.4 |
| [`reconciliation/1.6.1/`](reconciliation/1.6.1/) to [`1.6.6/`](reconciliation/1.6.6/) | OFFLINE REPROCESSING of the live evidence | W2, the field corrections of S6's 706 rows (final: `1.6.3/w2/`); W3, the 275 sponsored and variant decisions (`1.6.1/w3/`); W4, coverage by row, listing and page with the continuation estimate (`1.6.6/w4/`, which adds L12's page to `1.6.5/w4/`); the measured concurrency (`1.6.6/`) |

The runs, their releases and their results are in [`../data/RUN_SUMMARY.json`](../data/RUN_SUMMARY.json) and
[`../review/TECHNICAL_REPORT.md`](../review/TECHNICAL_REPORT.md), section 3. To trace one row back to the page it
was read from, see section 4 of [`../review/ACCEPTANCE_RUNBOOK.md`](../review/ACCEPTANCE_RUNBOOK.md).

## The evidence of release 1.5.2, as published on 2026-11-03

The evidence of release 1.5.2 (collector commit `627c804`), grouped by class. Each file comes from the delivery's
evidence ZIP `WALMART_EVIDENCE_1.5.2.zip` (1,364 files, SHA-256 `256b968e…187baa`) or from the delivery folder.
Their paths are rewritten here, but their contents are not, except for the redactions listed in
[`../manifests/REDACTIONS.csv`](../manifests/REDACTIONS.csv). [`../manifests/FILE_MAP.csv`](../manifests/FILE_MAP.csv)
gives each file's origin and both SHA-256 values.

**Read the class before the number.** Every live request was made on 2026-10-31, by releases 1.5.0 (`7b6f325`) and
1.5.1 (`488a033`). Release 1.5.2 has not made a live request. Its results come from stored pages, fixtures and
container tests.

| Folder | Class | What it holds |
|---|---|---|
| [`live/`](live/) | LIVE, releases 1.5.0 and 1.5.1 | the campaign of 2026-10-31 on the Oxylabs Web API: plan and budget (`plan/`), commands, logs, ledger and comparisons (`campaign/`), and the nine runs (`runs/<run id>/`: stored pages, database tables, exports, coverage). See the table below |
| [`offline-replay/1.5.2/`](offline-replay/1.5.2/) | OFFLINE REPLAY by 1.5.2 | the nine runs' stored pages read again by 1.5.2, twice (`replay_campaign/`, `repeat_replay/`); B3 of 1.4.1 read again (`replay_b3/`); correction maps; the agreement of the provenance files; private-label evidence. `offline_reprocessing/` holds the delivery's named copies of the S6 and B3 outputs, with its README |
| [`offline-replay/1.5.1/`](offline-replay/1.5.1/) | OFFLINE REPLAY by 1.5.1 | B3 read again by 1.5.1, earlier attempts, the capture index |
| [`offline-tests/1.5.2/`](offline-tests/1.5.2/) | OFFLINE TEST | the two defects of the first 1.5.2 commit shown before their fix |
| [`offline-tests/1.5.1/`](offline-tests/1.5.1/) | OFFLINE TEST | regressions before and after release 1.5.1 |
| [`synthetic/1.5.2/`](synthetic/1.5.2/) | SYNTHETIC TEST | the concurrency load test against a local fixture (no provider) |
| [`synthetic/1.5.1/`](synthetic/1.5.1/) | SYNTHETIC TEST | publication faults injected against a fixture (last-good protection) |
| [`owner-azure-test/1.5.2/`](owner-azure-test/1.5.2/) | OWNER AZURE TEST | on Hamza's Azure test VM, in containers, with no provider request: the Docker builds, the nine replays with a stop, a kill and their resumes (`azure_docker_recovery/`, `owner_vm/`), and the walkthrough's script and recording (`walkthrough/`) |
| [`reconciliation/1.5.2/`](reconciliation/1.5.2/) | OFFLINE REPROCESSING | the 651 sponsored and variant rows, one by one, and the 275 items that need their own page read |
| [`reconciliation/1.5.1/`](reconciliation/1.5.1/) | OFFLINE REPROCESSING and HISTORICAL | coverage and queues, offers audits, the cost model, known limitations, pack fixes, linked examples |
| [`historical/`](historical/) | HISTORICAL | references to earlier releases, the saved pages of the linked examples, the 1.4.1 manifests, and the 2026-11-01 recheck of Oxylabs' Classic documentation |
| [`accounts/`](accounts/) | ACCOUNT READINGS | Scrape.do `/info` readings (free calls) |
| [`tools/`](tools/) | TOOLS | the scripts that produced this evidence, redacted where listed; see "Not published" below |
| [`verification/`](verification/) | the delivery's verification | `PACKAGE_VERIFICATION.txt` and its raw record (`steps.jsonl`, logs, JUnit XML, data checks) from clean extractions of the delivered archives |
| [`as-packaged/`](as-packaged/) | INDEX | the evidence ZIP's own `README.md`, `EVIDENCE_MANIFEST.csv` (every archive file, its class and SHA-256 as packaged), `SANITIZATION.md`, `SANITIZATION_LOG.csv` and `ASSEMBLY_CHECK.txt` |

### The nine live runs (2026-10-31, store 3891, Pickup)

Each run is a capped pilot, rejected by the coverage gate G3 at least, so none was published. Fresh rows are the
ones a run observed itself. The other rows are carried from earlier runs and keep their own run and date.

| Stage | Run | Release | Fresh | Export | Listing pages |
|---|---|---|---:|---:|---:|
| S1 | [`01M69X9XHZR83KZ2FNWBJYJKA7`](live/runs/01M69X9XHZR83KZ2FNWBJYJKA7/) | 1.5.0 | 35 | 35 | 1 |
| S2 | [`01M69XM9RZN3C8D0K7W2NSXR3D`](live/runs/01M69XM9RZN3C8D0K7W2NSXR3D/) | 1.5.0 | 203 | 203 | 6 |
| S3 | [`01M69Y1J6YWFEZ1DJHAC2MT17M`](live/runs/01M69Y1J6YWFEZ1DJHAC2MT17M/) | 1.5.0 | 116 | 319 | 4 |
| S4 | [`01M69Y882GTVYRJZM0CXQ44MXN`](live/runs/01M69Y882GTVYRJZM0CXQ44MXN/) | 1.5.0 | 677 | 689 | 19 |
| S5b serial | [`01M69YPZTFCP7AWJ5B78AXEA2N`](live/runs/01M69YPZTFCP7AWJ5B78AXEA2N/) | 1.5.0 | 80 | 689 | 2 |
| S5b parallel | [`01M69YS2X0YG5JSEMCGKK8BHE5`](live/runs/01M69YS2X0YG5JSEMCGKK8BHE5/) | 1.5.0 | 80 | 689 | 2 |
| S5a | [`01M6A0JWYHTVK7XFH34P235F9Q`](live/runs/01M6A0JWYHTVK7XFH34P235F9Q/) | 1.5.0 | 67 | 689 | 2 |
| **S6** | [`01M6A2VQAA5VXJHJHMZPCTZTD4`](live/runs/01M6A2VQAA5VXJHJHMZPCTZTD4/) | **1.5.1** | **580** | 706 | 15 |
| S7 | [`01M6A52HA6XYCEDS6DBE5N5RQ7`](live/runs/01M6A52HA6XYCEDS6DBE5N5RQ7/) | 1.5.1 | 32 | 706 | 1 |

To trace one row back to the page it was read from, see section 4 of
[`../review/ACCEPTANCE_RUNBOOK.md`](../review/ACCEPTANCE_RUNBOOK.md).

### Reading a path written into an archive

Evidence files and JSON records still cite paths as `WALMART_EVIDENCE_1.5.2.zip: <path>`. Every member of the 1.5.1
evidence ZIP except its 5 root index files is carried byte for byte at the same path in the 1.5.2 ZIP, so
`WALMART_EVIDENCE_1.5.1.zip: <path>` reads the same way. The review documents are already rewritten.

| Archive path | Repository path |
|---|---|
| `1_new_live/` | `evidence/live/` |
| `2_offline_reprocessing/` | `evidence/offline-replay/1.5.1/` |
| `3_reconciliation/` | `evidence/reconciliation/1.5.1/` |
| `4_historical_references/` | `evidence/historical/` |
| `5_fault_and_publication_tests/` | `evidence/synthetic/1.5.1/` |
| `6_offline_regressions/` | `evidence/offline-tests/1.5.1/` |
| `7_release_1_5_2/replay_campaign/`, `repeat_replay/`, `replay_b3/`, `correction_maps/`, `agreement/`, `private_label/` | `evidence/offline-replay/1.5.2/` (same names) |
| `7_release_1_5_2/defects_before_the_fix/` | `evidence/offline-tests/1.5.2/defects_before_the_fix/` |
| `7_release_1_5_2/load/` | `evidence/synthetic/1.5.2/load/` |
| `7_release_1_5_2/owner_vm/`, `walkthrough/` | `evidence/owner-azure-test/1.5.2/` (same names) |
| `7_release_1_5_2/sponsored_and_variant_reconciliation/` | `evidence/reconciliation/1.5.2/sponsored_and_variant_reconciliation/` |
| `7_release_1_5_2/classic_documentation_recheck/` | `evidence/historical/classic_documentation_recheck/` |
| `7_release_1_5_2/accounts/`, `accounts/` | `evidence/accounts/1.5.2/`, `evidence/accounts/1.5.1/` |
| `7_release_1_5_2/tools/`, `tools/` | `evidence/tools/1.5.2/`, `evidence/tools/1.5.1/` |
| the archive's root files | `evidence/as-packaged/` |
| `WALMART_SOURCE_1.5.2.zip: <path>` | `source/<path>` |
| `OXYLABS_CLASSIC_OFFLINE_PROBE_1.5.2.zip: <path>` | `classic-probe/<path>` |

The delivery folder's own files moved as follows. `live/S6_1.5.1/` became [`../data/S6-1.5.1/`](../data/S6-1.5.1/),
and S7 and S4 moved the same way. `live/RUN_SUMMARY.json` and `COVERAGE_RECONCILIATION.csv` went to
[`../data/`](../data/). `offline_reprocessing/` went to `evidence/offline-replay/1.5.2/offline_reprocessing/`,
`azure_docker_recovery/` to `evidence/owner-azure-test/1.5.2/azure_docker_recovery/`, and `verification/` to
`evidence/verification/`. `CAMPAIGN_BUDGET.json` is published once, at `evidence/live/plan/CAMPAIGN_BUDGET.json`.
References to `shared/WALMART_SHARED_EVIDENCE_1.4.1.zip` point into the 1.4.1 delivery, which is not republished here.

### Not published

[`../manifests/EXCLUDED.csv`](../manifests/EXCLUDED.csv) lists each file left out, with its SHA-256 and the reason.
In short:

- the document generators of the 1.5.1 and 1.5.2 deliveries and the workstation utilities that rendered the
  client summary PDF;
- the delivery's verifier and builder (their record is in `verification/`);
- a workstation check of the owner's key file;
- client-message and access-request drafts;
- copies of files that are published once elsewhere.

The providers' raw responses are protected originals. They stay on the preparation workstation, and their hashes
are in each run's `RAW_ORIGINALS_MANIFEST.csv`.
