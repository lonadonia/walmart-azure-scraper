# Delivery index: Walmart collector release 1.6.6, with the shared Oxylabs Classic offline probe 1.7.1

Release 1.6.6 of the Walmart collector, commit `39cc61f61ee694c0659a611310605bee6ed42d6b`, in its two provider
editions (Oxylabs Web API and Scrape.do), built at `cbea802891d4e66b74a0abc33e0af0af74c89708`, and the shared Oxylabs
Classic offline probe 1.7.1. Store: Walmart #3891, 3900 Fountain Square Pl, Waukegan, IL 60085, fulfillment PICKUP.
Prepared on 2026-11-04 and 2026-11-05 (UTC) by Hamza. The message to the client is a draft kept outside this
repository; nothing here has been sent to the client.

**What this is: a correction delivery.** It corrects the points of the client's review of 1.6.5 that code and
documents can settle, and verifies them: Classic C2 and C4 (probe 1.7.1), the alert for a refused automatic
publication (collector 1.6.6), and the 1.6.5 statements that were not accurate. The named milestones are still
pending: a demonstration of 500 or more products with detail on, on the final revision (L12 is a 40-product canary
of it), the full catalogue, the client's environment, an observed schedule, a container build, Scrape.do live and a
live Classic successor. The live runs were made in the developer environment, on the user's Oxylabs Web API trial,
each attributed to the release that ran it. No client observed or ran anything, the collector is not presented as
production-ready, and every schedule is off.

## Start here

| File | What it is |
|---|---|
| [`TECHNICAL_REPORT.md`](TECHNICAL_REPORT.md) | what was fixed, what ran on the final revision and where, the fifteen live runs, counts, coverage, the shared ledger, what remains, disclosures |
| [`REQUIREMENT_MATRIX.md`](REQUIREMENT_MATRIX.md) | the state of each work item (W1 to W8), Classic finding (C1 to C5), audit item (W01 to W24) and contract rule |
| [`ACCEPTANCE_MATRIX.csv`](ACCEPTANCE_MATRIX.csv) | the 206 rows, with their 1.5.2 columns as published then (their `source/walmart-*-1.5.2/` paths are at the tag `review-1.5.2-20261103`), the four columns of 1.6.5, and four new columns of 1.6.6: PASS_OFFLINE 90, PASS_DEVELOPER_LIVE 66, BLOCKED_BUDGET 22, PENDING_CLIENT_AZURE 8, PENDING_OWNER 7, NOT_APPLICABLE_BY_CLARIFICATION 6, PENDING_CLIENT_DECISION 4, PENDING_OBSERVATION 3 |
| [`CORRECTION_MAP.md`](CORRECTION_MAP.md) | each correction with its cause, tests and live evidence, and the pinned diff from 1.5.2 |
| [`CLASSIC_PROBE_CORRECTIONS.md`](CLASSIC_PROBE_CORRECTIONS.md) | C1 to C5 in the probe 1.7.1: what 1.7.0 did, what 1.7.1 completes (C2, C4), and the reproductions |
| [`TEST_PLAN.md`](TEST_PLAN.md) | the next live work, priced, smallest first. Unapproved |
| [`MILESTONES.md`](MILESTONES.md) | what was done when, and what is open with its condition |
| [`COST_AND_RUNTIME_REPORT.md`](COST_AND_RUNTIME_REPORT.md) | the shared trial ledger per stage, measured runtimes, and the estimates for full scope |
| [`RECOVERY_AND_OPERATIONS.md`](RECOVERY_AND_OPERATIONS.md) | retention, recovery, the last-good publication, the refused publication's alert, concurrency, the schedule, the container |
| [`ACCEPTANCE_RUNBOOK.md`](ACCEPTANCE_RUNBOOK.md) | how to repeat the offline checks, and how the collector is installed and operated |
| [`../manifests/DOC_CORRECTIONS.md`](../manifests/DOC_CORRECTIONS.md) | the statements of the 1.6.5 publication that were not accurate, each with its correction |
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
| `67d216eb8ee2ec839a437b0b5bf2d594324b6982` | 2026-11-04T14:15:19Z | release 1.6.5 (publication `bcb53e8`, tag `review-1.6.5-20261104`). Live runs L11 and L11b; the re-validation of L10's and L8's exports |
| `2c085850b622330083eb4c7bdeb90f075e4f99db`, `48307cf20c6708fb57352559a113ed5bc65cb3e1` | 2026-11-03 | the shared Classic probe 1.7.0: its code, then its documents. Superseded by 1.7.1 |
| `6b9be92aa4fb8f5d18e1085316c20dd787690a86` | 2026-11-04T15:16:32Z | the builders of the 1.6.4 and 1.6.5 delivery archives (`scripts/`); it changes nothing under `headless/` |
| `68ff3d8518b38a3792792ed6ffb8e73c2756245f` | 2026-11-04T22:25:51Z | the shared Classic probe 1.7.1: C2 and C4 completed. It changes nothing in the collector folder |
| `39cc61f61ee694c0659a611310605bee6ed42d6b` | 2026-11-04T22:34:53Z | **release 1.6.6, the final revision**: a refused automatic publication is an `ERROR` and exits 6. Live run L12 |
| `cbea802891d4e66b74a0abc33e0af0af74c89708` | 2026-11-04T22:38:53Z | the builder of the 1.6.6 delivery archives (`scripts/`); it changes nothing under `headless/`. The archives' `BUILD_INFO.json` names this commit |

