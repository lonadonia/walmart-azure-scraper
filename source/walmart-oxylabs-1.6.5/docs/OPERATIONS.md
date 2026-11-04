# Operations

## Setup

### Local (a workstation or a server)

1. Python 3.12 and uv; `uv sync --frozen` installs the exact locked versions (`uv.lock`).
2. A PostgreSQL database for this collector alone (it must not be shared with another collector's tables).
3. `cp .env.example .env` and fill in `WALMART_COLLECTOR_DATABASE_URL` and the key of the provider the
   store uses (`SCRAPEDO_API_KEY`, or `SCRAPEDO_API_KEY_FILE` naming a file that holds it; for the Oxylabs
   Web API `OXYLABS_WEB_API_KEY` or `OXYLABS_WEB_API_KEY_FILE`). `.env` is never committed or packaged. An
   edition's `.env.example` names its own provider's key only, a database and a data folder of its own
   ([EDITIONS.md](EDITIONS.md)).
4. `walmart-collector db-upgrade`, then `walmart-collector validate-config --check-db --require-credentials`.
5. Spending: `walmart-collector set-ceiling --credits 250 --basis "monthly plan"` caps total Scrape.do
   spending; an Oxylabs run sends nothing until `set-ceiling --provider oxylabs --submissions N --usd X
   --basis ...` is set; `set-budget --usd X --basis ...` caps the task's money across both (CLI.md).

Data goes to `./data` (or `WALMART_COLLECTOR_DATA_DIR`). For a container, the same with the image
(Dockerfile): `docker run --env-file .env walmart-collector:1.6.5 validate-config --check-db`. For one Linux
VM (PostgreSQL on the VM, a service user, systemd units with no timer), see [AZURE_VM.md](AZURE_VM.md).

### Azure

See [AZURE.md](AZURE.md): build the image, put the two secrets in Key Vault, deploy `azure/main.bicep`,
run `db-upgrade` through the operations job.

## Operation

* **Scheduled collection.** Each store's Azure job fires every 30 minutes; `run --scheduled` starts a new
  run only at the store-local start time of a scheduled weekday (twice a week by default, Tuesday and
  Friday 06:00 America/Chicago). The other firings inside the daily window (the whole day in the shipped
  configuration, any weekday) continue that run while it is unfinished, one execution of at most
  `max_segment_minutes` (300) at a time; the rest exit in seconds. An occurrence that finds the previous
  scheduled run still unfinished lets it go on and starts no run (`OCCURRENCE_DEFERRED`;
  `schedule.on_overlap: continue`, release 1.3.1), so a run is never cut short by the next start; with
  `on_overlap: supersede` (the release 1.3.0 behaviour) it closes that run as partial (never published) and
  starts a new one. Since release 1.5.0 every start that has passed is a row of the occurrence ledger, kept
  until it has been run: a late firing, a hold, a manual run or an unfinished previous run makes it wait with
  the reason, never disappear (`schedule-status`, CLI.md). AZURE.md (Schedule, continuation and daylight-saving
  time) has the details. The shipped configuration has the schedule **off** (`collections.<store>.schedule.enabled:
  false`) until the client approves it; with it off a firing exits 0 with `SCHEDULE_OFF`.
* **Manual collection.** `run --store KEY` (with limits for a bounded pilot). In Azure, through the
  operations job (AZURE.md, Operations).
* **Stop, resume, finalize.** `stop` asks a running execution to stop at its next checkpoint and finalize.
  `resume` continues an interrupted run from its checkpoints. `finalize` exports what an unfinished run
  collected without requesting anything.
* **Provider.** One provider per run (`collections.<store>.provider`, or `run --provider`): `scrapedo`
  (the shipped default) or `oxylabs` (the Web API). The Oxylabs Web API is the provider demonstrated on
  Azure (2026-10-26, VERIFICATION.md): a deployment that uses it sets `provider: oxylabs` in its own
  configuration (the Azure VM's runs did). The shipped default stays `scrapedo` because the Container Apps
  template (`azure/main.bicep`) passes only the Scrape.do key; adding the Oxylabs key there has not been done
  or tested. A change of provider is a new run; a run is resumed with its own provider. Either way the store
  and fulfillment are proved from Walmart's own page data on every page, never from the provider's request
  parameters. An edition (release 1.4.0, [EDITIONS.md](EDITIONS.md)) is this collector built for one
  provider: its configuration's `edition.providers` names that provider only, and a run, a resumed run or a
  `provider-balance` naming the other is refused (exit 2) before any request, whatever keys are set. No run
  falls back to another provider.
* **Workers.** `parallel.workers` (default 1) or `run/resume --workers N` runs N workers in one execution:
  each leases its own listing tasks from the run's database queue, renews its lease while a request is
  slow, opens its own provider session and checks the store on its own pages. A worker that loses its
  lease (another took the task after it stalled) raises before it writes anything more; the task's
  checkpoint (the pages already collected) is where the next owner continues. `max_in_flight` and
  `min_interval_s` bound the requests of the whole process. More workers do not mean proportionally faster
  runs: the provider's own concurrency limit and its response time decide (VERIFICATION.md has the
  measured comparison).
* **Follow-ups.** After the listings, products seen only in sponsored placements and variant siblings named
  by result tiles (every tile of the result grid: the one a product was recorded from, a repeated tile of it
  and a sponsored tile; release 1.3.1) are read on their own product pages (CLI.md, run). A sponsored
  placement alone neither includes nor excludes a product: its own page must identify it, show it for the
  store under the listing's category and show Walmart (not a marketplace seller) offering it.
  `follow_up.max_pages` (or `--follow-up-pages`) is a pilot budget of pages per kind: the rest are recorded
  as not attempted and stay pending in the store's follow-up queue (`follow-ups --store KEY`), which the next
  run of the same lineage reads first, so a budget never drops a candidate for good. A variant sibling the
  run saw only as a sponsored tile (no record is kept from a sponsored tile) is read once: by the sponsored
  follow-up, its variant outcome saying so, or by the variant follow-up when the sponsored one is off
  (release 1.4.1; release 1.4.0 called it recorded from that placement, and read it nowhere when the
  sponsored follow-up was off). A run stopped before its follow-ups finish (a spending ceiling, a stop)
  records outcomes only for the candidates they reached: the others of a follow-up that had started stay
  pending in the queue; those of a follow-up that never started are not queued, and only a later run that
  names them again reads them.
* **Retained products are never yield** (release 1.4.0). A run publishes, with what it observed, the
  store's verified products it did not observe (carried forward, `historical`). The checks weigh them
  against the fresh valid records: a category, or the whole run, whose published products are more than
  half retained fails G4 (`RETAINED_MASKS_YIELD`; more than 30% warns: `yield.fail_retained_share`,
  `warn_retained_share`), so a run that observed almost nothing cannot pass on what earlier runs saw. A
  bounded run counts the retained products of the listings it read (it carries the others by design); a
  complete run counts every one. It covers what the yield-drop check cannot: a store's first complete run,
  which has no earlier one to compare with, and bounded runs, which are never compared.
* **Publication.** Only a complete, validated, non-pilot run is published: `published/<store>/latest.json`
  names the run and its manifest; the database pointer is authoritative. A pilot, partial or rejected run
  keeps its exports under `runs/<store>/<run>/exports/` (or `exports-<time>/`), labelled in its manifest
  (`"dataset": "pilot" | "partial"`), and never replaces the published dataset.
* **What a run exports.** `products.json` and `products.csv` (the 22 fields: what the run observed plus
  the store's verified products carried forward), `products_fresh.json` and `products_fresh.csv` (only what
  the run observed), `memberships.json` (where each product was listed, in page order), `offers.json` (the
  offers of the page each record is kept from, each with that page), `provenance.json`
  (the supporting log: per product, the page and check that observed it, exclusions with reasons, fresh or
  historical observation), `record_map.json` (per exported row: its run, observation time, code revision,
  stored page and SHA-256, store checks, field sources and times, UPC outcome), `validation_report.json`
  and `manifest.json` (hashes of every file). Their lists and counts are written in a fixed order
  (memberships, offers and the counts by reason since release 1.3.1), so exporting the same records again
  gives the same products, memberships and offers files; the other files also carry the time they were
  written.
* **Replay.** `replay --run ID` reads an earlier live run's stored pages again with the current code,
  offline, as a `REPLAY` run with the source's observation times (CLI.md). Use it after a rule changes to
  regenerate that run's outputs through the real pipeline; a replay is never published.

## When a listing is complete

Every result page read is recorded with its products, its new identities and the totals the listing
reports; only the page's result grid is the listing's results (release 1.3.1: a module such as an
"Available for shipping" carousel is not). A listing is `DONE` only when it ended (an empty later page, or
its last linked page) with a total that stayed the same on every page and that what its results placed
balances **exactly**: its distinct organic identities, those plus its sponsored-only identities, or its
tiles (sponsored tiles repeating organic products). There is no tolerance threshold
(`coverage.node_min_coverage_ratio` is fixed at 1.0), reaching the last page proves nothing by itself, and
more identities than the listing reports is an overcount, never done (sponsored products, scope, variants or
a stale total must explain it). An empty later page counts as an end only when its own data still names
store 3891 and Pickup (otherwise the run stops: exit 7). A listing whose first page shows 0 results is `EMPTY`
on the same condition, whatever other modules the page shows: a 0 the page reports is a total of 0 (release
1.6.4: on 2026-11-04 Walmart's "Bidets" listing reported 0 Pickup results for store 3891 beside an "Available
for shipping" carousel of 10 products; release 1.6.3 took the 0 for a missing total, read the carousel's 10 as
the total, stopped the run, exit 6, and held the store). A first page that reports results and shows none
still stops the run (exit 6). Otherwise the listing is `INCOMPLETE` with the
reason (`RESULT_WINDOW`, written "accessible pages exhausted; coverage incomplete": the site stopped serving
results while it reports more, as Walmart's listings did at page 11 on 2026-10-23, also when the total moved
while the listing was read and the site served less than its smallest total by more than it moved (release
1.6.2: Laundry, 2026-11-03); an overcount or an unreconciled difference; `REPEATED_PAGE`; `SAFETY_LIMIT`, a
listing still serving pages past 50 when Walmart links at most 25; `CATEGORY_PAGE`, a listing link that served
a category page instead of a listing, recorded with the listings that page links while the run goes on (release
1.6.2); `NOT_FOUND`, a listing link the site answered with its own not-found page (its data is the page `/404`),
recorded while the run goes on (release 1.6.3; 1.6.2 called that page a challenge, stopped the run, exit 5, and
held the store); any other page without a result grid stops the run, exit 6, and holds the store; a limit;
robots.txt),
and the run's coverage check (G3, which reads the difference no
exact balance explains) fails, so it is never published. `coverage-report --run ID` reconciles every scope unit of a run (CLI.md). The reported total
can include offers that are not the store's (marketplace, shipping): a gap is reported, never taken as
proof either way. What it counts depends on the grid Walmart served, which each result page records from
its own data (`grid_fulfillment_filter`, release 1.4.1): `Pickup` for Walmart's Pickup grid (both editions
ask for it: the Oxylabs Web API through `fulfillment_type`, the Scrape.do edition through Walmart's own
`facet=fulfillment_method:Pickup` on each result page), `none` for the store's unfiltered grid (release
1.4.0's Scrape.do runs), whose total counts out-of-stock and shipping-only items too. A listing that hits the window is partitioned (`coverage.partition_large_listings`): the
child categories its own "Departments" facet names (ids extending its id) are read as listings of their
own, linked to it, and a child that hits the window is partitioned in turn, as deep as those facets go
(`partition_max_depth` empty, the default since release 1.4.0; release 1.3.1 stopped at depth 2 and left a
deeper overflowing branch incomplete). A number there is an explicit cap for a bounded run: a listing it
leaves unpartitioned says so and stays incomplete. The parent is complete only when the distinct products
of the parent and its children balance its total exactly and every child ended (overlapping counts are
never added). Coverage is decided per listing, never from a category's summed totals.

