# Collector 1.6.3: offline tests of the three corrections

SYNTHETIC: fixture pages and a temporary local PostgreSQL; no request reached a provider or Walmart. The one record
here made from a live page is `NOT_FOUND_PAGE_CHECK.json`: the raw answer that run L6 stored for the Shampoo child
listing `nexxus-shampoo` (no new request), judged offline by each release's own code.

| File | What it holds |
|---|---|
| `COLLECTOR_1.6.2_TO_1.6.3.diff`, `DIFFSTAT.txt` | the whole change from release 1.6.2 (`1274056`) to 1.6.3 (`def55e5`), collector folder only |
| `COLLECTOR_1.5.2_TO_1.6.3.diff`, `DIFFSTAT_1.5.2_TO_1.6.3.txt` | the correction diff from release 1.5.2 (`627c804`), the one the client reviewed, to 1.6.3, collector folder only. The final pinned diff, to release 1.6.4, is [`../1.6.4-collector/COLLECTOR_1.5.2_TO_1.6.4.diff`](../1.6.4-collector/COLLECTOR_1.5.2_TO_1.6.4.diff) |
| `REGRESSION_SET.txt`, `REGRESSION_TESTS_ON_1.6.2.log`, `REGRESSION_TESTS_ON_1.6.2.junit.xml` | the 25 tests below, run against the unchanged 1.6.2 code (2026-11-04 11:46Z) |
| `UNIT_1.6.3.log`, `INTEGRATION_1.6.3.log`, `STATIC_1.6.3.log` | the full suites and the static checks on 1.6.3, in the development tree |
| `INTEGRATION_1.6.3_BEFORE_THE_TEST_CHANGE.log` | the full integration suite on the 1.6.3 code before the second test was changed: 1 failed, 197 passed |
| `NOT_FOUND_PAGE_CHECK.json` | L6's stored not-found answer judged by release 1.6.2 and by the installed 1.6.3 edition |

## The tests fail on 1.6.2 for the right reason

The 1.6.3 test files (`tests/unit/test_not_found_page.py`, `tests/integration/test_detail_path.py`,
`tests/integration/test_coverage_and_assortment.py`, `tests/integration/test_operations.py` and the fixture module
`tests/synthetic_walmart.py`) were copied into a clean copy of the 1.6.2 Oxylabs edition (its own code, lock and
other fixtures), and only the 25 tests of `REGRESSION_SET.txt` were run, as the log's third line shows: 13 failed and
12 passed.

