# Verification report: walmart-azure-headless 1.5.2

## Release 1.5.2

Release 1.5.2 corrects the known defects release 1.5.1 listed. Everything in this table is shown by offline tests
(authentic titles or synthetic pages, as each test says); a test does not establish live access or coverage. No live
request was made with this release: the campaign's allowance was spent. Its reprocessing of the saved pages is in the
delivery's reports and `PACKAGE_VERIFICATION.txt`, not here.

| Change | Until 1.5.1 | Where |
|---|---|---|
| Every evidence file names a value's real source: its capture, place in the response, hash, time, product and revision | `provenance.json` named the tile's title for a size recovered from a saved page, and no source for a UPC | `publishing/dispositions.py`, `publishing/supporting_log.py`; `tests/integration/test_detail_path.py`, `tests/unit/test_dispositions.py` |
| Only a page that was read can call a field absent | `missing_kind.upc` read `source_absent` on products whose page nobody requested | the same files |
| `blocked` and `request_failed` are separate classes | one class, `inaccessible_challenged` | the same files |
| A field source names the SHA-256 of its capture | `response_sha256` was always empty | `publishing/supporting_log.py`; `tests/integration/test_detail_path.py` |
| A carried row names the sources of its own earlier run | `provenance.json` showed none | the same file; the same test file |
| A set's two packages both stay ("12.5 oz shampoo + 10.6 oz conditioner") | the second was lost | `sites/walmart/records.py`, `sites/walmart/pack_size.py`; `tests/unit/test_pack_size.py` |
| A multipack is not repeated by a size that says only one ("(2 pack) ..., 1 Pack") | "2 pack, 1 Pack" | `sites/walmart/records.py`; `tests/unit/test_walmart.py` |
| Two strengths or a strength with its dose form are not a pack size | "500 mg + 200 mg Tablets, 24 Count" | `sites/walmart/records.py`; `tests/unit/test_pack_size.py` |
| Six brands confirmed at the USPTO are private label | `store_brand` "no" | `config/walmart_private_label_brands.yaml`, `docs/PRIVATE_LABEL.md`; `tests/unit/test_private_label.py` |
| Concurrency measured under load: one read of each page, ledger, pacing, retries, termination | small scopes only | `tests/integration/test_concurrency_load.py` |
| Daylight saving at both changes, a repeated and a missing hour, a backlog across a change | one firing rule only | `tests/unit/test_schedule_dst.py`, `tests/integration/test_operations.py` |
| An interrupted replay resumes or finalizes as a replay: stored pages only, no key, no request, no publication | `resume` built the live collector: it needed a provider key, and with one it sent live requests inside a REPLAY run | `operations.py`; `tests/integration/test_replay.py` |
| A row carried from a replay names the live run that fetched its page and the replay that read it again | it said the replay had observed it and, for a product page, `fetched_detail` with origin `fetched`, though a replay requests nothing. A live run that carried such a row said the same | `publishing/supporting_log.py`; `tests/integration/test_replay.py` |