## Approximate weight and products sold by weight (release 1.4.0)

* A product whose wording is approximate or estimated is excluded as a whole (`APPROX_WEIGHT`): a size
  written as approximate ("2.25 lbs/Bag Est.", "approx. 1 lb", an average weight), or a price stated as an
  estimate ("each (est.)" next to the price of a product sold by the piece and charged by weight). The
  record's field log names the wording, the field and its path in Walmart's page data, and the whole value.
  Within a run, a product one of whose tiles showed such wording is excluded whichever tile it is recorded
  from (a sponsored tile of the same product shows none).
* Being sold or charged by weight, or a "/lb" price per measure, excludes nothing. Such a product is kept
  with its displayed prices, flagged `RELATIVE_PRICE` and `SOLD_BY_WEIGHT`; when its title gives no size, its
  weight is the one Walmart states after its price ("$0.25 / 0.14lb" gives `0.14lb`). Release 1.3.1 excluded
  every weight-priced product; `records.exclude_relative_price_items: true` restores that rule.
* An earlier observation is carried forward only when it showed no such wording. One made by a release that
  kept no reading of the wording next to a weight-priced product's price (1.3.0) is not carried: whether it
  showed an estimate is unknown.

## Store assortment, availability and price

* A Pickup line of store 3891: the store's product and its price (also when out of stock, flagged).
* A Delivery line of the store, no Pickup line: the store's product, exported without prices
  (`NO_PICKUP_OFFER`): the displayed price is not taken as the Pickup price.
