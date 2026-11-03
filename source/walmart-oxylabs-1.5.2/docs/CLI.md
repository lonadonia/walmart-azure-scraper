# walmart-collector: command reference

```
walmart-collector [--config FILE] [--pretty] <command> [options]
```

`--config` defaults to `$WALMART_COLLECTOR_CONFIG`, else `config/collector.yaml`. Every command reads the
database from `WALMART_COLLECTOR_DATABASE_URL` (except `validate-config` without `--check-db`,
`schedule-info`, `validate-export --file` and `ops` itself) and, when it collects, the key of the run's
provider: Scrape.do from `SCRAPEDO_API_KEY` or `SCRAPEDO_API_KEY_FILE`; the Oxylabs **Web API** (release 1.3.0,
a Bearer key) from `OXYLABS_WEB_API_KEY` or `OXYLABS_WEB_API_KEY_FILE`. The Oxylabs Classic Web Scraper API
(an API username and password) is not supported: its credentials are a different product, and a Web API key
is never used as one. Every command but `db-upgrade` refuses to work on a database whose schema is not
current (exit 2).

## Output

Standard output carries one JSON object per line (Azure sends it to Log Analytics):

```json
{"ts": "2026-10-21T17:56:13.204Z", "level": "INFO", "event": "PAGE_COLLECTED", "collector": "walmart-azure-headless",
 "run_id": "01M5FSNW8AY1X8Y393KQ3M9S4M", "message": "Diapering › Diapering: result page 1", "data": {"products": 50, ...}}
```

`level` is `INFO`, `WARN` or `ERROR`; `event` is a stable code (below). The last line of a command is
`{"event": "RESULT", "command": ..., "exit_code": ..., "result": {...}}`; `--pretty` prints the result
indented instead of that line. A key value is never written: keys appear only as a 6-character fingerprint
(`…32d333`). `WALMART_COLLECTOR_LOG_LEVEL` (`DEBUG`, `INFO`, `WARN`, `ERROR`) filters the lines.

## Exit codes

| Code | Meaning | Typical next step |
|---|---|---|
| 0 | Done: the run validated (or published), a bounded pilot collected what its limits allowed, or there was nothing due | none |
| 1 | Unexpected error (logged as `UNEXPECTED` with its type) | read the log; resume if a run was interrupted |
| 2 | Configuration: invalid file, missing database URL, schema not current, unknown store or run; a provider the edition does not list (`COMMAND_REFUSED`, release 1.4.0: nothing is sent) | fix the configuration; `db-upgrade`; run the edition of that provider (EDITIONS.md) |
| 3 | Credentials: no key for the run's provider, or the provider refused it | set or replace the key (OPERATIONS.md) |
| 4 | Credits: the key's credits, the credit ceiling or a credit budget ran out; or the next request could cross a provider's spending ceiling or the task's money budget (`SPENDING_CEILING`, also when no Oxylabs ceiling is set) | add credits or raise the budget; after `SPENDING_CEILING` the run stays interrupted: raise the ceiling (`set-ceiling`, `set-budget`) and `resume` it |
| 5 | Site refusal: Walmart refused access (HTTP 403/429, challenge) | the store is held; investigate, then `release-hold` |
| 6 | Rejected: the run's checks rejected it, or an export did not verify | read `status --run`; nothing was published |
| 7 | Store or source checks failed: a page was not for store/Pickup, or the canary's records differ from the page | the store is held; investigate, then `release-hold` |
| 8 | Held: the store's collection is held after an earlier stop | `status` shows why; `release-hold` |
| 9 | Busy: another execution holds the store, or an unfinished run must be resumed or finalized first | wait, or `resume` / `finalize` |
| 75 | Interrupted, resumable: a termination signal (job timeout or stop), or a provider failure that persisted | `resume` (or the next scheduled occurrence closes it) |

## Commands

### validate-config [--require-credentials] [--check-db]
Loads `collector.yaml` and the files it names (settings, stores, category CSV, private-label brands) and
prints the stores, categories, limits, schedule (with the UTC cron expression and the next local start),
the provider, workers and follow-ups of each store, canary, historical and publication settings, and whether
the database URL and each provider's key are set (a key only as a fingerprint). `--require-credentials`
exits 3 without the key of a provider an enabled store uses; `--check-db` connects and compares the schema
revision with the package's (exit 2 when not current).

### db-upgrade
Creates or upgrades the schema (Alembic migrations shipped in the package), in one transaction.

### sync-config
Loads `stores.yaml` and the category CSV into the database (rows no longer in the CSV are disabled, never
deleted). `run` does this by itself.

