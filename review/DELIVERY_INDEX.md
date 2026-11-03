# Delivery index: Walmart collector release 1.5.2, with the Oxylabs Classic offline probe 1.5.2

> **Published copy.** This is the delivery's index as published in this repository. Its paths are rewritten to
> the repository's, and the rows of files that are not published here are removed or marked:
> [`manifests/DOC_CORRECTIONS.md`](../manifests/DOC_CORRECTIONS.md) lists each change. What it says of the
> delivery folder (what was sent, what was pushed) describes that folder as prepared on 2026-11-02.

Delivery folder: deliverables/20261102_walmart_1.5.2. Release 1.5.2 of the Walmart collector, commit
627c804d66aa33fc423fd2296c8896c5d5c2c3d4, in its two provider editions (Oxylabs Web API and Scrape.do), and the
Oxylabs Classic offline probe 1.5.2, built from the same commit. Store: Walmart #3891, 3900 Fountain Square Pl,
Waukegan, IL 60085, fulfillment PICKUP. Prepared on 2026-11-02 (UTC) by Hamza. Nothing in this folder has been sent to
the client.

**What this is: a correction update.** Release 1.5.2 fixes the known defects of release 1.5.1 and is verified offline
against the pages the live runs stored. It has not run live, so it is not an acceptance candidate and not an accepted
release. The last live evidence is run S6 on release 1.5.1 (`488a033`) and the runs on release 1.5.0 (`7b6f325`), and
it stays attributed to those revisions. No client observed or ran anything. This is not the full catalogue, the
collector is not production-ready, and every schedule is off.

## Start here

| File | What it is |
|---|---|
| [`TECHNICAL_REPORT.md`](TECHNICAL_REPORT.md) | the gap list, each fix with before and after, what ran where, counts and recovery, usage, what remains |
| [`TEST_PLAN.md`](TEST_PLAN.md) | **the one consolidated request**: the live stages, their cost and dated milestones. Unapproved |
| [`ACCEPTANCE_MATRIX.csv`](ACCEPTANCE_MATRIX.csv) | 206 rows with status: 103 VERIFIED OFFLINE, 49 VERIFIED LIVE, 32 PARTIAL, 18 BLOCKED, 4 NOT TESTED |
| [`walkthrough/WALKTHROUGH_1.5.2.mp4`](../walkthrough/WALKTHROUGH_1.5.2.mp4), [`evidence/owner-azure-test/1.5.2/walkthrough/WALKTHROUGH_1.5.2.cast`](../evidence/owner-azure-test/1.5.2/walkthrough/WALKTHROUGH_1.5.2.cast) | the recorded terminal walkthrough on the owner's test VM (see [`evidence/owner-azure-test/1.5.2/azure_docker_recovery/README.txt`](../evidence/owner-azure-test/1.5.2/azure_docker_recovery/README.txt)). It holds no live provider run |
| [`evidence/verification/PACKAGE_VERIFICATION.txt`](../evidence/verification/PACKAGE_VERIFICATION.txt) | the result of verifying this delivery from clean extractions, written after the files above |
| [`manifests/SHA256SUMS.txt`](../manifests/SHA256SUMS.txt) | the SHA-256 of every other file of this repository, written last. It replaces the delivery's own list, which named files not published here |

**The matrix.** Its rows are the 171 of release 1.5.1, with their text unchanged and this release's response, and 35 rows
for the brief of 2026-11-01. Each row gives the baseline issue, the implementation, the evidence paths, the evidence
class, the status, the revision that produced the evidence, the result per provider edition, what remains and its
blocker. Rows are not equal and are not added up, so there is no overall percentage.

## Every file