* No line for the store (out of stock without fulfillment, shipping only, a marketplace seller): the store's
  product only when an earlier run, or an earlier tile of the same run, verified it there; exported with its
  identity and size and empty prices (`NO_LOCAL_OFFER`, the earlier observation and price in the supporting
  log); otherwise `ASSORTMENT_UNRESOLVED`: recorded with the reason, not exported.
* A product shown by several result tiles of one run (release 1.3.1):
  * The record holds the latest state the run observed (availability, the store's line, prices, offers).
    Release 1.3.0 kept the first tile and counted the others as duplicates.
  * Its earlier states stay in the observation and in the exports' record map and supporting log
    (`earlier_in_run`), each with its page and time.
  * The latest earlier tile that verified the product at the store is the run's verification.
  * The record keeps the category of the listing it was first recorded from, and the UPC read from its own
    page.
  * A tile observed before the record's own tile (two workers' requests overlapping) never replaces the
    record; it is logged the same way.
* Verified products a run does not observe are carried forward unchanged with their own dates and age
  (`historical`). There is no age limit: `historical.max_age_days` must stay empty. Earlier observations
  count only under the current rules (a store line, no approximate or estimated-weight wording), and a
  replayed run counts through its replay. Carried products are published but never counted as the run's
  yield (Operation, retained products).