Two hashes stand on a value read from a product page, because one response has two stored forms. `body_sha256` is the
SHA-256 of the raw response as the provider returned it (the run's `raw/` folder), and `response_sha256` is the SHA-256
of the page as stored (the run's `pages/dom` folder). A page imported from an earlier delivery has only its HTML, so
there both hold the SHA-256 of that HTML. With origin `read_again`, `page_fetch_id` is the replay's own read of the page
the source run stored, and the hashes are those of that same page.

Test expectations changed deliberately, because the behaviour they described changed:
`disp.INACCESSIBLE` became `disp.BLOCKED` or `disp.REQUEST_FAILED`, and `test_one_refused_product_page_is_not_a_reason_to_refuse_the_run`
now expects `blocked`; "(2 pack) Ol' Roy ..., 1 Pack" gives "2 pack"; "(2 pack) Pure Balance Pro+ ..." gives
`store_brand` "yes".

## Release 1.5.1

Release 1.5.1 corrects what the bounded live campaign of 2026-10-31 showed in release 1.5.0. The campaign's stages
ran on 1.5.0, and their records stay attributed to it; the live re-check of 1.5.1 and its reprocessing of the saved
pages are in the delivery's reports and `PACKAGE_VERIFICATION.txt`, not here. Everything in this table is shown by
offline tests (authentic titles or synthetic pages, as each test says); a test does not establish live access or
coverage.

| Change | Until 1.5.0 | Where |
|---|---|---|
| A multipack outside the size segments stays beside the size | "(2 pack) ... Dry Dog Food, 16 lbs" gave "16 lbs" | `sites/walmart/records.py`; `tests/unit/test_walmart.py` |
| A page's larger size is explained by the title's pack, and nothing else | it was flagged as a conflict | `sites/walmart/pack_size.py`; `tests/unit/test_pack_size.py` |
| Inches, a load rating and a strength beside a package size are not the size | "9 Inch", "50 Pounds", "1200 mg, 14 Count" | `sites/walmart/records.py`; `tests/unit/test_walmart.py` |
| A volume before a count of loads stays; "Counts" is a count unit | "105 Loads"; "600 mg" for "300 Counts" | `sites/walmart/records.py`; `tests/unit/test_walmart.py` |
| A Walmart brand after a bracketed multipack, and two listed wordings | `store_brand` "no" | `assembly/private_label.py`, `config/walmart_private_label_brands.yaml`; `tests/unit/test_private_label.py` |
| A page budget does not stop what earlier reads established | products behind the budget's last page stayed blank | `collection/walmart.py`; `tests/integration/test_detail_path.py` |

Test expectations changed deliberately, because the behaviour they described changed: "StarKist ... (6 pack) ...
2.6 oz Pouch" now gives "6 pack, 2.6 oz Pouch"; `test_a_size_segment_ends_where_the_products_description_begins`
allows a segment part that the title brackets, since a bracketed multipack now stays beside the size, and keeps its
other assertions; `test_the_captured_pages_give_the_records_w1_exported` allows exactly one more difference from W1,
the authentic "(2 pack) Baby Dove ...,13 fl oz" (item 18030205038), now "2 pack, 13 fl oz".

One test was out of date in release 1.5.0 and is corrected here; the frozen 1.5.0 fails it. 1.5.0's integration tests
were run file by file before its freeze, with this file left for the final verification, so the whole suite of 1.5.1
brought it out: `test_a_replay_leaves_the_stores_follow_up_queue_alone` expected no queue rows of kind "detail", which
1.5.0 added,
and its synthetic site refuses the product pages 1.5.0 reads, which rejects the run (G2 DETAIL_PAUSED). The test now
expects the three kinds and runs with `--pilot-detail-pages 1`; what it checks is unchanged: a replay exits 0,
requests nothing and leaves the queue as it was. The product's behaviour did not change for this test.

## Release 1.5.0

Release 1.5.0 answers the client's review of release 1.4.1. The live checks of 1.5.0 and its reprocessing of the
saved pages are in the delivery's reports and `PACKAGE_VERIFICATION.txt`, not here. Everything in this table is
shown by offline tests (synthetic pages or saved captures, as each test's docstring says); a test does not establish
live access or coverage.

| Change | Until 1.4.1 | Where |
|---|---|---|
| "Buy 1 Save $1" is not a volume deal | any "Buy N" wording counted | `assembly/offers.py`; `tests/unit/test_offers.py` |
| Product detail path | a demonstration setting read no page; empty fields had one explanation | `collection/walmart.py`, `publishing/dispositions.py`; `tests/integration/test_detail_path.py`, `tests/unit/test_dispositions.py` |
| Pack size apart from serving size, unit price and sibling; conflicts kept | statements were not told apart | `sites/walmart/pack_size.py`; `tests/unit/test_pack_size.py` |
| Sizes in more title forms ("40 Fluid Ounces", "30 Tabs", "1 Bunch"), multipacks | left empty | `sites/walmart/records.py`; `tests/unit/test_walmart.py` |
| A local price needs Walmart named as the seller | a line for the store with no seller counted | `sites/walmart/records.py`; `tests/unit/test_product_page_offers.py` |
| Occurrences of the schedule keep their identity | a late firing, a hold or a running run dropped them | `collection/occurrences.py`, `operations.py`; `tests/integration/test_operations.py` |
| A scheduled run refuses a narrowed scope | not checked | `operations.py`; `tests/integration/test_operations.py` |
| Follow-ups share out among workers | one task per kind whatever the workers | `worker/pipeline.py`, `collection/walmart.py`; `tests/integration/test_followups.py` |
| A page budget holds with two workers at once | one page each could pass it | `collection/walmart.py`; `tests/integration/test_detail_path.py` |
| A stopped product-page path fails G2; mixed lineage refused on every target | such a run could publish | `validation/gates.py`, `publishing/publish.py`; `tests/integration/test_publication_safety.py` |
| Package path failures | three capture READMEs named workstation paths | `tests/captures/*/README.md` |

Test expectations changed deliberately, because the behaviour they described changed: "(6 pack) Enfamil ... 12.5 oz
Can" now gives "6 pack, 12.5 oz"; a firing after the tolerance starts the occurrence late instead of dropping it;
after an overlap the waiting occurrence runs at the next firing; repeated refusals of product pages reject the run
(`test_repeated_refusals_pause_detail_reading_and_say_so`); the W1 capture comparison switches the product-page path
off, since W1 read none and the captures hold none; the migration head is 0006.

## Release 1.4.1

Release 1.4.1 corrects three defects that release 1.4.0's live runs showed: one in a run, one in the
exports of two runs, and one in the result pages the Scrape.do edition asked Walmart for (the brief of
2026-10-28, section 8: a defect found live gets a new revision). Nothing else changes: records, exports (but
for the coverage report's new column) and the other checks are those of release 1.4.0 (`8c3fbb1`). The live
checks of 1.4.1 are in the delivery's reports and `PACKAGE_VERIFICATION.txt`, not here.

## 1. What changed from 1.4.0, and what showed each defect

| Change | Before the change | Where |
|---|---|---|
| **A page the provider never brought is not an integrity failure.** G13 verifies the hash of every page the run stored. A request that brought no page (the provider failed it after its retries, so nothing is stored) has nothing to verify: it fails G13 only when an observation or a record of the run names it as a source. The product keeps its UPC outcome `request_failed`, as the README already said. | Live on the Azure test VM: the Oxylabs edition's complete run `01M60JAPKBR4FNK22QMYTHNBSX` (disposable publication target, 2026-10-28T06:14Z) read every planned page and passed every other blocking check. One product page (item 929297252) failed at Oxylabs on all 3 attempts (HTTP 500, `REQUEST_FAILED_AFTER_TOO_MANY_RETRIES`, not charged). G13 failed ("artifact_hashes_verified not confirmed") and the run was rejected instead of published. The new test, run against 1.4.0's `worker/pipeline.py`, failed the same way (G13, `rejected`). Both editions share this code. | `worker/pipeline.py`; `tests/integration/test_scrapedo_walmart.py` |
| **A variant seen only as a sponsored tile is read once, and its outcome says by which follow-up.** No record is kept from a sponsored tile: the sponsored follow-up reads the product's own page, and the variant outcome says so (`duplicate`, "this run saw it only as a sponsored tile: the sponsored follow-up reads its own page"). When the sponsored follow-up is off, the variant follow-up reads it. | Found offline in the exports of the Scrape.do edition's live runs of 2026-10-28 (`01M60CG5Y3KY64JP0ZV5F6MBDP`, 4 rows; `01M60ESB2201KQ56K9GRTMY0V7`, 2 rows): a variant sibling whose only tiles were sponsored was reported "this run saw it as its own result tile: recorded from that placement", and no record of it existed. With the sponsored follow-up off, no follow-up read it. The new test (both settings), run against 1.4.0's `collection/walmart.py`, failed: the wrong reason with the sponsored follow-up on, the item never read with it off. | `collection/walmart.py`; `tests/integration/test_followups.py` |
| **The Scrape.do edition asks Walmart for its Pickup grid, and every result page records its grid's filter.** The store endpoint sets the store only (`storeid`, `zipcode`). Each result page is now requested with Walmart's own facet for the store's fulfillment, `facet=fulfillment_method:Pickup` (joined to a URL's own facets with `\|\|`, as Walmart's filter links join them); product pages, robots.txt, the store page and category pages are not. The page is kept under the collector's own URL, so a replay finds it, and the spending ledger's `target_url` names the URL the provider was asked for. Every result page records the filter its grid states (`meta.fulfillmentIntent`: `Pickup`, or `none`), and `coverage-report` gives it per page (`grid_fulfillment_filter`). The Oxylabs edition is unchanged: the Web API applies the same filter from its `fulfillment_type`. | Found offline in the stored pages of the 2026-10-28 runs (brief section 5, the audit of the listings classified complete): the same listing half an hour apart was Walmart's Pickup grid through the Oxylabs Web API (`meta.fulfillmentIntent` "Pickup"; the page's own search request `facet=fulfillment_method:Pickup`, `stores=3891`) and the store's unfiltered grid through Scrape.do (`fulfillmentIntent` null, an empty `facet`, `stores=3891`): Strawberries 2 results against 5 (3 of them out of stock), Laundry 624 against 18,682. The Scrape.do runs' result pages carried out-of-stock, shipping-only and marketplace items, which the record rules excluded (phase B2, the same scope and page limit: 561 valid products through Scrape.do, 675 through the Oxylabs Web API). The new tests, run against 1.4.0's `scrapedo_session.py`, `walmart.py`, `page_data.py` and `reconcile.py`, failed: no facet on the result-page requests, no grid filter recorded. Two authentic pages of those runs are kept as test captures (`tests/captures/listing_pages_20261028`). Whether Walmart serves its Pickup grid to the store endpoint with the facet is a live check of the delivery. | `acquisition/scrapedo_session.py`, `collection/walmart.py`, `sites/walmart/page_data.py`, `collection/reconcile.py`; `tests/unit/test_grid_filter.py`, `tests/integration/test_scrapedo_walmart.py`, `test_workers_and_oxylabs.py`, `test_replay.py`; the mocks (`tests/mock_scrapedo.py`, `tests/mock_oxylabs.py`, `tests/synthetic_walmart.py`) |

## 2. Offline checks of the release commit

On the preparation workstation (Windows 11, CPython 3.12.10, the locked environment):

* `ruff check src tests deploy`: pass. `ruff format --check src tests deploy`: 147 files already formatted.
* `mypy` 2.4.0 (strict; the package's 83 source files): no issues.
* `uv lock --check`: the lock matches `pyproject.toml`.
* `pytest`, the whole suite: 488 passed in 12 min 10 s (474 in release 1.4.0; 12 new tests, and the two new
  captures in the existing capture hygiene test).

## 3. Live checks

None before the commit. See the delivery.

## 4. Container: NOT TESTED

There is no Docker on the preparation workstation or on the Azure test VM.

## 5. Not verified at the commit

The items of release 1.4.0's list below are unchanged.

---

# Verification report: walmart-azure-headless 1.4.0

Release 1.4.0 corrects the defects that the brief of 2026-10-28 found in release 1.3.1, and ships the
collector as two editions built from one revision, one for each provider ([EDITIONS.md](EDITIONS.md)). This
section records the offline checks of the release commit. The live checks (canaries, a demonstration run of
each edition on the same scope, interruption and recovery, on the Azure test VM) are made after the commit,
with the editions built from it. Their results are in the delivery's reports and `PACKAGE_VERIFICATION.txt`,
not here, so the revision that was verified is exactly the one delivered.

## 1. What changed from 1.3.1, and what showed each defect before the change

Each "before" was reproduced by running the release's new test against release 1.3.1 (`7847f49`, in a
separate worktree, its own package imported). Where 1.3.1 already behaved correctly, the test was run against
a deliberately broken variant instead, to show that it detects the defect. The logs are in the delivery's
evidence package.

| Change | Before the change | Where |
|---|---|---|
| **Partition depth.** A listing larger than the site's result window is read through the child categories its facets name, as deep as they go: `coverage.partition_max_depth` is empty by default. A number is an explicit cap for a bounded run; a listing it leaves unpartitioned says so and stays incomplete. | 1.3.1 capped the depth at 2 by default: an overflowing third-level child category stayed `INCOMPLETE` (2 tests failed). | `core/settings.py`, `collection/walmart.py`, `config/settings.yaml`; `tests/integration/test_coverage_and_assortment.py` |
| **Approximate and estimated weight.** Only approximate or estimated wording excludes a product, and then the whole product (`APPROX_WEIGHT`): an approximate size, or a price stated as an estimate ("each (est.)"). Its field log names the wording, the field, its path in Walmart's page data and the whole value. A product sold or charged by weight, or with a "/lb" price per measure, is kept with its displayed prices and flagged `RELATIVE_PRICE` and `SOLD_BY_WEIGHT`. When its title states no size, its weight is the one stated after its price ("$0.25 / 0.14lb"). Within a run, a product one of whose tiles showed the wording is excluded whichever tile records it. An earlier observation is carried forward only when it showed no such wording, so the 1.3.0 observations of weight-priced products are not carried. | 1.3.1 excluded every weight-priced product as `RELATIVE_PRICE`, with or without estimate wording (6 unit and 3 integration tests failed). With the earlier tiles' wording not passed on, the product recorded from a later tile was kept (1 test failed). | `sites/walmart/records.py`, `assembly/record_builder.py`, `assembly/exclusions.py`, `collection/retention.py`, `collection/walmart.py`; `tests/unit/test_weight_priced.py`, `tests/integration/test_weight_wording.py`, the Fresh Vegetables capture (`tests/captures/listing_pages_20261026/`) |
| **Retained products never mask a run's yield.** G4 flags a category, or the whole run, whose published products are more than 30% retained from earlier runs, and fails it above 50% (`RETAINED_MASKS_YIELD`; `yield.warn_retained_share`, `yield.fail_retained_share`). A bounded run counts the retained products of the listings it read. This covers what the drop against the last good run cannot: a store's first complete run, and bounded runs, which are never compared. | A bounded run that observed 1 of a listing's 10 products and carried the other 9 was validated; a complete one was rejected only by the drop against the last good run (3 of 4 tests failed). | `validation/gates.py`, `collection/base.py`, `core/settings.py`, `core/findings.py`; `tests/unit/test_gates.py`, `tests/integration/test_retained_masking.py` |
| **The last good run.** G4 measures a run's yield against the store's last complete run, as the README says: the last run that read every page it planned and passed its checks, never a bounded run or one stopped early; for a network run, a network run only, so a test's synthetic pages never set what a real run must reach. The run records which run that was (`counts.yield_baseline`). | 1.3.1 took the last validated run of any kind: after a bounded run that read 2 of a category's products, a complete run that observed 1 product where the last complete run had verified 10 was validated with a warning ("drop 50% vs last good" instead of a 90% drop, which fails; 1 test failed). | `collection/base.py`; `tests/integration/test_yield_baseline.py` |
| **Scheduled execution of an Oxylabs store.** A scheduled run, and the continuation of one, checked the Scrape.do key whatever the store's provider; each now checks its own provider's key. | A scheduled run of an Oxylabs store without a Scrape.do key was refused: "no Scrape.do key" (1 test failed). | `operations.py`; `tests/integration/test_editions.py` |
| **Editions.** The configuration names its edition and the providers it runs (`edition:`). A run, a resumed run or `provider-balance` naming another provider is refused before any request, and a store naming one is a configuration error. `deploy/build_edition.py` builds an edition's reproducible source ZIP from a commit: it changes the edition line, the stores' provider lines and `.env.example`, and adds `BUILD_INFO.json` and `EDITION.json`, which records each change with hashes. `install.sh` installs an edition beside the core release, with its own database, data folder and environment; `walmart-cmd` and `walmart-run` run a command with an edition's release (`WC_RELEASE`) or another configuration file (`WC_CONFIG`). | New in 1.4.0. | `config_file.py`, `editions.py`, `operations.py`, `collection/control.py`, `deploy/build_edition.py`, `deploy/vm/install.sh`, `deploy/vm/walmart-cmd`, `deploy/vm/walmart-run`, `editions/`; `tests/unit/test_editions.py`, `tests/integration/test_editions.py` |
| **The test suite in an edition's source.** In an edition's extracted source, the tests that read the configuration use the core configuration the edition was made from (`tests/conftest.py` undoes the lines its `EDITION.json` lists), so the whole suite runs in each edition as in the core. | In the extracted editions of the first 1.4.0 candidate (`bdb9e9c`), 1 test (Scrape.do) and 2 tests (Oxylabs) failed: they read the edition's configuration, whose store names one provider. | `tests/conftest.py` |
| **Stop signals in the keep-alive helpers.** Regression tests for both providers' sessions: a stop during a request cancels it, a stop arriving while the helper is being stopped is not swallowed, and a failed renewal does not fail the request. | 1.3.1 passes all 8. A variant whose helper suppresses the cancellation fails 2 of them. | `tests/unit/test_keepalive_cancellation.py` |
| **mypy.** The supported range in `pyproject.toml` starts at the locked and tested version (`mypy>=2.4.0`, was `>=1.13`). Strict checking is unchanged, and no suppression was added. | | `pyproject.toml`, `uv.lock` |
| **UPC outcomes.** Documented: what each outcome means and which cause of an empty UPC it is. | | `docs/OPERATIONS.md` (UPC outcomes) |

## 2. Offline checks of the release commit

On the preparation workstation (Windows 11, CPython 3.12.10, the locked environment):

* `ruff check src tests deploy`: pass. `ruff format --check src tests deploy`: 145 files formatted.
* `mypy` (strict; the package's 83 source files): no issues. The tests are not type-checked, as in 1.3.1.
* `uv lock --check`: the lock matches `pyproject.toml`.
* `pytest`, the whole suite: 474 passed in 11 min 22 s (the integration tests on a temporary PostgreSQL server
  that they start).

The clean extraction of each edition's source ZIP (install, imports, CLI, migrations, lint, mypy, all tests)
is recorded in the delivery's `PACKAGE_VERIFICATION.txt`.

## 3. Live checks

None before the commit. See the delivery.

## 4. Container: NOT TESTED

There is no Docker on the preparation workstation or on the Azure test VM.

## 5. Not verified at the commit

- **Oxylabs Classic Web Scraper API: NOT TESTED.** The required credentials (an API username and password)
  are unavailable; the Oxylabs credential at hand is a Web API key.
- **A full-scope run** (all CSV rows, every subcategory, every page). It was not executed.
- **Unattended scheduled operation.** Schedules stay off; the scheduling logic is tested offline only.
- **A displayed volume deal or digital coupon.** No stored page shows one; the offer rules are tested on
  synthetic pages only.

---

# Verification report: walmart-azure-headless 1.3.1

Release 1.3.1 corrects the defects that the review of 2026-10-27 found in release 1.3.0, and the defects
found while correcting them. **It has made no provider request**: it was not deployed to the Azure test VM
(which still holds release 1.3.0, `c1c47b4`), and every check of its handling of Walmart pages reads pages
that earlier live runs stored. The live evidence of the delivery remains release 1.3.0's, from 2026-10-26,
and is labelled as such.

The commit of the release and the complete verification of the delivered revision, from a clean extraction
of the source package, are in the delivery's `PACKAGE_VERIFICATION.txt`. They are not written here, so the
revision that was verified is exactly the one delivered.

## 1. What changed from 1.3.0

| Change | Where |
|---|---|
| **Challenge detection.** A challenge is recognised from the response's structure: its HTTP status, the bot manager's own elements (CAPTCHA container, script or frame, an edge error page) or a response without the site's page data. Denial wording counts only beside one of those, and is never read inside the page's data scripts. On 2026-10-26 a brand's reply to a customer review ("provide the reference #...") on item 15353921746's product page was taken for an Akamai refusal, and that UPC was not read. | `acquisition/challenge.py`; `tests/unit/test_challenge_detection.py` (that page, authentic challenge pages, ambiguous responses) |
| **Lineage.** Every run records where its pages came from: `network`, or `substituted` when a test or fault-injection harness replaced a provider transport's HTTP client. A run takes earlier observations only from runs of its own lineage, and a carried record whose source run has another lineage fails G13. A run that is not `network` is published only to a configured test target. A run made before 1.3.1 serves later runs only after `attest-lineage`. On the disposable test target of 2026-10-26, a synthetic record of an injected run was carried into a publication; a regression test reproduces that case. The main database never ran an injected run. | `acquisition/lineage.py`, `collection/retention.py`, `validation/gates.py`, `publishing/publish.py`; `tests/integration/test_lineage_retention.py`, `test_publish.py` |
| **Retention checks.** A carried record is checked again when it is carried. Records from a run whose checks invalidate its observations, or read from a challenged page, never serve. An earlier observation whose final cost depends on the weight is never carried as a fixed price. A product the store was verified to carry and that is unavailable now stays retained, with empty prices. | `collection/retention.py`; `tests/unit/test_retention_rules.py`, `tests/integration/test_lineage_retention.py`, `test_coverage_and_assortment.py` |
| **Abandoned segments.** A collection segment left open by a killed process is recorded as abandoned (`SEGMENT_ABANDONED`). It keeps its last heartbeat, its last durable observation and the bounds of its end. Its recorded values and the run's earlier events are kept, and no end time is invented. Run statistics come from durable observations: the provider ledger, observations and stored pages. | `collection/segments.py`, `operations.py`; `tests/integration/test_abandoned_segments.py` |
| **Price provenance.** Each price records the exact path it was read from (a tile's `priceInfo.priceDetails` price line, or the product page's own field) and any change made to it. Release 1.3.0 named `priceInfo.currentPrice` / `wasPrice` for values read from price lines. The 1.3.0 evidence is not rewritten; a correction overlay accompanies it. | `sites/walmart/page_data.py`, `sites/walmart/records.py`; `tests/unit/test_price_provenance.py` |
| **Coverage rule.** A listing is complete only at the last page the site serves, with a stable reported total balanced exactly by its organic identities, or by its organic and sponsored-only identities. A result window the site does not serve beyond stays "accessible pages exhausted; coverage incomplete", and more identities than reported is an overcount. Only the result grid of a page is read: release 1.3.0 also counted a page's other product modules. G3 uses the difference left after the exact balance. | `collection/walmart.py`, `collection/reconcile.py`, `validation/gates.py`; `tests/unit/test_listing_reconciliation.py` |
| **Follow-up queue.** Sponsored-only products and variant siblings are kept per store across runs (migration 0004, `follow-ups`). A candidate that a page budget, a pause or a failed page left unread stays pending. Options named by a repeated tile of a product, or by a sponsored tile, are candidates too (migration 0005, `tile_options`). A follow-up or detail page budget, or a follow-up or detail reading switched off, makes a run a pilot. | `collection/follow_queue.py`, `collection/walmart.py`, `collection/config.py`; `tests/integration/test_follow_queue.py`, `test_followups.py` |
| **Marketplace sellers on product pages.** A product page names its seller in `sellerDisplayName` with `sellerType`, where a result tile uses `sellerName`. Release 1.3.0 read `sellerName` only, so no product page was ever recognised as a marketplace offer. | `sites/walmart/page_data.py`; `tests/unit/test_product_page_offers.py` |
| **Weight-priced items.** An item sold by the piece and charged by its weight (sales unit `EACH_WEIGHT` or `WEIGHT`, a `SOLD_BY_WEIGHT` price line, `finalCostByWeight`, Walmart's condition "each (est.)") is a relative price and is excluded. Release 1.3.0 exported 31 such estimates as fixed prices. | `sites/walmart/page_data.py`, `sites/walmart/records.py`; `tests/unit/test_weight_priced.py` |
| **Size.** A size taken from the title ends at the first word that names neither the quantity nor its package. Release 1.3.0 exported 10 of its 633 rows with descriptive text in the weight ("3 lb Bag - Naturally Ripened Citrus Fruit"). | `sites/walmart/records.py`; `tests/unit/test_walmart.py` |
| **Stored-page sanitizer.** Walmart's camel-case session and trace identifiers (`isomorphicSessionId`, `adSessionId`, `traceId`, ...) are redacted. The test captures were sanitized again, with their earlier hashes kept in their manifests. | `sites/walmart/sanitize.py`; `tests/unit/test_capture_hygiene.py` |
| **Schedule.** The shipped schedule collects the whole day, has no run time limit, and lets an unfinished scheduled run go on when the next occurrence starts (`on_overlap: continue`, `OCCURRENCE_DEFERRED`). Release 1.3.0's 06:00-18:00 window, 48-hour limit and superseding could never let a full-scope run finish. Schedules stay disabled. | `collection/config.py`, `config/collector.yaml`, `operations.py`; OPERATIONS.md |
| **Replay of an Oxylabs run.** The replay recorded Scrape.do's store parameters for every page, so the replay of an Oxylabs run stopped at its first listing page's store check (`STORE_NOT_VERIFIED`). Each replayed page now records the parameters its source request carried, by the source provider's own request rule. Found by the offline reprocessing of the 1.3.0 main run; release 1.3.0 had the same defect. | `collection/replay.py`, `acquisition/scrapedo_session.py` (`store_scoped`); `tests/integration/test_workers_and_oxylabs.py` |
| **Labels of a replay's exports.** A replay's record map and supporting log called each row a fresh observation of the replay run (`observation_kind: fresh`, `observed_by_run` the replay) and its manifest counted `fresh_record_count`, although a replay requests nothing. Its rows are now `replayed`, `observed_by_run` is the source run and `read_again_by_run` the replay; the manifest counts `replayed_record_count`. A live run's labels are unchanged. Found by the offline reprocessing of the 1.3.0 main run. | `publishing/supporting_log.py`, `publishing/exports.py`; `tests/integration/test_replay.py` |
| **The offers and memberships of an export.** Two things were found in the reprocessing of the 1.3.0 main run. First, after a later tile decided a record again (the latest-state fix above), the earlier tile's offers stayed in `offers.json` beside the later tile's: an offer the record no longer had, or the same offer twice, with nothing to tell the two tiles apart. `offers.json` now holds the offers of the page each record is kept from, each with its `page_fetch_id`; the earlier tile's offers stay in the database with its state. Second, two reprocessings of the same stored pages exported the same 845 memberships in a different order. Memberships were ordered by category and listing only, the database's sort is not stable, and offers had no order at all. Both are now written in a fixed order: memberships in page order, offers by product, page and content. A third reprocessing found the same in the reports: the coverage report's counts by reason (`other_exclusions`, `follow_up_outcomes`) and the validation report's `excluded_by_reason` followed the database's order of the records, so one listing's exclusions came out in another order. They are now sorted by reason. | `worker/pipeline.py`, `collection/reconcile.py`; `tests/integration/test_coverage_and_assortment.py` (3 tests) and `tests/integration/test_followups.py` (one assertion added), which failed on the unfixed code |
| **A replay's UPC outcomes.** After that fix, a replay's supporting log still counted its UPC outcomes as `upc_outcomes_of_fresh_exported`. It also marked each product page it read again from storage `fresh`, as if the replay had requested it. The count is now `upc_outcomes_of_replayed_exported`. Each such page names the run that requested it (`observed_by_run`, at its own `requested_at`) and the replay (`read_again_by_run`). A live run's log is unchanged, and the database keeps its own flag, which a later run uses to count a replay's UPCs through the replay. Found in the fourth offline reprocessing of the 1.3.0 main run. | `publishing/supporting_log.py`; `tests/integration/test_replay.py` (the test failed on the unfixed code) |
| **The log's encoding.** The JSON lines on standard output were written in the stream's own encoding. On Windows, with the output redirected to a file, that is the ANSI code page: the reprocessing logs held "Food › Fresh Fruits" as byte 0x9B (26 lines of each replay log are not UTF-8). A line holding a character outside that code page raised `UnicodeEncodeError`, which the writer took for a closed stream, so the line was dropped without a trace. The lines are now UTF-8 on every OS. On the Linux VM, standard output was already UTF-8. | `core/logs.py`; `tests/unit/test_logs.py` (failed on the unfixed code) |
| **A replay's log.** The seventh reprocessing's log still described the stored pages as live requests: "Oxylabs Web API applies it on every page" (`STORE_SELECTED`) and "requests of the closed Oxylabs Web API session" (`PROVIDER_TRAFFIC`). Its data said `provider: replay`, and no request was made. Its 612 product-page events (`PRODUCT_DETAIL_READ`) said `fresh: true`. A replay's messages, and the store method it records, now name the source run whose stored pages are read again and say that no request is made. Its product-page events name `observed_by_run` and `read_again_by_run`, as its supporting log does. A live run's log is unchanged. | `collection/walmart.py`, `collection/replay.py`; `tests/integration/test_workers_and_oxylabs.py` and `tests/integration/test_replay.py` (assertions added to two tests, each of which failed on the unfixed code) |
| **Independent source check of a record exported without a local price.** `validate-export` chose the best page for a record before it set aside the prices of a page without the store's Pickup line, so when a product's earlier page with the line scored as well as the page that shows it without the line, it chose the earlier page and reported a mismatch. Found with Fresh Strawberries 1175460573 (in stock with store 3891's Pickup line at 21:52Z, out of stock without it at 23:01Z on 2026-10-26) in the offline reprocessing of the repeat run. Each page is now judged with its own Pickup line before the best one is chosen. | `checks/source_check.py`; `tests/unit/test_walmart_offers_partition.py` |
| **A product's latest state in the run.** Release 1.3.0 recorded a product from its first result tile of the run and counted every later tile as a duplicate. A later tile showing another local state was dropped, so the run exported a Pickup price its own later page no longer showed. Found with Fresh Strawberries 8.8 oz (1175460573) in the main run of 2026-10-26: in stock with store 3891's Pickup line at 21:52Z on Fresh Fruits, out of stock without the line at 22:29Z on Strawberries. 1.3.1 changes this: a later tile with another local state decides the record again. The run's earlier tiles verify the product at the store and stay in the log (`earlier_in_run`, with page and time), and a later run is verified by them. A tile observed earlier but processed later (overlapping requests) is logged and verifies an unresolved record as if read in order. | `collection/walmart.py` (`repeated_tile`), `collection/retention.py`, `publishing/supporting_log.py`; `tests/integration/test_coverage_and_assortment.py` (3 tests, which failed on the unfixed code) |
| **Strict typing.** The 13 strict mypy errors in `collection/reconcile.py` and `collection/walmart.py` are corrected with checked readers of the database's JSON values (`core/jsonvalues.py`): a value of an unexpected shape stops the work that reads it. No error was suppressed. The project's mypy run checks `src` (`[tool.mypy] packages`), not the tests. Three `type: ignore` comments added to test files during the 1.3.1 work are replaced by types (`tests/unit/test_challenge_detection.py`, `tests/unit/test_retention_rules.py`; a strict mypy run on both files passes). The `type: ignore` comments that predate release 1.3.1 are unchanged: 17 in `src` (none in `reconcile.py` or `walmart.py`) and 22 in the tests. | `core/jsonvalues.py` |
| **Test database lifecycle.** In the 1.3.0 pre-test, one integration file failed (1 failure, 13 errors) because the throwaway PostgreSQL server stopped during it; each later test waited for the 130-second connection timeout. The integration fixture now connects with a 15-second timeout. | `tests/integration/conftest.py` |

## 2. Offline checks during the repair

Each change was checked with targeted runs of the affected unit and integration files, `ruff`, and strict
`mypy`. The evidence package's test register lists every run with its command, duration, exit code and log,
including the failed runs and the defects they revealed.

## 3. Offline reprocessing of the 1.3.0 main run

The pages that release 1.3.0 stored for its main run `01M5X364...` were read again by release 1.3.1
(`replay`). Nothing was requested. The result is a separate corrected export with a row and field change
report, labelled **offline reprocessing**: it is not a new live run, and release 1.3.1 did not produce the
1.3.0 observations. See the delivery's technical report and `CORRECTIONS.csv`.

## 4. Live checks: none with 1.3.1

Release 1.3.1 sent no provider request. Its behaviour on live pages has not been observed.

## 5. Container: NOT TESTED

There is no Docker on the preparation workstation.

## 6. Not verified

- **Oxylabs Classic Web Scraper API: NOT TESTED.** The required credentials (an API username and password)
  are unavailable.
- **Release 1.3.1 on Azure.** It was not deployed.
- **A full-scope run** (all CSV rows, every subcategory, every page). It was not executed.
- **Unattended scheduled operation.** Schedules stay off; the scheduling logic is tested offline only.
- **A displayed volume deal or digital coupon.** No stored page shows one; the offer rules are tested on
  synthetic pages only.

---

# Verification report: walmart-azure-headless 1.3.0

Release 1.3.0 is three commits, `e9da6ac`, `36682b8` and `c1c47b4`. The collector itself is the same in all
three: `src/`, `tests/`, `config/`, `azure/`, `pyproject.toml`, `uv.lock` and the `Dockerfile` have the same
git trees. The two later commits change only `deploy/vm/` and `docs/AZURE_VM.md`.

**The release installed and run on the Azure test VM on 2026-10-26 is `c1c47b4`**
(`c1c47b4d8b6fb9fb51a589acb944290843dd036e`). It was frozen before the Oxylabs probe and the demonstration,
and no code changed during the test. The documentation revision that follows it changes only
`docs/AZURE_VM.md`, `docs/CLI.md` and this file, to state what the Azure test measured.

## 1. What changed from 1.2.1

| Change | Where |
|---|---|
| **Follow-ups.** Two kinds of product are now read on their own product page, in the store's context: products seen only in sponsored placements, and the variant siblings a tile names. One is included only when its page identifies the item, shows it for the store and files it under the listing's category. Every candidate's outcome is recorded with its reason: included, excluded, inaccessible, duplicate or not attempted. | `collection/walmart.py` (`follow_up`); CLI.md, Follow-ups |
| **Coverage.** There is no tolerance threshold any more (`node_min_coverage_ratio` is fixed at 1.0). A listing whose pages run out early is "accessible pages exhausted; coverage incomplete". `coverage-report` reconciles every scope unit. | `collection/walmart.py`, `collection/reconcile.py`, `operations.py` (`coverage_report`) |
| **Oxylabs Web API as a provider.** It uses a Bearer key. Store-scoped pages go through `/v1/scrape/walmart` with `store_id` and `fulfillment_type`; other pages go through `/v1/scrape`. Only raw HTML is used. A ceiling (submissions, US dollars, minutes) and the task's money budget are reserved in the database before every request. | `acquisition/oxylabs.py`, `acquisition/budget.py` |
| **Parallel workers** within one run (`--workers`, default 1). Tasks are leased from the database queue, and every write is fenced by the lease. | `worker/runner.py`, `db/queue.py` |
| **`deploy/vm/`.** Installation with PostgreSQL 16 on the local socket, a backup before migration and the switch after it. Also sandboxed command wrappers, resource sampling, SSH restriction and rollback. No timer is installed. | AZURE_VM.md |

## 2. Offline checks

The release was tested on the preparation workstation with:
- the unit and integration suites;
- `ruff` and strict `mypy`;
- the command line;
- the Bicep template.

The integration suites run in two forms:
- **offline replay**: authentic Walmart pages saved by earlier live runs (`tests/captures/`), read again with no request;
- **synthetic**: invented pages, and in-memory mock providers for Scrape.do and Oxylabs.

The delivery's package verification repeats every check from a clean extraction and states the counts.

## 3. Live checks on Azure (2026-10-26, release `c1c47b4`, Oxylabs Web API)

The delivery's `AZURE_EXECUTION_REPORT.md` has every command, exit code, time and measurement, with the
evidence package's paths.

- **Oxylabs Web API probe** (run `01M5X27Z…`):
  - 6 submissions, all HTTP 200, no challenge;
  - store 3891 and its Pickup context were attested on Walmart's own pages;
  - the canary checked 38 records, with 0 mismatches.
- **Main demonstration run** (`01M5X364…`):
  - 633 distinct, valid, freshly observed products in 6 of the 11 CSV categories, plus 93 excluded with their reasons;
  - 5 execution segments, 736 submissions;
  - it is a bounded pilot: 2 result pages per listing, and only some subcategories;
  - it was never published.
- **Workers:**
  - one worker: 9.62 requests a minute (segment 1, 15 minutes);
  - two workers: 22.7 (segment 2, 15 minutes), then 18.4 and 19.9 in the interrupted segments 3 and 4;
  - two workers were 1.92 to 2.36 times faster against one.
- **Recovery:**
  - a termination signal (exit 75) and a process kill, each followed by a resume;
  - after recovery: 726 records with 726 distinct keys, no duplicate membership and no duplicate observation;
  - the 4 product pages in flight at the interruptions were submitted again.
- **Conflicts refused** (exit 9):
  - a second `run` while the run was interrupted;
  - a concurrent `resume`;
  - a second `run` while the run was collecting.
- **Repeat run** (`01M5X73P…`, Fresh Fruits):
  - 96 products observed again, with the same prices in 95 cases;
  - one genuine change from available to unavailable was observed (Fresh Strawberries 8.8 oz). That
    product was kept in the retained file with empty prices.
- **Publication protection** on a disposable database and publication folder:
  - a pilot's publication was refused;
  - so were INJECTED empty, thin, blocked and wrong-store runs;
  - the published files' hashes were unchanged after each.

## 4. Container: NOT TESTED

There is no Docker on the preparation workstation. The Azure VM runs the release without containers.

## 5. Not verified

- **Oxylabs Classic Web Scraper API: NOT TESTED.** The required credentials (an API username and password)
  are unavailable, and the Web API key was not used as one.
- **A full-scope run:** all CSV rows, every subcategory and every page. It was not executed.
- **Unattended scheduled operation.** Schedules stay off; the scheduling logic is tested offline only.
- **The Container Apps option** (`azure/main.bicep`). It was not deployed.

## 6. Found during the Azure test (not changed in 1.3.0)

- **A false challenge detection.** The challenge marker for an Akamai reference number matched a customer
  review's "reference #…" on one product page (item 15353921746). Its UPC was recorded as `blocked` and not
  read. The product itself was exported from its result tile, without a UPC.
- **Carry-forward also takes verified records from rejected live runs of the same database.** On the
  disposable target, an INJECTED test run's synthetic record was carried into the second published version
  there. Fault injection must never run against a production database. The main database never ran one.
- **A killed execution keeps stale counters.** An execution killed with `SIGKILL` keeps its last
  `products_verified` and an empty `ended_at`. The next `resume` recovers the run, but these counters are
  not rewritten.
- **Price selector labels in the record map are imprecise.** For result tiles, the labels name
  `priceInfo.currentPrice` / `wasPrice`, while the values come from the tile's `priceInfo.priceDetails`
  price lines. Every exported price was checked against those price lines.

---

# Verification report: walmart-azure-headless 1.2.1

Release 1.2.1 (`dd7f4bc`) changes three things found by the live checks and the
audit of 2026-10-24 (the live checks ran on release 1.2.0, commit `038510d`):

- `validate-export` reported 1 of 1,127 records of run `01M5P24C...` as a mismatch: a verified product shown
  that day out of stock with no Pickup line for the store, exported without prices as intended, while the
  page still displays a price. The source check now verifies such a record on its other fields when the page
  shows no Pickup line for the store (`verified_without_local_price`); empty prices where the page has the
  store's Pickup line remain a mismatch.
- A listing's coverage row was written only when its category row finished: a run stopped later in the row
  left the row of a partitioned listing as `IN_PROGRESS`. It is now written when the listing ends.

- `store_logo` was empty in every exported row since 1.0.0, on the assumption that Walmart's header shows
  its logo only as an inline drawing. The audit of 2026-10-24 found the logo image in the header's "Walmart
  Homepage" link on every stored page sampled (96 result pages and 8 store pages of 2026-10-23 and
  2026-10-24, and the W1 capture of 2026-10-21): `https://i5.walmartimages.com/dfw/63fd9f59-14e2/9d304ce6-96de-4331-b8ec-c5191226d378/v1/spark-icon.svg`.
  1.2.1 reads it from the store page's header (`store_logo`, with its source in the supporting log).

The first two changes alter no collected or exported value; the third fills `store_logo` in runs of 1.2.1
and later (the files produced by 1.2.0 keep it empty). The rest of this report describes 1.2.0, which
1.2.1 contains otherwise unchanged.

# Verification report: walmart-azure-headless 1.2.0

Prepared 2026-10-24 on the same Windows workstation (Python 3.12, uv, PostgreSQL through `pgserver`,
`PSYCOPG_IMPL=python`, mypy 1.18.2 built from source). Release 1.2.0 is commit `038510d`.
Evidence classes are never mixed: **offline synthetic** (invented pages), **offline replay** (the stored
pages of the 2026-10-23 live runs read again by this code: corrected evidence about those runs, not fresh
observations), **live** (requests to Scrape.do and Walmart from the workstation), **container**, **Azure**.

## 1. What changed, and what reproduced each finding before the change

| Finding (audit of 1.1.0) | Reproduced on the stored evidence | Change |
|---|---|---|
| 5 products with "(2.25 lbs/Bag Est.)" / "(1.9 lbs/Bag Est.)" exported, `weight` empty | the 5 rows of the 998-row export; the trailing-segment parser left `weight` empty, so the approximate-weight rule never saw the wording | approximate weight wording in the title or a size field excludes the product (`sites/walmart/records.py`, `assembly/exclusions.py`); the export check also reads titles |
| 340 empty weights, sizes inside titles missed | 121 of them show a quantity with a unit in the title | sizes read from size groups and quantities inside the title, as written; ambiguous or dimension-only titles give none |
| Diapering 30,534 and Balloons 45,017 reported, 396 seen each, marked DONE | page 11 of both: 0 products, 0 results reported, page 10 reported 30,538 / 45,038 and 25 linked pages | evidence-based completion; `RESULT_WINDOW`; partition through the listing's own Departments facet (`collection/walmart.py`) |
| 39 fresh products accepted on OUT_OF_STOCK alone | all 39: no fulfillment line at all on their pages | a store line is required; earlier verification or unresolved; Delivery line never a Pickup price |
| Food row summary collapsed two listings | the 1.1.0 report: one listing, 472 / 200, where Fresh Fruits (242 / 177) and Fresh Vegetables (472 / 200) were read | coverage per listing (`listing_outcomes`), never from summed totals |
| UPCs: 86 extracted, 4 failed, 717 not attempted | the principal run's records | outcomes unchanged in kind; a replay reads every stored product page; reuse records its original time |
| Promotion text over 200 characters dropped; a fulfillment word dropped an offer | no live item lost text (0 promotion strings over 200 characters on 2,850 placements); the filters were latent | whole terms kept inside promotion objects; conditions kept with the offer; structured promotion data logged only |
| `/cp/` category pages: HTTP 502 | the stored answers are Scrape.do's own JSON ("Walmart-store plugin failure."), not Walmart's | category pages through the general API (navigation only); listings stay store-scoped |
| Age limit could drop verified products | `historical.max_age_days` was configurable | refused when set; age reported per carried record |

## 2. Offline checks

The unit and integration suites, `ruff`, strict `mypy`, the CLI and the Bicep template; the delivery's
package verification repeats them from a clean extraction and states the counts.

## 3. Offline replay of the 2026-10-23 runs

The five live runs that produced records were replayed in order by `replay` (no request; original
observation times): the principal run `01M5MZNS…` gives 763 valid fresh records (807 before: 5
approximate weights and 39 products with no store line left out) and 184 carried forward (191 before: 7
earlier out-of-stock acceptances no longer verify). The delivery's corrections report lists every changed
row. These are corrected readings of the same stored pages, not new observations.

## 4. Live checks

Recorded in the delivery of 2026-10-24 with their run ids, commands, credits and this release's commit.

## 5. Container: NOT TESTED

No Docker on the preparation workstation. A valid Dockerfile is not a successful build.

## 6. Azure: deferred by Hamza for this task (not a client waiver)

Azure deployment, execution and live scheduling were deferred by Hamza for this task; they stay pending.
The Bicep template builds and lints; that is not a deployment. Schedules stay off.

---

# Earlier report: walmart-azure-headless 1.1.0

Prepared 2026-10-23 on a Windows workstation (Python 3.12, uv, PostgreSQL through `pgserver`). Release
1.1.0 is the commit this file belongs to. The final delivery `walmart-final-<timestamp>-1.1.0` holds the
evidence named here (`reports/`, `evidence/`) and maps every live run to its source commit
(`SOURCE_VERSION.json`); its package verification repeats the offline checks from a clean extraction.
Evidence classes are never mixed: **offline** (synthetic or captured inputs), **live** (real requests to
Scrape.do and Walmart from the workstation), **container**, **Azure**.

## 1. Offline checks

Unit and integration suites, `ruff`, strict `mypy`, the CLI and the Bicep template, rerun on the release
from a clean extraction (the delivery's package verification states the counts). New in 1.1.0:
publication safety on the real pipeline (an incomplete, refused, wrong-store, empty or thin run never
replaces the published dataset; an interrupted publication is retried once, atomically), continuation
across executions, configured subcategory listings read without their category page, the exit code of a
finished run, and `validate-export` for carried-forward records.

Workstation note: from about 18:00 UTC on 2026-10-23, Windows Application Control on the preparation
workstation blocked compiled modules it had allowed before (psycopg's `pq.pyd`, mypy's `librt`). Checks
after that ran with psycopg's pure-Python implementation and the `libpq.dll` shipped inside pgserver
(`PSYCOPG_IMPL=python`), and with mypy 1.18.2 built from source. This is a property of that workstation.

## 2. Live checks of 2026-10-23 (workstation, not Azure)

Store #3891 Waukegan, Pickup, through Scrape.do. Every run's log, database rows, request ledger and saved
pages are in the delivery.

| Run | Scope | Result |
|---|---|---|
| `01M5MZNSFTM2EYNAEHR75FX65W` | rows 0, 1, 2, 5, 7: six subcategory listings read directly, 5 result pages each | **807 fresh verified products** (Fresh Fruits 151, Fresh Vegetables 195, Laundry 152, Bath & Body 119, Baby Formula 120, Dry Dog Food 70) and 191 carried forward: 998 rows; `validate-export`: 998 of 998 equal to the pages that observed them, contract passed; 392 credits; 90 product pages read for UPCs (the run's limit): 86 extracted, 4 failed, 717 not attempted |
| `01M5MJ9EYTDXTNDPP0WD15QKD3` | rows 4 Diapering and 8 Balloons, to Walmart's last result page | 196 verified of 792 shown; Ctrl+Break after 8 pages, a second run and a concurrent resume refused (exit 9), resumed as the same run; UPC outcome for every product (94 extracted, 81 reused from pages already read, 20 absent from the page, 1 blocked); 339 credits |
| `01M5MN1SV8BFC81YFNYZZ9HHTQ` | repeat of Balloons page 1 | 32 products in both runs, 0 value changes, 1 new, 165 carried forward unchanged |
| `01M5MEFB66GVXZ5WWMY8BK7YA4` | Food (category page) | Scrape.do answered HTTP 502 for the category page in 4 sessions; the operating system then killed the process tree (a real crash); the next command recovered the run, refused a new one (exit 9); stopped and finalized, nothing published |

Found during the live checks: Scrape.do's Walmart store endpoint answered HTTP 502 for every `/cp/`
category page tried that day while listing pages worked; Walmart serves at most about 400 products per
listing (page 11 shows none). No run was complete over its configured scope (each was bounded), so none
was published; publication is verified offline (section 1).

## 3. Container: NOT TESTED

No Docker on the preparation workstation.

## 4. Azure: NOT VERIFIED

No Azure access or deployment authorization was available. The Bicep template builds and lints; that is
not a deployment.

---

# Earlier report: walmart-azure-headless 1.0.0 (2026-10-22)

Prepared 2026-10-22 on a Windows workstation (Python 3.12.15, uv 0.13.1, PostgreSQL through `pgserver`).
Source revision: the commit this file belongs to. Code verified at commit `2b29aa0`; the live runs below
ran on commit `59172cd` (the later commits change the Mariano's collector, documentation, scripts and the
coverage record of listings not read, below). Derived from mscraper 1.2.6 (`f9c03085`). Evidence is kept in
four classes that are never mixed: **offline** (synthetic or captured inputs, no network), **live** (real
requests to Scrape.do and Walmart, from the workstation), **container** and **Azure**. The delivery's
`WALMART_TEST_EVIDENCE.zip` holds the live runs' logs, sanitized page captures, database rows, reports and
terminal screenshots.

## 1. Offline checks: PASS

`pytest` at `2b29aa0`, run in two groups (memory): **200 passed** (unit 153, integration 47), 0 failed,
0 skipped. `ruff check` and `ruff format --check` clean; `mypy --strict` clean with mypy 1.19.1 installed
from source (`uv run --with "mypy==1.19.1" --no-binary-package mypy mypy`): the workstation's application
control blocks the compiled mypy wheels' native modules, which is a property of that workstation, not of
the code. Every test runs against a throwaway PostgreSQL and, for collection, an in-memory mock of
Scrape.do's documented API; nothing reaches Scrape.do or Walmart. The delivery's
`PACKAGE_VERIFICATION.txt` repeats these checks from a clean extraction of the source ZIP.

| Area | What is checked |
|---|---|
| 22-field contract | field order, strings only, `""` for missing, `gupc`/`unit_price` empty, UPC kept as shown and never made from the item id, prices as displayed, PPM as displayed, approximate weights excluded, variants kept apart; CSV export with the same 22 columns |
| Product-page UPC | the product's own page, in production for every product missing a field and in a pilot within `--pilot-detail-pages N`, gives the 12 to 14 digits the product's own page states for that item (its `__NEXT_DATA__` item, then JSON-LD), leading zeros kept, never the item id; every attempt recorded with the record, found or not, and never repeated by a resumed run |
| Store and fulfillment | every listing page checked for store 3891 and Pickup from Walmart's own page data; a page for shipping, or another store, stops the run before any record (exit 7) |
| Canary | the first recorded page's valid records are compared with the page's own item data by a separate reader; a disagreement stops the run (`CANARY_CHECK_FAILED`) and holds the store |
| Marketplace / shipping-only | excluded; a product a later page shows only that way keeps its earlier local observation with its date, run and age in the supporting log (`observation_kind: historical`), never the marketplace price; past `max_age_days` it is not kept |
| Provider | the key from `SCRAPEDO_API_KEY` or a mounted key file, never stored or logged; the ledger charges by the cost header; an exhausted key stops the run resumably and no other key or provider is tried; a 429 is retried, a site refusal stops (exit 5) and holds the store; the credit ceiling and run budgets are never crossed |
| Runs | product, page and credit limits; a limit or an operator's stop finalizes the run as a pilot/partial export, never published; a complete validated run is published and a later partial run never replaces it |
| Publication (fault injection, offline) | a refusal, a rejected run and a crash before, during or after the publication's commit leave the published dataset as it was (or repair it from the database) |
| Coverage record | every listing a category page names has a coverage row; one not read says why (excluded by the CSV, not a product listing, not chosen, a limit of the run) |
| Interruption | SIGTERM, SIGINT or (Windows) Ctrl+Break during a page: the run is left `interrupted` (`TERMINATED`), the provider session and segment closed, the store lock released, exit 75; `resume` finishes it without recording a product twice |
| Schedule | ships **disabled**; the Azure cron covers both UTC offsets; only the store-local occurrence acts (checked at both daylight-saving changes), an Azure retry or the second firing does nothing twice, a held store exits 8, an unfinished earlier occurrence is closed as partial |
| CLI | exit codes 0/2/3/4/5/6/7/8/9/75, JSON log lines, the operations entry point (`ops`) |
| Isolation | the code imports only the standard library, its own package and its declared dependencies; no reference to the original application; no web files |

**Authentic captures, replayed offline.** `tests/captures/w1_20261021` holds the store page and two
Diapering result pages that the deployed application's live run W1 captured on 2026-10-21 (sanitized
copies). Served through the Scrape.do mock, they give the same 37 products W1 exported. These are earlier
captures, not new evidence.

## 2. Live checks (workstation, not Azure)

### 2026-10-22, commit `59172cd`: 437 unique valid products

Key `…32d333` (Scrape.do's free plan; read from a local key file, never copied into any file of this
package), store 3891, Pickup. Each command ran as its own process through `scripts/headless_live_campaign.py`
(the repository's driver), with a run budget and a balance check before each paid step. Balances are
Scrape.do's own `/info` readings.

| Run | Time (UTC) | Scope | Result | Scrape.do credits |
|---|---|---|---|---|
| canary `01M5HX1M5NZ04J6QN65YW2TMHT` | 13:33–13:35 | Diapering (row 4), 1 page, product-page sample 2 | store 3891 and Pickup verified from Walmart's data; canary passed; **24 valid**, 16 excluded (no Pickup offer at the store; 13 of them sold by marketplace sellers); UPC from the product page for **2 of 2** sampled products (12 digits); one provider failure (HTTP 502, not charged) retried | 267 → 235 (32) |
| repeat `01M5HX799ZXWSDEX8W3ECJ8SQ9` | 13:36 | the same page, no sample | the same **24 valid** products with the same prices and flags; the same 16 excluded | 235 → 223 (12) |
| demonstration `01M5HX89AEX9HQMXEN5X4ZMT5J` | 13:36–13:43 | rows 1, 2, 5, 7, 8 (Household Essentials, Personal Care, Feeding, Pets, Balloons), one listing each, 3 pages each | **real interruption**: Ctrl+Break sent to the collector's process group after the 5th page; the run stopped `TERMINATED` (exit 75), the page in flight was cancelled and the provider session closed. A second `run` while it was unfinished ("has an unfinished run ...: resume or finalize it") and a second `resume` while the first one collected ("is running") were refused (exit 9). `resume` continued from the checkpoints: no completed page was requested again; the cancelled page was read once. **413 valid**, 186 excluded (no Pickup offer at the store; 75 of them marketplace offers), 6 out-of-stock products kept with their price and flag | 223 → 29 (194; the ledger's 10 for the cancelled request were not charged) |

All three are **pilot** runs (narrowed on the command line): exported, never published. `validate-export
--run` passed for each: the manifest and export files verified, the 22-field contract passed, and every
valid record equal to its item in the stored page, read independently (demonstration: 413 of 413).
Pagination: the listings announced 6 to 25 pages; the runs read the pages their limits allowed (real `page=` requests; across the demonstration's 15 result pages one product appeared on two pages). Coverage per
listing, exclusions, duplicates (51 products shown in more than one place), field completeness and the
per-record provenance are in the evidence package. **Not reached: 500 products** (437; the remaining 29
credits allow two more pages).

### 2026-10-21, commit before `053bf13`: 10 valid products

Run `01M5FSNW8AY1X8Y393KQ3M9S4M`: one Diapering page, 10 valid products, 12 credits (279 → 267); an
earlier attempt stopped after robots.txt on a local path-length problem (fixed). Evidence in the
2026-10-21 delivery.

## 3. Container: NOT RUN (pending)

No Docker is available on the preparation workstation, so the image has not been built or started. The
same CLI was run from the locked environment (`uv sync --frozen`), which is what the image installs.

## 4. Azure: NOT RUN (pending)

No Azure subscription or credentials were available. Option A (Container Apps, `azure/main.bicep`)
compiles and lints without warnings (Bicep CLI 0.48.1); option B (one VM, AZURE_VM.md) is documented
only. Nothing was deployed or provisioned and no Azure charge was incurred.

## 5. Not verified

* A full-scope run (every category and page) and its duration (estimated at about 26 hours of
  collection at the measured page rate, OPERATIONS.md); the twice-weekly cost is an estimate.
* Publication of a live run (pilot runs are never published; publication is tested offline only).
* An authentic in-stock to out-of-stock change in the 2026-10-22 runs (none occurred between them;
  historical examples are in the evidence package).
* UPC for every product: only a bounded product-page sample was read (2 of 2 found).
* The twice-weekly schedule firing in Azure (the decision logic is tested offline only).

## 6. Found and fixed while verifying

* 2026-10-22: a skipped or capped listing's coverage row had an empty reason (`2b29aa0`); Windows had no
  stop signal the collector listened to (Ctrl+Break added, `59172cd`); the schedule shipped enabled (now
  off, `09f3575`); the UPC was never read because result pages do not show it (product-page sample,
  `09f3575`).
* 2026-10-21: the Scrape.do keep-alive helper swallowed a cancellation; local storage passed Windows'
  260-character path limit; a half-finished export task collided with its files; a run narrowed with
  `--categories` alone could have been published (now a pilot).