| Path | What it is |
|---|---|
| `DELIVERY_INDEX.md` | this index |
| [`source/`](../source/) | the complete source of release 1.5.2: file for file the source ZIP `WALMART_SOURCE_1.5.2.zip` (SHA-256 1100aa16ce7d459afd020c057eff3fb42cd54bcc172a4c22f04ba3f1859af941), which is not republished as an archive (see the note below the table) |
| [`evidence/`](../evidence/) | the evidence by class, from the evidence ZIP `WALMART_EVIDENCE_1.5.2.zip` (1,364 files; SHA-256 256b968ea2502a233a16828797ae90e359bf5bdbcb78551cea3800c12c187baa). Folders 1 to 6 are those of 1.5.1, byte for byte. Folder 7 is this release. Its `README.md` explains each ([`evidence/as-packaged/README.md`](../evidence/as-packaged/README.md)), and [`evidence/README.md`](../evidence/README.md) gives the repository folder of each |
| [`classic-probe/`](../classic-probe/) | the Classic probe, file for file the probe ZIP `OXYLABS_CLASSIC_OFFLINE_PROBE_1.5.2.zip` (SHA-256 d4785ccbb8b23a4d2bb6cfb6b16ba1242cab5cab0b292e3222581f7844282193): source, lock, payload plan, shared limits, tests, offline results and the saved Oxylabs documentation. Its live mode is disabled, and it holds no credential |
| [`data/RUN_SUMMARY.json`](../data/RUN_SUMMARY.json), [`data/S6-1.5.1/`](../data/S6-1.5.1/), [`data/S7-1.5.1/`](../data/S7-1.5.1/), [`data/S4-1.5.0/`](../data/S4-1.5.0/) | **the live product files of 2026-10-31, unchanged**: byte for byte those of the 1.5.1 delivery. [`data/S6-1.5.1/products_fresh.json`](../data/S6-1.5.1/products_fresh.json) holds run S6's 580 fresh products |
| [`evidence/offline-replay/1.5.2/offline_reprocessing/`](../evidence/offline-replay/1.5.2/offline_reprocessing/) | **OFFLINE REPLAY and OFFLINE REPROCESSING by 1.5.2**: S6 and B3 read again, with their correction maps. Not a new collection. [`evidence/offline-replay/1.5.2/offline_reprocessing/README.txt`](../evidence/offline-replay/1.5.2/offline_reprocessing/README.txt) explains each file |
| [`evidence/owner-azure-test/1.5.2/azure_docker_recovery/`](../evidence/owner-azure-test/1.5.2/azure_docker_recovery/) | **OWNER AZURE TEST**: on the owner's test VM, the Docker build of both editions, and in the Oxylabs edition's container the nine replays with a stop, a kill and their resumes; the suites, load and publication faults from the source ZIP. [`evidence/owner-azure-test/1.5.2/azure_docker_recovery/README.txt`](../evidence/owner-azure-test/1.5.2/azure_docker_recovery/README.txt) gives the results and [`evidence/owner-azure-test/1.5.2/azure_docker_recovery/DOCKER_VM_RESULT.json`](../evidence/owner-azure-test/1.5.2/azure_docker_recovery/DOCKER_VM_RESULT.json) the record |
| [`data/COVERAGE_RECONCILIATION.csv`](../data/COVERAGE_RECONCILIATION.csv) | coverage per CSV row, listing, child listing and page. No row is complete |
| [`evidence/reconciliation/1.5.2/sponsored_and_variant_reconciliation/SPONSORED_AND_VARIANT_RECONCILIATION_1_5_2.csv`](../evidence/reconciliation/1.5.2/sponsored_and_variant_reconciliation/SPONSORED_AND_VARIANT_RECONCILIATION_1_5_2.csv) | the 651 sponsored-only, tile-only and variant rows, one by one, each with what closes it |
| [`evidence/reconciliation/1.5.2/sponsored_and_variant_reconciliation/EXACT_LIVE_READ_QUEUE_1_5_2.csv`](../evidence/reconciliation/1.5.2/sponsored_and_variant_reconciliation/EXACT_LIVE_READ_QUEUE_1_5_2.csv) | the 275 distinct items that still need their own page read, with the reason. It is not a run. |
| [`evidence/reconciliation/1.5.1/coverage_and_queues/FOLLOW_UP_QUEUE_RECONCILIATION_1_5_1.csv`](../evidence/reconciliation/1.5.1/coverage_and_queues/FOLLOW_UP_QUEUE_RECONCILIATION_1_5_1.csv) | the follow-up queues by kind and state, carried from 1.5.1 |
| [`LINKED_EXAMPLES.csv`](LINKED_EXAMPLES.csv) | 54 examples, each linked to its stored page and that page's hash. E049 to E054 are this release's |
| [`COST_AND_RUNTIME_REPORT.md`](COST_AND_RUNTIME_REPORT.md) | usage of this release, the measured stages, the load test and the full-scope estimates |
| [`ACCEPTANCE_RUNBOOK.md`](ACCEPTANCE_RUNBOOK.md) | how to repeat every offline check, the Docker commands and the live sequence for the client to observe |
| [`classic-probe/oxylabs-classic-probe/CLASSIC_TEST_PLAN.md`](../classic-probe/oxylabs-classic-probe/CLASSIC_TEST_PLAN.md) | the proposed Classic campaign, **unapproved**. What Azure access would need was drafted as a separate request, which is not published here |
| [`evidence/live/plan/CAMPAIGN_BUDGET.json`](../evidence/live/plan/CAMPAIGN_BUDGET.json) | the campaign's budget and ledger reconciliation, byte for byte the 1.5.1 file: 119 of 120 rows, not reset |
| [`THIRD_PARTY_LICENSES.csv`](THIRD_PARTY_LICENSES.csv) | the 53 packages of the locked environment, byte for byte the 1.5.1 file: this release changed only the project's own version in the lock |
| [`manifests/SOURCE_AND_RUN_MANIFEST.json`](../manifests/SOURCE_AND_RUN_MANIFEST.json) | the revisions, the ZIPs and their hashes, the editions, every run and replay |
| [`evidence/verification/`](../evidence/verification/) | the raw record of the verification: each step's log, the JUnit XML and the data checks. The verifier's own scripts are not published ([`manifests/EXCLUDED.csv`](../manifests/EXCLUDED.csv)) |

