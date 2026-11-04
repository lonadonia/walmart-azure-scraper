# Collector 1.6.5: offline tests of the correction

No request reached a provider or Walmart. The tests use two authentic pages that run L10 stored and the 26 records L10
read from one of them. A few tests apply SYNTHETIC changes to an authentic record or placement; each such change is
named in its test.

The two pages are:

- Beauty's "New Arrivals", fetch `01M6KB69AJA2N65MDQP4V1QWTE`: the flat layout;
- Men's Hair & Beard Care, fetch `01M6KB1YNCARK7HQ80N2KNCE23`: price lines.

Release 1.6.5 changes only the independent source check (`checks/source_check.py`). The page reader, the records,
the exports and the publication step are as in 1.6.4.

| File | What it holds |
|---|---|
| `COLLECTOR_1.6.4_TO_1.6.5.diff`, `DIFFSTAT.txt` | the whole change from release 1.6.4 (`28ac7d3`) to 1.6.5 (`67d216e`), collector folder only |
| `COLLECTOR_1.5.2_TO_1.6.5.diff`, `DIFFSTAT_1.5.2_TO_1.6.5.txt` | the pinned correction diff, collector folder only: from release 1.5.2 (`627c804`), the one the client reviewed, to 1.6.5. Each release's own step is in its folder, `../1.6.0-collector/` to `../1.6.5-collector/` |
| `REGRESSION_SET.txt`, `REGRESSION_TESTS_ON_1.6.4.log`, `REGRESSION_TESTS_ON_1.6.4.junit.xml` | the 8 tests of the new test file, run against the unchanged 1.6.4 code |
| `UNIT_1.6.5.log`, `STATIC_1.6.5.log` | the unit suite (533 passed) and the static checks on the 1.6.5 commit, in the development tree |
| `FLAT_LAYOUT_SCAN.json`, `flat_layout_scan_165.py` | every stored page copy of the 23 live runs of store 3891 Pickup on the workstation. Each product placement is sorted by the layout its prices are given in; each run's release is the one the run database recorded |

The integration suite is not repeated here. It ran on clean extractions of both 1.6.5 editions: 200 passed in each,
with 533 unit tests, ruff, format and mypy (`../../verification/1.6.5/package/`).

## The tests fail on 1.6.4 for the right reason

The 1.6.5 test file `tests/unit/test_flat_price_layout.py` and its capture folder
`tests/captures/listing_pages_20261104_flat/` were copied into a clean extraction of the 1.6.4 Oxylabs edition.
That extraction is `WALMART_OXYLABS_SOURCE_1.6.4.zip`, sha256 `8d226b2f…`, the edition that ran L10, with its own
code and lock. Neither path existed in it before. The log's second line names the copy, and the source check it
imports is the copy's own. Result: 6 failed, 2 passed.

| Test | On 1.6.4 | Why |
|---|---|---|
| `test_the_prices_read_are_those_the_page_displays` | FAIL | for a placement that displays $5.00, 1.6.4 expects no price at all: `('', '', '')` |
| `test_the_records_the_run_read_from_the_page_are_verified_against_it` | FAIL | the 26 records L10 read from the flat page, judged on that page: 26 mismatches on 1.6.4, 26 verified on 1.6.5 |
| `test_a_record_seen_on_two_pages_is_judged_on_the_page_it_was_read_from` | FAIL | Head & Shoulders `20409871453` has a placement on each page. 1.6.4 cannot read the flat page's prices, judges the record on the other page and reports that page's other image size, as L10's validation did |
| `test_the_canary_comparison_accepts_the_page` | FAIL | the canary's comparison finds every record's regular price unequal. A run whose first recorded page came in this layout would have been stopped |
| `test_a_wrong_price_or_unit_price_is_still_a_mismatch` | FAIL | three SYNTHETIC wrong copies of an authentic record. 1.6.4 reports 2 and verifies the third, whose price and unit price were both emptied: it expects no price from this page. 1.6.5 reports all 3 |
| `test_a_flat_was_price_above_the_current_price_is_a_sale` | FAIL | SYNTHETIC: a flat was-price above the current price. 1.6.4 reads no price at all; 1.6.5 reads a sale (regular $19.97, sale $16.97, $1.06/oz) |
| `test_the_fixture_matches_its_manifest` | pass | the capture is the stored copies named in its manifest |
| `test_the_live_page_gives_its_prices_as_flat_strings_only` | pass | a fact about the pages, the same with either release. The flat page has 50 placements of 42 products, with flat strings and no price line. The other page has 59 placements: 58 with price lines, 1 with no price, none flat |

On the 1.6.5 commit (`67d216e`, clean tree) all 8 pass with the rest of the unit suite (`UNIT_1.6.5.log`). The
JUnit file's host name is replaced by `(workstation)`.

## Which pages are in which layout

`FLAT_LAYOUT_SCAN.json` reads all 1,531 page copies stored by the 23 live runs (2026-10-31 to 2026-11-04).

| Runs | Page copies | Placements | in price lines | nested objects | flat strings only | no price |
|---|---|---|---|---|---|---|
| 21 runs of releases 1.5.0 to 1.6.4 | 1,527 | 33,736 | 32,736 | 675 | 50 | 275 |
| L11 and L11b (release 1.6.5) | 4 | 104 | 53 | 0 | 50 | 1 |

By page kind:

- **Listing pages with a result grid** (774): every one but two gives its prices in price lines. 19 of them list no
  product, and 266 placements on them show no price. The two are Beauty's "New Arrivals", page 1:
  - fetched by L10 at 13:15:20Z;
  - fetched again by L11 at 14:24:41Z;
  - 50 of 50 placements with flat strings only, both times.
- **Product pages with product data** (685): they give their price as nested objects (675), or show none (10).
- **The other 72 copies** hold no product placement:
  - 53 store pages;
  - 12 category pages;
  - 3 listing and 3 product fetches whose page has no result grid or product data;
  - one L6 listing fetch with no page data at all: the challenge page (`01M6K2F80M1AFY26P6BMN56F4C`).

The 1.6.5 capture's README counts "1,526 pages stored by the collector's 21 live runs". That is the 1,527 copies less
the challenge page. A comment in the 1.6.5 test file says the price-lines page gives its prices in price lines "as
every other stored page of the live runs". That is true of the listing pages; product pages use the nested objects.