### run --store KEY [--scheduled] [--categories ROWS] [limits]
Creates a run of one store and collects it in this execution. Without limits it collects every configured
category row and every subcategory listing and result page. Options that narrow the run (it is then
labelled **pilot**, exported, never published; from release 1.3.1 the product-page budgets
`--pilot-detail-pages`, `--pilot-no-detail` and `--follow-up-pages` count too, as do `follow_up.max_pages`, `detail.max_per_run` and a
follow-up or detail reading switched off in the configuration):

| Option | Limit |
|---|---|
| `--categories 4,7` | CSV rows (counted from 0) instead of the configured ones |
| `--max-products N` | verified products in this run |
| `--max-products-per-category N` | verified products per category row |
| `--max-pages-per-listing N` | result pages read per listing |
| `--max-subcategories-per-category N` | subcategory listings read per category page |
| `--subcategory ROW:LISTING` | narrow a category row to one subcategory listing its category page names, by path or URL (repeatable), e.g. `0:/browse/food/fresh-fruits/976759_976793_9756351` |
| `--pilot-detail-pages N` | at most N product pages read for missing fields, once the listings have named every product, in the store's queue order (never-read first). What an earlier read established is reused first and counts against nothing (release 1.5.1). The rest stay empty with the disposition `budget_deadline_interruption` and stay queued. A pilot's budget only: production has none |
| `--pilot-no-detail` | read no product page for missing fields in this pilot (disposition `not_attempted`; not a statement about the source) |
| `--follow-up-pages N` | at most N product pages per follow-up kind (below); the rest are recorded as not attempted and stay pending in the store's follow-up queue |

Budgets, not scope limits (the run is not a pilot; one that reaches its budget ends incomplete: a
`partial` dataset, never published):

| Option | Budget |
|---|---|
| `--max-credits N` | provider units this run may spend (Scrape.do credits; Oxylabs results) |
| `--max-minutes N` | active collection time |

Options that do not bound the run:

| Option | Meaning |
|---|---|
| `--provider scrapedo\|oxylabs` | the run's page provider (default: the configuration, `scrapedo`). One provider per run: a change of provider is another run, with its own segments. `oxylabs` uses the Web API: `POST /v1/scrape/walmart` with the store's `store_id` and `fulfillment_type` for store-scoped pages, `POST /v1/scrape` for robots.txt, the store page and category pages; raw HTML only (no parsed or AI output). Nothing is sent without an Oxylabs ceiling (`set-ceiling --provider oxylabs`) |
| `--workers N` | parallel workers of this execution (1 to 8; default: the configuration, 1). Each worker leases its own listing tasks from the run's queue, opens its own provider session and checks the store on its own pages; `max_in_flight` and `min_interval_s` bound the process's requests |

`--pdp-sample` (release 1.4.1 and earlier, used with 0 for the capped demonstrations) is refused since release 1.5.0,
and `detail.max_per_run: 0` is refused in the configuration file: the zero-detail demonstration setting is gone
from production behaviour.

**Follow-ups (release 1.3.0).** After every listing, follow-up tasks (since release 1.5.0 one per kind and worker
of the run, each with its own share of the candidates) read product pages in the store's
context: (a) products the run saw **only in sponsored placements**, and (b) the **variant siblings** that a
result tile names (an option with its own item and link; a label such as "More sizes" is never followed)
without showing them as their own tile. A product is added only when its own page identifies the item, is
shown for the store and files it under the listing's category; each candidate's outcome is an event
(`FOLLOW_UP_INCLUDED`, `_EXCLUDED`, `_INACCESSIBLE`, `_DUPLICATE`, `_NOT_ATTEMPTED`) with its reason and
evidence. A sponsored label alone neither includes nor excludes a product. After
`detail.pause_after_failures` consecutive failed pages the follow-ups pause (`FOLLOW_UP_PAUSED`) and the rest
are not attempted. `follow_up.seeds` in the configuration names items of an earlier report to read first.

**Follow-up queue (release 1.3.1).** Every candidate a run names is kept in the store's follow-up queue
across runs (`follow-ups`). A run reads the configured seeds first, then the candidates no run has read to a
decision, the longest-waiting first (including those that earlier runs of the same lineage left pending on a
listing this run reads), then those whose page failed before. Included, duplicate and excluded resolve a
candidate; not attempted and inaccessible keep it pending, so a page budget, a pause or a failed page never
drops one for good. Options named by a repeated tile of a product, or by a sponsored tile, are candidates
too (kept as `tile_options` observations, never records).

At the end the run is finalized: a limit, a credit stop or an operator's stop leads to the checks and the
export of what was collected; a transient provider failure is resumed in the same execution up to
`max_auto_resumes` times. A complete validated run is published (`published/<store>/latest.json`).

