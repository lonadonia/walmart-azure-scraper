# Correction map: releases 1.6.0 to 1.6.5

This page maps every point of the client's two latest reviews, and every defect this delivery found, to its
correction, its tests and its evidence. The baseline is what the client reviewed: the publication
`c4e665c4a89a5e8fcbae3e2797ba6527957e2c28` (tag `review-1.5.2-20261103`), collector 1.5.2
(`627c804d66aa33fc423fd2296c8896c5d5c2c3d4`) and the Walmart Classic probe 1.5.2. The final release of this delivery
is collector **1.6.5**, commit `67d216eb8ee2ec839a437b0b5bf2d594324b6982`, with the shared Classic probe **1.7.0**.
Store: Walmart #3891, 3900 Fountain Square Pl, Waukegan, IL 60085, PICKUP.

Each state is defined in [`REQUIREMENT_MATRIX.md`](REQUIREMENT_MATRIX.md). Source paths start at
[`source/walmart-oxylabs-1.6.5/`](../source/walmart-oxylabs-1.6.5/). The Scrape.do edition has the same code and
differs only in its four edition files.

## The pinned correction diff

| From, to | Diff | Size |
|---|---|---|
| Collector 1.5.2 to 1.6.5, the whole correction | [`COLLECTOR_1.5.2_TO_1.6.5.diff`](../evidence/offline-tests/1.6.5-collector/COLLECTOR_1.5.2_TO_1.6.5.diff), [`DIFFSTAT_1.5.2_TO_1.6.5.txt`](../evidence/offline-tests/1.6.5-collector/DIFFSTAT_1.5.2_TO_1.6.5.txt) | 45 files, 2,841 lines added and 72 removed; of them, tests: 23 files, 2,091 added and 20 removed |
| One release at a time | [`1.6.0`](../evidence/offline-tests/1.6.0-collector/COLLECTOR_1.5.2_TO_1.6.0.diff), [`1.6.1`](../evidence/offline-tests/1.6.1-collector/COLLECTOR_1.6.0_TO_1.6.1.diff), [`1.6.2`](../evidence/offline-tests/1.6.2-collector/COLLECTOR_1.6.1_TO_1.6.2.diff), [`1.6.3`](../evidence/offline-tests/1.6.3-collector/COLLECTOR_1.6.2_TO_1.6.3.diff), [`1.6.4`](../evidence/offline-tests/1.6.4-collector/COLLECTOR_1.6.3_TO_1.6.4.diff), [`1.6.5`](../evidence/offline-tests/1.6.5-collector/COLLECTOR_1.6.4_TO_1.6.5.diff) | each folder's `DIFFSTAT.txt` |
| Classic probe 1.6.0 (shared, as published with Mariano's) to 1.7.0 | [`CLASSIC_PROBE_1.6.0_TO_1.7.0.diff`](../evidence/offline-tests/1.7.0-classic-probe/CLASSIC_PROBE_1.6.0_TO_1.7.0.diff) | 24 files; [`CLASSIC_PROBE_CORRECTIONS.md`](CLASSIC_PROBE_CORRECTIONS.md) |

The diffs are of the development repository, relative to each product's folder. Releases 1.6.0 and 1.6.1 answer the
review and this delivery's own reconciliation. Releases 1.6.2 to 1.6.5 each correct a defect that a live run of
this delivery met, and each was frozen before the next live stage ran on it.

## What each release corrected

| Release | Correction | Found by | Tests (fail before, pass after) | Live on it |
|---|---|---|---|---|
| **1.6.0** `56f078e`, 2026-11-03T16:59:04Z | The four deal fields are always `""` in every exported row, from every path: fresh, carried, legacy, replayed, re-exported, published. A nonconforming row is refused at the last step. What a page showed stays in provenance and `offers.json` | the client's clarification (W1) | `tests/unit/test_exports_policy.py`; `tests/integration/test_deal_fields_policy.py` | L1, L2 |
| | An optional account-wide spending gate for Oxylabs: each submission's worst case is reserved in the shared trial ledger before it is sent; a refusal sends nothing; an unanswered submission stays unknown | the brief's one shared budget | `tests/integration/test_account_gate.py` | every stage |
| **1.6.1** `1780349`, 2026-11-03T18:18:22Z | A run that ends before its detail pass still uses what earlier reads of a product's page established (30 days), with that read's time, run, revision and page | this delivery's W2 reconciliation: the live S7 of 2026-10-31 left 32 products blank that S6's saved reads answered | `test_detail_path.py::test_a_run_that_ends_before_its_detail_pass_still_uses_what_earlier_reads_established` | L3, L2b, L4r, L4 |
| **1.6.2** `1274056`, 2026-11-04T10:24:46Z | A listing whose total moved while it was read, and whose served results fall short by more than the total moved, ends at the result window and is read through its child categories, never `DONE` | live L4r on 1.6.1 (Laundry 615/613/614/611 reported, 393 served; Shampoo 608/607, 399 served) | `test_listing_reconciliation.py`, `test_coverage_and_assortment.py` (2 fail on 1.6.1, 1 control) | L5, L6 |
| | A listing link that serves a category page is recorded `INCOMPLETE` (`CATEGORY_PAGE`) with the listings it links; the run goes on and the store is not held | live L4 on 1.6.1: "Fresh Flowers" served "Flower Shop" and the census stopped | `test_walmart.py`, `test_coverage_and_assortment.py` (2 fail on 1.6.1, 2 controls) | L5, L6 |
| **1.6.3** `def55e5`, 2026-11-04T11:54:09Z | Saved reads are used when detail reading is off, too | the W2 reconciliation of live L5 | 1 new and 2 changed tests fail on 1.6.2, 1 control | L8, L9, L7 |
| | A carried row with an empty UPC or size gets it from a saved read that it names; never forced (a UPC another row has, an approximate or conflicting size: withheld, with the reason) | the same | 2 fail on 1.6.2, 2 controls | L8, L9, L7 |
| | Walmart's own not-found page is recognized (its page data id unquoted): a listing link that answers with it is `INCOMPLETE` (`NOT_FOUND`) and the run goes on; a product page that is the not-found page is `request_failed` | live L6 on 1.6.2: "nexxus-shampoo" stopped the run as a site refusal and held the store | `tests/unit/test_not_found_page.py`, 2 integration tests (8 fail on 1.6.2, 5 controls) | L9 (the same link, recorded `NOT_FOUND` live) |
| **1.6.4** `28ac7d3`, 2026-11-04T12:32:58Z | A listing total the page reports as 0 is a total of 0; the page's `count` (other modules' products too) is read only when no total is reported | live L7 on 1.6.3: "Bidets" reported 0 Pickup results beside an "Available for shipping" carousel of 10, was read as 10, and stopped the census | `tests/unit/test_empty_pickup_grid.py` (on the authentic stored page), 2 integration tests (4 fail on 1.6.3, 7 controls) | L10 (the same link, recorded `EMPTY` live) |
| **1.6.5** `67d216e`, 2026-11-04T14:15:19Z | The independent source check (`checks/source_check.py`, used by `validate-export --run` and by the automated canary on a run's first recorded page) reads the three layouts in which the page reader reads prices: price lines, nested price objects, and flat display strings. A was-price above the current price is a sale in each layout; a wrong price or unit price is still a mismatch. Nothing a run collects or exports changes | live L10 on 1.6.4: `validate-export --run` exited 6, reporting 21 of 10,301 records as mismatches. All 21 were read from Beauty's "New Arrivals" page, whose 50 placements give their prices as flat strings, and each equals that page | `tests/unit/test_flat_price_layout.py`, on two authentic stored pages and L10's 26 records from the flat page (6 fail on 1.6.4, 2 controls) | L11, L11b (the canary passed, 35 of 35); L10's and L8's exports checked again offline |

Each release's tests, logs and regression runs against the release before it are in
`evidence/offline-tests/<release>-collector/`; the source's `docs/VERIFICATION.md` describes every change and test.
The final release's suites, on its commit: unit 533 passed, ruff, ruff format and mypy (strict) clean
([`evidence/offline-tests/1.6.5-collector/`](../evidence/offline-tests/1.6.5-collector/)). From the delivered source
ZIP, in a clean extraction of each edition: unit 533 and integration 200 passed, with the same static checks
([`evidence/verification/1.6.5/package/`](../evidence/verification/1.6.5/package/)).

**Replay of the 1.6.4 change.** 1.6.4 reads 342 of the 343 listing pages stored by 20 live runs exactly as 1.6.3
does; the one it reads differently is L7's Bidets page
([`REPLAY_TOTALS_SUMMARY.json`](../evidence/offline-tests/1.6.4-collector/REPLAY_TOTALS_SUMMARY.json)). So the live
results of L8 (1.6.3) are not changed by 1.6.4. That is shown by replay, not by a new live run.

**The 1.6.5 change, on the stored pages.** 1.6.5 changes only what the check expects from a page. All 1,531 page
copies stored by the 23 live runs of store 3891 Pickup were sorted by the layout of their prices
([`FLAT_LAYOUT_SCAN.json`](../evidence/offline-tests/1.6.5-collector/FLAT_LAYOUT_SCAN.json)). Before 1.6.5, one
listing page gave its prices as flat strings: L10's copy of "New Arrivals". L11 fetched the same page again, in the
same layout. With 1.6.5, the exports of L10 (1.6.4) and L8 (1.6.3) are verified in full against their stored pages,
with no mismatch ([`source_check_l10/`](../evidence/verification/1.6.5/source_check_l10/)). Both runs stay
attributed to the releases that collected them.

## The points of the reviews

### The four deal fields (W1)
- **Rule (the client's clarification):** `volume_deals_description`, `volume_deals_price`,
  `digital_deals_description` and `digital_deals_price` are always `""`. A live Walmart offer example is no longer
  required, and none was sought: no trial credit was spent on coupons or multibuys.
- **Where:** `core/schema.py` (`DEAL_FIELDS`, `apply_output_policy`), `assembly/record_builder.py`,
  `collection/retention.py`, `publishing/exports.py` (the final boundary), `checks/contract.py`.
- **Tests:** they start from nonempty deal data. Fresh JSON and CSV, a carried legacy row, a replay and a re-export,
  the publication, the contract check, and both editions (from the delivered source ZIP).
- **Live:** `""` in all four fields of every row of every export of the fourteen 1.6.x runs. The published files
  are checked by [`manifests/check_data.py`](../manifests/check_data.py).
- **History kept:** the 1.5.x exports in `data/S6-1.5.1/`, `data/S7-1.5.1/` and `data/S4-1.5.0/` are not edited.
  They were made under the earlier rule.
- **State:** PASS_OFFLINE and PASS_DEVELOPER_LIVE. The offer rows A39, A41, G06, N6-03, N6-05 and P5-02 are
  NOT_APPLICABLE_BY_CLARIFICATION.

### UPC, size and provenance (W2)
- **Rule (unchanged since 1.5.2):** a product page counts only when it names the requested item. A UPC comes from
  the page's own UPC or GTIN field, with its leading zeros. A page never read is `not_attempted`, never absent.
- **New in 1.6.1 and 1.6.3:** saved reads are used whenever they exist (a run that stops early, detail reading off,
  carried rows), always named as the read they are: its time, run, revision and page. A freshly observed listing row
  with an older recovered UPC says so; it never claims the page was read today.
- **The table:** [`W2_FIELD_CORRECTIONS_1_6_3.csv`](../evidence/reconciliation/1.6.3/w2/W2_FIELD_CORRECTIONS_1_6_3.csv),
  one row per product and field, from S6's 706 delivered rows to their state in L8's export, with the old and new
  value and reason, the source page, the private original's and the public copy's hashes, the run, the revision and
  the evidence class. Aggregates: [`W2_SUMMARY_1_6_3.json`](../evidence/reconciliation/1.6.3/w2/W2_SUMMARY_1_6_3.json).
- **S6's 580 fresh rows:** UPC filled 353 in 1.5.2, 539 now (187 filled, 1 cleared, 40 still blank); size filled 567,
  now 572 (5 filled, 1 changed, 8 still blank).
- **All 706 rows, still blank:** UPC 51 (48 never read, 1 cut by a limit, 1 absent on its page, 1 page of another
  item); size 14 (8 absent, 3 conflicting statements, 3 never read).
- **Limit, disclosed:** carried rows left as carried, their blank fields unfilled, although a saved read of their
  page exists, because that read's statements about the size conflict (`recovery_withheld`): 4 in L8, 12 in L10.
  Nothing is guessed.
- **State:** PASS_DEVELOPER_LIVE for the reads made; BLOCKED_BUDGET for the 48 UPCs never read.

### Sponsored and variant products (W3)
- **The queue:** the 275 distinct products of
  [`EXACT_LIVE_READ_QUEUE_1_5_2.csv`](../evidence/reconciliation/1.5.2/sponsored_and_variant_reconciliation/EXACT_LIVE_READ_QUEUE_1_5_2.csv)
  that needed their own page.
- **Result:** all 275 were read live (L2, L3 and L2b, on 1.6.0 and 1.6.1) and decided: 48 included, 224 excluded with
  the page's own reason, 3 duplicates of another identity. A sponsored label alone decided nothing.
- **The client's cases:** the 11 sponsored-only placements were closed before 1.5.2. Of the 30 variant siblings, 5
  were closed before, 24 are excluded on their own page and 1 is included.
- **Tables:** [`W3_DECISIONS_1_6_1.csv`](../evidence/reconciliation/1.6.1/w3/W3_DECISIONS_1_6_1.csv),
  [`W3_CLIENT_CASES_1_6_1.csv`](../evidence/reconciliation/1.6.1/w3/W3_CLIENT_CASES_1_6_1.csv).
- **State:** PASS_DEVELOPER_LIVE.

### Coverage, partitions and the census (W4)
- **Tables:** [`evidence/reconciliation/1.6.5/w4/`](../evidence/reconciliation/1.6.5/w4/) gives row, root, child and
  page, every 1.6.x read, and the exact outstanding queue ([`TEST_PLAN.md`](TEST_PLAN.md) prices it).
- **The revisits the review asked for:** the five listings S6 left capped, Strawberries, Dry Dog Food (139/137/138)
  and Fresh Fruits were read again in L4r on 1.6.1 (`W4_REVISITS_1_6_5.csv`).
- **The census:** L7 on 1.6.3 (rows 0 and 1) and L10 on 1.6.4 (rows 2 to 10, and Household Essentials' Bidets
  listing) read page 1 of 451 listings that their category pages name today, in the 11 CSV rows, with the client's
  exclusions applied. 395 more listings those pages name were not reached before L10's credit limit.
- **Partitions:** live at depth 1 only: 21 child listings (L6 18, L10 3), none above the result window.
- **Full scope:** not reached. No CSV row is complete (0 of 11).
- **State:** BLOCKED_BUDGET for full scope (A19, A70, G05, P4-01) and for a live second partition level (A18).

### Retention, recovery and publication (W6)
- **Live, on the release each ran:**
  - pause, overlap refusal, forced kill and resume on 1.6.1 (L3), 1.6.2 (L5) and 1.6.3 (L8);
  - unavailable and later-missing products carried with their own dates (every demonstration run).
- **Synthetic, on a clean extraction of 1.6.5:** the last-good publication against every listed fault, 19 passed.
- **Where:** [`RECOVERY_AND_OPERATIONS.md`](RECOVERY_AND_OPERATIONS.md).
- **Not observed:** no natural available-to-unavailable transition: PENDING_OBSERVATION (A34, B17).

### The live data (W5)
- **The demonstrations** (each run's exports in `evidence/live/1.6.x/runs/`; `data/` holds the product files of L8
  and L10):
  - L2 on 1.6.0: 707 fresh valid;
  - L3 on 1.6.1: 676;
  - L5 on 1.6.2: 679;
  - L8 on 1.6.3: 675.

  Each was one logical run, store 3891 Pickup, with detail on.
- **The census L10 on 1.6.4:** detail off, 7,055 fresh valid. Its export was checked again with 1.6.5's source
  check: 10,301 of 10,301 records verified.
- **On the final release 1.6.5:** the live canary L11b passed on its first recorded page, 35 of 35 records verified.
  L11, the first 1.6.5 canary, recorded no product (its listing was rejected for its identity; see
  [`TECHNICAL_REPORT.md`](TECHNICAL_REPORT.md), section 8). A detail-on run of 1.6.5 is BLOCKED_BUDGET.
- **S6 (1.5.1):** 580 fresh valid and 706 retained, as delivered in 1.5.2. It is not relabelled.
- **Where:** [`data/RUN_SUMMARY.json`](../data/RUN_SUMMARY.json) and
  [`COST_AND_RUNTIME_REPORT.md`](COST_AND_RUNTIME_REPORT.md).

### Classic (W7)
- C1 to C5 are corrected in the shared probe 1.7.0, offline, with live mode disabled
  ([`CLASSIC_PROBE_CORRECTIONS.md`](CLASSIC_PROBE_CORRECTIONS.md)).
- The Mariano's adapter is the published blob `9de6510b`, unchanged.
- **State:** PASS_OFFLINE; a live Classic probe is PENDING_CLIENT_DECISION.

### Azure, container, schedule, Scrape.do (W6, W8)
- **Container:** not rebuilt for 1.6.5, because this workstation has no container runtime. Since the 1.5.2 image
  built on the owner's VM, the Dockerfile changed only in two comment lines that give the version.
- **Azure templates:** the Bicep build and lint of both editions pass, with no deployment
  ([`BICEP_CHECKS.txt`](../evidence/verification/1.6.5/package/BICEP_CHECKS.txt)).
- **Client VM:** deallocated, as the client confirmed. No SSH attempt was made.
- **Schedule:** stays disabled.
- **Scrape.do:** no credits are authorized in this delivery.
- **States:** PENDING_CLIENT_AZURE, PENDING_OBSERVATION and BLOCKED_BUDGET; see
  [`REQUIREMENT_MATRIX.md`](REQUIREMENT_MATRIX.md).
