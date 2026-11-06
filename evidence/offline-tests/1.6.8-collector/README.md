# Collector 1.6.8: offline tests of the corrections

No request in these tests reached a provider or Walmart. The tests run the collector against scripted local stubs on
`127.0.0.1` and a local PostgreSQL.

Release 1.6.8 is commit `85c29e7` (`85c29e7b2404500299056973f50c84b84e187a5a`) of the development monorepo. Its
archives were built by the builder of commit `2cab0a2` (`scripts/build_walmart_168_delivery.py`), which reads the
release commit's tree; each edition's `BUILD_INFO.json` names `85c29e7`. Release 1.6.8 carries every change of
release 1.6.7 (`7ee2fa1`), which was prepared on 2026-11-05 and never delivered, and adds the corrections below.
Three earlier 1.6.8 commits, `745607e`, `7a96218` and `9c14425`, were found wanting before delivery and replaced
(below). No archive of any of them was delivered, and no live run was made with any of them.

## What 1.6.7 changed (carried into 1.6.8)

These changes answer the client's review of 1.6.6.

- **Rows complete only through their listings.** A partitioned listing is complete only when every child category
  ended complete and the children's distinct products balance its total. Release 1.6.6 marked such a listing done
  when its identities balanced, even if a child had ended on any of these:
  - a moving total;
  - a repeated or wrong page;
  - its result window.

  A child cut by a run limit now makes the listing `CAPPED`. A partition with no child recorded is incomplete.
- **Rows read in part.** A CSV row read only in part is `CAPPED`, never done. This covers configured listings,
  `--subcategory`, and listings the run did not choose.
- **The coverage report.**
  - Each listing has `effective_status` and `effective_reason`; a partition is judged through its children.
  - `csv_rows` gives each CSV row's verdict, alongside `csv_rows_complete` and `csv_rows_read_in_part`.
  - `coverage_complete` is true only when every row is complete.
- **The agreed category mapping.**
  - A listing read by its path takes the name the CSV row's category page gives it. No request is made for this.
  - A carried row takes that name too, and its lineage keeps the old one (`historical.renamed_by_mapping`).
  - This resolves the "Fabric Softener"/"Fabric Softeners" discrepancy of `1115193_1071967_1630538`: the
    Household Essentials page names it "Fabric Softeners".
- **UPC and size decided separately.** A size conflict withholds the size only (`historical.size_withheld`), never a UPC
  that the same read verifies.

## What 1.6.8 adds

### Subcategories that are category pages of their own

A link in a row's navigation to a category page of its own (`/cp/…`) used to be skipped as "a category page or other
page, not a product listing". So the listings named only on that page were never read, and the row could still be
called complete. The stored category pages of the nine CSV rows that have one link 106 such pages (Food: 49). The
1.6.6 coverage tables recorded 95 of them as out of scope; for 56 of those 95, no listing under the page's id is known.

In 1.6.8:
- **Reading such a page.** The collector reads the page through the general API and adds the listings its own
  navigation names as listings of the row. The page is recorded as `EXPANDED` and the event is
  `SUBCATEGORY_PAGE_READ`. A subcategory page of that page is read in turn.
- **Pages that cannot be read.** These keep the row incomplete, with the reason recorded (`SUBCATEGORY_PAGE_NOT_READ`):
  - a not-found page;
  - unreadable page data;
  - a page `robots.txt` disallows;
  - a page past the safety ceiling of 2,000 subcategory pages per row.
- **Pages skipped by older releases.** In the coverage report, a `/cp/` page that release 1.6.7 or earlier skipped
  keeps its row open (`effective_status` `INCOMPLETE`). So the earlier live runs' coverage is never overstated.

### Links that show a listing filtered, or show one view twice

The stored category pages of the live runs record 1,505 links. Checked against their full URLs (on the workstation,
2026-11-05, no request), some of them show a listing filtered, through a facet in the link's query, and some show
one view of a listing twice:

| Category page | Listing | Links (position on the page) | What 1.6.8 does |
|---|---|---|---|
| Food | `976759_976794_2002490` | "Pantry" (9th), "Great Value Pantry" (55th): both the listing itself | reads it once, as "Pantry" |
| Feeding | `5427_132943_2441534` | "Baby Health Care" (55th), "Baby Healthcare" (63rd): both the listing itself | reads it once, as "Baby Health Care" |
| Personal Care | `1005862_1001487` | "Deodorant" (3rd): the listing itself; "Men's Deodorant" (70th): `facet=gender:Male` | reads the listing as "Deodorant"; the filtered view is recorded, not read |
| Health & Wellness | `976760_4661388_6244277_7158394` | "Cough" (1st): `facet=health_concern:Cough`; "Subscription" (8th): `facet=subscription_eligible:Subscription item` | reads the listing itself, in full, once; neither filtered view names it |

