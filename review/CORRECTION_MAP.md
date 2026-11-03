# Correction map: release 1.5.2

Written for this publication from the acceptance matrix, the source and the evidence. It adds no test and changes no
status. Each status below is the one in [`ACCEPTANCE_MATRIX.csv`](ACCEPTANCE_MATRIX.csv), named by its row id so you
can check it there. Store: Walmart #3891, 3900 Fountain Square Pl, Waukegan, IL 60085, Pickup.

**How to read a status.**
- **VERIFIED LIVE:** a live run on 2026-10-31 showed it. Those runs used release 1.5.0 (`7b6f325`) or 1.5.1
  (`488a033`). Release 1.5.2 (`627c804`) has made no live request.
- **VERIFIED OFFLINE:** release 1.5.2's tests, or its replay of the stored pages, show it.
- **PARTIAL, BLOCKED and NOT TESTED:** still open.

Source paths start at [`source/walmart-oxylabs-1.5.2/`](../source/walmart-oxylabs-1.5.2/). The Scrape.do edition has
the same code and differs only in four configuration files.

## What 1.5.2 corrected

The before and after are in section 3 of [`TECHNICAL_REPORT.md`](TECHNICAL_REPORT.md). The tests are listed in the
source's [`docs/VERIFICATION.md`](../source/walmart-oxylabs-1.5.2/docs/VERIFICATION.md) under "Release 1.5.2".

| Correction | Until 1.5.1 | Shown by |
|---|---|---|
| Each provenance file names the real capture of a recovered value | `provenance.json` named the listing title | the per-run maps in [`correction_maps/`](../evidence/offline-replay/1.5.2/correction_maps/); [`agreement/`](../evidence/offline-replay/1.5.2/agreement/): 0 problems on S1 to S7 and B3 |
| Five carried sizes from 1.5.0 | "30 lb" | "2 pack, 30 lb" and four more ([`LINKED_EXAMPLES.csv`](LINKED_EXAMPLES.csv), E049 to E053) |
| A pack stated twice | "2 pack, 1 Pack" | "2 pack" (E054) |
| A set of two sizes | "12.5 oz" | "12.5 oz shampoo + 10.6 oz conditioner", by a unit test only. The delivered report called this a remaining limit; [`manifests/DOC_CORRECTIONS.md`](../manifests/DOC_CORRECTIONS.md) has the erratum |
| `blocked` and `request_failed` | one class, `inaccessible_challenged` | `publishing/dispositions.py`; `tests/unit/test_dispositions.py` |
| An interrupted replay resumes as a replay | `resume` built the live collector | [`replay_resume_before_fix.txt`](../evidence/offline-tests/1.5.2/defects_before_the_fix/replay_resume_before_fix.txt); `tests/integration/test_replay.py` |
| A row carried from a replay names the live run that read it | it said the replay had fetched it | [`carried_replay_before_fix.txt`](../evidence/offline-tests/1.5.2/defects_before_the_fix/carried_replay_before_fix.txt); `tests/integration/test_replay.py` |
| Six private-label brands, from USPTO records | `store_brand` "no" | [`docs/PRIVATE_LABEL.md`](../source/walmart-oxylabs-1.5.2/docs/PRIVATE_LABEL.md); S6: 100 "yes" instead of 80 |

## The points of the review

### UPC and size from the product's own page
- **Rule:** a product page counts only when it names the requested item id. Otherwise the outcome is
  `identity_mismatch`.
- **UPC:** taken only from the page's own UPC or GTIN field, with its leading zeros. It is never the item id or a
  sibling's. A UPC the listing already states is never replaced: if the page disagrees, the record keeps
  `UPC_SOURCE_MISMATCH`. See "Product detail path" in
  [`docs/OPERATIONS.md`](../source/walmart-oxylabs-1.5.2/docs/OPERATIONS.md).
- **Tests:** `tests/integration/test_detail_path.py` and `tests/unit/test_product_identifier.py` (which checks
  `007874201234`).
- **Status:**
  - VERIFIED LIVE: A36, A37, N4-04 and P3-02. Each response matched the requested product, store and Pickup.
  - VERIFIED OFFLINE: A35.
  - BLOCKED: P3-01. S6 left 226 UPCs and 9 sizes unread.
  - NOT TESTED: A38 (a page that answers 404).

### "Not fetched" versus "absent"
- **Rule:** only a page that was read can call a field absent. A page never read is `not_attempted`, with its reason.
  A refused request is `blocked`, and a failed one is `request_failed`. See "UPC outcomes" in
  [`docs/OPERATIONS.md`](../source/walmart-oxylabs-1.5.2/docs/OPERATIONS.md).
- **S6's 580 fresh rows:**
  - Live on 1.5.1: UPC fetched 1, recovered from a saved page 352, absent 1, not read 226.
  - Replay by 1.5.2: recovered 353, absent 1, `not_attempted` 226.
  - Evidence: [`agreement/S6.json`](../evidence/offline-replay/1.5.2/agreement/S6.json) and
    [`S6_CORRECTION_MAP.csv`](../evidence/offline-replay/1.5.2/offline_reprocessing/S6_CORRECTION_MAP.csv).
