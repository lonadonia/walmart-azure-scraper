# walmart-azure-headless

A headless collector of Walmart store prices for one or more configured stores, built to run as Azure
Container Apps Jobs or on one Linux VM. It reads Walmart pages through **one provider per run**: Scrape.do's
Walmart store endpoint (`https://api.scrape.do/plugin/walmart/store`, with the store's `storeid` and
`zipcode`, and since release 1.4.1 Walmart's own Pickup filter on result pages; the default) or, since
release 1.3.0, the **Oxylabs Web API** (`POST /v1/scrape/walmart` with the store's `store_id` and
`fulfillment_type`; Bearer key). It checks every page against the configured store
and fulfillment from Walmart's own data, never from the provider's parameters, and exports products with
exactly the client's 22 fields. It has no web interface and no login.

Release 1.4.0 ships it as two **editions** built from one revision, the Scrape.do edition and the Oxylabs
Web API edition: the same code, each configured for its own provider, credentials, database and data, and
refusing the other provider ([docs/EDITIONS.md](docs/EDITIONS.md)).

Configured store: **Walmart #3891**, 3900 Fountain Square Pl, Waukegan, IL 60085, **Pickup**
(`config/stores.yaml`, key `walmart-3891-pickup`).

Derived from the deployed application (mscraper 1.2.6, commit `f9c03085`): the Walmart parser, record
rules, Scrape.do client and credit ledger, validation checks and export format are that application's,
moved into a standalone package (`walmart_headless`) with its own command line, database schema and
configuration. Nothing here needs the original application, its database or its files.

## What runs where

| Where | What |
|---|---|
| Azure Container Apps Jobs | `walmart-collector` (this package): one scheduled job per store, one manual operations job. Each execution runs one command and exits. |
| Azure Database for PostgreSQL | runs, task checkpoints, records, the credit ledger, store locks, holds, publications (one database for this collector). |
| Azure Blob Storage | the stored pages of each run, its exports, and `published/<store>/latest.json` (one container for this collector). |
| Azure Key Vault | the Scrape.do key and the database URL, read by the jobs through their managed identity. |
| Scrape.do | fetches each Walmart result page with the store's location (`/plugin/walmart/store`, 10 credits a page) and, since release 1.4.1, Walmart's own filter for the store's fulfillment (`facet=fulfillment_method:Pickup`); robots.txt, the store page, category pages (read only for their navigation) and product pages (read only for identifiers) through its general API (1 credit each); reports the key's balance (`/info`, free). |
| Oxylabs Web API (optional, `--provider oxylabs`) | the same pages: store-scoped pages through `/v1/scrape/walmart` (`store_id`, `fulfillment_type`), the others through `/v1/scrape`; raw HTML only. Billed per result; it has no balance API, so the operator's ceiling (`set-ceiling --provider oxylabs`) is required before anything is sent. |
| Walmart | serves the pages; nothing is sent to Walmart except through the run's provider. |

## Quick start (local)

Requirements: Python 3.12 and [uv](https://docs.astral.sh/uv/), a PostgreSQL database, a Scrape.do key.

```bash
uv sync --frozen
cp .env.example .env            # fill in WALMART_COLLECTOR_DATABASE_URL and the key (never commit .env)
set -a; . ./.env; set +a
uv run walmart-collector db-upgrade
uv run walmart-collector validate-config --check-db --require-credentials
uv run walmart-collector provider-balance       # free: reads the key's remaining credits
# A small, bounded run (labelled "pilot", never published): one category row, one page, at most 10 products
uv run walmart-collector run --store walmart-3891-pickup --categories 4 --max-pages-per-listing 1 \
    --max-products 10 --max-credits 30
uv run walmart-collector status --store walmart-3891-pickup
```

The exports of a run are under `data/runs/<store>/<run>/exports/` (`products.json`, `products.csv`,
`manifest.json`, the supporting log `provenance.json`, ...). A complete validated run is also published:
`data/published/<store>/latest.json` names it.

## Commands

`validate-config`, `db-upgrade`, `sync-config`, `run` (`--scheduled` for Azure), `schedule-status`,
`field-dispositions`, `import-detail-captures`, `resume`, `stop`,
`finalize`, `replay` (an earlier run's stored pages read again offline), `publish`, `status`, `export`,
`validate-export`, `provider-balance`, `set-ceiling`, `set-budget`, `coverage-report`, `release-hold`,
`schedule-info`, `ops`. Every command writes JSON log lines and exits with a code that
says how it ended (0 done, 2 configuration, 3 credentials, 4 credits, 5 site refusal, 6 rejected,
7 store or source checks, 8 held, 9 busy, 75 interrupted and resumable). See [docs/CLI.md](docs/CLI.md).

## Documentation

* [docs/CLI.md](docs/CLI.md): every command, its options, exit codes and log format.
* [docs/OPERATIONS.md](docs/OPERATIONS.md): setup, operation, monitoring, backup, maintenance, recovery,
  adding stores and categories, replacing the Scrape.do key.
* [docs/AZURE.md](docs/AZURE.md): the Azure resources, deployment, secrets and managed identity, the
  twice-weekly schedule and daylight-saving time, overlap, timeouts and retries.
* [docs/AZURE_VM.md](docs/AZURE_VM.md): the smallest test on one Linux VM (size checked against measured
  use, permissions without subscription-wide Owner, runtime limits, deallocation and cleanup).
* [docs/EDITIONS.md](docs/EDITIONS.md): the two editions, what differs between them, their isolation, how
  they are built from one revision and installed.
* [docs/VERIFICATION.md](docs/VERIFICATION.md): what was checked, and how (offline, synthetic, live,
  Azure), with the results.

## What releases 1.6.0 to 1.6.6 change

Release 1.6.0 follows the client's clarification for Walmart: `volume_deals_description`, `volume_deals_price`,
`digital_deals_description` and `digital_deals_price` are always `""` in every exported row, whatever path the row
took (fresh, carried, legacy, replayed, re-exported or published), and an export that would break this is refused.
What a page showed stays in the row's provenance and in `offers.json`. It also adds an optional account-wide gate for
Oxylabs, so that several collectors can share one allowance: each submission is reserved before it is sent, and an
unanswered one stays unknown, never free. Release 1.6.1 makes the assembly reuse what earlier reads of a product's own
page established when the run ended before its detail pass, as the pass would have. Release 1.6.2 corrects two
defects the live runs of 2026-11-03 found: a listing whose total moved a little while the site served far fewer
results is now a result-window end and is read through its child categories (it was left "not reconciled"), and a
listing link that serves a category page is recorded as not read, with the listings that page links, instead of
stopping the run and holding the store. Release 1.6.3 corrects three defects the live runs of 2026-11-04 found: a
run with product detail reading off now still uses what earlier reads of a product's own page established (it
exported those products blank); a carried row whose UPC or size is empty now gets them from such a read, naming
that read, and never when the value would clash with another row; and a listing link the site answers with its
own not-found page is recorded `NOT_FOUND` while the run goes on (release 1.6.2 did not recognize that page's
data, called it a challenge, stopped the run and held the store). Release 1.6.4 corrects the defect that stopped
the census of 2026-11-04: a listing whose Pickup grid the page reports empty (0 results) is an empty listing
once the page names the store and Pickup, even when the page also shows an "Available for shipping" carousel
(release 1.6.3 took the reported 0 for a missing total, read the carousel's products as results it could not
show, stopped the run and held the store). Release 1.6.5 corrects the independent source check that
`validate-export --run` and the canary use: it now reads Walmart's flat price strings, the third price layout the
page reader reads (release 1.6.4 reported 21 correct records of the census as mismatches, all from the one page in
that layout). What a run collects and exports is unchanged. Release 1.6.6 makes a refused automatic
publication an alert: a complete validated run that could not be published is logged and recorded as an
`ERROR` (`PUBLICATION_REFUSED`), and its execution, and Azure's retry of it, exits 6 instead of 0 (release 1.6.5
logged a `WARN` and exited 0, so no documented alert fired). What a run collects, checks and exports is
unchanged. See `docs/VERIFICATION.md`.

## What release 1.5.2 changes

Release 1.5.2 corrects the known defects of release 1.5.1 and changes what is exported in two ways: six more brands
read `store_brand` "yes" on the record of their marks (`docs/PRIVATE_LABEL.md`), and two title forms give a fuller
size. Everything else is in the evidence files. `provenance.json`, `record_map.json` and `field_dispositions.json` now
agree on each value's capture, place in the response, hash, observation time, product and revision, also for a value
reused from an earlier read and for a carried row. Only a page that was read can call a field absent from the source,
and `blocked` and `request_failed` are separate classes. See `docs/VERIFICATION.md`.

## What release 1.5.1 changes

Release 1.5.1 corrects what the live campaign of 2026-10-31 showed in release 1.5.0, and changes what is collected,
so nothing that campaign observed through 1.5.0 is attributed to it. `weight` keeps a multipack the title states
outside the size segments: "(2 pack) Pure Balance ... Dry Dog Food, 16 lbs" gives "2 pack, 16 lbs" (1.5.0 gave
"16 lbs", while the displayed price is for both bags). A measure in inches, what a product bears ("Holds Up to 300
lbs") and a strength beside what the package holds ("1200 mg, 14 Count") are no longer read as the size. `store_brand`
finds a Walmart brand after a bracketed multipack and in two wordings seen on the pages ("Organic Marketside",
"Children's Equate"). A pilot's page budget no longer stops products whose page is already saved: they are reused
first, at no request. Of 1,470 authentic titles 43 change `weight`; docs/VERIFICATION.md shows where.

## What release 1.5.0 changes

Every exported product says why its UPC and size are filled or empty (`field_dispositions.json` and `.csv`). A
product missing either gets its own page read once, and production has no budget for that. Scheduled occurrences
keep their identity until they have been run (`schedule-status`). Follow-ups run in parallel with the workers. A
local price needs Walmart named as the seller. docs/OPERATIONS.md (Product detail path) has the rules, and
docs/VERIFICATION.md what shows them.

## Collection rules (release 1.4.1)

* Exactly the 22 fields, in order, all strings, `""` when missing; `gupc` and `unit_price` always empty;
  `store_logo` is the logo image the store page's header shows (1.2.1).
* `upc` only when Walmart states one (leading zeros kept), never made from Walmart's item id: the result
  pages do not show it, so each exported product's own page is read once (1 credit, general API; the
  outcome is recorded per product: extracted, reused with its original time, absent, blocked, failed, not
  attempted with the reason); product and image URLs as Walmart gives them.
* `weight`: the size the title writes, unchanged (its trailing size segments, else one size group or one
  quantity with a unit inside the title); several separate expressions, dimensions and "Size 4" give none.
  A size segment ends where the product's description begins (release 1.3.1): "3 lb Bag - Naturally
  Ripened Citrus Fruit" gives "3 lb Bag", "84 Loads Liquid Laundry Detergent, 100.8 fl oz" gives "84 Loads,
  100.8 fl oz"; its package stays ("8 oz Clam Shell", "13 lb. Bag"); "10g Protein" is not a size. 1.3.0
  exported 10 of its 633 rows with such text in `weight`. Since release 1.5.1 a multipack the title states
  elsewhere stays beside the size ("2 pack, 16 lbs", never multiplied), and inches, a load rating and a
  strength beside a package size are not read as the size.
* A product with approximate or estimated wording is excluded as a whole (`APPROX_WEIGHT`), even when no
  size reached `weight`: a size written as approximate ("2.25 lbs/Bag Est.", "approx. 1 lb"), or a price
  stated as an estimate ("each (est.)" next to the price of a product sold by the piece and charged by
  weight; release 1.4.0). The wording, its field and path in Walmart's data and the whole value are logged;
  within a run, such wording on any of a product's tiles excludes it.
* Being sold or charged by weight, or a "/lb" price per measure, excludes nothing (release 1.4.0; release
  1.3.1 excluded every weight-priced product, `records.exclude_relative_price_items: true` restores that).
  Such a product is kept with its displayed prices and flagged `RELATIVE_PRICE` and `SOLD_BY_WEIGHT`
  (Walmart's sales unit WEIGHT or EACH_WEIGHT, a `SOLD_BY_WEIGHT` price line or a `finalCostByWeight` code
  says so); without a size in its title, its weight is the one stated after its price ("$0.25 / 0.14lb"
  gives `0.14lb`). Release 1.3.0 exported 31 products priced "each (est.)" with the estimate as a fixed price.
* Prices as displayed (`regular_price`, `sale_price` with its struck-through price); `ppm` exactly as
  displayed, never calculated; volume and digital deals kept apart with their whole wording and
  conditions; no calculated promotion price; Walmart Cash never an immediate reduction.
* Store assortment, availability and the local price are decided apart: a price only with a Pickup line of
  store 3891; a Delivery line of the store is the store's product without a Pickup price; out of stock with
  no line for the store is the store's product only when an earlier run, or an earlier tile of the same run,
  verified it there (then without a price), otherwise it is recorded as unresolved, not exported.
  Marketplace and shipping-only offers never give a price. Verified store products are kept indefinitely
  (no age limit), carried forward with their own dates when a run does not observe them.
* A run records each product once, with the latest state its result tiles showed (release 1.3.1; 1.3.0 kept
  the first tile). Earlier states stay in the supporting log (`earlier_in_run`, with page and time).
* A listing is complete only when what its result grid placed balances the total it reports exactly, at its
  last page and with a stable total (release 1.3.1; no tolerance: the coverage ratio is fixed at 1.0; a
  count above the total is an overcount, never complete); the site's result window, a repeated page or an empty page for another
  store is never an end, and a listing whose pages run out first is "accessible pages exhausted; coverage
  incomplete". A listing larger than the window is read through the child categories its own
  "Departments" facet names, as deep as those facets go (release 1.4.0: no depth limit unless one is set
  for a bounded run). `coverage-report` reconciles every scope unit (1.3.0), with the filter each result
  page's grid states (`grid_fulfillment_filter`, release 1.4.1: Walmart's Pickup grid, or the store's
  unfiltered grid, whose reported total counts out-of-stock and shipping-only items too).