**The source.** [`source/`](../source/) is the source ZIP's top folder walmart-source-1.5.2. It holds walmart-oxylabs-1.5.2 and walmart-scrapedo-1.5.2, one per
edition. Each edition has 216 files and runs on its own. The two differ only in `.env.example`, `BUILD_INFO.json`,
`EDITION.json` and `config/collector.yaml`.

**Superseded documents.** The 1.5.1 plan of the live campaign is not repeated here: [`TEST_PLAN.md`](TEST_PLAN.md) is now the plan of the
next live work. The campaign's plan stays in [`evidence/live/plan/`](../evidence/live/plan/). `VIDEO_STORYBOARD.md` is gone
because the walkthrough is now recorded.

## Revisions

| Commit | What it is |
|---|---|
| 37ffca808f2163287e3d50b91529c5fd69213418 | release 1.4.1, reviewed by the client. Run B3 |
| 7b6f3258e0f4ab755732605eb88717c592d07073 | release 1.5.0. Live runs S1 to S5 |
| 488a033fc22d09db9f6270feae274d8c77963d6f | release 1.5.1. Live runs S6 and S7 |
| 2ed64b70809a67c49c68ebda5e3c3420f079073b | release 1.5.2, first commit: the corrections below, and the Classic probe's last code change |
| 627c804d66aa33fc423fd2296c8896c5d5c2c3d4 | **release 1.5.2, final revision**: adds the fix for a row carried from a replay. The replays, the source ZIP and the probe ZIP |
| the packaging commit ([`manifests/SOURCE_AND_RUN_MANIFEST.json`](../manifests/SOURCE_AND_RUN_MANIFEST.json), revisions.packaging) | adds the delivery builder and verifier under scripts/ and changes nothing under headless/ |

All commits are local (branch walmart-1.5.2), and nothing was pushed. Each run is attributed to the revision that ran it
and to no other.

## What changed since release 1.5.1

Each change has a regression test in the source's `tests/`. [`TECHNICAL_REPORT.md`](TECHNICAL_REPORT.md), section 3, gives each with its before and
after.

- **Provenance.** `provenance.json`, `record_map.json` and `field_dispositions.json` now name the same capture, place in the
  response, time, product, run and revision for a recovered value. This closes erratum 3 of the 1.5.1 index.
