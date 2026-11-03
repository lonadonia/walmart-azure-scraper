# Technical report: Walmart release 1.5.2

Commit 627c804d66aa33fc423fd2296c8896c5d5c2c3d4. Prepared by Hamza, 2026-11-02 (UTC). Times are UTC. Store: Walmart
#3891, 3900 Fountain Square Pl, Waukegan, IL 60085, PICKUP.

**What this release is: a correction update.** It is not an acceptance candidate and not an accepted release. Release
1.5.2 has not run live, the full catalogue has not been read, and no client has observed a run. Its corrections are
verified offline against the pages the live runs stored.

## 1. Evidence classes

| Class | What it is here | Where |
|---|---|---|
| Fresh live collection | The nine runs of 2026-10-31, on releases 1.5.0 and 1.5.1. None on 1.5.2 | [`data/`](../data/) |
| Reused historical field observations | UPCs and sizes from saved product pages, each with its original run, time and revision | `field_dispositions.json` of each export |
| Carried products | Rows a run did not observe itself, with their own run and date. Never counted as fresh | `products_retained` files, `record_map.json` |
| Offline replay | Stored pages read again by 1.5.2. No request | [`evidence/offline-replay/1.5.2/offline_reprocessing/`](../evidence/offline-replay/1.5.2/offline_reprocessing/) |
| Synthetic tests | Fixtures and a local load server, labelled as such | the test suites, the publication faults, section 6 |
| Owner Azure tests | Hamza's test VM, in a container, with no provider request | [`evidence/owner-azure-test/1.5.2/azure_docker_recovery/`](../evidence/owner-azure-test/1.5.2/azure_docker_recovery/) |
| Client-observed acceptance | None | [`ACCEPTANCE_RUNBOOK.md`](ACCEPTANCE_RUNBOOK.md), section 7 |

## 2. Gap list

Each gap of the brief of 2026-11-01, classed by what it needs.

| Gap | Class | State in 1.5.2 |
|---|---|---|
| Provenance files disagree on a recovered size | implementation defect | fixed, verified offline |
| Five carried rows keep 1.5.0's size | implementation defect | corrected by replay, verified offline |
| A pack stated twice, and other size rules | implementation defect | fixed, verified offline |
| Failed and blocked reads share one class | implementation defect | split into `blocked` and `request_failed` |
| An interrupted replay resumed as a live run | implementation defect, found here | fixed, verified offline |
| A row carried from a replay claims the replay fetched it | implementation defect, found here | fixed, verified offline |
| Private-label brands left to the client | implementation defect | researched: six added, with the limits of section 3 |
| 226 UPCs and 9 sizes of S6 unread | missing live validation | BLOCKED: allowance |
| Final revision never run live | missing live validation | BLOCKED: allowance |
| Sponsored and variant queue | missing live validation | PARTIAL: 275 items need a page read |
| Full coverage, twice-weekly fit | missing live validation; funding | BLOCKED: approval and funding |
| A live offer example | missing live validation | PARTIAL: none offered in the verified scope |
| Scrape.do demonstration | external dependency | BLOCKED: 10 credits, about 213 needed |
| Docker | missing validation | built and run on the owner's VM |
| Walkthrough | missing packaging | recorded on the owner's VM |
| Client Azure access, paid Classic | external dependency | request drafted; unapproved |
| Client-observed acceptance, support, IP | external dependency | not self-certified |

## 3. What was fixed, with before and after

Each fix has a regression test in the source's `tests/`. Before-evidence is in
[`evidence/offline-tests/1.5.2/defects_before_the_fix/`](../evidence/offline-tests/1.5.2/defects_before_the_fix/) and the correction maps.