`--scheduled` is the Azure job's form: it takes the settings from the configuration only and does nothing
twice for an occurrence. Since release 1.5.0 every scheduled start that has passed has a row in the store's
occurrence ledger (`schedule_occurrences`), whether or not a firing happened at its time: an occurrence that
could not start because of a hold, a closed window, a manual run or the previous run stays waiting with the
reason and starts later, oldest first, one at a time. It is never dropped. An occurrence still waiting at the
next occurrence's start is recorded as past its deadline; queuing does not satisfy the cadence, and
`schedule-status` states the capacity gap. A configuration that narrows the scheduled scope (limits, page
budgets, follow-ups or product pages switched off) is refused: the required scope is not a setting to trade
for time. The log says what each firing decided: `SCHEDULE_OFF`, `NOT_DUE`, `COLLECTION_HELD`,
`OCCURRENCE_WAITING`, `OCCURRENCE_DONE`, `OCCURRENCE_CONTINUED`, `OCCURRENCE_DEFERRED`, `RUN_SUPERSEDED`,
`MANUAL_RUN_OPEN`, `STORE_BUSY`, or `RUN_CREATED`.

### resume (--run ID | --store KEY) [--workers N]
Continues an interrupted run from its checkpoints (pages already collected are not requested again), with
the run's own provider, and `--workers N` workers in this execution. Refused while the store is held, and
while another execution collects the store (exit 9). An interrupted replay resumes as a replay: from its
source run's stored pages, with no key and no request, and it is never published (release 1.5.2).

### replay --run ID
Reads an earlier LIVE run's stored pages again with this release's code, offline: a new run of mode
`REPLAY` through the normal pipeline (store check, listings, records, checks, exports) with the source
run's plan and limits. Nothing is requested and no key is needed: robots.txt, the store page, result pages
and product pages are served from the source run's storage with their original request times, so every
record keeps the source's observation time and crawl date. A page the source never requested is not
fetched (the listing or product says `NOT_IN_SOURCE`); every product page the source stored is read again.
Earlier verified products and UPCs count only when observed before the source run started, and a later run
of the store counts a replayed run through its replay. A run is replayed once; a replay is never published
and never fresh contest evidence (G14). A replay has the lineage of the run whose pages it reads (see
`attest-lineage`) and neither notes nor reads the follow-up queue. Its exports say what it is: every row
of its record map and supporting log is `replayed`, `observed_by_run` names the source run (whose time and
stored page it is) and `read_again_by_run` the replay; its manifest counts `replayed_record_count`, never
`fresh_record_count` (release 1.3.1 labelled replayed rows as fresh observations of the replay run). In its
supporting log, the UPC outcomes are counted as `upc_outcomes_of_replayed_exported`. Each product page the
source run requested names that run and the replay (`upc_detail.observed_by_run`, `read_again_by_run`),
never `fresh`. A row a later run carries from a replay names the same two runs (`observed_by_run`, the
fields' `source_run`, `read_again_by_run`, origin `read_again`), never `fetched_detail`. Its log names the source run's stored pages too: the store check (`STORE_SELECTED`) and the
closed session's traffic (`PROVIDER_TRAFFIC`) say the pages were read again and that no request was made,
and each product page's event (`PRODUCT_DETAIL_READ`) names `observed_by_run` and `read_again_by_run`
instead of `fresh` (release 1.3.1 logged "requests of the closed Oxylabs Web API session" and `fresh: true`
for them).
Exit codes as for `run`.

### stop (--run ID | --store KEY) [--reason TEXT]
Asks for collection to stop. A running execution stops at its next checkpoint and finalizes; for a run
that no execution is collecting, run `finalize`.

### finalize (--run ID | --store KEY)
Checks and exports what an unfinished run collected, without any provider request. The result is a
partial (or pilot) dataset, kept under the run and never published.

### publish --run ID [--accept-warnings REASON]
Publishes a complete validated run (normally automatic). A run with WARN findings needs a reason; a FAIL
can never be published; the published pointer moves only after every export file is verified again.

### status [--store KEY] [--run ID] [--limit N]
The configured stores: whether held (and why), the last runs (status, dataset label, stop reason, record
counts, canary, historical observations, whether an execution is collecting it), the published dataset,
and the provider ledger (credits recorded, last balance reading). With `--run`: that run, its statistics
from durable observations (requests and credits from the provider ledger, products from the observations,
pages; release 1.3.1) and its export files. A collection segment that a killed process left open is
reported as abandoned, with its last heartbeat, its last durable observation and the bounds of its end
(`SEGMENT_ABANDONED`); no end time is invented and its recorded values are never changed.

### export (--run ID | --store KEY) --out DIR
Verifies a run's export files against its manifest and copies them to `DIR` (with `--store`, the store's
published dataset): `products.json` / `.csv` (the observed and carried-forward products),
`products_fresh.json` / `.csv` (what the run observed itself), `record_map.json` (each row's run, time,
code revision, stored page and hash, store checks and field sources), memberships, offers, the supporting
log, the validation report and the manifest (release 1.2.0 runs; earlier runs have the files their
manifest lists).

