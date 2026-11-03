# Cost and runtime report: Walmart release 1.5.2

Sections 2 to 11 are the report of release 1.5.1, carried: no provider request has been made since, so their measurements still stand and belong to the releases they name. Sections 1 and 6b are new. It was first written offline by `cost_report_151.py` (in [`evidence/reconciliation/1.5.1/cost_model_151/`](../evidence/reconciliation/1.5.1/cost_model_151/)) from the campaign's ledger and measures and the cost model: the tables are computed from those files, and the text quotes figures from the same files, from [`evidence/live/plan/CAMPAIGN_BUDGET.json`](../evidence/live/plan/CAMPAIGN_BUDGET.json) and from the campaign's command log. This report made no request. Store 3891 (3900 Fountain Square Pl, Waukegan, IL 60085), fulfillment PICKUP. Times are UTC.

Three kinds of figure are kept apart: **measured** (ledger rows and stored pages of real runs), **published** (the providers' and Azure's price pages, with the date they were read) and **estimate** (a model over an assumed scope). Nothing here is an invoice or a quote. A pilot's cost is the cost of that pilot: **no figure in sections 1 to 6 is the cost of a complete production run.** The full store size and the full-run runtime have not been measured.

## 1. What this task used (2026-11-01)

- **Oxylabs Web API: no request.** The ledger stands at 119 of 120 rows, unchanged and not reset ([`evidence/live/plan/CAMPAIGN_BUDGET.json`](../evidence/live/plan/CAMPAIGN_BUDGET.json), byte for byte the 1.5.1 file). One row is left and a session needs at least 3 (robots.txt, store page, one page). Spent in all, as estimates from the collector's ledger, not an invoice: USD 0.1785 at the reserve rate, USD 0.1190 at the published USD 0.0010.
- **Balance:** not verified. The Web API documents no balance endpoint for a Bearer key, and the owner's dashboard was not opened.
- **Scrape.do: no request.** The free `/info` reading at 2026-11-01T18:23:14Z showed 10 of 1,000 monthly credits left. The final-version demonstration needs about 213 credits (canary about 21, a 19-page run about 192), so it stays BLOCKED.
- **Oxylabs Classic:** no request, no credential. The campaign stays proposed and unapproved ([`classic-probe/oxylabs-classic-probe/CLASSIC_TEST_PLAN.md`](../classic-probe/oxylabs-classic-probe/CLASSIC_TEST_PLAN.md)).
- **Azure:** Hamza's test VM ran the container and recovery tests. It was already running, and its power state was not changed: USD 0.113 an hour at the retail price read on 2026-10-28, while it runs. No Azure bill was read.
- **No purchase, top-up, new account, subscription change, overage or schedule activation. Nothing was charged to the client.**

## 2. Measured per stage (2026-10-31, this PC, isolated PostgreSQL)

Source: [`evidence/live/campaign/summary/CAMPAIGN_MEASURES_BY_STAGE.csv`](../evidence/live/campaign/summary/CAMPAIGN_MEASURES_BY_STAGE.csv). *Rows* are all of a run's ledger rows (result pages, product pages, robots.txt, store page, abandoned and free ones). *Valid fresh* are the products the run observed itself. The money columns are an estimate at the rate named. S1 to S5 ran release 1.5.0 (commit 7b6f325); S6 and S7 ran release 1.5.1 (commit 488a033).

