# Collector 1.6.2: offline tests of the two corrections

SYNTHETIC: fixture pages and a temporary local PostgreSQL; no request reached a provider or Walmart.

| File | What it holds |
|---|---|
| `COLLECTOR_1.6.1_TO_1.6.2.diff`, `DIFFSTAT.txt` | the whole change from release 1.6.1 (`1780349`) to 1.6.2, collector folder only |
| `REGRESSION_TESTS_ON_1.6.1.log`, `REGRESSION_TESTS_ON_1.6.1.junit.xml` | the seven 1.6.2 tests run against the unchanged 1.6.1 code (2026-11-03 19:23Z) |
| `UNIT_1.6.2.log`, `INTEGRATION_1.6.2.log`, `STATIC_1.6.2.log` | the full suites and the static checks on 1.6.2, in the development tree |
| `COLLECTOR_1.5.2_TO_1.6.2.diff`, `DIFFSTAT_1.5.2_TO_1.6.2.txt` | the correction diff from release 1.5.2 (`627c804`) to 1.6.2, collector folder only. The final pinned diff, to release 1.6.4, is [`../1.6.4-collector/COLLECTOR_1.5.2_TO_1.6.4.diff`](../1.6.4-collector/COLLECTOR_1.5.2_TO_1.6.4.diff) |

## The tests fail on 1.6.1 for the right reason

The three 1.6.2 test files were copied into a clean copy of the 1.6.1 Oxylabs edition (its own code, lock and
fixtures; the three files it had are identical to those of commit `1780349`), and only the new tests were run:

| Test | On 1.6.1 | Why |
|---|---|---|
| `tests/unit/test_walmart.py::test_a_category_page_is_told_from_its_own_data_and_no_other_page_is_one` | FAIL | 1.6.1 has no `category_page` reader |
| `tests/unit/test_listing_reconciliation.py::test_a_moving_total_far_above_what_the_site_served_is_a_result_window_never_done` | FAIL | 1.6.1 ends the listing `INCOMPLETE` at `EMPTY_PAGE` ("not reconciled"), not at the result window |
| `tests/integration/test_coverage_and_assortment.py::test_a_moving_total_does_not_hide_a_window_end_and_the_listing_is_read_through_its_children` | FAIL | 1.6.1 leaves the parent `INCOMPLETE` and never reads its child categories |
| `tests/integration/test_coverage_and_assortment.py::test_a_listing_link_that_serves_a_category_page_is_recorded_unread_and_the_run_goes_on` | FAIL | 1.6.1 stops the run (`ABNORMAL_RESULT`) before the listing's coverage is written |
| `tests/unit/test_listing_reconciliation.py::test_a_shortfall_no_larger_than_the_totals_moved_stays_unreconciled_not_a_window` | pass | unchanged behaviour: a shortfall within the moved totals is still "not reconciled" |
| `tests/integration/test_coverage_and_assortment.py::test_any_other_page_without_a_result_grid_still_stops_the_run[an-unknown-page-without-a-grid]` | pass | unchanged: a page of unknown shape still stops the run |
| `tests/integration/test_coverage_and_assortment.py::test_any_other_page_without_a_result_grid_still_stops_the_run[a-category-page-after-the-first-result-page]` | pass | unchanged: a category page after a listing's first result page still stops the run |

On 1.6.2 all seven pass, with the rest of both suites. The JUnit file's host name is replaced by `(workstation)`.