| Test | On 1.6.2 | Why |
|---|---|---|
| `test_not_found_page.py::test_the_site_not_found_page_is_no_challenge` | FAIL | 1.6.2 calls Walmart's not-found page a challenge (`missing_initial_state`): it does not see the page data script whose `id` is written without quotes |
| `test_not_found_page.py::test_its_page_data_is_read_and_says_it_is_the_not_found_page` | FAIL | 1.6.2's page data reader finds no script (`PageDataMissing`) |
| `test_not_found_page.py::test_the_stored_copy_keeps_that_page_data_redacted_and_readable` | FAIL | 1.6.2's sanitizer drops that page data from the stored copy (`page_data_kept=False`) |
| `test_not_found_page.py::test_the_page_data_script_is_found_however_its_id_is_quoted[single-quoted]` | FAIL | 1.6.2 finds the script only when its `id` is in double quotes |
| `test_not_found_page.py::test_the_page_data_script_is_found_however_its_id_is_quoted[unquoted]` | FAIL | the same, without quotes |
| `test_not_found_page.py::test_a_listing_page_and_a_category_page_are_not_the_not_found_page` | FAIL | 1.6.2 has no `not_found_page` reader |
| `test_coverage_and_assortment.py::test_a_listing_link_the_site_answers_with_its_not_found_page_is_recorded_unread_and_the_run_goes_on` | FAIL | 1.6.2 stops the run (`SITE_REFUSAL`, store held) before the listing's coverage is written |
| `test_detail_path.py::test_a_run_with_detail_reading_off_still_uses_what_earlier_reads_established` | FAIL | with detail reading off, 1.6.2 exports the UPC an earlier read established as blank |
| `test_detail_path.py::test_a_carried_row_gets_its_empty_upc_and_size_from_a_saved_read_that_it_names` | FAIL | 1.6.2 leaves a carried row's empty UPC and size empty, although a saved read answers them |
| `test_detail_path.py::test_a_carried_row_never_takes_a_upc_another_exported_row_has` | FAIL | 1.6.2 has no recovery for carried rows, so it records no withheld recovery either |
| `test_detail_path.py::test_a_product_page_that_is_the_site_not_found_page_is_a_failed_request_never_a_parse_failure` | FAIL | 1.6.2 records a product page that is the not-found page as `parse_failed` |
| `test_detail_path.py::test_every_outcome_of_an_empty_field_is_told_apart` (changed in 1.6.3) | FAIL | with detail reading off, 1.6.2 calls the product an earlier read found without a UPC `not_attempted`; 1.6.3 keeps that read's outcome, `absent_in_source`, named as that read (its run and time). The products no read answers for stay `not_attempted` in both |
| `test_operations.py::test_a_pilot_budget_is_named_on_the_run_and_never_published` (changed in 1.6.3) | FAIL | the second pilot, with detail reading off, exports all four products `not_attempted` on 1.6.2, the one whose UPC the first pilot read included. 1.6.3 requests no product page either, keeps that read's UPC named as that read (`recovered_from_saved_detail`, its run), and leaves that product's queue entry resolved; the three others stay `not_attempted`, "product detail reading is off", and pending in the store's queue |
| `test_not_found_page.py::test_the_page_data_script_is_found_however_its_id_is_quoted[double-quoted]` | pass | unchanged: the usual page data script |
| `test_not_found_page.py::test_a_challenge_is_still_a_challenge_with_unquoted_page_data` | pass | unchanged: a challenge page stays a challenge, whatever its page data |
| `test_not_found_page.py::test_a_page_without_the_page_data_script_is_still_refused_as_before[no-page-data]` | pass | unchanged: a page without page data is refused |
| `test_not_found_page.py::test_a_page_without_the_page_data_script_is_still_refused_as_before[the-name-elsewhere]` | pass | unchanged: the name elsewhere in the page is not page data |
| `test_not_found_page.py::test_a_page_without_the_page_data_script_is_still_refused_as_before[another-id]` | pass | unchanged: a script with another `id` is not page data |
| `test_detail_path.py::test_a_page_nobody_requested_is_never_called_absent_in_any_evidence_file` | pass | unchanged: a page never requested is never called absent |
| `test_detail_path.py::test_a_carried_row_names_the_sources_of_its_own_earlier_run` | pass | unchanged: a carried row names its earlier run's sources |
| `test_detail_path.py::test_a_carried_row_names_the_run_that_read_its_fields` | pass | unchanged: a carried row names the run that read its fields |
| `test_detail_path.py::test_a_run_that_ends_before_its_detail_pass_still_uses_what_earlier_reads_established` | pass | unchanged (1.6.1's correction) |
| `test_coverage_and_assortment.py::test_a_listing_link_that_serves_a_category_page_is_recorded_unread_and_the_run_goes_on` | pass | unchanged (1.6.2's correction) |
| `test_coverage_and_assortment.py::test_any_other_page_without_a_result_grid_still_stops_the_run[an-unknown-page-without-a-grid]` | pass | unchanged: a page of unknown shape still stops the run |
| `test_coverage_and_assortment.py::test_any_other_page_without_a_result_grid_still_stops_the_run[a-category-page-after-the-first-result-page]` | pass | unchanged: a category page after a listing's first result page still stops the run |

Five of the twelve controls are new tests (the five `test_not_found_page.py` controls). The two changed tests are
the only existing tests 1.6.3 changes. The integration suite on the 1.6.3 code found them, unchanged: a first run
stopped at the first failure (`test_every_outcome_of_an_empty_field_is_told_apart`), and the full run of 11:19Z to
11:41Z failed only `test_a_pilot_budget_is_named_on_the_run_and_never_published`, 197 passed
(`INTEGRATION_1.6.3_BEFORE_THE_TEST_CHANGE.log`). Their earlier versions encoded what 1.6.3 corrects.

On the 1.6.3 commit (`def55e5`, clean tree) all 25 pass with the rest of both suites: `UNIT_1.6.3.log` 513 passed
(11:54Z), `INTEGRATION_1.6.3.log` 198 passed (11:54Z to 12:17Z), and `STATIC_1.6.3.log` has ruff, ruff format and
mypy (strict) clean. The JUnit file's host name is replaced by `(workstation)`.

## The live answer, judged by each release

`NOT_FOUND_PAGE_CHECK.json` holds, for release 1.6.2 and for the installed 1.6.3 edition, the verdict on the stored
raw answer (SHA-256 of the body, `6d976799...`), the verdict on the sanitized copy each release stores, and the page
data route each release reads from it. 1.6.2: a challenge (`missing_initial_state`), page data dropped. 1.6.3: not a
challenge, page data kept, route `/404`. No page content is printed.