| Stage | Release | Purpose | Rows | Listing pages | Product pages (detail + follow-up) | Valid fresh | Valid per listing page | Rows per 1,000 valid | USD per 1,000 valid at 0.0010 / 0.0015 | Active s | End |
|---|---|---|---:|---:|---:|---:|---:|---:|---|---:|---|
| S1 | 1.5.0 | canary | 4 | 1 | 1 + 0 | 35 | 35.0 | 114.3 | 0.114 / 0.171 | 101.6 | completed its steps |
| S2 | 1.5.0 | targeted product pages | 28 | 6 | 10 + 10 | 203 | 33.8 | 137.9 | 0.138 / 0.207 | 369.0 | completed its steps |
| S3 | 1.5.0 | one category, several pages | 9 | 4 | 3 + 0 | 116 | 29.0 | 77.6 | 0.078 / 0.116 | 101.2 | completed its steps |
| S4 | 1.5.0 | B3's scope, kill and resume, 2 workers | 39 | 19 | 10 + 0 | 677 | 35.6 | 57.6 | 0.058 / 0.086 | 254.2 | completed its steps |
| S5b_serial | 1.5.0 | 1 worker | 4 | 2 | 0 + 0 | 80 | 40.0 | 50.0 | 0.05 / 0.075 | 42.4 | RUN_CREDIT_LIMIT |
| S5b_parallel | 1.5.0 | 2 workers | 6 | 2 | 0 + 0 | 80 | 40.0 | 75.0 | 0.075 / 0.113 | 39.7 | RUN_CREDIT_LIMIT |
| S5a | 1.5.0 | repeat of S4's first pages, about 40 min later | 4 | 2 | 0 + 0 | 67 | 33.5 | 59.7 | 0.06 / 0.09 | 53.8 | completed its steps |
| S6 | 1.5.1 | the demonstration on 1.5.1, kill and resume | 22 | 15 | 1 + 0 | 580 | 38.7 | 37.9 | 0.038 / 0.057 | 300.5 | SPENDING_CEILING |
| S7 | 1.5.1 | repeat of S6's first page, about 39 min later | 3 | 1 | 0 + 0 | 32 | 32.0 | 93.8 | 0.094 / 0.141 | 83.3 | SPENDING_CEILING |

Every run's status is `rejected` by the coverage gate (G3): each read capped pages. That is correct. They were pilots and none replaced a dataset. The figures differ by stage because the stages did different things: they are not comparable as rates of a full run.

## 3. Answer times (measured)

Seconds per answered request, all stages, ledger `elapsed_ms`:

| Purpose | n | Median | Mean | p90 | Max |
|---|---:|---:|---:|---:|---:|
| listing | 52 | 10.62 | 13.15 | 19.09 | 67.23 |
| product_detail | 25 | 9.36 | 14.09 | 34.39 | 73.06 |
| product_page | 10 | 7.88 | 14.31 | 69.41 | 69.41 |
| robots | 14 | 2.59 | 3.04 | 5.88 | 6.14 |
| store_page | 14 | 7.19 | 8.4 | 12.28 | 20.39 |

The spread is the provider's: the same kind of page took about 10 s or more than 60 s (S7's one listing page took 67.23 s). A run's time cannot be read from the median alone.

## 4. Product-detail enrichment and refresh policy

Policy as shipped: a run reads a product's own page when its UPC or size is blank. An earlier read (fetched or imported) is reused when it was observed within `detail.reuse_days` (30 days), with its original time, run and revision, and is never described as newly fetched. A pilot states its budget on the command line: `--pilot-detail-pages N` (at least 1), or `--pilot-no-detail`, which reads no product page and records those blanks as `not_attempted` (S5b used it). The configuration has no zero-detail setting any more (`detail.max_per_run: 0` is refused, `--pilot-detail-pages 0` too, and `--pdp-sample` was removed), and a scheduled run refuses any pilot budget. Since 1.5.1 a page budget never stops reuse.

| Stage | UPC outcomes of its fresh products | Weight outcomes of its fresh products |
|---|---|---|
| S1 | fetched_detail 1; recovered_from_saved_detail 34 | absent_in_source 4; present_in_listing 24; recovered_from_saved_detail 5; unresolved_conflict 2 |
| S2 | budget_deadline_interruption 122; fetched_detail 14; recovered_from_saved_detail 67 | absent_in_source 3; budget_deadline_interruption 22; fetched_detail 1; present_in_listing 169; recovered_from_saved_detail 7; unresolved_conflict 1 |
| S3 | budget_deadline_interruption 94; fetched_detail 3; recovered_from_saved_detail 19 | present_in_listing 116 |
| S4 | budget_deadline_interruption 601; fetched_detail 10; recovered_from_saved_detail 66 | absent_in_source 4; budget_deadline_interruption 25; fetched_detail 1; present_in_listing 637; recovered_from_saved_detail 8; unresolved_conflict 2 |
| S5b_serial | not_attempted 80 | not_attempted 1; present_in_listing 79 |
| S5b_parallel | not_attempted 80 | not_attempted 1; present_in_listing 79 |
| S5a | recovered_from_saved_detail 67 | absent_in_source 5; present_in_listing 50; recovered_from_saved_detail 10; unresolved_conflict 2 |
| S6 | absent_in_source 1; budget_deadline_interruption 226; fetched_detail 1; recovered_from_saved_detail 352 | absent_in_source 3; budget_deadline_interruption 9; present_in_listing 555; recovered_from_saved_detail 12; unresolved_conflict 1 |
| S7 | budget_deadline_interruption 32 | budget_deadline_interruption 6; present_in_listing 26 |