## Product detail path (release 1.5.0)

A product whose result page states no UPC or no size gets its own page read once in the run, as the listings go:
production has no budget. What that page says is accepted only for its own item: the page must name the requested
item id (`identity_mismatch` otherwise), a UPC is taken only from the page's own UPC or GTIN field with its leading
zeros (never the item id, never a sibling's), and a UPC the listing already states is never replaced (a page that
disagrees is kept as a conflict, `UPC_SOURCE_MISMATCH`).

The size is read apart from what is not a size (`sites/walmart/pack_size.py`): the page's statements are separated
into pack size, count and multipack, while serving size, the unit-price denominator and a sibling variant's size
are never read as the product's size. A size is never calculated, and a multipack keeps both of its numbers
as written ("4.5 fl oz, 6 Pack"). Statements that disagree are kept in the record's provenance and flagged
`SIZE_CONFLICT`, and the field stays empty when they cannot be decided. Approximate wording on a pack statement
excludes the whole product, as it does on a title.

Outcomes are kept across runs in `detail_observations` with the read's original time, run, source revision and
page hash. A later run reuses them for `detail.reuse_days` (30), and what is reused says so
(`recovered_from_saved_detail`, with the original time and run); it is never described as newly fetched, and a
later "absent" never erases an earlier value. Work not done stays in the store's queue (`follow-ups --kind detail`,
never-read first, so a budget does not fall on the same first products run after run), and each page is charged
through the same ledger as a listing page. Reuse costs no request, so a page budget does not stop it: since
release 1.5.1 a pilot applies every saved outcome before it spends its budget on pages never read. After `detail.pause_after_failures` (3) consecutive refused or failed
pages the path stops for the run and the run fails its access check (G2, `DETAIL_PAUSED`): it is kept, never
published, and the last good dataset stays. One refused page does not cost the run its publication: its field
stays empty with `blocked` (or `request_failed`) and a later run reads it again.