- **Sizes.** A pack beside a size is kept, and a pack stated twice is stated once. The five carried rows and the "2 pack, 1
  Pack" row of the 1.5.1 errata now read correctly in the replays, and the delivered live files are not rewritten.
- **Failure classes.** A blocked page and a failed request are separate outcomes, `blocked` and `request_failed`, in place
  of `inaccessible_challenged`. A page never read is never `source_absent`.
- **Private label.** Six brands were added from USPTO records, with their limits, in the source's `docs/PRIVATE_LABEL.md`.
- **Replay resume.** An interrupted replay now resumes as a replay. It used to build the live collector, and so could not
  finish offline.
- **A row carried from a replay.** It now names the live run that fetched its page, and the replay as `read_again_by_run`. The
  check of the three files against each other found this defect, on the first replays of `2ed64b7`.
- **Tests.** Deterministic-simulation cases for size and pack rules, and a concurrency load test against a local fixture.

**Test expectations.** No assertion was removed. Where 1.5.2 changes a behaviour on purpose, the test states the new
behaviour, and `git diff 488a033 627c804 -- headless/walmart-azure-headless/tests` shows each one.

**The offer readers did not change** (`git diff 488a033 627c804` shows nothing in `assembly/offers.py`), so the offer
search of 1.5.1 stands, and it was not rerun.

## What ran for this release

| What | Where | Class |
|---|---|---|
| Nine replays of the campaign, twice on separate copies | the workstation | OFFLINE REPLAY |
| B3 replay, with the saved product pages of ten earlier runs | the workstation | OFFLINE REPROCESSING |
| The agreement of the provenance files with the stored bytes, ten exports | the workstation | OFFLINE REPLAY |
| Docker build and run of both editions, from the source ZIP | the owner's Azure test VM | OWNER AZURE TEST |
| Stop, kill and resume, in the container, on replays | the owner's Azure test VM | OWNER AZURE TEST |
| Load test with a local fixture | the workstation and the VM | SYNTHETIC TEST |
| Publication faults | the owner's Azure test VM | SYNTHETIC TEST |
| The full clean-extraction verification | the workstation | [`evidence/verification/PACKAGE_VERIFICATION.txt`](../evidence/verification/PACKAGE_VERIFICATION.txt) |

**No live request was made.** Oxylabs Web API stays at 119 of 120 rows, Scrape.do at 10 credits left, and Classic at no access.

## The product files

- **Which file is authoritative.** The live record is [`data/S6-1.5.1/products_fresh.json`](../data/S6-1.5.1/products_fresh.json), what run S6 exported. Its corrected
  reading by 1.5.2 is [`evidence/offline-replay/1.5.2/offline_reprocessing/S6_products_fresh_OFFLINE_REPLAY.json`](../evidence/offline-replay/1.5.2/offline_reprocessing/S6_products_fresh_OFFLINE_REPLAY.json). It is not a new collection, and
  there is no merged dataset. Oxylabs and Scrape.do rows are never mixed.
- **Fresh and retained.** A fresh file holds what a run observed itself. A retained file adds rows carried from earlier
  runs, each with its own run, time and stored page. Carried rows are never counted as fresh.
- **Fields.** 22 fields in order, all strings, `""` for a missing value. `gupc` and `unit_price` are always empty. PPM is as
  displayed. `crawl_date` is the store-local date (America/Chicago) of the row's own observation.
- **Blank UPCs and sizes in S6, read again by 1.5.2:**

  | Field | Present in the listing | Recovered from a saved page | Absent from its page | Conflict | Page not read |
  |---|---:|---:|---:|---:|---:|
  | UPC | 0 | 353 | 1 | 0 | 226 |
  | Size | 555 | 12 | 3 | 1 | 9 |

  Live, S6 fetched 1 of those UPCs and recovered 352. Its blanks of pages not read said `budget_deadline_interruption`, and a
  replay says `not_attempted`, because a replay fetches nothing. Either way, the page has not been read.

## How to read a path into a ZIP