### validate-export (--file products.json | --run ID)
The 22-field contract of a products file. For a run, also: the manifest and every export file verified
from storage, and every exported record compared with the run's stored pages, read independently of the
parser (title, URL, image, prices, PPM). No provider request. Exit 6 on any problem.
A record exported without a local price (a verified store product the page shows with no Pickup line for
the store) is verified on its other fields (`verified_without_local_price`); empty prices where the page has
the store's Pickup line are a mismatch.

### provider-balance [--provider scrapedo|oxylabs]
Scrape.do: reads the key's remaining credits from `/info` (free, no page requested) and records it.
Oxylabs: the Web API documents no balance or usage endpoint, so nothing is requested: the result is the
operator's ceiling, the room left under it, the task's money budget and what the ledger recorded.

### set-ceiling [--provider scrapedo|oxylabs] ... --basis TEXT
A provider's spending ceiling across every run and process from now on, recorded with its basis. Every
request is reserved against it in the database (under a lock) **before** it is sent, so no request may
cross it; a run that reaches it stops with `SPENDING_CEILING` (exit 4) and stays resumable.

| Provider | Options |
|---|---|
| `scrapedo` | `--credits N` total credits; `--usd-per-credit X` the plan's price of one credit (0 for the free plan), used by the task's money budget |
| `oxylabs` | `--submissions N` total submissions (every attempt counts); `--usd X` total US dollars; `--minutes M` from the first submission; `--usd-per-result X` the rate reserved for each submission (default: the highest documented non-AI rate, $0.0015). A submission whose charge is not known (a timeout, a non-2xx answer other than the documented uncharged one) keeps its reservation |

### set-budget --usd X --basis TEXT
The task's money budget across every provider from now on: each request's cost (Scrape.do credits at their
recorded price, Oxylabs submissions at their rate) is reserved against it before the request is sent.

### coverage-report --run ID [--out DIR]
The run's coverage reconciliation, from its own records: one row per scope unit (a CSV row's listing, a
subcategory listing, a child category), with the navigation evidence, the store checks, the filter each
result page's grid states (`grid_fulfillment_filter`, release 1.4.1: `Pickup`, `none` for the store's
unfiltered grid, `not recorded` for a page read before 1.4.1), the reported total and when it was read, pages and fetches, raw and organic placements, distinct identities, duplicates,
sponsored placements and sponsored-only products, variant identities named and not seen as their own tile,
the follow-up outcomes, exclusions by reason, retained unavailable products, the unresolved difference, the
status and the stop reason. No tolerance threshold is applied: a listing is complete only when, at its last
page and with a total that stayed the same, what its result grid placed balances its reported total exactly
(`reconciliation_basis`: organic identities, those plus sponsored-only identities, or tiles whose sponsored
repeats are organic products); a count above the total is an overcount, never complete. Otherwise it says
"accessible pages exhausted; coverage incomplete" (or why it stopped), with the signed difference. With `--out`, writes `coverage_reconciliation_<run>.csv` and `.json` and
`follow_up_outcomes_<run>.csv`. No provider request.

### follow-ups --store KEY [--state pending|resolved|all] [--kind sponsored|variant|detail]
(Since release 1.5.0 the kind `detail` is the queue of products whose missing UPC or size has no outcome yet.)
The store's follow-up queue (release 1.3.1): its counts by kind and state, the pending candidates by their
last outcome, and the candidates (pending ones by default, oldest first) with the listing and tile that
named them, the runs that saw them, the last outcome and its reason, and the product pages read. No provider
request.

### attest-lineage --run ID --reason TEXT --evidence TEXT
From release 1.3.1 every run records where its pages came from (its lineage): `network` (the provider
transports talked to the network), `substituted` (a test or fault-injection harness replaced a transport's
HTTP client, so the pages are synthetic or recorded) or, for a run made before 1.3.1, `unrecorded`. A run
takes earlier observations only from runs of its own lineage, a carried record whose source run has another
lineage fails G13, and a run whose lineage is not `network` is published only to a target configured as a
test target (`publication.test_target`). A LIVE run made before 1.3.1 counts as `network` only after an
operator records this attestation with its reason and the evidence it rests on (audit log
`lineage_attested`, event `LINEAGE_ATTESTED`). Refused for a run that records its own lineage, a run that is
not LIVE, a run with a segment of another lineage, and without a reason or evidence. No provider request.