* Follow-ups (1.3.0): a product seen only in sponsored placements, and a variant sibling a tile names with
  its own item and link, are read on their own product page in the store's context and added only when
  that page identifies the item, is shown for the store and files it under the listing's category; every
  outcome (included, excluded, inaccessible, duplicate, not attempted) is recorded with its reason. A
  sponsored label alone neither includes nor excludes; a label such as "More sizes" is never followed. A
  variant seen only as a sponsored tile is read once, by the sponsored follow-up, or by the variant
  follow-up when that one is off (release 1.4.1). A run stopped before its follow-ups finish records the
  outcomes of the candidates they reached (docs/OPERATIONS.md).
* Parallel workers (1.3.0, default 1): one run's listing tasks are leased from the database queue with
  fencing, so a worker that lost its lease never writes again, and a page already collected is never
  requested again after a stop or a restart.
* Spending: every request is reserved against the provider's ceiling and the task's money budget in the
  database before it is sent; nothing is sent to Oxylabs without an operator's ceiling.
* Every page is checked: store 3891 and Pickup from Walmart's own page data (and the store the provider
  says it reflects). A refusal, a challenge, a page priced for another store or fulfillment, or a page
  without the content it must have stops the run and holds the store until an operator releases it; an
  abnormal drop in a category's yield against the store's last complete run (never a bounded run; for a
  network run, a network run) rejects the run. Retained products
  (carried forward) are published but never counted as yield: a category or a run whose published products
  are more than half retained is rejected (release 1.4.0).
* Editions (release 1.4.0): a run, a resumed run or a balance request for a provider the edition does not
  list is refused before any request; no run falls back to another provider.
* A partial, failed, bounded or replayed run never replaces the last complete published dataset.
* Integrity (G13): every page a run stored must match its recorded hash. A product page the provider never
  brought (it failed after its retries, so nothing is stored) is that product's UPC outcome
  (`request_failed`), not an integrity failure, unless an observation or a record names it as a source
  (release 1.4.1; release 1.4.0 rejected a complete run for one such page).