The delivery wrote a file inside an archive as `ZIP: path`, below the archive's single top folder. In this
repository's review documents those references are rewritten to repository paths. The evidence files and the JSON
records keep them as written: [`evidence/README.md`](../evidence/README.md) gives the repository folder of each archive
folder, and [`manifests/FILE_MAP.csv`](../manifests/FILE_MAP.csv) maps every file. The archive's [`EVIDENCE_MANIFEST.csv`](../evidence/as-packaged/EVIDENCE_MANIFEST.csv)
lists each file with its class and SHA-256 as packaged, [`SANITIZATION_LOG.csv`](../evidence/as-packaged/SANITIZATION_LOG.csv) lists each file
changed when packaged, and [`SANITIZATION.md`](../evidence/as-packaged/SANITIZATION.md) explains the rules. The files changed again for
this publication are listed in [`manifests/REDACTIONS.csv`](../manifests/REDACTIONS.csv).

## Known limitations and errata

**Closed from the 1.5.1 index.** Erratum 2 (five carried sizes), 3 (provenance of a recovered size) and 5 (a pack stated
twice), by offline replay. A carried row in a delivered live file keeps what that run exported.

1. **Erratum to the 1.5.1 index: S3, not S4.** It said S4 observed the five carried Dry Dog Food rows. Run S3 observed them
   (`01M69Y1J6YWFEZ1DJHAC2MT17M`, 2026-10-31T21:33:20Z, page `01M69Y3901A9Q22MBPXAVG92Y5`), as the run's own `record_map.json` says.
2. **No live validation of 1.5.2.** Every correction is verified offline only. A stored page says what it said on its date.
3. **Two packs of different sizes (erratum corrected in this publication).** The delivered index said that "Shampoo and
   Conditioner Dual Pack, 12.5 oz shampoo + 10.6 oz conditioner" gives "12.5 oz" and that this was unchanged. "12.5 oz" was
   the result of releases 1.5.0 and 1.5.1 ([`pack_fix_151/`](../evidence/reconciliation/1.5.1/pack_fix_151/)). Release 1.5.2 gives "12.5 oz shampoo +
   10.6 oz conditioner": [`test_pack_size.py`](../source/walmart-oxylabs-1.5.2/tests/unit/test_pack_size.py), passed in the delivery's
   verification ([`unit.xml`](../evidence/verification/junit/oxylabs/unit.xml)). No stored page of the live runs or of B3 has such a
   title, so it is shown offline by that test only.
4. **A quantity discount outside the Pickup grid.** The stored page and its reasoning are in item 6 of the 1.5.1 index. It is not a
   Pickup offer of the store and is not exported.
5. **Serial against parallel** ran live on release 1.5.0 only (S5b), on 2 pages. The load test of this release used a local
   fixture, so it shows no provider's rate.
6. **Pure Balance, Clear American and ReliOn** have limits in their USPTO evidence ([`TECHNICAL_REPORT.md`](TECHNICAL_REPORT.md), section 3).
7. **The first attempts on `2ed64b7`.** The first Docker and replay runs on the VM were on the commit before the final
   revision. They were redone on `627c804`, and the first attempts stay on the VM and are not evidence of this delivery.
8. **The VM.** The Azure test VM stays running, as found. Its deallocation is Hamza's decision (matrix row A73).

## Accounts, external services, licensing and costs

**Accounts read in this release.**

- **Oxylabs Web API:** no request. The balance is UNVERIFIED: the Web API has no balance endpoint, and the dashboard belongs
  to the owner. **An owner action is outstanding:** the key has not been replaced yet.
- **Scrape.do:** its free `/info` reading showed 10 of 1,000 monthly credits left at 2026-11-01T18:23:14Z.
- **Azure:** the owner's test VM ran the container tests. Packages installed on it for those tests are listed in
  [`evidence/owner-azure-test/1.5.2/azure_docker_recovery/README.txt`](../evidence/owner-azure-test/1.5.2/azure_docker_recovery/README.txt).