| Fix | Before | After | Evidence |
|---|---|---|---|
| Provenance of a recovered size | `provenance.json` named the listing title (S1 5 rows, S2 7, S4 8, S5a 10, S6 12, B3 19) | the three provenance files name one capture, place, time, product, run and revision: 0 problems on S1 to S7 and B3 | [`evidence/offline-replay/1.5.2/offline_reprocessing/S6_CORRECTION_MAP.csv`](../evidence/offline-replay/1.5.2/offline_reprocessing/S6_CORRECTION_MAP.csv); [`evidence/offline-replay/1.5.2/agreement/S6.json`](../evidence/offline-replay/1.5.2/agreement/S6.json) |
| Five carried sizes | "30 lb" | "2 pack, 30 lb", and the other four | [`evidence/offline-replay/1.5.2/offline_reprocessing/README.txt`](../evidence/offline-replay/1.5.2/offline_reprocessing/README.txt); [`LINKED_EXAMPLES.csv`](LINKED_EXAMPLES.csv), E049 to E053 |
| A pack stated twice | "2 pack, 1 Pack" | "2 pack" | [`LINKED_EXAMPLES.csv`](LINKED_EXAMPLES.csv), E054 |
| Failure classes | `inaccessible_challenged` | `blocked` and `request_failed`; a page never read is never `source_absent` | [`source/walmart-oxylabs-1.5.2/docs/VERIFICATION.md`](../source/walmart-oxylabs-1.5.2/docs/VERIFICATION.md) |
| Resuming an interrupted replay | built the live collector, so it could not finish offline | stays a replay | [`evidence/offline-tests/1.5.2/defects_before_the_fix/replay_resume_before_fix.txt`](../evidence/offline-tests/1.5.2/defects_before_the_fix/replay_resume_before_fix.txt) |
| A row carried from a replay | said the replay observed it; for a product page, `fetched_detail` by the replay | names the live run, and the replay as `read_again_by_run` | [`evidence/offline-tests/1.5.2/defects_before_the_fix/carried_replay_before_fix.txt`](../evidence/offline-tests/1.5.2/defects_before_the_fix/carried_replay_before_fix.txt) |
| store_brand | S6 fresh 80 yes, 500 no | 100 yes, 480 no | [`source/walmart-oxylabs-1.5.2/docs/PRIVATE_LABEL.md`](../source/walmart-oxylabs-1.5.2/docs/PRIVATE_LABEL.md) |

**Private-label evidence.** Each brand was read in the USPTO's TSDR records on 2026-11-01. Each record's current owner is
Walmart Apollo, LLC:

| Brand | Mark read | Serial, registration | Goods on the record |
|---|---|---|---|
| Prima Della | PRIMA DELLA | 76458530, 2862043 | meats and cheese |
| Clear American | CLEAR AMERICAN ESSENTIALS | 87727865, 5801294 | soft drinks and sparkling waters |
| ReliOn | RELION | 75980144, 2454191 | blood pressure apparatus and thermometers |
| Special Kitty | SPECIAL KITTY | 74539951, 1910334 | cat food |
| Vibrant Life | VIBRANT LIFE | 87892205, 5617359 | dog and cat food, pet treats |
| Pure Balance | PURE BALANCE | 97302333, 7109375 | pet supplements |

A trademark record shows who owns a name, and three of these have limits. For Pure Balance the live record covers pet
supplements. The pet-food record read, PB PURE BALANCE (85055908, 4448075), has the same owner but was cancelled on
2024-06-21. For Clear American the record read is CLEAR AMERICAN ESSENTIALS. The ReliOn record does not name diabetes
supplies. Scent Theory and Millie Moon stay "no": on the evidence read, Walmart does not own them. The list is configuration, so
the client can overrule any brand. The full reasoning is in [`source/walmart-oxylabs-1.5.2/docs/PRIVATE_LABEL.md`](../source/walmart-oxylabs-1.5.2/docs/PRIVATE_LABEL.md).