`budget_deadline_interruption` and `not_attempted` mean the page was not read. They do not mean the value is absent from Walmart. S7 stopped at its ceiling before its detail and reuse step, so all its UPCs carry that label.

B3's blanks after offline reprocessing and the campaign's reads (`3_reconciliation/b3_blanks_after_campaign/`):

| Field and state | Products |
|---|---:|
| upc: filled by the campaign | 21 |
| upc: not in any listing page the campaign read | 39 |
| upc: read, no value: absent_in_source | 1 |
| upc: seen by the campaign, its page not read within the budget | 182 |
| weight: filled by the campaign | 2 |
| weight: filled by the listing's own title in a campaign run | 1 |
| weight: not in any listing page the campaign read | 1 |
| weight: read, no value: absent_in_source | 7 |
| weight: read, no value: unresolved_conflict | 3 |
| weight: seen by the campaign, its page not read within the budget | 6 |

So 221 of B3's 662 products still need their own page read for a UPC: about 221 submissions if nothing is reused and no retry is needed, USD 0.22 to 0.33 at the rates above, an estimate. This budget did not reach them.

## 5. Sponsored and variant follow-ups

Of the earlier 41 cases (11 sponsored-only placements and 30 tile-only siblings), 16 are closed live on 2026-10-31 (10 by their own product page in S2, 6 seen as their own organic tile) and 25 stay PENDING, each needing 1 product page; reading them needs about 29 submissions (robots, store, 2 listings and 25 pages), more than the campaign had left. Of the 610 variant identities of the 1.4.1 reconciliation, 199 keep a 1.4.1 decision not re-observed, 167 were named again with that decision carried, and 244 are open.

As shipped, every candidate a run names is read in that run: a sponsored or variant candidate costs one product page per run (unless it is seen as its own organic tile). Since 1.5.0 those pages are shared among the workers. That sharing is covered by offline tests only: no live run has measured it.

## 6. Failures, retries, restarts and concurrency (measured)

- **Provider failure:** one, on stage S6 at 2026-10-31T23:02:20Z: HTTP 500 after 67.7 s on a product page, 0 credits in the ledger; retried once as the documented transient rule allows, answered in 10.2 s. That retry used the stage's last room, so the run stopped at its ceiling. The time and the row are the cost of a transient, even when no credit is charged.
- **Forced kills:** S4 and S6, one each. The kill left 3 reservations in total (2 in S4, 1 in S6) whose billing outcome is unknown: they stay counted. A resume verifies robots.txt and the store page again: **2 more submissions per resumed worker session** (S4 and S6 each paid them). S6 lost no record. Its one request in flight at the kill (page 3 of Shampoo) stays counted, and the resume asked for that page again; no page already answered was asked for again: 15 answered listing fetches of 15 distinct listing URLs. The killed session's segment is abandoned, with no invented end time.
- **Overlap refusals:** exit 9, no request, in both states (another execution running, and an unfinished run not yet resumed). A first attempt during S6 named `--max-credits 2`, below the configuration's minimum of 5: it was refused as an invalid configuration (exit 2) before any check or request, and repeated with 5 ([`evidence/live/campaign/commands.csv`](../evidence/live/campaign/commands.csv), steps 65 and 66).
- **`finalize`:** closes an unfinished run with no request. S6 and S7 used it at their ceilings. A resume would have cost 2 submissions.
- **Serial against parallel through the real pipeline (S5b, release 1.5.0; not repeated on 1.5.1, no budget):** the same 2 first pages and the same 80 products with 0 field differences. Serial: 4 requests, 42.4 s active. Two workers: 6 requests, 39.7 s active: each worker verifies robots.txt and the store page itself. The difference of 2.7 s is smaller than the variation in provider latency, so this says **nothing about throughput at scale**. It does measure the cost of a second worker's session: 2 submissions.

## 6b. Controlled concurrency on the final revision (SYNTHETIC: a local fixture, not a provider)

`tests/integration/test_concurrency_load.py` runs the real collector, its database, queue, locks, pacing and accounting, against a local fixture server, with `LOAD_PAGES=6` listings. It measures the implementation, not a provider: **no figure here is a provider throughput, and none is a full run's runtime.**

