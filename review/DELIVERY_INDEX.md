# Delivery index: Walmart collector release 1.6.5, with the shared Oxylabs Classic offline probe 1.7.0

Release 1.6.5 of the Walmart collector, commit `67d216eb8ee2ec839a437b0b5bf2d594324b6982`, in its two provider
editions (Oxylabs Web API and Scrape.do), and the shared Oxylabs Classic offline probe 1.7.0. Store: Walmart #3891,
3900 Fountain Square Pl, Waukegan, IL 60085, fulfillment PICKUP. Prepared on 2026-11-04 (UTC) by Hamza. The message
to the client is a draft kept outside this repository; nothing here has been sent to the client.

**What this is: a correction delivery.** Every point of the client's two latest reviews is corrected and verified,
and the named milestones are still pending: the full catalogue, a detail-on run of the final revision, the client's
environment, an observed schedule, Scrape.do live and a live Classic successor. The live runs were made in the
developer environment, on the user's Oxylabs Web API trial, each attributed to the release that ran it. No client
observed or ran anything, the collector is not presented as production-ready, and every schedule is off.

## Start here

| File | What it is |
|---|---|
| [`TECHNICAL_REPORT.md`](TECHNICAL_REPORT.md) | what was fixed, what ran on the final revision and where, the fourteen live runs, counts, coverage, the shared ledger, what remains, disclosures |
| [`REQUIREMENT_MATRIX.md`](REQUIREMENT_MATRIX.md) | the state of each work item (W1 to W8), Classic finding (C1 to C5), audit item (W01 to W24) and contract rule |
| [`ACCEPTANCE_MATRIX.csv`](ACCEPTANCE_MATRIX.csv) | the 206 rows, with their 1.5.2 columns as published then (their `source/walmart-*-1.5.2/` paths are at the tag `review-1.5.2-20261103`) and four new columns: PASS_OFFLINE 90, PASS_DEVELOPER_LIVE 66, BLOCKED_BUDGET 22, PENDING_CLIENT_AZURE 8, PENDING_OWNER 7, NOT_APPLICABLE_BY_CLARIFICATION 6, PENDING_CLIENT_DECISION 4, PENDING_OBSERVATION 3 |
| [`CORRECTION_MAP.md`](CORRECTION_MAP.md) | each correction with its cause, tests and live evidence, and the pinned diff from 1.5.2 |
| [`TEST_PLAN.md`](TEST_PLAN.md) | the next live work, priced, smallest first. Unapproved |
| [`MILESTONES.md`](MILESTONES.md) | what was done when, and what is open with its condition |
| [`COST_AND_RUNTIME_REPORT.md`](COST_AND_RUNTIME_REPORT.md) | the shared trial ledger per stage, measured runtimes, and the estimates for full scope |
| [`RECOVERY_AND_OPERATIONS.md`](RECOVERY_AND_OPERATIONS.md) | retention, recovery, the last-good publication, concurrency, the schedule, the container |
| [`ACCEPTANCE_RUNBOOK.md`](ACCEPTANCE_RUNBOOK.md) | how to repeat the offline checks, and how the collector is installed and operated |
| [`CLASSIC_PROBE_CORRECTIONS.md`](CLASSIC_PROBE_CORRECTIONS.md) | C1 to C5 in the probe 1.7.0 |
| [`../data/RUN_SUMMARY.json`](../data/RUN_SUMMARY.json) | every live run of this store that the repository publishes, with its release, commit, edition ZIP, times, gates, counts and spending |
| [`../manifests/SHA256SUMS.txt`](../manifests/SHA256SUMS.txt) | the SHA-256 of every other file of this repository, written last |

## Revisions