The development commits are local (branches `walmart-1.6` and `walmart-1.6.6`). This repository receives the
delivered files: the source ZIP's tree, the probe's, the product files, the evidence and the review documents. Each
run is attributed to the release that ran it and to no other.

## The folders

| Folder | What it is |
|---|---|
| [`source/`](../source/) | `WALMART_SOURCE_1.6.6.zip`, file for file: `walmart-oxylabs-1.6.6/` and `walmart-scrapedo-1.6.6/`, which differ in four edition files |
| [`classic-probe-1.7.1/`](../classic-probe-1.7.1/) | `OXYLABS_CLASSIC_OFFLINE_PROBE_1.7.1.zip`, file for file; live mode disabled |
| [`classic-probe-1.7.0/`](../classic-probe-1.7.0/) | the probe 1.7.0 of the 1.6.5 delivery, unchanged; superseded by 1.7.1 |
| [`classic-probe/`](../classic-probe/) | the Walmart Classic probe 1.5.2, as the client reviewed it, unchanged |
| [`data/`](../data/) | the product files of L10 (`L10-1.6.4/`) and L8 (`L8-1.6.3/`), the run summary, and the 1.5.x runs' files, unchanged; the run summary adds L12. L12's own export is in its run folder |
| [`evidence/live/1.6.x/`](../evidence/live/1.6.x/) | `runs/`: each run's database rows, stored pages (sanitized, with the SHA-256 of each private original), exports and coverage, L12's included; `campaign/`: the harness, step definitions, commands and logs, checks, and the shared ledger's Walmart extract; `builds/`: the Oxylabs edition ZIP of each release that ran live, 1.6.6's included |
| [`evidence/offline-tests/`](../evidence/offline-tests/) | per release (`1.6.0-collector/` to `1.6.6-collector/`, `1.7.0-classic-probe/`, `1.7.1-classic-probe/`): its diff, its tests run against the release before, and its suites on its commit |
| [`evidence/verification/1.6.6/`](../evidence/verification/1.6.6/) | the clean-extraction verification of both editions with the Bicep checks (`package/`), and the last-good publication check (`last_good_publication/`). The records of 1.6.1, 1.6.4 and 1.6.5 stay beside it; the top of `evidence/verification/` is release 1.5.2's record |
| [`evidence/reconciliation/`](../evidence/reconciliation/) | W2 (`1.6.3/w2/`), W3 (`1.6.1/w3/`), W4 and the measured concurrency (`1.6.6/`, which adds L12's page to `1.6.5/`'s tables, kept) |
| [`review/`](.) | this index and the review documents |
| [`manifests/`](../manifests/) | the file map, the redactions, the exclusions, the documentation corrections, the publication record, the data and tree checks, and `SHA256SUMS.txt` |
| [`walkthrough/`](../walkthrough/) | the 1.5.2 recording, unchanged; no 1.6.x recording was made |

## The product files

| Folder | Release that collected it | Rows | What it is |
|---|---|---|---|
| [`data/L10-1.6.4/`](../data/L10-1.6.4/) | 1.6.4 (`28ac7d3`) | `products_fresh`: 7,057 (7,055 valid); `products_retained`: 10,301 | the census, detail reading off. Its export passes 1.6.5's `validate-export --run`. L12's export passes 1.6.6's; its 10,301 retained rows are L10's, except the products that L11b (35) and L12 (40) read again |
| [`data/L8-1.6.3/`](../data/L8-1.6.3/) | 1.6.3 (`def55e5`) | `products_fresh`: 675; `products_retained`: 2,515 | the last demonstration of 500 or more with detail reading on |