### release-hold --store KEY --reason TEXT
Lets a held store collect again (recorded with the reason and the previous hold).

### schedule-info --store KEY
The store's schedule and the UTC cron expressions for its Azure job: `cron_utc` (the local start, for
standard and daylight time) and, when `continue_unfinished` is on, `cron_utc_with_continuation`
(`*/30 * * * *`, the expression to deploy: AZURE.md, Schedule, continuation and daylight-saving time).

### schedule-status --store KEY
Reads only. Each occurrence with its state (`due`, `deferred`, `running`, `completed`, `superseded`), its
scheduled start, how late it started, the run it became, its deadline (the next start) and why it waited; the
backlog, the oldest wait, the missed deadlines and runs that ended after the next start; and `capacity`:
`GAP` (runs do not fit the cadence: the required scope and cadence stand, so more capacity is needed),
`UNKNOWN` (no scheduled run has collected its full scope) or `NO GAP MEASURED`.

### field-dispositions --run ID [--csv FILE]
Reads only. Why each exported product's `upc` and `weight` are filled or empty: `present_in_listing`,
`recovered_from_saved_detail`, `fetched_detail`, `not_attempted`, `blocked`, `request_failed`, `parse_failure`,
`identity_mismatch`, `absent_in_source`, `budget_deadline_interruption`, `unresolved_conflict`. Every run also
exports the same table as `field_dispositions.json` and `field_dispositions.csv`, with the capture, its place in
the response, its hash, its time, the product and the revision of the read. `provenance.json` and
`record_map.json` state the same facts (release 1.5.2). Until release 1.5.1 `blocked` and `request_failed` were one
class, `inaccessible_challenged`.

### import-detail-captures --store KEY --index FILE
Loads saved product pages into `detail_observations`, so later runs reuse what they state (within
`detail.reuse_days` of the page's original time) instead of paying for it again. Requests nothing.
OPERATIONS.md (Product detail path) has the index format.

### ops
Runs the command written in `WALMART_COLLECTOR_COMMAND` (default `status`), e.g.
`WALMART_COLLECTOR_COMMAND="resume --store walmart-3891-pickup"`. This is the entry point of the Azure
operations job (AZURE.md, Operations).

## Events

Collection: `RUN_CREATED`, `RUN_EXECUTING`, `PROVIDER_BALANCE`, `PROVIDER_SESSION_OPENED`, `STORE_SELECTED`,
`STORE_VERIFIED`, `WORKERS_STARTED`, `SUBCATEGORIES_FOUND`, `PAGE_COLLECTED`, `LISTING_PARTITIONED`,
`CANARY_PASSED` / `CANARY_FAILED`, `NODE_DONE` / `NODE_INCOMPLETE` / `NODE_CAPPED`, `FOLLOW_UP_INCLUDED` /
`FOLLOW_UP_EXCLUDED` / `FOLLOW_UP_INACCESSIBLE` / `FOLLOW_UP_DUPLICATE` / `FOLLOW_UP_NOT_ATTEMPTED`,
`FOLLOW_UP_PAUSED`, `FOLLOW_UP_DONE`, `PRODUCT_DETAIL_PAUSED`, `REPLAY_SESSION_OPENED`, `RUN_LIMIT_REACHED`,
`RUN_STOPPED`, `RUN_PAUSED`, `PROVIDER_SESSION_CLOSED`, `PROVIDER_TRAFFIC`, `COLLECTION_CLOSED`.
Results: `HISTORICAL_OBSERVATIONS`, `RECORDS_ASSEMBLED`, `CHECKS_COMPLETE`, `EXPORTS_STAGED`,
`PARTIAL_EXPORT`, `RUN_VALIDATED` / `RUN_REJECTED`, `RUN_PUBLISHED` / `PUBLICATION_REFUSED`,
`RUN_FINISHED` (with the exit code and the run's summary). Control: `SIGNAL_RECEIVED`, `RUN_INTERRUPTED`,
`TERMINATED`, `RUN_AUTO_RESUMED`, `RUN_RECOVERED`, `SEGMENT_ABANDONED`, `COLLECTION_HELD`, `HOLD_RELEASED`,
`STORE_BUSY`, `LINEAGE_ATTESTED`, `COMMAND_REFUSED`, `CONFIG_INVALID`, `UNEXPECTED`.