- **Status:** VERIFIED OFFLINE: P3-03 and A08.

### Reused observations keep their original time, run and revision
- **Rule:** an outcome read from a product page stays in `detail_observations`, with the read's time, run, source
  revision and page hash. It is reused for 30 days (`detail.reuse_days`), labelled `recovered_from_saved_detail`,
  and never described as newly fetched. A row carried from a replay names the live run, and names the replay as
  `read_again_by_run`.
- **Example:** item 1016968548, read 2026-10-28T05:32:39Z by run `01M60F6GHNXCTZPJ6G1PRM7KW7` on `8c3fbb1`
  ([`detail_observations_imported.csv`](../evidence/live/campaign/db/detail_observations_imported.csv)).
- **Status:** VERIFIED OFFLINE: N4-07 and P3-04.

### Packs, serving sizes, multipacks and conflicts
- **Rule:** serving size, the unit-price denominator and a sibling's size are never taken as the product's size. A
  multipack keeps both of its numbers ("4.5 fl oz, 6 Pack"). Statements that disagree are flagged
  `SIZE_CONFLICT`, and the field stays empty. A size is never calculated.
- **Source:** `sites/walmart/pack_size.py` and `sites/walmart/records.py`.
- **Tests:** `tests/unit/test_pack_size.py` and `tests/unit/test_walmart.py`.
- **Evidence:** [`SIZE_RULE_CHANGES_ON_AUTHENTIC_TITLES.csv`](../evidence/reconciliation/1.5.1/pack_fix_151/SIZE_RULE_CHANGES_ON_AUTHENTIC_TITLES.csv).
- **Status:**
  - VERIFIED OFFLINE: N4-05, N4-06, P3-06, P3-07 and A07.
  - Still open: a live example of bulk wording (E022 is PENDING in [`LINKED_EXAMPLES.csv`](LINKED_EXAMPLES.csv)).

### Promotions, and the Walmart-seller and Pickup price context
- **Price:** a price is the store's Pickup price only when Walmart is named as the seller on a Pickup line of store
  3891. A Delivery line exports no price (`NO_PICKUP_OFFER`), and so does a shipping-only or marketplace line. See
  "Store assortment, availability and price" in
  [`docs/OPERATIONS.md`](../source/walmart-oxylabs-1.5.2/docs/OPERATIONS.md).
- **Offers:** an offer is read with its full terms, and no price is computed from it. A saving on a single pack is
  not a volume offer.
- **Source and tests:** `assembly/offers.py`, `tests/unit/test_offers.py`, `tests/unit/test_price_provenance.py` and
  `tests/unit/test_product_page_offers.py`.
- **Status:**
  - VERIFIED LIVE: A27.
  - VERIFIED OFFLINE: A28, N7-04, A39, A40 and N6-05.
  - PARTIAL: A41, G06, P5-02 and N6-03. The search found 0 offers on 52 listing pages, 25 product-detail pages and
    10 product pages (2,415 tiles). See
    [`LIVE_OFFERS_SUMMARY.json`](../evidence/reconciliation/1.5.1/offers_live_final/LIVE_OFFERS_SUMMARY.json) and
    [`OFFERS_AUDIT_SUMMARY.json`](../evidence/reconciliation/1.5.1/offers_audit_saved_pages/OFFERS_AUDIT_SUMMARY.json).
    One quantity discount sits in an "Available for shipping" module, is not a Pickup offer and is not exported.

### Pagination, coverage, variants and sponsored products
- **Rule:** a listing is `DONE` only when its result grid balances the total it reports exactly. A result window,
  a repeated page, a block or a truncated page leaves it `INCOMPLETE`, and coverage gate G3 rejects the run. See
  "When a listing is complete" in [`docs/OPERATIONS.md`](../source/walmart-oxylabs-1.5.2/docs/OPERATIONS.md).
- **Status of pagination:**
  - VERIFIED LIVE: A11, A13, A14 and A15.
  - VERIFIED OFFLINE: A12.
  - PARTIAL: A17 and A18 (partition).
- **Full coverage:** BLOCKED: A19, A70, P4-01 and N1A-11. The campaign read 7 of the scope's 945 listings, and no CSV
  row is complete ([`COVERAGE_RECONCILIATION.csv`](../data/COVERAGE_RECONCILIATION.csv)).
- **Sponsored products and variants:** PARTIAL: A24, A25, B16, P4-02 and N5-04. There are 651 rows:
  - 215 are closed: 199 historical and 16 live.
  - Of the 436 open rows, saved pages settle 41 (identity, category and Pickup) and 24 (identity and category, no
    Pickup line). 96 have no category, 1 page is unusable, and 274 need their own page.
  - That leaves 275 distinct items in
    [`EXACT_LIVE_READ_QUEUE_1_5_2.csv`](../evidence/reconciliation/1.5.2/sponsored_and_variant_reconciliation/EXACT_LIVE_READ_QUEUE_1_5_2.csv).