Each has a CSV and a JSON of each file, the 22 fields in order, all strings, the four deal fields `""` in every row.
A carried row keeps its own run and date. `data/RUN_SUMMARY.json` gives each file's SHA-256 and row count, and
[`manifests/check_data.py`](../manifests/check_data.py) checks them against their runs' exports. L12 (40 fresh
valid products, a canary) has no folder in `data/`: its exports are in
[`evidence/live/1.6.x/runs/L12_01M6MC7YE4PBXV88G3PJ5ENW4B/exports/`](../evidence/live/1.6.x/runs/L12_01M6MC7YE4PBXV88G3PJ5ENW4B/exports/).

## Known limitations

1. **No demonstration of 500 or more with detail on, on the final revision.** L12 on 1.6.6 read with detail on, but
   it is a canary: 40 fresh valid, 10 product pages, UPC 27 of 40. The last demonstration of that size is L8 on
   1.6.3 (675 fresh valid). The one on 1.6.6 needs about 28 to 45 submissions (at most about USD 0.07); Walmart's
   envelope has USD 0.003 left (N1A-05, BLOCKED_BUDGET).
2. **Not the full catalogue.** No CSV row is complete (0 of 11); 407 listings were never reached. The continuation
   is priced in [`TEST_PLAN.md`](TEST_PLAN.md).
3. **The flat price layout, live.** The source check's reading of it (1.6.5 and later) is verified offline on the
   authentic stored page and on L10's records from it. No live run of 1.6.5 or 1.6.6 checked a page in that layout:
   L11 meant to, and its listing was rejected for its identity; L12's page gives its prices in price lines.
4. **Two L10 rows without a price.** Their page showed them with no price at all. They are in L10's fresh export with
   empty prices, marked `exported_not_valid` in `record_map.json`, and are not counted among the 7,055.
5. **Partitions live at depth 1 only** (21 child listings); the second level is tested offline (A18).
6. **Recovery live on 1.6.1 to 1.6.3.** It was not repeated live on 1.6.4 to 1.6.6, which did not change it.
7. **No container build of 1.6.6**: the workstation has no container runtime, and the client's VM is deallocated.
8. **Scrape.do has no 1.6.x live run**; no Scrape.do spending was authorized.
9. **Memory under load was not measured.**
10. **L12's rows name their subcategory "Fabric Softener"**, from the listing's path; the site says "Fabric
    Softeners" ([`TECHNICAL_REPORT.md`](TECHNICAL_REPORT.md), section 8).

The tenth limitation of 1.6.5, a refused automatic publication that exited 0 with a `WARN`, is corrected in 1.6.6
([`RECOVERY_AND_OPERATIONS.md`](RECOVERY_AND_OPERATIONS.md), section 3).

## Accounts, external services, licensing and costs

- **Oxylabs Web API:** the user's trial account, designated by Hamza, through the shared ledger: Walmart committed
  USD 2.247 of its USD 2.25 envelope, Mariano's nothing of its own (see
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

The 1.5.2 and 1.6.5 publications are unchanged at their tags, `review-1.5.2-20261103` (`c4e665c`) and
`review-1.6.5-20261104` (`bcb53e8`). This publication is a new commit after 1.6.5's, under its own tag,
`review-1.6.6-20261105`. The 1.5.x files of `data/` and `evidence/`, `classic-probe/` and `classic-probe-1.7.0/` are
unchanged; the frozen trees are checked by [`manifests/check_frozen_trees.py`](../manifests/check_frozen_trees.py).

## Not in this delivery

- The providers' raw answers as received: protected originals kept on the workstation, with their hashes in each run
  folder's `RAW_ORIGINALS_MANIFEST.csv`.
- Credentials, the databases and their dumps, and virtual environments.
- The Scrape.do edition ZIP as a file: its tree is in `source/walmart-scrapedo-1.6.6/`, and its SHA-256 is in
  [`evidence/verification/1.6.6/package/README.txt`](../evidence/verification/1.6.6/package/README.txt).
- The message to the client: a draft for Hamza, outside the repository, not sent.
- A summary PDF: none was made for 1.6.6 (N10-08, PENDING_OWNER).