Up to release 1.6.7, each link was read by its path, as if it were the listing. So part of a listing could stand for
all of it: L10 (release 1.6.4) has 19 products "Cough" and 31 "Subscription" from the one listing, each read through a
filtered view.

In 1.6.8:
- **One read per view.** Two links to the same view of a listing are one read, under the first name the page gives
  it (`navigation.view_key`, `listing_key`; in `discover` and `expand`). A link whose query narrows the listing (a
  facet, a price; `navigation.narrowing`) is not read as such. The listing itself is read, in full, once, named as the
  page names the listing itself, or by its own result page when the page links it only through filtered views. An
  unknown parameter counts as a filter: taken wrongly, it costs at most a name, never coverage. Each filtered link is
  recorded in the page's event (`filtered_views`).
- **Filtered views of the row's own category.** Household Essentials "Clearance", Personal Care "Clearance" and Pets
  "Under $5" are recorded and not read: the row's subcategories list their products.
- **Shelves.** Shelf links (listing ID `0`, `_be_shelf_id`) are listings of their own, each recorded under its own ID
  (`0@shelf_id:N`, `navigation.read_id`). Food links two: shelf 8210692 and shelf 7195079.
- **The agreed mapping is per view.** It takes the first name a stored page gives a view
  (`navigation.category_page_names`); a later page still replaces an earlier page's name. A carried record takes only
  the name of the exact view its read showed (`retention.Verified.named_view`). So a name a page gives a filtered
  view never renames the listing itself.
- **The coverage report.** A stored read of a filtered view never completes its listing (`effective_status`
  `INCOMPLETE`; `filtered_view`; `filtered_view_of` `listing`). A stored read of a filtered view of the row's own
  category is not a listing of the row and blocks nothing (`SKIPPED`; `filtered_view_of` `row`). The published 1.6.6
  W4 tables counted four listings complete from a filtered view alone (L10: Emergency Contraception, Celebrity
  Colognes, Allergy, Contact solution).

A 1.6.8 run can make more requests than a 1.6.7 run. It makes one request per subcategory page, plus the result
pages of the listings those pages name. A listing linked only filtered is now read whole. It reads one listing fewer
for each second link to the same view.

## The three candidates that were replaced

| Commit | What was found | What replaced it |
|---|---|---|
| `745607e` (first) | One existing test kept its 1.6.7 expectation; the full Linux suite on the owner's VM failed that test (2026-11-05). | `7a96218` changes only that test's expected list and a paragraph of `docs/VERIFICATION.md`; no collector code (`candidates/COLLECTOR_745607e_TO_7a96218.diff`: 2 files, 14 lines added, 2 removed). |
| `7a96218` (second) | Replayed on the stored pages of L12 on the workstation (2026-11-05, no request), its export compared with L12's published one. Beside the agreed renames (52 records "Fabric Softener" to "Fabric Softeners"), 268 carried records became "Subscription", 35 "Men's Deodorant" and 43 "Great Value Pantry". | `9c14425`: a listing a page links twice read once, under the first name (`candidates/COLLECTOR_7a96218_TO_9c14425.diff`: 5 files, 159 lines added, 9 removed). |
| `9c14425` (third) | Its rule, checked against the full URLs of the 1,505 stored links, did not hold: its key took only the listing ID. "Subscription" and "Men's Deodorant" are filtered views, not second names, and two shelves share listing ID `0`. | `85c29e7`: the rules above (`candidates/COLLECTOR_9c14425_TO_85c29e7.diff`: 10 files, 853 lines added, 139 removed). |

## Files