| Commit | Date (UTC) | What it is |
|---|---|---|
| `627c804d66aa33fc423fd2296c8896c5d5c2c3d4` | 2026-11-01 | release 1.5.2, the one the client reviewed (publication `c4e665c`, tag `review-1.5.2-20261103`) |
| `56f078efce4df3b40165dbeafcfe49e6c6f581eb` | 2026-11-03T16:59:04Z | release 1.6.0. Live runs L1, L2 |
| `1780349e522d771a3642fe88bfb7b542044ec844` | 2026-11-03T18:18:22Z | release 1.6.1. Live runs L3, L2b, L4r, L4 |
| `12740567afc1499d1eb850c9faa306439b0798d2` | 2026-11-04T10:24:46Z | release 1.6.2. Live runs L5, L6 |
| `def55e5c5f69fc60053f52fe49d077ec7648a513` | 2026-11-04T11:54:09Z | release 1.6.3. Live runs L8, L9, L7 |
| `28ac7d3b6b7c5fc8aee38cf15cb597d51f465cf2` | 2026-11-04T12:32:58Z | release 1.6.4. Live run L10 |
| `67d216eb8ee2ec839a437b0b5bf2d594324b6982` | 2026-11-04T14:15:19Z | **release 1.6.5, the final revision**. Live runs L11 and L11b; the re-validation of L10's and L8's exports |
| `2c085850b622330083eb4c7bdeb90f075e4f99db`, `48307cf20c6708fb57352559a113ed5bc65cb3e1` | 2026-11-03 | the shared Classic probe 1.7.0: its code, then its documents. Its tree is unchanged at `67d216e` |
| `6b9be92aa4fb8f5d18e1085316c20dd787690a86` | 2026-11-04T15:16:32Z | the builders of the 1.6.4 and 1.6.5 delivery archives (`scripts/`); it changes nothing under `headless/` |

The development commits are local (branch `walmart-1.6`). This repository receives the delivered files: the source
ZIP's tree, the probe's, the product files, the evidence and the review documents. Each run is attributed to the
release that ran it and to no other.

## The folders

| Folder | What it is |
|---|---|
| [`source/`](../source/) | `WALMART_SOURCE_1.6.5.zip`, file for file: `walmart-oxylabs-1.6.5/` and `walmart-scrapedo-1.6.5/`, which differ in four edition files |
| [`classic-probe-1.7.0/`](../classic-probe-1.7.0/) | `OXYLABS_CLASSIC_OFFLINE_PROBE_1.7.0.zip`, file for file; live mode disabled |
| [`classic-probe/`](../classic-probe/) | the Walmart Classic probe 1.5.2, as the client reviewed it, unchanged |
| [`data/`](../data/) | the product files of L10 (`L10-1.6.4/`) and L8 (`L8-1.6.3/`), the run summary, and the 1.5.x runs' files, unchanged |
| [`evidence/live/1.6.x/`](../evidence/live/1.6.x/) | `runs/`: each run's database rows, stored pages (sanitized, with the SHA-256 of each private original), exports and coverage; `campaign/`: the harness, step definitions, commands and logs, checks, and the shared ledger's Walmart extract; `builds/`: the Oxylabs edition ZIP of each release that ran live |
| [`evidence/offline-tests/`](../evidence/offline-tests/) | per release (`1.6.0-collector/` to `1.6.5-collector/`, `1.7.0-classic-probe/`): its diff, its tests run against the release before, and its suites on its commit |
| [`evidence/verification/1.6.5/`](../evidence/verification/1.6.5/) | the clean-extraction verification of both editions (`package/`), the last-good publication check, and the check of the live exports with 1.6.5's source check. The last-good checks of 1.6.1 and 1.6.4 stay beside it, in `1.6.1/` and `1.6.4/`; the top of `evidence/verification/` is release 1.5.2's record |
| [`evidence/reconciliation/`](../evidence/reconciliation/) | W2 (`1.6.3/w2/`), W3 (`1.6.1/w3/`), W4 and the measured concurrency (`1.6.5/`) |
| [`review/`](.) | this index and the review documents |
| [`manifests/`](../manifests/) | the file map, the redactions, the exclusions, the documentation corrections, the publication record, the data and tree checks, and `SHA256SUMS.txt` |
| [`walkthrough/`](../walkthrough/) | the 1.5.2 recording, unchanged; no 1.6.x recording was made |

## The product files

| Folder | Release that collected it | Rows | What it is |
|---|---|---|---|
| [`data/L10-1.6.4/`](../data/L10-1.6.4/) | 1.6.4 (`28ac7d3`) | `products_fresh`: 7,057 (7,055 valid); `products_retained`: 10,301 | the census, detail reading off. Its export passes the final 1.6.5's `validate-export --run` |
| [`data/L8-1.6.3/`](../data/L8-1.6.3/) | 1.6.3 (`def55e5`) | `products_fresh`: 675; `products_retained`: 2,515 | the last demonstration with detail reading on |

