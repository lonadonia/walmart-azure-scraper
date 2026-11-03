# Evidence

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

## The nine live runs (2026-10-31, store 3891, Pickup)

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

## Reading a path written into an archive

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

## Not published

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
