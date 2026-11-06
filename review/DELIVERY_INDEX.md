# Delivery index: Walmart collector release 1.6.8, with the shared Oxylabs Classic offline probe 1.7.2

Release 1.6.8 of the Walmart collector, commit `85c29e7b2404500299056973f50c84b84e187a5a`, in its two provider
editions (Oxylabs Web API and Scrape.do), and the shared Oxylabs Classic offline probe 1.7.2, commit `7768514aa1ffbaa7f96ca242d7b64e495fffefa5`. Store: Walmart #3891,
3900 Fountain Square Pl, Waukegan, IL 60085, fulfillment PICKUP. Prepared on 2026-11-05 and 2026-11-06 (UTC) by Hamza. The message to the client is a draft kept outside this
repository; nothing here has been sent to the client.

**What this is: a correction delivery.** It corrects the points of the client's review of 1.6.6 that code and
documents can settle, and verifies them: Classic C4 and C2 and the Linux test discrepancy (probe 1.7.2), what "complete" means, the scope that was skipped, the category
mapping, UPC and size decided apart (collector 1.6.7 and 1.6.8), the coverage tables, the unread UPCs and the 275 decisions at row level, and the 1.6.6 statements that were not accurate. The named
milestones are still pending: a demonstration of 500 or more products with detail on, on this revision, the full catalogue, the client's environment, an observed schedule, Scrape.do live and a
live Classic successor. **No live run was made on 1.6.7 or 1.6.8.** The live runs were made in the developer environment, on the owner's Oxylabs Web API trial (free credit),
each attributed to the release that ran it. No client observed or ran anything, the collector is not presented as
production-ready, and every schedule is off.

## Start here

| File | What it is |
|---|---|
| [`WALMART_1.6.8_SUMMARY.pdf`](WALMART_1.6.8_SUMMARY.pdf) | a short readable summary: what was corrected, what was verified where, coverage, and what is pending |
| [`TECHNICAL_REPORT.md`](TECHNICAL_REPORT.md) | what was fixed, what ran on this revision and where, the fifteen live runs, counts, coverage, the shared ledger, what remains, disclosures |
| [`REQUIREMENT_MATRIX.md`](REQUIREMENT_MATRIX.md) | the state of each work item (W1 to W8), Classic finding (C1 to C5), audit item (W01 to W24) and contract rule |
| [`ACCEPTANCE_MATRIX.csv`](ACCEPTANCE_MATRIX.csv) | the 206 rows, with their earlier columns as published (1.5.2, 1.6.5 and 1.6.6; their paths are at those tags), and four new columns of 1.6.8: PASS_OFFLINE 91, PASS_DEVELOPER_LIVE 66, PASS_OWNER_AZURE 5, BLOCKED_BUDGET 22, PENDING_CLIENT_AZURE 5, PENDING_OWNER 4, NOT_APPLICABLE_BY_CLARIFICATION 6, PENDING_CLIENT_DECISION 4, PENDING_OBSERVATION 3 |
| [`CORRECTION_MAP.md`](CORRECTION_MAP.md) | each correction with its cause, tests and evidence, and the pinned diffs from 1.6.6 and from 1.5.2 |
| [`CLASSIC_PROBE_CORRECTIONS.md`](CLASSIC_PROBE_CORRECTIONS.md) | C1 to C5 in the probe 1.7.2: what 1.7.0 and 1.7.1 did, what 1.7.2 completes (C2, C4), the Linux test, and the reproductions |
| [`TEST_PLAN.md`](TEST_PLAN.md) | the next live work, priced part by part, smallest first. Unapproved |
| [`MILESTONES.md`](MILESTONES.md) | what was done when, and what is open with its condition |
| [`COST_AND_RUNTIME_REPORT.md`](COST_AND_RUNTIME_REPORT.md) | the shared trial ledger per stage, measured runtimes, and the estimates for full scope |
| [`RECOVERY_AND_OPERATIONS.md`](RECOVERY_AND_OPERATIONS.md) | retention, recovery, the last-good publication, the refused publication's alert, the operator drill, concurrency, the schedule, the container |
| [`ACCEPTANCE_RUNBOOK.md`](ACCEPTANCE_RUNBOOK.md) | how to repeat the offline checks, and how the collector is installed and operated |
| [`../manifests/DOC_CORRECTIONS.md`](../manifests/DOC_CORRECTIONS.md) | the statements of the 1.6.6 publication that were not accurate, each with its correction; the errata in files that are not edited |
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
| `39cc61f61ee694c0659a611310605bee6ed42d6b` | 2026-11-04T22:34:53Z | release 1.6.6. Live run L12 |
| `cbea802891d4e66b74a0abc33e0af0af74c89708` | 2026-11-04T22:38:53Z | the builder of the 1.6.6 delivery archives (`scripts/`); it changes nothing under `headless/`. The archives of 1.6.6 name this commit (publication `4bae4fb`, tag `review-1.6.6-20261105`) |
| `7768514aa1ffbaa7f96ca242d7b64e495fffefa5` | 2026-11-05T09:21:39Z | **the shared Classic probe 1.7.2**: C2 and C4 completed, the Linux test. It changes nothing in the collector folder. The probe's tree is the same at `85c29e7` (`3ada8871`) |
| `7ee2fa1e00512a3ce7a9481268f4e5302294f94f` | 2026-11-05T10:12:41Z | release 1.6.7: prepared, never delivered; 1.6.8 carries it. No live run |
| `745607e1ffc60ffd79a35a522139729e958fbbc8`, `7a96218f5cb64c7759d5b6544da797fe381281e1`, `9c144251cc099c01e67ff6a20582d2eaddcb2adc` | 2026-11-05T16:55:59Z, 17:27:22Z, 18:56:32Z | three 1.6.8 commits, replaced before any archive was delivered ([`1.6.8-collector/`](../evidence/offline-tests/1.6.8-collector/)). No live run |
| `2cab0a26f81902b898af8da7ad10b19c7f30ad8b` | 2026-11-05T16:57:12Z | the builder of the 1.6.8 delivery archives (`scripts/`); it reads the release commit's tree |
| `85c29e7b2404500299056973f50c84b84e187a5a` | 2026-11-05T20:51:52Z | **release 1.6.8, the revision of this delivery.** Its archives' `BUILD_INFO.json` names this commit. No live run |

