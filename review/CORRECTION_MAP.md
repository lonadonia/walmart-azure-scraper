# Correction map: releases 1.6.0 to 1.6.8

This page maps every point of the client's reviews, and every defect this delivery found, to its correction, its tests
and its evidence. Release 1.6.8 and probe 1.7.2 answer the client's review of 1.6.6; the 1.6.6 statements they
correct are listed in [`../manifests/DOC_CORRECTIONS.md`](../manifests/DOC_CORRECTIONS.md). The baseline is what the client reviewed first: the publication
`c4e665c4a89a5e8fcbae3e2797ba6527957e2c28` (tag `review-1.5.2-20261103`), collector 1.5.2
(`627c804d66aa33fc423fd2296c8896c5d5c2c3d4`) and the Walmart Classic probe 1.5.2. The revision of this delivery
is collector **1.6.8**, commit `85c29e7b2404500299056973f50c84b84e187a5a`, with the shared Classic probe **1.7.2** (commit `7768514aa1ffbaa7f96ca242d7b64e495fffefa5`).
Store: Walmart #3891, 3900 Fountain Square Pl, Waukegan, IL 60085, PICKUP.

**The probe 1.7.4 revision** (tag `review-1.6.8-probe174-20261111`, 2026-11-11) answers the client's review of the 1.6.8 delivery's probe: the shared Classic probe
becomes **1.7.4** (commit `a1def53747dfabcb2ad9ca97efc421c1e70f0ac6`), which corrects C2 on Windows ([Classic (W7)](#classic-w7)),
and two statements of the 1.6.8 publication are corrected: C2 as completed in 1.7.2, and the 275 decisions
([Sponsored and variant products (W3)](#sponsored-and-variant-products-w3)). The collector is unchanged.

Each state is defined in [`REQUIREMENT_MATRIX.md`](REQUIREMENT_MATRIX.md). Source paths start at
[`source/walmart-oxylabs-1.6.8/`](../source/walmart-oxylabs-1.6.8/). The Scrape.do edition has the same code and
differs only in its four edition files.

## The pinned correction diff

| From, to | Diff | Size |
|---|---|---|
| Collector 1.6.6 to 1.6.8, this delivery's correction | [`COLLECTOR_1.6.6_TO_1.6.8.diff`](../evidence/offline-tests/1.6.8-collector/COLLECTOR_1.6.6_TO_1.6.8.diff), [`DIFFSTAT.txt`](../evidence/offline-tests/1.6.8-collector/DIFFSTAT.txt) | 24 files, 2,267 lines added, 73 removed |
| Its two steps | [`1.6.6 to 1.6.7`](../evidence/offline-tests/1.6.8-collector/COLLECTOR_1.6.6_TO_1.6.7.diff), [`1.6.7 to 1.6.8`](../evidence/offline-tests/1.6.8-collector/COLLECTOR_1.6.7_TO_1.6.8.diff) | 18 files, 814 lines added, 30 removed; 22 files, 1,489 lines added, 79 removed |
| Collector 1.5.2 to 1.6.8, the whole correction | [`COLLECTOR_1.5.2_TO_1.6.8.diff`](../evidence/offline-tests/1.6.8-collector/COLLECTOR_1.5.2_TO_1.6.8.diff), [`DIFFSTAT_1.5.2_TO_1.6.8.txt`](../evidence/offline-tests/1.6.8-collector/DIFFSTAT_1.5.2_TO_1.6.8.txt) | 55 files, 5,221 lines added, 136 removed |
| One release at a time | [`1.6.0`](../evidence/offline-tests/1.6.0-collector/COLLECTOR_1.5.2_TO_1.6.0.diff), [`1.6.1`](../evidence/offline-tests/1.6.1-collector/COLLECTOR_1.6.0_TO_1.6.1.diff), [`1.6.2`](../evidence/offline-tests/1.6.2-collector/COLLECTOR_1.6.1_TO_1.6.2.diff), [`1.6.3`](../evidence/offline-tests/1.6.3-collector/COLLECTOR_1.6.2_TO_1.6.3.diff), [`1.6.4`](../evidence/offline-tests/1.6.4-collector/COLLECTOR_1.6.3_TO_1.6.4.diff), [`1.6.5`](../evidence/offline-tests/1.6.5-collector/COLLECTOR_1.6.4_TO_1.6.5.diff), [`1.6.6`](../evidence/offline-tests/1.6.6-collector/COLLECTOR_1.6.5_TO_1.6.6.diff) | each folder's `DIFFSTAT.txt` |
| Classic probe 1.6.0 (shared, as published with Mariano's) to 1.7.0 | [`CLASSIC_PROBE_1.6.0_TO_1.7.0.diff`](../evidence/offline-tests/1.7.0-classic-probe/CLASSIC_PROBE_1.6.0_TO_1.7.0.diff) | 24 files; [`CLASSIC_PROBE_CORRECTIONS.md`](CLASSIC_PROBE_CORRECTIONS.md) |
| Classic probe 1.7.0 to 1.7.1 | [`CLASSIC_PROBE_1.7.0_TO_1.7.1.diff`](../evidence/offline-tests/1.7.1-classic-probe/CLASSIC_PROBE_1.7.0_TO_1.7.1.diff), [`DIFFSTAT.txt`](../evidence/offline-tests/1.7.1-classic-probe/DIFFSTAT.txt) | 16 files, 1,492 lines added and 167 removed |
| Classic probe 1.7.1 to 1.7.2 | [`CLASSIC_PROBE_1.7.1_TO_1.7.2.diff`](../evidence/offline-tests/1.7.2-classic-probe/CLASSIC_PROBE_1.7.1_TO_1.7.2.diff), [`DIFFSTAT.txt`](../evidence/offline-tests/1.7.2-classic-probe/DIFFSTAT.txt) | 19 files, 1,917 lines added and 188 removed |
| Classic probe 1.7.2 to 1.7.3 (T05, published with Mariano's) | [`CLASSIC_PROBE_1.7.2_TO_1.7.3.diff`](../evidence/offline-tests/1.7.4-classic-probe/CLASSIC_PROBE_1.7.2_TO_1.7.3.diff) | 7 files, 280 lines added and 23 removed; no process code |
| Classic probe 1.7.3 to 1.7.4, the probe 1.7.4 revision's correction | [`CLASSIC_PROBE_1.7.3_TO_1.7.4.diff`](../evidence/offline-tests/1.7.4-classic-probe/CLASSIC_PROBE_1.7.3_TO_1.7.4.diff), [`DIFFSTAT.txt`](../evidence/offline-tests/1.7.4-classic-probe/DIFFSTAT.txt) | 8 files, 1,091 lines added and 74 removed (from the archive's first build, `05d8d87`, to this one: 2 files, 48 added and 41 removed, 10 and 3 with whitespace ignored) |

The diffs are of the development repository, relative to each product's folder. Releases 1.6.0 and 1.6.1 answer the
review and this delivery's own reconciliation. Releases 1.6.2 to 1.6.5 each correct a defect that a live run
met, and each was frozen before the next live stage ran on it. Release 1.6.6 and probe 1.7.1 correct
what the client's review of 1.6.5 found. Releases 1.6.7 and 1.6.8 and probe 1.7.2 correct what its review of 1.6.6 found, and what this delivery's
own checks found. No live run was made on 1.6.7 or 1.6.8.

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
| **1.6.6** `39cc61f`, 2026-11-04T22:34:53Z | A complete validated run whose automatic publication is refused is an error: `PUBLICATION_REFUSED` is an `ERROR` line and an `ERROR` event recorded on the run, with its reason, and the execution exits 6. Azure's retry of a scheduled execution whose run is done exits 6 too (`OCCURRENCE_DONE`). The alert advice of `docs/OPERATIONS.md` names the case. Nothing a run collects, checks or exports changes | the client's review of 1.6.5: 1.6.5 logged the refusal at `WARN` and exited 0, so no documented alert fired | `tests/integration/test_operations.py`: 2 new tests (both fail on 1.6.5; an intermediate fix that missed the retry path failed the second), 1 control unchanged | L12 (canary with detail on: 40 fresh valid, 10 product pages; a rejected pilot, never published) |
| **1.6.7** `7ee2fa1`, 2026-11-05T10:12:41Z, never delivered | A partition is complete only through its children: a child that ended on a moving total, a repeated or wrong page or its window keeps the listing incomplete; a child cut by a limit makes it `CAPPED` | the client's review of 1.6.6 | `tests/unit/test_completeness_167.py`: 7 fail on 1.6.6 | none |
| | A CSV row read only in part is `CAPPED`, never `DONE`. `coverage-report` gives each listing its effective outcome and each CSV row its verdict; `coverage_complete` is true only when every row is complete | the same | `test_category_mapping.py`, `test_coverage_and_assortment.py` (fail on 1.6.6) | none |
| | The agreed category mapping, on fresh and carried rows, the earlier name kept in lineage (`historical.renamed_by_mapping`): "Fabric Softener" and "Fabric Softeners" resolved | the same | `test_category_mapping.py`: 3 fail on 1.6.6 | none |
| | A carried row's UPC and size are decided apart: a size conflict withholds the size only | the same, and this delivery's W2 recheck | `test_detail_path.py` (fails on 1.6.6: `'' == '078742371245'`) | none |
| **1.6.8** `85c29e7`, 2026-11-05T20:51:52Z | A link to a category page of its own (`/cp/`) is read for the listings that page names; a page that cannot be read keeps its row incomplete, with why. A run makes more requests | this delivery's rebuild of the tables under 1.6.7's rule: 95 pages recorded as out of scope, 56 of them with no listing known | `test_scrapedo_walmart.py`, `test_subcategory_pages_168.py`, `test_coverage_and_assortment.py` (fail on 1.6.7) | none |
| | A view linked twice is read once under its first name; a filtered link has the listing itself read, in full; a filtered view of the row's own category is recorded and not read; two shelves are two listings; the mapping is per view; a read of a filtered view never completes a listing | L12 replayed by `7a96218`, and the 1,505 stored links checked against `9c14425`'s rule | `test_category_mapping.py`, `test_filtered_views_168.py` (9 and 7 fail on the two earlier commits, by the messages the report quotes) | none |

Each release's tests, logs and regression runs against the release before it are in
`evidence/offline-tests/<release>-collector/`; the source's `docs/VERIFICATION.md` describes every change and test.
This release's suites, from the delivered source ZIP on Linux, in a clean extraction of each edition: unit 554 and integration 222 passed, ruff, ruff format and mypy (strict) clean
([`qualification/`](../evidence/owner-azure-test/1.6.8/qualification/)). On Windows, from the same ZIP: unit 554 and the integration files the change touches, with the same static checks
([`evidence/verification/1.6.8/package/`](../evidence/verification/1.6.8/package/)).

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
- **Live:** `""` in all four fields of every row of every export of the fifteen 1.6.x runs. The published files
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
- **Limit, on the releases that ran live:** carried rows left as carried, their blank fields unfilled, although a saved read of their
  page exists, because that read's statements about the size conflict (`recovery_withheld`): 4 in L8, 12 in L10.
  Since 1.6.7 the conflict withholds the size only. Nothing is guessed.
- **1.6.6, live:** L12 read 10 product pages on 1.6.6. Three of them are of the UPCs never read: item `14561172064`
  (UPC `072613474844`), `1398092439` (`827854009580`) and `14620357163` (`072613474912`), in L12's fresh export with
  their leading zeros. The fourth of those items on the Fabric Softeners listing, `20242472444`, was not on page 1.
- **The recheck of 1.6.8:** every blank UPC and size of S6's rows, against every saved read, in
  [`W2_RECHECK_1_6_7.csv`](../evidence/reconciliation/1.6.8/w2/W2_RECHECK_1_6_7.csv) (no request). After release 1.6.3, 52 UPCs were missing (51 blank, 1 cleared):

  | Class | UPCs |
  |---|---:|
  | filled by L12 on 1.6.6 | 3 |
  | a saved read states it; 1.6.6 withheld it only for a size conflict, and 1.6.7 recovers it with no request (items 16664823, 314089142, 40347953) | 3 |
  | no read of the item's own page in any run (43 never attempted; 1, item 338270604, cut by a run's limit) | 44 |
  | absent from the item's own page (item 10496473297) | 1 |
  | the page read was of another item (655257631 read as 195134138) | 1 |

  Sizes: 4 conflicting, 8 absent at the source, 2 never attempted. No UPC, size or price was guessed, and a blank keeps its reason, its run and its page's hash.
- **The queue is 44, not the 45 the 1.6.6 delivery reported.** The table above of 1.6.3 stays against L8's export.
- **State:** PASS_DEVELOPER_LIVE for the reads made; BLOCKED_BUDGET for the 44 UPCs with no read.


### Sponsored and variant products (W3)
- **The queue:** the 275 distinct products of
  [`EXACT_LIVE_READ_QUEUE_1_5_2.csv`](../evidence/reconciliation/1.5.2/sponsored_and_variant_reconciliation/EXACT_LIVE_READ_QUEUE_1_5_2.csv)
  that needed their own page.
- **Result:** all 275 were read live (L2, L3 and L2b, on 1.6.0 and 1.6.1) and decided. A sponsored label alone decided nothing. At row level
  ([`W3_ROW_LEVEL_1_6_7.csv`](../evidence/reconciliation/1.6.8/w3/W3_ROW_LEVEL_1_6_7.csv)):

  | Outcome | Products |
  |---|---:|
  | included | 48 |
  | excluded: the item's own page places it in another category, identified | 165 |
  | excluded: the page states no category path (`categoryPathId` -1, no breadcrumb), so the required category cannot be proven | 4 |
  | excluded: the page does not prove local eligibility | 55 |
  | duplicate, linked to the original observation and the SHA-256 of the stored page (items 122787913, 567228522, 15565153181) | 3 |
  | failed, blocked or unresolved | 0 |

  So 169 exclusions lack proof of the required category and 55 lack proof of local eligibility. A missing path is kept apart from a positively identified other category. The 1.6.6 text
  said "224 excluded with the page's own reason", which was not accurate for all of them.

  **Corrected by the probe 1.7.4 revision.** The table above counts as excluded 59 products whose sources support no
  exclusion: the 4 with no category path and the 55 whose page does not prove local eligibility (`LOCATION_UNATTESTED`
  and `ASSORTMENT_UNRESOLVED`; 14 of them also show a marketplace offer, which does not show the product absent from
  the store). Missing evidence leaves a product unresolved. From the same rows
  ([`W3_275_RECOUNT.csv`](../evidence/reconciliation/1.6.8-probe174/w3/W3_275_RECOUNT.csv)):

  | Outcome | Products |
  |---|---:|
  | included | 48 |
  | excluded: the item's own page places it in another category, identified | 165 |
  | duplicate, linked to the original observation | 3 |
  | **unresolved**: no category path on the item's page | 4 |
  | **unresolved**: local eligibility not proven by the item's page | 55 |

  The reads, their pages and the collector's own labels are unchanged; the 59 need their pages read again with the
  store's context (paid requests). The 44 unread UPCs are a separate queue.
- **The client's cases:** the 11 sponsored-only placements were closed before 1.5.2. Of the 30 variant siblings, 5
  were closed before, 24 are excluded on their own page and 1 is included. *(Corrected by the probe 1.7.4 revision: of
  those 24, 17 are excluded on a positively identified other category and 7 are unresolved: V25, V27, V28 and V30 with no
  category path, V22, V26 and V29 with local eligibility not proven.)*
- **Tables:** [`W3_DECISIONS_1_6_1.csv`](../evidence/reconciliation/1.6.1/w3/W3_DECISIONS_1_6_1.csv),
  [`W3_CLIENT_CASES_1_6_1.csv`](../evidence/reconciliation/1.6.1/w3/W3_CLIENT_CASES_1_6_1.csv).
- **State:** PASS_DEVELOPER_LIVE for the reads and the 216 products with a source-supported outcome; BLOCKED_BUDGET for the
  59 unresolved (the probe 1.7.4 revision; on 1.6.8 the whole item was given as PASS_DEVELOPER_LIVE).

### Coverage, partitions and the census (W4)
- **Tables:** [`evidence/reconciliation/1.6.8/w4/`](../evidence/reconciliation/1.6.8/w4/) gives row, root, child and
  page, every 1.6.x read, and the queue known today ([`TEST_PLAN.md`](TEST_PLAN.md) prices it part by part). They are made from 1.6.8's own
  coverage report of each live run. The tables of 1.6.5 and 1.6.6 stay beside them. The 1.6.6 tables recorded 230 listings out of scope: of them, 95 are category pages of their own, 35 are shop, brand, search, product or account pages, 6 are excluded by the CSV, and the others are listings of their rows that the census did not choose. So the "exact outstanding queue" of 1.6.6 lacked the category pages and the listings they name.
- **What is complete:** 252 of 1,104 listings, against the 244 published. Under the 1.6.8 rules, 239 of the 244 stay complete. Four were complete only through a filtered view, read in L10, and one (Cough) had a total that moved while it was read. The 230 out of scope are now told apart. 95 are subcategory pages of their own that no run read, so their rows stay open. 35 are not category pages, 6 are excluded by the CSV, and 1 is a filtered view of its row's own category. The other 93 are listings the census did not choose ([`w4/README.txt`](../evidence/reconciliation/1.6.8/w4/README.txt)).
- **The revisits the review asked for:** the five listings S6 left capped, Strawberries, Dry Dog Food (139/137/138)
  and Fresh Fruits were read again in L4r on 1.6.1 (`W4_REVISITS_1_6_8.csv`).
- **The census:** L7 on 1.6.3 (rows 0 and 1) and L10 on 1.6.4 (rows 2 to 10, and Household Essentials' Bidets
  listing) read page 1 of 451 listings that their category pages name today, in the 11 CSV rows, with the client's
  exclusions applied. 395 more listings those pages name were not reached before L10's credit limit. Those runs read some listings through a filtered link; 1.6.8 reads the listing itself.
- **Partitions:** live at depth 1 only: 21 child listings (L6 18, L10 3), none above the result window.
- **Full scope:** not reached. No CSV row is complete (0 of 11).
- **State:** BLOCKED_BUDGET for full scope (A19, A70, G05, P4-01) and for a live second partition level (A18).

### Retention, recovery and publication (W6)
- **Live, on the release each ran:**
  - pause, overlap refusal, forced kill and resume on 1.6.1 (L3), 1.6.2 (L5) and 1.6.3 (L8);
  - unavailable and later-missing products carried with their own dates (every demonstration run).
- **Synthetic, on a clean extraction of 1.6.8:** the last-good publication against every listed fault, 19 passed (2026-11-05, 21:22:13Z to 21:25:33Z); the three corrupt-evidence cases exit 6.
  A refused automatic publication is an `ERROR` with exit 6 since 1.6.6 (1.6.5: `WARN`, exit 0). The operator drill shows it on 1.6.8 through the ordinary commands, on the run's own attempt and again on a manual `publish` of that run (exit 6 both times), with the pointer unchanged.
- **In containers on the owner's VM, on 1.6.8:** a replay killed with SIGKILL and resumed by the ordinary command, its export byte for byte the uninterrupted replay's (no result page read twice; robots.txt and the store page were, as a resumed execution verifies the store first), and the data compared across a daemon restart ([`container/`](../evidence/owner-azure-test/1.6.8/container/)).
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
- **On release 1.6.5:** the live canary L11b passed on its first recorded page, 35 of 35 records verified. L11, the
  first 1.6.5 canary, recorded no product (its listing was rejected for its identity; see
  [`TECHNICAL_REPORT.md`](TECHNICAL_REPORT.md), section 8).
- **On release 1.6.6:** the canary L12, with product-page collection on, passed on its first recorded page
  (40 of 40 verified): 40 fresh valid, 10 product pages read, UPC 27 of 40, size 39 of 40, its export of 10,301
  records verified (10,261 of them carried).
- **On 1.6.8:** no live run. A run of 500 or more with detail on is BLOCKED_BUDGET (at most 45 submissions, USD 0.0675; USD
  0.003 is left, and the ceiling is 0). L12 and L10 were replayed from stored pages: a replay, not new collection.
- **S6 (1.5.1):** 580 fresh valid and 706 retained, as delivered in 1.5.2. It is not relabelled.
- **Where:** [`data/RUN_SUMMARY.json`](../data/RUN_SUMMARY.json) and
  [`COST_AND_RUNTIME_REPORT.md`](COST_AND_RUNTIME_REPORT.md).

### Classic (W7)
- C1, C3 and C5 are corrected in the shared probe 1.7.0. C2 and C4 were advanced in 1.7.1 and are completed in 1.7.2, offline, with live
  mode disabled ([`CLASSIC_PROBE_CORRECTIONS.md`](CLASSIC_PROBE_CORRECTIONS.md)). The 1.6.5 and 1.6.6 deliveries overstated them; the review's tests fail on 1.7.1 (13 on Windows, 14 on Linux) and pass on 1.7.2.
- **The probe 1.7.4 revision: C2 on Windows** (the client's review of 1.7.2). The 1.6.8 delivery overstated C2 too. On
  Windows 1.7.2 held the session's tree only when a job object could be made and the process joined it. Otherwise it
  ran the session under a `taskkill /T` fallback that cannot reach a child whose parent has exited, and it reported an
  unreadable count as nothing left running. Probe 1.7.4 runs a session only once a verified job object holds it,
  refuses it otherwise with no fallback, and keeps a cleanup it cannot verify as `unknown` or `failed`. On Windows the
  5 new tests fail on 1.7.2 by their output and pass on 1.7.4, and the whole suite gives 229 passed, 5 skipped
  ([`1.7.4-classic-probe/`](../evidence/offline-tests/1.7.4-classic-probe/)). On Linux, from the archive: 227 passed, 7 skipped,
  and the 3 review tests that run there pass on 1.7.4 and 2 fail on 1.7.2 (the archive's first build failed mypy on Linux and was built again).
- The Linux discrepancy is closed: the published 1.7.1 gave 169 passed, 1 failed and 3 skipped on Linux; 1.7.2 gives 201 passed and 3 skipped on Linux and 199 passed and 5 skipped on Windows, each skip explained.
- The Mariano's adapter is the published blob `9de6510b`, unchanged.
- **State:** PASS_OFFLINE; a live Classic probe is PENDING_CLIENT_DECISION.

### Azure, container, schedule, Scrape.do (W6, W8)
- **Container:** both 1.6.8 images built with `docker build` from the delivered ZIPs on the owner's Azure test VM, their digests recorded, smoke-tested with no network and a read-only root,
  migrated on an isolated PostgreSQL 16, with a replay of stored pages, a kill and resume, a rollback and persistence across a daemon restart
  ([`container/`](../evidence/owner-azure-test/1.6.8/container/)). An owner test, not the client's environment.
- **Azure templates:** the Bicep build and lint of both 1.6.8 editions pass, with no deployment
  ([`BICEP_CHECKS.txt`](../evidence/verification/1.6.8/package/BICEP_CHECKS.txt)).
- **Monitoring:** a refused automatic publication is an `ERROR` with exit 6 since 1.6.6, and the alert advice names
  it ([`RECOVERY_AND_OPERATIONS.md`](RECOVERY_AND_OPERATIONS.md), section 3).
- **Client VM:** deallocated, as the client confirmed. No SSH attempt was made.
- **Schedule:** stays disabled.
- **Scrape.do:** no credits are authorized in this delivery.
- **States:** PASS_OWNER_AZURE, PENDING_CLIENT_AZURE, PENDING_OBSERVATION and BLOCKED_BUDGET; see
  [`REQUIREMENT_MATRIX.md`](REQUIREMENT_MATRIX.md).