Each has a CSV and a JSON of each file, the 22 fields in order, all strings, the four deal fields `""` in every row.
A carried row keeps its own run and date. `data/RUN_SUMMARY.json` gives each file's SHA-256 and row count, and
[`manifests/check_data.py`](../manifests/check_data.py) checks them against their runs' exports.

## Known limitations

1. **No detail-on run of the final revision.** The last detail-on demonstration is L8 on 1.6.3 (675 fresh valid).
   1.6.4 and 1.6.5 did not change the detail path, but the run on the final revision was not funded (N1A-05).
2. **Not the full catalogue.** No CSV row is complete (0 of 11); 407 listings were never reached. The continuation
   is priced in [`TEST_PLAN.md`](TEST_PLAN.md).
3. **The flat price layout, live.** 1.6.5's reading of it is verified offline on the authentic stored page and on
   L10's records from it. No live run of 1.6.5 checked a page in that layout: L11 meant to, and its listing was
   rejected for its identity.
4. **Two L10 rows without a price.** Their page showed them with no price at all. They are in L10's fresh export with
   empty prices, marked `exported_not_valid` in `record_map.json`, and are not counted among the 7,055.
5. **Partitions live at depth 1 only** (21 child listings); the second level is tested offline (A18).
6. **Recovery live on 1.6.1 to 1.6.3.** It was not repeated live on 1.6.4 or 1.6.5, which did not change it.
7. **No container build of 1.6.5**: the workstation has no container runtime, and the client's VM is deallocated.
8. **Scrape.do has no 1.6.x live run**; no Scrape.do spending was authorized.
9. **Memory under load was not measured.**
10. **A refused automatic publication exits 0** (found on 2026-11-03, not changed): alert on `PUBLICATION_REFUSED`
    ([`RECOVERY_AND_OPERATIONS.md`](RECOVERY_AND_OPERATIONS.md), section 3).

## Accounts, external services, licensing and costs

- **Oxylabs Web API:** the user's trial account, designated by Hamza, through the shared ledger: Walmart committed
  USD 2.2275 of its USD 2.25 envelope, Mariano's nothing of its own (see
  [`COST_AND_RUNTIME_REPORT.md`](COST_AND_RUNTIME_REPORT.md)). The provider-side balance is UNVERIFIED: the Web API
  has no balance endpoint, and the dashboard is the owner's.
- **Scrape.do:** not used in this delivery.
- **Azure:** nothing deployed. The Bicep templates were built and linted offline. The client's VM is
  deallocated (the client's statement); it was not touched, and no SSH attempt was made.
- **External services:** unchanged since 1.5.2: Walmart.com through a provider (the Oxylabs Web API or Scrape.do),
  the operator's PostgreSQL and, optionally, Azure. The Docker base images are unchanged. The Classic probe names
  `https://realtime.oxylabs.io/v1/queries`, but its live mode is disabled. The collector sends no telemetry and has no
  remote switch.
- **Licensing:** unchanged since 1.5.2: the lock changed only in the collector's own version, so
  [`THIRD_PARTY_LICENSES.csv`](THIRD_PARTY_LICENSES.csv) stands. The collector's source carries no licence text; its
  licence and the transfer of its intellectual property are a client agreement item.

## Client agreement items

The defect-support period and the transfer of intellectual property are **not agreed, and not waived**. Nothing in
this delivery states or assumes terms for them.

## Earlier deliveries

The 1.5.2 publication is unchanged at its tag, `review-1.5.2-20261103` (`c4e665c`). This publication is a new commit
after it, under its own tag, `review-1.6.5-20261104`. The 1.5.x files of `data/` and `evidence/` are unchanged; the
frozen trees are checked by [`manifests/check_frozen_trees.py`](../manifests/check_frozen_trees.py).

## Not in this delivery

- The providers' raw answers as received: protected originals kept on the workstation, with their hashes in each run
  folder's `RAW_ORIGINALS_MANIFEST.csv`.
- Credentials, the databases and their dumps, and virtual environments.
- The message to the client: a draft for Hamza, outside the repository, not sent.
- A summary PDF: none was made for 1.6.5 (N10-08, PENDING_OWNER).