The development commits are local (branches `walmart-1.6` and `walmart-1.6.6`). 1.7.1's shared probe is `68ff3d8518b38a3792792ed6ffb8e73c2756245f`. This repository receives the
delivered files: the source ZIP's tree, the probe's, the product files, the evidence and the review documents. Each
run is attributed to the release that ran it and to no other.

## The folders

| Folder | What it is |
|---|---|
| [`source/`](../source/) | `WALMART_SOURCE_1.6.8.zip`, file for file: `walmart-oxylabs-1.6.8/` and `walmart-scrapedo-1.6.8/`, which differ in four edition files |
| [`classic-probe-1.7.2/`](../classic-probe-1.7.2/) | `OXYLABS_CLASSIC_OFFLINE_PROBE_1.7.2.zip`, file for file; live mode disabled |
| [`classic-probe-1.7.1/`](../classic-probe-1.7.1/), [`classic-probe-1.7.0/`](../classic-probe-1.7.0/) | the probes of the 1.6.6 and 1.6.5 deliveries, unchanged; superseded by 1.7.2 |

| [`classic-probe/`](../classic-probe/) | the Walmart Classic probe 1.5.2, as the client reviewed it, unchanged |
| [`data/`](../data/) | the product files of L10 (`L10-1.6.4/`) and L8 (`L8-1.6.3/`), the run summary, and the 1.5.x runs' files, unchanged; the run summary adds L12. L12's own export is in its run folder |
| [`evidence/live/1.6.x/`](../evidence/live/1.6.x/) | `runs/`: each run's database rows, stored pages (sanitized, with the SHA-256 of each private original), exports and coverage, L12's included; `campaign/`: the harness, step definitions, commands and logs, checks, and the shared ledger's Walmart extract; `builds/`: the Oxylabs edition ZIP of each release that ran live, 1.6.6's included |
| [`evidence/offline-tests/`](../evidence/offline-tests/) | per release (`1.6.0-collector/` to `1.6.6-collector/`, `1.6.8-collector/`, `1.7.0-classic-probe/` to `1.7.2-classic-probe/`): its diff, its tests run against the release before, and its suites on its commit |
| [`evidence/verification/1.6.8/`](../evidence/verification/1.6.8/) | the clean-extraction verification of both editions on Windows with the Bicep checks (`package/`), and the last-good publication check (`last_good_publication/`). The records of 1.6.1, 1.6.4, 1.6.5 and 1.6.6 stay beside it; the top of `evidence/verification/` is release 1.5.2's record |
| [`evidence/owner-azure-test/1.6.8/`](../evidence/owner-azure-test/1.6.8/) | the owner's Azure test VM, Linux: the qualification of both editions, the operator drill, the container gate, the probe, the recording's source and the host's state before and after |
| [`evidence/reconciliation/`](../evidence/reconciliation/) | `1.6.8/`: W2 (the blanks rechecked), W3 (the 275 at row level), W4 and the continuation estimate. Earlier tables stay beside it: W2 (`1.6.3/w2/`), W3 (`1.6.1/w3/`), W4 and the measured concurrency (`1.6.5/`, `1.6.6/`) |
| [`review/`](.) | this index and the review documents |
| [`manifests/`](../manifests/) | the file map, the redactions, the exclusions, the documentation corrections, the publication record, the data and tree checks, and `SHA256SUMS.txt` |
| [`walkthrough/`](../walkthrough/) | the 1.6.8 recording on the owner's VM (no live run), and the 1.5.2 recording, unchanged |