**External services.** They are unchanged from 1.5.1: Walmart.com through a provider, the Oxylabs Web API or Scrape.do, the
operator's PostgreSQL and, optionally, Azure. The Docker base images are `python:3.12-slim-bookworm` and
`ghcr.io/astral-sh/uv:0.13.1`. The Classic probe names `https://realtime.oxylabs.io/v1/queries`, but its live mode is disabled.
The collector sends no telemetry and has no remote switch.

**Licensing.** The collector's source carries no licence text. Its licence and the transfer of its intellectual property are a
client agreement item. Runtime packages include psycopg and psycopg-binary 3.3.6 (LGPL-3.0-only) and certifi (MPL 2.0).

**Costs.** See [`COST_AND_RUNTIME_REPORT.md`](COST_AND_RUNTIME_REPORT.md). Known, as ledger estimates: USD 0.1785 at the reserve rate for the whole campaign, none
in this release. Unknown: the Oxylabs balance, its rate for Walmart pages, the size of the store's Pickup assortment and so
the full-run runtime and monthly cost, the Classic rates of the client's account, and the actual Azure bill.

## Client agreement items

The defect-support period and the transfer of intellectual property are **not agreed, and not waived**. Nothing in this delivery
states or assumes terms for them.

## Earlier deliveries

The work on this release changed nothing in `deliverables/20261101_walmart_1.5.1` or
`deliverables/20261028_walmart_1.4.1_dual_provider`. The SHA-256 of the 1.5.1 `SHA256SUMS.txt` is
a72a7d623b3b7e80e51695e81eec28a77a32325e2b246ea056e9104f0c1c929e. The verification rechecks each earlier Walmart delivery
against its own list and reports every file that differs or is absent ([`evidence/verification/PACKAGE_VERIFICATION.txt`](../evidence/verification/PACKAGE_VERIFICATION.txt)).

## Milestones (UTC)

| Time | Milestone |
|---|---|
| 2026-11-01T00:39Z to 04:25Z | the 1.5.1 delivery built and verified |
| 2026-11-01T18:23Z | Scrape.do `/info` read |
| 2026-11-01T19:03Z | the Classic documentation pages rechecked: 12 of 12 identical |
| 2026-11-01T19:52Z | release 1.5.2 final revision frozen (627c804) |
| 2026-11-01T20:05Z to 20:11Z | the final replays finished on the workstation |
| 2026-11-01T19:07Z to 19:08Z | the owner's Azure test VM: Docker, ffmpeg and asciinema installed for this work (166 packages) |
| 2026-11-01T19:25:58Z | the VM's environment and its six databases' row counts recorded, and the databases backed up |
| 2026-11-01T19:55:15Z to 19:55:31Z | the Classic probe from its ZIP alone on the VM; its live command refused, nothing sent |
| 2026-11-01T19:55:31Z to 19:56:20Z | both editions built in Docker from the source ZIP on the VM |
| 2026-11-01T19:56:50Z to 19:59:22Z | the nine replays in the Oxylabs edition's container, with a stop (S4) and a kill (S6) and their resumes |
| 2026-11-01T19:59:25Z to 20:20:08Z | on the VM: the suites, the publication faults and the load tests (SYNTHETIC); the row counts unchanged |
| 2026-11-01T21:06:33Z | both images checked again |
| 2026-11-01T21:19:22Z to 21:22:52Z | the walkthrough recorded on the VM |
| 2026-11-01T21:25:27Z to 21:26:17Z | the VM cleaned: containers, images, volumes and the 166 packages removed; row counts unchanged; the VM left running |
| 2026-11-02T00:39Z | the Classic probe ZIP rebuilt from the same revision, to replace the workstation's name in one recorded file |
| see [`evidence/verification/PACKAGE_VERIFICATION.txt`](../evidence/verification/PACKAGE_VERIFICATION.txt) | the start and end of the verification from clean extractions |

The next dates are in [`TEST_PLAN.md`](TEST_PLAN.md), and all of them depend on an approval.

## Not in this delivery

- The providers' raw answers as received. They are protected originals kept on the workstation, and their hashes are in each run
  folder's `RAW_ORIGINALS_MANIFEST.csv`.
- Credentials, the databases and their dumps, and virtual environments.