A pilot's budget is explicit (`run --pilot-detail-pages N`, `--pilot-no-detail`) and makes the run a pilot.
`--pilot-no-detail` (or `detail.enabled: false`) stops product-page requests only: what earlier reads of a
product's own page established within `detail.reuse_days` is still used, at no request, with that read's own
time, run, revision and page (release 1.6.3; `detail.reuse_days: 0` turns reuse off). A carried row whose UPC
or size is empty gets them from such a read too, never forced (release 1.6.3, `docs/VERIFICATION.md`).
`detail.max_per_run: 0` and `--pdp-sample` are refused, and a scheduled run refuses any budget.

Saved pages are loaded with `import-detail-captures --store KEY --index FILE`. The index is a JSON list next to the
pages, one object per page: `item_id`, `observed_at` (when the page was read, ISO 8601), `run_id` (the run that
read it) and `path` (relative to the index, `.html` or `.html.gz`) are required; `page_fetch_id`,
`source_revision` and `url` are optional. A page that does not identify its item is refused and listed, never
loaded. The command requests nothing.

## UPC outcomes

Every exported product of a run records why its `upc` is filled or empty (`upc_detail` in the record map
and the supporting log; counted in the run's `counts.upc_detail` and the supporting log's
`upc_outcomes_of_fresh_exported`). The item id is never used as a UPC, and no price is taken from a
product's own page.