## The product files

| Folder | Release that collected it | Rows | What it is |
|---|---|---|---|
| [`data/L10-1.6.4/`](../data/L10-1.6.4/) | 1.6.4 (`28ac7d3`) | `products_fresh`: 7,057 (7,055 valid); `products_retained`: 10,301 | the census, detail reading off. Its export passes 1.6.5's `validate-export --run`. L12's export passes 1.6.6's; its 10,301 retained rows are L10's, except the products that L11b (35) and L12 (40) read again. Its names are as collected ([`TECHNICAL_REPORT.md`](TECHNICAL_REPORT.md), section 8) |
| [`data/L8-1.6.3/`](../data/L8-1.6.3/) | 1.6.3 (`def55e5`) | `products_fresh`: 675; `products_retained`: 2,515 | the last demonstration of 500 or more with detail reading on |

Each has a CSV and a JSON of each file, the 22 fields in order, all strings, the four deal fields `""` in every row.
A carried row keeps its own run and date. `data/RUN_SUMMARY.json` gives each file's SHA-256 and row count, and
[`manifests/check_data.py`](../manifests/check_data.py) checks them against their runs' exports. L12 (40 fresh
valid products, a canary) has no folder in `data/`: its exports are in
[`evidence/live/1.6.x/runs/L12_01M6MC7YE4PBXV88G3PJ5ENW4B/exports/`](../evidence/live/1.6.x/runs/L12_01M6MC7YE4PBXV88G3PJ5ENW4B/exports/).

## Known limitations

1. **No live run on 1.6.7 or 1.6.8, so no demonstration of 500 or more with detail on, on this revision.** L12 on 1.6.6 read with detail on, but
   it is a canary: 40 fresh valid, 10 product pages, UPC 27 of 40. The last demonstration of that size is L8 on
   1.6.3 (675 fresh valid). The one on 1.6.8 is capped at 45 submissions, USD 0.0675; Walmart's
   envelope has USD 0.003 left, and the ceiling is 0 (N1A-05, BLOCKED_BUDGET).
2. **What 1.6.8 now reads has not been seen live.** The category pages of their own, and a listing behind a filtered link, are tested on synthetic pages and on stored links only. Their requests and yields are
   priced as assumptions in [`TEST_PLAN.md`](TEST_PLAN.md).
3. **Not the full catalogue.** No CSV row is complete (0 of 11); 464 listings were never reached and 95 category pages of their own were never read. The continuation
   is priced in [`TEST_PLAN.md`](TEST_PLAN.md), part by part. Product pages are the largest part.
4. **The flat price layout, live.** The source check's reading of it (1.6.5 and later) is verified offline on the
   authentic stored page and on L10's records from it. No live run since has checked a page in that layout.