| Where | Workers | Peak requests in flight | Products | Requests | Elapsed s | Requests per s | Peak process memory MB |
|---|---:|---:|---:|---:|---:|---:|---:|
| workstation | 1 | 1 | 360 | 381 | 62.9 | 6.06 | 146.0 |
| workstation | 2 | 2 | 360 | 383 | 54.4 | 7.04 | 155.3 |
| workstation | 4 | 2 | 360 | 383 | 51.8 | 7.4 | 158.9 |
| owner VM (2 vCPU, 3.9 GB) | 1 | 1 | 360 | 381 | 44.1 | 8.65 | 145.0 |
| owner VM (2 vCPU, 3.9 GB) | 2 | 2 | 360 | 383 | 30.9 | 12.38 | 148.1 |
| owner VM (2 vCPU, 3.9 GB) | 4 | 2 | 360 | 383 | 31.1 | 12.32 | 151.1 |

With 4 workers 2 stayed idle: the collector's parallelism is per CSV-row task, and the fixture holds 2 such tasks. Every run kept its products with none lost or duplicated, and every request has one ledger row. A run terminated after 320 of 360 products resumed from its checkpoints to 360; the one page in flight at the termination was requested again, as in live S6 ([`evidence/synthetic/1.5.2/load/workstation/`](../evidence/synthetic/1.5.2/load/workstation/) and `7_release_1_5_2/owner_vm/load/`).

## 7. Historical measurements (2026-10-28, carried)

The 1.4.1 campaign's measurements are carried unchanged in [`evidence/reconciliation/1.5.1/cost_model_151/MEASURED_COST_PER_RUN_1_4_1_CARRIED.csv`](../evidence/reconciliation/1.5.1/cost_model_151/MEASURED_COST_PER_RUN_1_4_1_CARRIED.csv) and `THROUGHPUT_1_4_1_CARRIED.csv`. They belong to releases 1.4.0 and 1.4.1 and are the only measurements with up to 4 workers. The per-worker rates the estimates use:

- Oxylabs, requests a minute per worker: result pages 8.1 to 12.1; UPC pages 4.9 to 13.6; follow-up pages 9.8 to 13.9.
- Scrape.do, requests a minute per worker: result pages 3.8 to 8.9; UPC pages 14.0 to 15.0; follow-up pages 8.1 to 15.6.
- Valid fresh products per Pickup result page: 35.2 (Oxylabs runs B2 (1.4.0) and B3 (1.4.1), Pickup grid, no follow-up and no UPC page: valid fresh products per result page read, pooled over the two runs: B2 675/19; B3 662/19; together 1337/38). The campaign's pages above agree in order of magnitude; they were not used to change the model.

## 8. Full scope: estimates, not measurements

**No run has read the full scope, and the store's Pickup assortment has not been counted.** N, the distinct products of store 3891's Pickup assortment in the 11 required CSV rows, is an assumption: 20,000, 40,000 and 80,000, with 120,000 kept only as the historical reference to Walmart's unfiltered online assortment. Two cases (lean, heavy) bracket overlap, variant candidates and sponsored-only products per product; two follow-up policies: *shipped* (every candidate a run names is read in that run) and *reuse* (a design option, **not implemented**: an exclusion is reused for 30 days).

The model is the 1.4.1 model with one change, the one thing release 1.5.0 changed in it: follow-up pages are shared among the workers. Its prices are those read on 2026-10-28. The Oxylabs plan step depends on a rate Oxylabs does not publish for Walmart: USD 0.50, 1.00 or 1.50 per 1,000 results are readings of its price page.

