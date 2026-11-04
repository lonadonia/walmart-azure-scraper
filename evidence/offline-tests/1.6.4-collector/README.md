# Collector 1.6.4: offline tests of the correction

SYNTHETIC tests and one authentic stored page. No request reached a provider or Walmart. The tests use fixture
pages and a temporary local PostgreSQL. The live page here was stored by run L7 for the Household Essentials link
"Bidets"; no new request was made for it. Release 1.6.4 reads that page's reported total of 0 as 0.

| File | What it holds |
|---|---|
| `COLLECTOR_1.6.3_TO_1.6.4.diff`, `DIFFSTAT.txt` | the whole change from release 1.6.3 (`def55e5`) to 1.6.4 (`28ac7d3`), collector folder only |
| `COLLECTOR_1.5.2_TO_1.6.4.diff`, `DIFFSTAT_1.5.2_TO_1.6.4.txt` | the pinned correction diff, collector folder only: from release 1.5.2 (`627c804`), the one the client reviewed, to 1.6.4. Each release's own step is in its folder: `../1.6.0-collector/` to `../1.6.4-collector/` |
| `REGRESSION_SET.txt`, `REGRESSION_TESTS_ON_1.6.3.log`, `REGRESSION_TESTS_ON_1.6.3.junit.xml` | the 11 tests below, run against the unchanged 1.6.3 code |
| `THE_SAME_SCENARIO_ON_1.6.3.log`, `THE_SAME_SCENARIO_ON_1.6.3.test.py` | the scenario of the new integration test, asserting what 1.6.3 does with it: the run stops (`ABNORMAL_RESULT`, "the page reports results but shows no product"), as live L7 did. This test file was run in the 1.6.3 copy only; it is in no release |
| `UNIT_1.6.4.log`, `INTEGRATION_1.6.4.log`, `STATIC_1.6.4.log` | the full suites and the static checks on the 1.6.4 commit, in the development tree |
| `EMPTY_GRID_PAGE_CHECK.json`, `empty_grid_check.py` | L7's Bidets answer, judged by each release's own page reader. Both the private raw answer and the stored copy are judged; the files give their SHA-256 values only |
| `REPLAY_TOTALS_1.6.3_VS_1.6.4.csv`, `REPLAY_TOTALS_SUMMARY.json`, `replay_totals.py` | every stored listing page of the live runs on the workstation, read by both releases: 343 pages of 20 runs (the 1.5.x and 1.6.x campaigns) |

## The tests fail on 1.6.3 for the right reason

The 1.6.4 test files were copied into a clean copy of the 1.6.3 Oxylabs edition. That copy is
`WALMART_OXYLABS_SOURCE_1.6.3.zip`, with its own code and lock. The copied files are:

- `tests/unit/test_empty_pickup_grid.py`;
- the capture folder `tests/captures/listing_pages_20261104/`;
- `tests/synthetic_walmart.py`;
- `tests/integration/test_coverage_and_assortment.py`.

The edition's own copies of the last two equal the 1.6.3 commit's, and 1.6.4 only adds to them. Only the 11 tests of
`REGRESSION_SET.txt` were run, as the log's third line shows: 4 failed and 7 passed.

| Test | On 1.6.3 | Why |
|---|---|---|
| `test_empty_pickup_grid.py::test_the_live_bidets_page_reports_a_total_of_zero_not_the_count_of_its_carousel` | FAIL | 1.6.3 reads the authentic page's total as 10: the page's `count`, its shipping carousel's products |
| `test_empty_pickup_grid.py::test_a_reported_zero_is_the_total_and_count_is_read_only_without_one[zero-beside-a-carousel]` | FAIL | `aggregatedCount` 0 with `count` 10: 1.6.3 reads 10 |
| `test_empty_pickup_grid.py::test_a_reported_zero_is_the_total_and_count_is_read_only_without_one[zero-written-as-text]` | FAIL | the same with `"0"` |
| `test_coverage_and_assortment.py::test_a_listing_whose_pickup_grid_is_empty_beside_a_shipping_carousel_is_empty_and_the_run_goes_on` | FAIL | 1.6.3 stops the run before the listing's coverage is written (`KeyError` on its row). `THE_SAME_SCENARIO_ON_1.6.3.log` shows the stop itself: rejected, `ABNORMAL_RESULT`, "the page reports results but shows no product" |
| `test_empty_pickup_grid.py::test_the_fixture_matches_its_manifest` | pass | the capture is the stored copy named in its manifest |
| `test_empty_pickup_grid.py::...[a-total-above-zero]`, `[no-aggregated-count]`, `[a-null-aggregated-count]`, `[zero-and-no-product]` | pass | unchanged: a total above 0, the page's own `count` when it reports no `aggregatedCount`, and a listing that shows 0 of 0 |
| `test_empty_pickup_grid.py::test_the_synthetic_copy_has_the_shape_of_the_live_page` | pass | the synthetic page the integration tests use reads like the authentic one (with either release) |
| `test_coverage_and_assortment.py::test_a_page_that_reports_results_it_does_not_show_still_stops_the_run` | pass | unchanged: a first page that reports 5 results and shows none still stops the run |

On the 1.6.4 commit (`28ac7d3`, clean tree) all 11 pass with the rest of both suites (`UNIT_1.6.4.log`,
`INTEGRATION_1.6.4.log`, `STATIC_1.6.4.log`). The JUnit file's host name is replaced by `(workstation)`.

## The live answer, judged by each release

`EMPTY_GRID_PAGE_CHECK.json` applies each release's own page reader to the raw answer and to the stored copy:

| | Release 1.6.3 | Release 1.6.4 |
|---|---|---|
| Listing total | 10 (the page's `count`: 10 carousel products) | 0 (`aggregatedCount`) |
| What the collector does | stops: "the page reports results but shows no product" | records the listing as empty, once the page's own store check passes |

Both releases see the same page:

- the result grid is empty, with fulfillment Pickup;
- the "Available for shipping" carousel holds 10 products (fulfillment Shipping), which are not results;
- the page location names store 3891, ZIP 60085 and PICKUP.

## The change, replayed on every stored listing page

`REPLAY_TOTALS_1.6.3_VS_1.6.4.csv` covers the 343 listing pages of 20 live runs stored on the workstation, among them
L8's 18 (the 1.6.3 demonstration). 1.6.4 reads 342 of them exactly as 1.6.3 does: the same total, count, last page,
products, placements and branch. The one it reads differently is L7's Bidets page. Six other pages also report
`aggregatedCount` 0, but each has `count` 0 and no product. Both releases read those as empty listings.