5. **Two L10 rows without a price.** Their page showed them with no price at all. They are in L10's fresh export with
   empty prices, marked `exported_not_valid` in `record_map.json`, and are not counted among the 7,055.
6. **Partitions live at depth 1 only** (21 child listings); the second level is tested offline (A18).
7. **Recovery live on 1.6.1 to 1.6.3.** On 1.6.8 it ran in the suites, in the container and in the drill, on stored and synthetic pages.
8. **The container ran on the owner's VM, not the client's.** The client's VM is deallocated (the client's statement);
   access waits for the client: a restart and its window, the new public key installed and the old one revoked.
9. **The full integration suite ran on Linux, not on Windows.** On Windows the unit suite and the files the change touches ran, each in its own process ([`TECHNICAL_REPORT.md`](TECHNICAL_REPORT.md), section 3).
10. **Scrape.do has no 1.6.x live run**; no Scrape.do spending was authorized.
11. **Memory under a live load was not measured.** On the owner's Azure test VM (2 vCPU, 3.9 GB of memory), the delivered Oxylabs edition of 1.6.8 replayed L10 from its stored pages, on the host rather than in Docker: 424 pages and 6,880 valid records (the container's replay gave the same), in 511.5 s of wall time and 212 s of CPU. A replay serves the stored pages through one session, so it ran one worker in one process; L10 itself ran two. That process's resident memory peaked at 1.38 GiB by the kernel's count (1.31 GiB in samples every 0.25 s), and the host never had less than 1.75 GiB available ([`memory/`](../evidence/owner-azure-test/1.6.8/memory/)). A replay makes no request, so this is not a live run's measurement.
12. **The published L10 and L12 files keep the names they were collected with** ("Fabric Softener" in L12; "Subscription", "Cough" and "Great Value Pantry" in L10's). 1.6.8 corrects the rule, on later runs and on carried rows. The files are not edited ([`TECHNICAL_REPORT.md`](TECHNICAL_REPORT.md), section 8).
13. **`validate-export --run` needs every stored page its records cite**, earlier runs' pages included, since it checks each
   record against its own page. If one is missing on the host, it exits 2 (`CONFIG_INVALID`) and its message names only
   the missing file. With all stored pages in place, it passed for each replay on 1.6.8 ([`IMAGES.md`](../evidence/owner-azure-test/1.6.8/container/IMAGES.md)).


## Accounts, external services, licensing and costs

- **Oxylabs Web API:** the owner's trial account (free credit at the documented rate), designated by Hamza, through the shared ledger: Walmart committed
  USD 2.247 of its USD 2.25 envelope, Mariano's nothing of its own (see
  [`COST_AND_RUNTIME_REPORT.md`](COST_AND_RUNTIME_REPORT.md)). The provider-side balance is UNVERIFIED: the Web API
  has no balance endpoint, and the dashboard is the owner's.
- **Scrape.do:** not used in this delivery.
- **Azure:** nothing deployed. The Bicep templates were built and linted offline. Hamza's own Azure test VM ran this delivery's gates; its compute is his. The client's VM is
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

The 1.5.2, 1.6.5 and 1.6.6 publications are unchanged at their tags, `review-1.5.2-20261103` (`c4e665c`),
`review-1.6.5-20261104` (`bcb53e8`) and `review-1.6.6-20261105` (`4bae4fb`). This publication is a new commit after 1.6.6's, under its own tag,
`review-1.6.8-20261106`. The 1.5.x files of `data/` and `evidence/`, `classic-probe/`, `classic-probe-1.7.0/` and `classic-probe-1.7.1/` are
unchanged; the frozen trees are checked by [`manifests/check_frozen_trees.py`](../manifests/check_frozen_trees.py).


## Not in this delivery

- The providers' raw answers as received: protected originals kept on the workstation, with their hashes in each run
  folder's `RAW_ORIGINALS_MANIFEST.csv`.
- Credentials, the databases and their dumps, and virtual environments.
- The Scrape.do edition ZIP as a file: its tree is in `source/walmart-scrapedo-1.6.8/`, and its SHA-256 is in
  [`evidence/verification/1.6.8/package/README.txt`](../evidence/verification/1.6.8/package/README.txt).
- The message to the client: a draft for Hamza, outside the repository, not sent.