### Unavailable products retained
- **Rule:** a verified product the run does not observe is carried with its own date. There is no age limit, and a
  shipping or marketplace price never replaces the store's price.
- **Tests:** `tests/integration/test_lineage_retention.py` and `tests/integration/test_retained_masking.py`.
- **Status:**
  - VERIFIED OFFLINE: A30 and P6-04.
  - VERIFIED LIVE: N7-05. S6 retained 706 rows.
  - PARTIAL: A34. No natural change from available to unavailable has been observed.

### Interruption recovery, overlap refusal and last-good preservation
- **What happened live on 1.5.1:** S6 was killed after 8 pages and resumed, with no record lost. Two overlapping
  starts were refused with exit 9 and no request. Evidence:
  - [`s6_kill_record.json`](../evidence/live/campaign/s6_kill_record.json);
  - [`69_s6_resume.jsonl`](../evidence/live/campaign/logs/69_s6_resume.jsonl);
  - [`66_s6_overlap_during_run_b.jsonl`](../evidence/live/campaign/logs/66_s6_overlap_during_run_b.jsonl);
  - [`68_s6_overlap_unfinished.jsonl`](../evidence/live/campaign/logs/68_s6_overlap_unfinished.jsonl).
- **What happened on 1.5.2, in its container on the owner's Azure test VM:** a graceful stop during S4's replay and
  a forced kill during S6's, then a resume. Both resumes exited 0
  ([`README.txt`](../evidence/owner-azure-test/1.5.2/azure_docker_recovery/README.txt)).
- **Last-good protection:** shown against a fixture only (SYNTHETIC). All 10 fault cases passed
  ([`owner_vm/publication/`](../evidence/owner-azure-test/1.5.2/owner_vm/publication/README.txt)):
  - in the 7 refused cases, the last-good publication stayed unchanged;
  - in the 2 interrupted cases, it was kept until the retried or resumed run published;
  - with one failed product page, the run was allowed to publish.
- **Status:**
  - VERIFIED LIVE: A47, A48, N7-02 and P6-02.
  - VERIFIED OFFLINE: P6-01, A50, N7-01 and P6-05.

### The live data, S6
[`data/S6-1.5.1/`](../data/S6-1.5.1/) holds 580 valid, distinct fresh products. Release **1.5.1** collected them on
2026-10-31 from 15 Pickup result pages of five listings. The S6 export also has 706 retained rows.
[`manifests/check_data.py`](../manifests/check_data.py) checks the files against the run's own export and record
map. The run is a capped pilot, rejected by G3, and its rows are not a 1.5.2 result. Status: PARTIAL, A56 and N1A-05
(500 or more fresh from one run of the final version).

### Docker, Azure, Scrape.do, walkthrough, final-version live validation, full coverage
- **VERIFIED OFFLINE:**
  - A61: Docker. Both editions built on the owner's Azure test VM, and a run without a key is refused (exit 3).
  - A64: the walkthrough, [`walkthrough/`](../walkthrough/). It contains no live provider run.
- **PARTIAL:** A63 and G08: Azure. The tests used the owner's test VM. Nothing ran in the client's environment.
- **BLOCKED:**
  - G02: Scrape.do. 10 of 1,000 credits were left at 2026-11-01T18:23:14Z, and about 213 are needed.
  - P8-01: a live run of the final version.
  - A19 and A70: full coverage.
  - A66: client-observed acceptance.
  - A73: deallocating the test VM. This is Hamza's decision.

### Classic
- **The probe:** [`classic-probe/`](../classic-probe/) is the frozen probe 1.5.2 (revision `627c804`; its code last
  changed in `2ed64b7`). Its live mode is disabled in the code, and it has sent no request. The newer
  Mariano's/shared probe is not here.
- **Proposed limits:** 10 requests per retailer and 20 for both. Those counts include setup, authentication and
  qualification calls, every retry and every restart. The other limits are 30 minutes and USD 5.00 combined. These
  are ceilings proposed to the client, not an approval
  ([`CLASSIC_TEST_PLAN.md`](../classic-probe/oxylabs-classic-probe/CLASSIC_TEST_PLAN.md)).
- **Offline results:** tested from its archive on the owner's VM: 71 passed and 1 skipped, and the live command was
  refused (exit 3).
- **Status:** NOT TESTED: A67. Evidence from the Oxylabs Web API is not proof of Classic access.

### The data corrections
Each replay has its row-by-row correction map in
[`correction_maps/`](../evidence/offline-replay/1.5.2/correction_maps/):
- one map for each of the nine runs;
- one map for B3 against 1.5.1;
- one map for B3 against 1.4.1, in `b3_1_4_1_to_1_5_2/`.

Each row gives the item, the file and field, the value before and after, and the reason. The delivered live files in
[`data/`](../data/) are unchanged. A corrected value appears only in the replay outputs, which are evidence and not
live data.