| Scenario | Edition | Units first run | Units later month | Plan, later month | Provider USD a later month | First-run hours (workers) | Later-run hours (workers) | 1.4.1 model: later-run hours (workers) | Fits 72 h on paper | Azure USD a later month |
|---|---|---:|---:|---|---|---|---|---|---|---|
| N20k/lean/shipped | oxylabs | 31,769 results | 123,410 | Basic / Flexible / Flexible (low / central / worst rate) | 100 / 500 / 500 (at the rate alone: 62 / 123 / 185) | 9.5 to 21.9 (4) | 17.0 to 28.8 (1) | 16.3 to 27.8 (1) | yes | 39.03 to 93.55 |
| N20k/lean/shipped | scrapedo | 133,505 credits | 1,002,543 | Pro | 99 | 8.7 to 12.1 (4) | 15.7 to 28.0 (1) | 15.0 to 26.8 (1) | yes | 38.31 to 93.55 |
| N20k/lean/reuse | oxylabs | 31,769 results | 72,175 | Basic / Basic / Flexible (low / central / worst rate) | 100 / 100 / 500 (at the rate alone: 36 / 72 / 108) | 9.5 to 21.9 (4) | 10.0 to 18.9 (1) | 9.7 to 18.4 (1) | yes | 29.32 to 93.55 |
| N20k/lean/reuse | scrapedo | 133,505 credits | 497,479 | Pro | 99 | 8.7 to 12.1 (4) | 9.5 to 16.1 (1) | 9.2 to 15.5 (1) | yes | 26.61 to 93.55 |
| N20k/heavy/shipped | oxylabs | 49,719 results | 281,343 | Flexible / Flexible / Flexible (low / central / worst rate) | 500 / 500 / 500 (at the rate alone: 141 / 281 / 422) | 13.7 to 28.0 (4) | 35.7 to 58.6 (1) | 31.4 to 52.5 (1) | yes | 73.06 to 98.39 |
| N20k/heavy/shipped | scrapedo | 273,493 credits | 2,220,396 | Business | 249 | 12.5 to 19.4 (4) | 32.7 to 59.1 (1) | 28.8 to 51.7 (1) | yes | 73.5 to 98.39 |
| N20k/heavy/reuse | oxylabs | 49,719 results | 169,055 | Basic / Flexible / Flexible (low / central / worst rate) | 100 / 500 / 500 (at the rate alone: 85 / 169 / 254) | 13.7 to 28.0 (4) | 21.6 to 38.6 (1) | 19.4 to 35.5 (1) | yes | 48.65 to 93.59 |
| N20k/heavy/reuse | scrapedo | 273,493 credits | 1,200,135 | Pro | 99 | 12.5 to 19.4 (4) | 20.1 to 34.9 (1) | 18.1 to 31.2 (1) | yes | 45.06 to 93.59 |
| N40k/lean/shipped | oxylabs | 63,515 results | 246,714 | Flexible / Flexible / Flexible (low / central / worst rate) | 500 / 500 / 500 (at the rate alone: 123 / 247 / 370) | 19.1 to 43.7 (4) | 34.0 to 57.5 (1) | 32.6 to 55.5 (1) | yes | 71.98 to 98.56 |
| N40k/lean/shipped | scrapedo | 266,950 credits | 2,004,901 | Business | 249 | 17.4 to 24.3 (4) | 31.4 to 56.0 (1) | 30.1 to 53.6 (1) | yes | 70.52 to 98.56 |
| N40k/lean/reuse | oxylabs | 63,515 results | 144,245 | Basic / Flexible / Flexible (low / central / worst rate) | 100 / 500 / 500 (at the rate alone: 72 / 144 / 216) | 19.1 to 43.7 (4) | 20.1 to 37.7 (1) | 19.4 to 36.8 (1) | yes | 52.57 to 98.56 |
| N40k/lean/reuse | scrapedo | 266,950 credits | 994,756 | Pro | 99 | 17.4 to 24.3 (4) | 18.9 to 32.1 (1) | 18.3 to 31.0 (1) | yes | 47.12 to 98.56 |
| N40k/heavy/shipped | oxylabs | 99,418 results | 562,582 | Flexible / Flexible / Enterprise (low / central / worst rate) | 500 / 500 / 2,500 (at the rate alone: 281 / 563 / 844) | 27.4 to 55.9 (4) | 35.7 to 58.6 (2) | 49.8 to 72.6 (more than 8) | yes | 82.65 to 108.25 |
| N40k/heavy/shipped | scrapedo | 546,894 credits | 4,440,687 | Advanced | 699 | 25.0 to 38.8 (4) | 32.7 to 59.0 (2) | 44.7 to 84.7 (more than 8) | yes | 83.08 to 108.25 |
| N40k/heavy/reuse | oxylabs | 99,418 results | 338,005 | Flexible / Flexible / Flexible (low / central / worst rate) | 500 / 500 / 500 (at the rate alone: 169 / 338 / 507) | 27.4 to 55.9 (4) | 21.6 to 38.6 (2) | 38.8 to 71.0 (1) | yes | 53.44 to 98.65 |
| N40k/heavy/reuse | scrapedo | 546,894 credits | 2,399,992 | Business | 249 | 25.0 to 38.8 (4) | 40.1 to 69.8 (1) | 36.3 to 62.4 (1) | yes | 84.03 to 98.65 |
| N80k/lean/shipped | oxylabs | 127,014 results | 493,331 | Flexible / Flexible / Enterprise (low / central / worst rate) | 500 / 500 / 2,500 (at the rate alone: 247 / 493 / 740) | 38.2 to 87.5 (4) | 34.0 to 57.5 (2) | 50.1 to 73.4 (more than 8) | yes | 81.57 to 108.59 |
| N80k/lean/shipped | scrapedo | 533,848 credits | 4,009,704 | Advanced | 699 | 34.9 to 48.6 (4) | 31.3 to 56.0 (2) | 45.0 to 85.2 (more than 8) | yes | 80.1 to 108.59 |
| N80k/lean/reuse | oxylabs | 127,014 results | 288,393 | Flexible / Flexible / Flexible (low / central / worst rate) | 500 / 500 / 500 (at the rate alone: 144 / 288 / 433) | 38.2 to 87.5 (4) | 20.0 to 37.7 (2) | 30.2 to 52.1 (2) | yes | 62.16 to 108.59 |
| N80k/lean/reuse | scrapedo | 533,848 credits | 1,989,310 | Business | 249 | 34.9 to 48.6 (4) | 37.7 to 64.2 (1) | 36.6 to 62.0 (1) | yes | 88.13 to 108.59 |
| N80k/heavy/shipped | oxylabs | 198,807 results | 1,125,059 | Flexible / Enterprise / Enterprise (low / central / worst rate) | 500 / 2,500 / 2,500 (at the rate alone: 563 / 1125 / 1688) | 54.9 to 111.9 (4) | 35.7 to 58.6 (4) | 99.6 to 145.3 (more than 8) | yes | 101.84 to 127.96 |
| N80k/heavy/shipped | scrapedo | 1,093,695 credits | 8,881,269 | Advanced | 699 | 50.1 to 77.7 (4) | 32.7 to 59.0 (4) | 89.3 to 169.4 (more than 8) | yes | 102.27 to 127.96 |
| N80k/heavy/reuse | oxylabs | 198,807 results | 675,905 | Flexible / Enterprise / Enterprise (low / central / worst rate) | 500 / 2,500 / 2,500 (at the rate alone: 338 / 676 / 1014) | 54.9 to 111.9 (4) | 21.6 to 38.6 (4) | 51.8 to 77.4 (more than 8) | yes | 63.04 to 108.76 |
| N80k/heavy/reuse | scrapedo | 1,093,695 credits | 4,799,879 | Advanced | 699 | 50.1 to 77.7 (4) | 40.1 to 69.8 (2) | 46.6 to 87.5 (more than 8) | yes | 93.6 to 108.76 |
| N120k_historical_reference/lean/shipped | oxylabs | 190,514 results | 739,957 | Flexible / Enterprise / Enterprise (low / central / worst rate) | 500 / 2,500 / 2,500 (at the rate alone: 370 / 740 / 1110) | 57.2 to 131.2 (4) | 25.5 to 43.1 (4) | 75.2 to 110.1 (more than 8) | yes | 86.69 to 128.21 |
| N120k_historical_reference/lean/shipped | scrapedo | 800,747 credits | 6,014,594 | Advanced | 699 | 52.3 to 72.8 (4) | 23.5 to 42.0 (4) | 67.5 to 127.7 (more than 8) | yes | 85.58 to 128.21 |
| N120k_historical_reference/lean/reuse | oxylabs | 190,514 results | 432,533 | Flexible / Flexible / Enterprise (low / central / worst rate) | 500 / 500 / 2,500 (at the rate alone: 216 / 433 / 649) | 57.2 to 131.2 (4) | 30.1 to 56.5 (2) | 38.8 to 62.0 (4) | yes | 99.81 to 128.21 |
| N120k_historical_reference/lean/reuse | scrapedo | 800,747 credits | 2,983,968 | Business | 249 | 52.3 to 72.8 (4) | 28.3 to 48.1 (2) | 35.4 to 64.8 (4) | yes | 91.6 to 128.21 |
| N120k_historical_reference/heavy/shipped | oxylabs | 298,205 results | 1,687,574 | Enterprise / Enterprise / Enterprise (low / central / worst rate) | 2,500 / 2,500 / 2,500 (at the rate alone: 844 / 1688 / 2531) | 41.1 to 83.9 (8) | 26.8 to 44.0 (8) | 149.4 to 217.9 (more than 8) | yes | 87.49 to 128.46 |
| N120k_historical_reference/heavy/shipped | scrapedo | 1,640,577 credits | 13,322,198 | custom quote (above Advanced's 10M credits) | custom quote | 37.5 to 58.3 (8) | 24.5 to 44.3 (8) | 134.0 to 254.1 (more than 8) | yes | 87.81 to 128.46 |
| N120k_historical_reference/heavy/reuse | oxylabs | 298,196 results | 1,013,767 | Flexible / Enterprise / Enterprise (low / central / worst rate) | 500 / 2,500 / 2,500 (at the rate alone: 507 / 1014 / 1521) | 82.3 to 167.8 (4) | 32.3 to 57.9 (4) | 77.7 to 116.1 (more than 8) | yes | 101.13 to 128.46 |
| N120k_historical_reference/heavy/reuse | scrapedo | 1,640,497 credits | 7,199,974 | Advanced | 699 | 75.1 to 116.5 (4) | 30.1 to 52.3 (4) | 69.9 to 131.3 (more than 8) | yes | 95.71 to 128.46 |

The hours assume the per-worker rates of section 7 hold: 8 workers were never run (4 is the most measured), and sharing follow-ups among workers has never been measured live.

## 9. Twice-weekly cadence: capacity

**Status: UNKNOWN, not met and not refuted.** The requirement is the full required scope twice weekly per store. A full run has never been timed, so no measured runtime shows that the cadence is met. On paper, 32 of 32 scenarios now fit the 72 hours between the Tuesday and Friday occurrences with 1 to 8 workers, where the 1.4.1 model had many beyond it because the follow-up stage ran one worker per kind. That is an estimate resting on rates not measured for this design.

What the collector does meanwhile: it does not drop an occurrence. A scheduled occurrence keeps its identity and backlog in `schedule_occurrences`; a late, held, deferred or overlapped one is reported, overlapping writes are refused, and `schedule-status` reports capacity as GAP or UNKNOWN. Queuing alone does not meet the cadence. Schedules stay off: none has run in this campaign.

If one full run shows a gap, the changes available are, in order of cost: more workers up to the configured maximum of 8 (each worker session costs 2 submissions per segment, and a Scrape.do plan's concurrency must allow them); reuse of exclusions for follow-ups for 30 days (a design option, not implemented; it would need a new release); and a higher provider tier. The scope is not narrowed in any of them.

## 10. Azure (estimates)

Retail prices read on 2026-10-28 (none re-read in this task): VM USD 0.113/h; public IP USD 3.65/month; OS disk (E4) USD 2.4/month; data disk E6 64 GiB USD 4.8, E10 128 GiB USD 9.6, E15 256 GiB USD 19.2, E20 512 GiB USD 38.4, E30 1024 GiB USD 76.8 a month; Blob hot LRS USD 0.0208/GB-month; Internet egress free for the first 100 GB a month, then USD 0.087/GB.

Example, N40k lean shipped (Oxylabs): VM 498.5 collection hours USD 56.33 (always on USD 82.49), OS disk USD 2.4, IP USD 3.65, data disk E10 128 GiB USD 9.6 for 85.1 GB retained, Blob copy option USD 0.42, egress 7.88 GB USD 0.0. Release 1.5.2 ran in a container on Hamza's test VM, offline; it has not been deployed by the template, and the historical live Azure runs belong to releases up to 1.4.1.

## 11. What would turn the estimates into measurements

1. A scope census: one Pickup result page per root listing (613 roots) reads each root's Pickup total. The sum bounds N from above and fixes the result pages of a full run: about 615 Oxylabs results, USD 0.31 to 0.92 as an estimate.
2. A written Oxylabs rate for the walmart source, and a current reading of the owner's dashboard.
3. One full run of the configured scope on the final revision, timed by stage, with the follow-ups read.

Model: `cost_model_151 (cost_model_141 version 4, revision 2, with follow-up pages shared among workers)`; tool SHA-256 `99949cb3a1fd76ccfa0093360c4dcd9ca21423e0bddf14b8ad5a292829de7d89`; requests made: 0. In [`evidence/reconciliation/1.5.1/cost_model_151/`](../evidence/reconciliation/1.5.1/cost_model_151/).