**A set of two sizes (erratum corrected in this publication).** The delivered report said that a Dual Pack of two sizes keeps
the first size, as a known limit. That was releases 1.5.0 and 1.5.1. Release 1.5.2 keeps both: "Shampoo and Conditioner
Dual Pack, 12.5 oz shampoo + 10.6 oz conditioner" gives "12.5 oz shampoo + 10.6 oz conditioner"
([`test_pack_size.py`](../source/walmart-oxylabs-1.5.2/tests/unit/test_pack_size.py), on an authentic title of 1.4.1's pages). No stored page of
the live runs or of B3 has such a title, so this is shown by that test only.

## 4. What ran on the final revision, and where

| What | Where | Result |
|---|---|---|
| Nine replays of the campaign, twice, on separate copies | workstation, offline | the product, offer and membership files are byte-identical; the field-outcome files are identical once each replay's own run and fetch ids are numbered; only the replay's clock differs |
| B3 replay | workstation, offline | 862 rows, 0 agreement problems |
| Agreement of the three provenance files with the stored bytes | workstation, offline | 0 problems on ten exports |
| Docker: both editions built from the delivered source ZIP | the owner's Azure test VM | built in 27 s and 22 s; `--version` gives 1.5.2 and `validate-config` exits 0 for both; without a key a run is refused (exit 3); the container network has no route out |
| The nine replays in the container | the container on the VM | for all nine, the product, offer and membership files are byte-identical to the workstation's replay, and the field-outcome files once the replay's own ids are numbered ([`evidence/owner-azure-test/1.5.2/azure_docker_recovery/README.txt`](../evidence/owner-azure-test/1.5.2/azure_docker_recovery/README.txt)) |
| A graceful stop (TERM) in S4's replay and a forced kill (KILL) in S6's, then the real resume | the container on the VM | resume exit 0 for both, and the same product, offer and membership files as the workstation's replays, which were not stopped. Read twice: robots.txt and the store page only |
| The Oxylabs edition's lint, types, unit and integration suites, from the source ZIP | the owner's Azure test VM | all exit 0 |
| Publication faults, and the load test with a local fixture | the owner's Azure test VM | SYNTHETIC: 10 passed; 6 passed |
| The Classic probe from its ZIP alone: install from the lock, tests, plan, offline campaign, the live command | the owner's Azure test VM | 71 passed, 1 skipped; live refused (exit 3); nothing sent. The delivered ZIP was rebuilt afterwards to replace the workstation's name in one recorded file; 131 of its 132 files are identical to the ZIP tested there ([`evidence/owner-azure-test/1.5.2/azure_docker_recovery/README.txt`](../evidence/owner-azure-test/1.5.2/azure_docker_recovery/README.txt)) |
| A recorded walkthrough | the owner's Azure test VM | [`walkthrough/WALKTHROUGH_1.5.2.mp4`](../walkthrough/WALKTHROUGH_1.5.2.mp4), no live provider run in it |
| Full clean-extraction verification | workstation | [`evidence/verification/PACKAGE_VERIFICATION.txt`](../evidence/verification/PACKAGE_VERIFICATION.txt) |

**Nothing ran live on 1.5.2.** No Oxylabs, Scrape.do, Classic or Walmart request was made in this release. The VM's own six
databases kept their row counts from before this work (19:25:59Z) to after it (20:20:08Z).

## 5. Counts, field completeness, coverage and recovery

**Fresh live counts stand as delivered:** S6 on 1.5.1, 580 valid distinct fresh products from 15 Pickup result pages of
five listings; 706 retained. 1.5.2 changes how those pages are read, not what was collected.

| S6, 580 fresh rows | Filled | From the listing | From a saved page | Page not read | Absent | Conflict |
|---|---:|---:|---:|---:|---:|---:|
| UPC | 353 | 0 | 353 | 226 | 1 | 0 |
| Size | 567 | 555 | 12 | 9 | 3 | 1 |

S6 fetched 1 of those UPCs live and recovered 352. A replay fetches nothing, so its export shows 353 as recovered.

| Retained rows | Rows | UPC filled | Size filled | store_brand yes |
|---|---:|---:|---:|---:|
| S6 replay | 706 | 434 | 685 | 123 |
| B3 replay | 862 | 539 | 823 | 136 |

**Coverage.** No CSV row is complete. The campaign read 7 of the scope's 945 listings. Five stopped at their page cap,
Strawberries showed no results, and Dry Dog Food reached its last page in S3 with a total that changed while it was read
(139, 137, 138), so it is not reconciled. [`data/COVERAGE_RECONCILIATION.csv`](../data/COVERAGE_RECONCILIATION.csv) gives each row, listing and page. No listing was
read in this release.

**Sponsored and variants.** Of the 651 rows, 215 are closed (199 historical, 16 live). Of the 436 open rows, saved pages
settle 41 for identity, category and Pickup, and 24 for identity and category with no Pickup line. 96 have no category established, 1 page is
unusable, and 274 need their own page. That makes 275 distinct items in [`evidence/reconciliation/1.5.2/sponsored_and_variant_reconciliation/EXACT_LIVE_READ_QUEUE_1_5_2.csv`](../evidence/reconciliation/1.5.2/sponsored_and_variant_reconciliation/EXACT_LIVE_READ_QUEUE_1_5_2.csv). A saved page is
HISTORICAL: it says what that page said on its date.

**Offers.** 0 offers on 52 listing pages, 25 product-detail pages and 10 product pages (2,415 tiles). No offer reader
changed in 1.5.2, so that search stands and the live example stays unproven. One quantity-tier discount exists on a stored
page, in a module titled "Available for shipping": it is not a Pickup offer and is not exported.

**Recovery.** Live on 1.5.1: S6 was killed after 8 pages and resumed, with no record lost; two overlapping starts were
refused with no request. On the final revision, in its container: see section 4. A resume reads robots.txt and the store
page again, as a live resume does. Unavailable and later-missing products are covered by tests. No natural
available-to-unavailable transition has been observed live.

**Publication.** The fault suite runs against a fixture and is labelled synthetic. No incomplete dataset was published.

## 6. Provider usage against the estimates

| Account | Used in this release | Used in all | Note |
|---|---:|---:|---|
| Oxylabs Web API | 0 rows | 119 of 120 rows | USD 0.1785 at the reserve rate, 0.1190 at the published rate; ledger estimates, not an invoice |
| Scrape.do | 0 credits | 990 of 1,000 this month | read free at 2026-11-01T18:23:14Z |
| Oxylabs Classic | 0 | 0 | no access |
| Azure | the owner's VM ran throughout | | USD 0.113 an hour while running; no bill read |

**Concurrency, measured against a local fixture and not a provider** ([`COST_AND_RUNTIME_REPORT.md`](COST_AND_RUNTIME_REPORT.md), section 6b): 360
products, 6.06 requests a second with 1 worker and 7.04 with 2 on the workstation; 8.65 and 12.38 on the VM. With 4 workers
two stay idle (12.32 on the VM): parallelism is per CSV-row task. These are not provider rates and do not time a full run.

## 7. What remains, and why

| What | Why | Next |
|---|---|---|
| A live run of 1.5.2 | 1 row left; a session needs at least 3 | Stage 1 of [`TEST_PLAN.md`](TEST_PLAN.md) |
| 226 UPCs and 9 sizes of S6 | the same | Stage 1 |
| 275 sponsored and variant items | the same | [`evidence/reconciliation/1.5.2/sponsored_and_variant_reconciliation/EXACT_LIVE_READ_QUEUE_1_5_2.csv`](../evidence/reconciliation/1.5.2/sponsored_and_variant_reconciliation/EXACT_LIVE_READ_QUEUE_1_5_2.csv) |
| Full coverage, runtime, twice-weekly fit, monthly cost | no full run; approval and funding | Stages 2 and 3 |
| Scrape.do on the final version | 10 credits, about 213 needed | renewal or a paid plan |
| A live offer example | none offered in the verified scope | when Walmart shows one |
| Live Azure run, client environment | not approved | an Azure access request, drafted separately (not published here) |
| Paid Classic | not approved; live mode disabled | [`classic-probe/oxylabs-classic-probe/CLASSIC_TEST_PLAN.md`](../classic-probe/oxylabs-classic-probe/CLASSIC_TEST_PLAN.md) |
| Unattended scheduled operation | schedules stay off | after a full run |
| Client-observed acceptance, support, IP | cannot be self-certified | the client |
| Owner key rotation, VM deallocation | owner actions | Hamza |

The Classic artifact implements the Walmart stage. Reserving Mariano's budget does not implement or qualify its adapter.

## 8. Client actions

[`TEST_PLAN.md`](TEST_PLAN.md) holds the one consolidated request, with amounts and dated milestones.

## 9. Package

[`DELIVERY_INDEX.md`](DELIVERY_INDEX.md) lists every file of the delivery, and [`evidence/verification/PACKAGE_VERIFICATION.txt`](../evidence/verification/PACKAGE_VERIFICATION.txt) holds the result of the
verification from clean extractions. In this repository, [`manifests/SHA256SUMS.txt`](../manifests/SHA256SUMS.txt) holds the hashes of every
published file, and [`manifests/`](../manifests/) records what was moved, corrected, redacted or left out (`FILE_MAP.csv`,
`DOC_CORRECTIONS.md`, `REDACTIONS.csv`, `EXCLUDED.csv`).