| File | What it holds |
|---|---|
| `COLLECTOR_1.6.6_TO_1.6.8.diff`, `DIFFSTAT.txt` | the whole change from 1.6.6 (`39cc61f`) to 1.6.8 (`85c29e7`), collector folder only: 24 files, 2,267 lines added, 73 removed. `DIFFSTAT.txt` also gives the two steps |
| `COLLECTOR_1.6.6_TO_1.6.7.diff`, `COLLECTOR_1.6.7_TO_1.6.8.diff` | the two steps: 18 files (+814/−30), and 22 files (+1,489/−79) |
| `COLLECTOR_1.5.2_TO_1.6.8.diff`, `DIFFSTAT_1.5.2_TO_1.6.8.txt` | the pinned correction diff from release 1.5.2 (`627c804`), the one the client reviewed: 55 files (+5,221/−136), tests 30 of them (+3,390/−28) |
| `FAILBEFORE_1.6.8_ON_9c14425_WINDOWS.log` | the fourth commit's tests on the third commit, Windows (below) |
| `FAILBEFORE_1.6.8_ON_7a96218_WINDOWS.log` | the same tests on the second commit, Windows (below) |
| `FAILBEFORE_1.6.8_ON_1.6.7_WINDOWS.log` | the subcategory-page tests on the frozen 1.6.7 collector, Windows (below) |
| `DEVTREE_AFFECTED_WINDOWS.log` | the development tree with the fourth commit's change (the 10 files its header names), run from 20:50:10Z; the change was committed as `85c29e7` at 20:51:52Z. Unit 554 passed; 13 integration files (the 12 of the archive check below and `test_detail_path.py`), 177 of 177, each file in its own process |
| `candidates/9c14425/` | the third commit's development-tree run (unit 547; the four integration files that read category pages, 66 of 66) and its fail-before on the second commit |
| `candidates/7a96218/` | the second commit's development-tree integration run, stopped by hand (79 passed in its first 8 files), `test_editions.py` alone on it (4 passed), its full Linux suite on the owner's VM, and `clean-zip-windows-stopped/`: a Windows check of its ZIP that the session's low-memory protection stopped after 56 integration tests had passed and none had failed; it was not repeated |
| `candidates/745607e/FAILBEFORE_ON_1.6.7_WINDOWS.log` | the first commit's fail-before on 1.6.7 |
| `release-1.6.7-not-delivered/FULL_1.6.7_WINDOWS.log` | release 1.6.7's full suite on Windows (unit 542; integration 210 in 23 files, one file at a time; ruff, format, mypy and the lock check clean). It ran on 1.6.7, not 1.6.8 |
| `release-1.6.7-not-delivered/FULL_1.6.7_LINUX.log` | the same suite on Linux, the owner's Azure test VM, from a `git archive` of `7ee2fa1` (2026-11-05, 10:13:31Z to 10:34:51Z): unit 542, integration 210 in 23 files, each file in its own process, all passed; ruff, format, mypy and the lock check clean (`vm_full.sh`) |
| `release-1.6.7-not-delivered/FAILBEFORE_1.6.7_ON_1.6.6_LINUX.log` | 1.6.7's new tests on the frozen 1.6.6 collector (`39cc61f`), the owner's VM (10:35:39Z), the four test files of `7ee2fa1` copied in (the log checks each against the commit): 16 failed, 1 passed (`vm_full.sh`, which ran it after the suite) |
| `release-1.6.7-not-delivered/FAILBEFORE_1.6.7_TESTS_ON_1.6.6_LINUX.log` | an earlier run of that check (09:51:41Z), with the development tree's test files of the time: 13 failed, 26 passed (`vm_failbefore.sh`; `vm_fb_final.sh` is the final check's first script) |

The same fail-before checks ran on Linux on the owner's Azure test VM, from the commit's clean extraction, with every
1.6.8 test file of `85c29e7` copied in (`../../owner-azure-test/1.6.8/linux-suite/`). They fail with the same messages.

## The tests fail on the earlier code for the right reason

**The fourth commit's tests on the third commit**, Windows (`FAILBEFORE_1.6.8_ON_9c14425_WINDOWS.log`, 21:16:57Z to
21:18:53Z). The tree is `git archive 9c14425:headless/walmart-azure-headless`, with three test files of `85c29e7`
copied in (SHA-256 in the log). The import check shows the `9c14425` source is the one imported.