| Outcome | What it means | Empty UPC, by cause |
|---|---|---|
| `extracted` | read from the product's own page in this run: the value, its field and its path in the page data, the page's request id and stored SHA-256 | |
| `extracted_from_listing` | the result page stated it | |
| `extracted_reused` | the same product's UPC read from its own page within `detail.reuse_days` (default 30): not re-read; `reused_from` names the run, page and time it was read | |
| `absent_in_source` | the page was read and is the item's, and its page data states no UPC or GTIN | source absent |
| `not_attempted` | the page was not read; `reason` says why: detail reading off, the pilot's `--pilot-detail-pages` budget reached, reading paused after consecutive refusals, the run stopped first, no item id or URL, or (a replay) the source run never requested it | detail not attempted |
| `blocked`, `request_failed` | the request was refused or challenged (the reasons the page's structure gave), or failed (an HTTP status or a provider error) | access failure |
| `parse_failed` | a page was returned without Walmart's page data | parser failure |
| `identity_mismatch` | the page is another item's, or its data names no item its identifiers can be tied to | identity mismatch |

A `blocked` or `request_failed` product page never rejects the run by itself (a stopped path does: see Product
detail path above): the product keeps what its
result page showed. When the provider brings no page at all (it failed the request after its retries),
nothing is stored for it, and G13 does not count that as a missing page unless an observation or a record
names it as a source (release 1.4.1; release 1.4.0 rejected such a run).

`extracted_from_listing` and `extracted_reused` are the run's counts; a record's own `upc_detail` says
`extracted` with `fresh: false` and, when reused, `reused_from`. An earlier UPC is never presented as read in
this run: a carried product's row gives its earlier run's outcome and names that run (`observed_by_run`), and
is not counted among the run's own outcomes.

## Capacity of one run (measured rates; read before enabling the schedule)

Read `schedule-status` for what the store's occurrences actually did (release 1.5.0). If measured runs do not
fit the interval between two starts, that is a capacity gap: the required scope and cadence stand, and more
workers within the provider's limits or more provider throughput are what closes it. Queuing occurrences keeps
them, but does not meet the cadence.

Pages are read one at a time per worker. Measured on 2026-10-22 and 2026-10-23 (VERIFICATION.md): a Walmart result
page through Scrape.do's store endpoint took about 8 to 14 s (median about 10 s), and Walmart serves about
10 result pages (about 400 products) of a listing whatever page count it announces. Since 1.2.0 such a
listing is not complete: it is partitioned into its child categories, so a full-scope run reads more pages
than the earlier estimate of about 9,400 result pages (roughly 26 hours) assumed. The number of child
listings is not known until they are read: the delivery's cost report gives the measured inputs and the
range; it is an estimate, **no full-scope run has been executed**. Product pages read for UPCs: median
about 11 s each, 1 credit each; an item's UPC is reused for `detail.reuse_days` (30), so later runs read
only new or stale items.

That is longer than one execution (`max_segment_minutes`, 300) and, at the rates measured so far, longer
than the interval between two starts (72 hours from Tuesday 06:00 to Friday 06:00, 96 hours from Friday to
Tuesday). A run is carried by several executions (AZURE.md, Schedule, continuation and daylight-saving
time): each pauses at its checkpoint and the next continues it. Since release 1.3.1 the schedule shipped never
cuts such a run short: the daily window is the whole day, `limits.max_run_minutes` is empty (no time limit;
spending stops at the provider ceiling and the credit budgets), and an occurrence that finds the previous
scheduled run unfinished lets it go on (`schedule.on_overlap: continue`). A long run costs frequency, not
scope: while it is unfinished no new run starts, so the store gets a complete dataset less often than twice
a week. Until a run completes it is a partial run and never replaces the published dataset. Narrowing the
configured scope is not a way to fit the schedule: a narrowed run is a pilot and is never published as the
store's catalogue. Shorter runs come from more workers within the provider's concurrency limit (measured
with one and two workers only, on segments with different workloads: an indication, not a controlled
benchmark, and no linear speed-up is assumed) or from fewer pages per run (the UPC reuse period). The
delivery's cost and runtime report reconciles the projected durations with these intervals; they are
estimates from measured page rates, and **no full-scope run has been executed**.

## Monitoring

* **Exit codes** of each execution (Azure shows them per execution; CLI.md lists them). Anything but 0 needs
  a look; 8 repeats until someone releases the hold.
* **Logs** in Log Analytics (`ContainerAppConsoleLogs_CL`, or `ContainerAppConsoleLogs` in newer
  workspaces). Each line is JSON; for example:

  ```kusto
  ContainerAppConsoleLogs_CL
  | where ContainerJobName_s startswith "walmart-collector"
  | extend e = parse_json(Log_s)
  | where e.event in ("RUN_FINISHED", "COLLECTION_HELD", "UNEXPECTED", "TERMINATED", "PUBLICATION_REFUSED")
  | project TimeGenerated, ContainerJobName_s, e.level, e.event, e.exit_code, e.run_id, e.stop_code, e.message
  ```

  Alert suggestions: any `ERROR` line; `RUN_FINISHED` with `exit_code != 0`; no `RUN_FINISHED` for a store
  in 4 days; `PROVIDER_BALANCE` with `usable` below the next run's need.
* **`status`** (operations job, or locally): holds, last runs, published dataset, credits recorded.
* **`schedule-status`**: occurrences, backlog, missed deadlines, capacity. **`follow-ups`**: unfinished
  product-page work. **`field-dispositions --run ID`**: why each product's UPC and size are filled or empty.
* **Credits**: `provider-balance` (free). Each Walmart page costs 10 credits, robots.txt and the store page
  1 each; a run's `PROVIDER_TRAFFIC` event gives what it spent. Oxylabs has no balance API:
  `provider-balance --provider oxylabs` gives the ceiling, the room left and the ledger; the balance itself
  is read in the Oxylabs dashboard.

## Backup

* **Database.** Azure Database for PostgreSQL keeps automated backups with point-in-time restore (7 days by
  default, up to 35: set it on the server). Locally: `pg_dump -Fc` of the collector's database, kept away
  from the machine. The database holds the runs, records, ledger and publication pointer.
* **Blob container.** Turn on blob soft delete and versioning on the storage account; the exports of every
  run and `published/` are there. The published dataset can also be copied out with
  `export --store KEY --out DIR`.
* **Configuration.** `config/` is part of the source (and the image); keep it under version control.
* Secrets are not backed up by the collector: Key Vault keeps versions and soft-deleted secrets.

## Maintenance

* **Upgrade.** Build and push the new image, update the jobs' image (`azure/deploy.sh` does both), then
  run `db-upgrade` through the operations job before the next scheduled execution. Schema changes ship as
  migrations in the package; `run` refuses a database whose schema is not current.
* **Configuration changes** (stores, categories, limits, schedule) are files in `config/`: edit, rebuild the
  image, update the jobs. `validate-config` before deploying.
* **Stored pages.** Each run keeps the pages it read (`runs/<store>/<run>/live/`, a few MB per page set) as
  evidence. Add a Blob lifecycle rule to delete `runs/` blobs older than your retention (e.g. 90 days);
  the exports you need longer can be kept by excluding `exports` paths or copying them out.
* **Dependencies.** `uv lock --upgrade`, run the tests (`uv run pytest`), rebuild.

## Recovery

| Situation | What happened | What to do |
|---|---|---|
| Exit 75, `TERMINATED` | The job timed out or was stopped; the run is `interrupted` with its checkpoints | `resume --store KEY` (or let the next scheduled occurrence close it as partial and start anew) |
| Exit 75, `PROVIDER_ERROR` after the automatic resumes | Scrape.do kept failing | check Scrape.do's status, then `resume` |
| Exit 3 | No key, or Scrape.do refused it (the store is held for `PROVIDER_AUTH`) | fix the secret, `release-hold`, `resume` |
| Exit 4 | Credits or a budget ran out; the partial run is exported, nothing published | add credits or raise the budget; the next run starts anew |
| Exit 4, `SPENDING_CEILING` | The next request could cross a provider's ceiling or the task's money budget (or no Oxylabs ceiling is set); the run stays `interrupted` with its checkpoints | decide the spending; `set-ceiling` / `set-budget` with the basis, then `resume` (or `finalize` to export what was collected) |
| Exit 5 / 7, store held | Walmart refused access, a page was not for store 3891 / Pickup, or the canary records differ from the page | read the run's events and stored pages (`status --run`, the blob container); fix (configuration, code) before `release-hold --reason ...` |
| Exit 6 | The run's checks rejected it (coverage, yield drop, integrity) | `status --run` lists the failed checks; the published dataset is unchanged |
| Exit 9 | Another execution holds the store, or an unfinished manual run blocks it | wait; or `resume` / `finalize` that run |
| An execution died (node loss) | The run looks active but no execution holds its lock | the next command recovers it (`RUN_RECOVERED`), `resume` continues it |
| Database restored to an earlier time | Runs after that time are gone; their blobs remain | nothing breaks: new runs get new ids; old blobs can be deleted |
| `latest.json` missing or stale | written after the database commit | the database pointer is authoritative; the next publication rewrites it |

## Adding a store

1. Add an entry to `config/stores.yaml` (key, `location_id` = Walmart store number, expected ZIP and
   address, `modality: PICKUP` or `IN_STORE`, timezone, `store_page_url`).
2. Add `collections.<key>` to `config/collector.yaml` (categories, limits, schedule, timezone).
3. `walmart-collector validate-config`, then `schedule-info --store <key>` for its UTC cron.
4. Add `{storeKey, cronUtc, jobName}` to the `schedules` parameter of `azure/main.bicep`, rebuild and deploy.

The first run checks the new store on Walmart's own store page and on every listing page; a mismatch stops
it (exit 7) before any record is exported.

## Adding or changing categories

Edit `config/Walmart_Category_URLs.csv` (same columns: `Retailer,Category (Auto),URL,Scope,Notes`; a
`Notes` text such as `Exclude 'Recipes' subcategories` leaves those subcategories out). Rows are numbered
from 0 in file order; `collections.<store>.categories` lists the rows to collect (empty = all). A row
removed from the CSV is disabled in the database at the next run, never deleted.

## Replacing the Scrape.do key

* Azure: add a new version of the Key Vault secret `walmart-collector-scrapedo-api-key`. Container Apps
  reads Key Vault references when an execution starts (references are refreshed periodically); run
  `provider-balance` through the operations job and check the fingerprint in its result.
* Locally: change `SCRAPEDO_API_KEY` (or the key file).

The ledger keys usage by a fingerprint of the key, so a new key starts with no exhaustion carried over.
Never put the key in `config/`, the image, or a log.

## Replacing the Oxylabs Web API key

* Write the new key to the secret file named by `OXYLABS_WEB_API_KEY_FILE` (mode 0600, owned by the
  service user), or set `OXYLABS_WEB_API_KEY`. The file holds the bare key, or a line
  `OXYLABS_WEB_API_KEY=<key>` (also `OXYLABS_API_KEY` or `OXYLABS_API`, with `=` or `:`).
* `validate-config --require-credentials` shows the new fingerprint. The ceiling and the ledger are not
  tied to a key: a new key does not reset what was spent.
* Only Web API (Bearer) keys are used. Classic Web Scraper API credentials (an API username and password)
  are a different product and are not supported.