| Test | Failure on `9c14425` |
|---|---|
| `test_category_mapping.py::test_a_listing_linked_only_through_filtered_views_is_read_itself_in_full_once` | `'organic' not in ...`: the filtered view was requested, as the listing |
| `::test_a_link_to_the_listing_itself_after_a_filtered_view_names_it_and_it_is_read_once` | the same |
| `::test_a_subcategory_page_that_links_a_listing_filtered_has_it_read_itself_and_found_on_the_page` | the same, on a subcategory page |
| `::test_two_shelves_that_share_listing_id_0_are_two_listings` | `assert 1 == 2`: one shelf read |
| `::test_a_filtered_view_of_the_rows_own_category_is_not_a_listing_of_its_own` | `assert ['https://www...hod%3APickup'] == []`: the Clearance view was requested |
| `::test_a_name_a_page_gives_a_filtered_view_never_renames_the_listing_itself` | `assert ['Organic Milk'] == ['Milk Products']` |
| `::test_a_stored_read_of_a_filtered_view_never_completes_its_listing_in_the_coverage_report` | `assert ('DONE', None) == ('INCOMPLETE', 'listing')` |

The file's seven earlier tests pass on `9c14425` as on `85c29e7` (controls): 7 failed, 7 passed. The new unit file
`tests/unit/test_filtered_views_168.py` fails in all seven tests: six with `AttributeError` for the functions this
commit adds (`narrowing`, `filtered_listing`, `read_id`, `view_key`), and one because `9c14425` gives the two filtered
views of the cough listing one key. In `tests/unit/test_subcategory_pages_168.py`, the pin of the report's last
columns fails (`('end', 'stop...', 'found_on') == ('found_on', ...ered_view_of')`), 1 failed and 4 passed.

**The same tests on the second commit**, Windows (`FAILBEFORE_1.6.8_ON_7a96218_WINDOWS.log`, 21:18:54Z to 21:20:56Z):
`test_category_mapping.py` 9 failed, 5 passed (the seven above, and the third commit's two:
`test_a_listing_the_category_page_links_twice_is_read_once_under_its_first_name`, `assert (2 == 1)`, the Milk
listing requested twice; `test_a_stored_category_page_that_named_a_listing_twice_gives_it_its_first_name`,
`'Subscription' == 'Milk'`). `test_filtered_views_168.py` cannot import (`cannot import name 'listing_key'`); the
pin fails as above.

**The subcategory-page tests on 1.6.7**, Windows (`FAILBEFORE_1.6.8_ON_1.6.7_WINDOWS.log`, 17:31:13Z to 17:33:15Z).
The tree is `git archive 7ee2fa1:headless/walmart-azure-headless`, with six test files copied in from `7a96218`.
Five of them are unchanged at `85c29e7` (the same SHA-256 as in the log's header); the sixth,
`tests/unit/test_subcategory_pages_168.py`, changed only its column pin. Five 1.6.8 tests fail on their own
assertions:

| Test | Failure on 1.6.7 |
|---|---|
| `test_a_subcategory_with_a_category_page_of_its_own_is_read_through_the_listings_it_names` | `KeyError: 'wm:7401'`: the listing the page names was never read |
| `test_a_subcategory_page_the_site_does_not_serve_keeps_its_row_incomplete` | `assert (True is False)`: the row was called complete |
| `test_a_subcategory_page_an_earlier_release_skipped_keeps_its_row_open_in_the_coverage_report` | `assert (0 == 0 and True is False)` |
| `test_a_run_checks_every_page_against_the_store_and_charges_the_ledger` | the page was `SKIPPED`, not `EXPANDED` |
| `test_the_category_page_is_read_through_the_general_api_never_the_store_plugin` | the Dairy & Eggs page was never requested |

Three control tests pass on 1.6.7 as on 1.6.8, 7 test cases with their parameters. These are tests whose credit
budget 1.6.8 raised by one credit for the extra page. The unit file `tests/unit/test_subcategory_pages_168.py` cannot
import its functions on 1.6.7 (`ImportError: cannot import name 'NOT_A_CATEGORY'`). The Linux run of the same check
used all of `85c29e7`'s test files and gives the same results, plus `test_category_mapping.py` 9 failed, 5 passed.

## Checks of the delivered archive

The clean extraction of `WALMART_SOURCE_1.6.8.zip` was checked on the workstation, both editions, on 2026-11-05:
lock, install, ruff, format, mypy, unit 554 per edition, and the integration files the change from 1.6.6 touches
(Oxylabs 151 tests in 12 files, Scrape.do 73 in 4), with no failure, error or skip (37 steps, 0 not ok;
`../../verification/1.6.8/package/`). The whole suite (unit 554, integration 222 in 23 files) ran on Linux on the
owner's Azure test VM, from the commit's clean extraction (`../../owner-azure-test/1.6.8/linux-suite/`) and again
from each edition ZIP (`../../owner-azure-test/1.6.8/qualification/`).
