# Cost and runtime report: Walmart release 1.6.5

Release 1.6.5, commit `67d216eb8ee2ec839a437b0b5bf2d594324b6982`. Store: Walmart #3891, 3900 Fountain Square Pl,
Waukegan, IL 60085, PICKUP. Times are UTC. Measured values and estimates are kept apart, and every estimate is
labelled as one.

Money in this report is at the shared trial's **reserve rate, USD 0.0015 per result**: a list price that the ledger
reserves before each submission, not an invoice. Oxylabs' price page, read for release 1.5.2, gave USD 0.50 to 1.50
per 1,000 results and named no rate for Walmart; the estimates of section 4 use that range. The Web API has no usage
endpoint, and the provider dashboard's reading is the owner's (A74).

## 1. What this delivery used: the shared trial ledger (measured)

Hamza authorized USD 5 in total across Walmart and Mariano's, on the designated free trial account: no top-up,
overage, new subscription, other paid provider or client-account charge. One account-wide ledger outside both
repositories (`.shared-oxylabs-trial-20261103`) enforces it: each submission's worst case is reserved
before it is sent, and an outcome that is not known stays reserved. Read after the last stage closed:

| | USD |
|---|---|
| Cap | 5.00 |
| Headroom kept inside the cap | 0.50 |
| Walmart's envelope | 2.25 |
| Mariano's envelope | 2.25 |
| Walmart: settled, 1,469 billable results | 2.2035 |
| Walmart: unknown outcomes held, 16 reservations | 0.0240 |
| Walmart: committed | 2.2275 |
| Walmart: left in its envelope | 0.0225 |
| Mariano's: committed (0 reservations) | 0 |

Walmart's 1,500 reservations: 1,484 settled (1,469 results; the other 15 were refused or documented free and
settled at 0) and 16 unknown. The collector's own ledger agrees: 1,499 requests, USD 2.2275; the 1,500th reservation
is W0, a request made outside the collector (see [`TECHNICAL_REPORT.md`](TECHNICAL_REPORT.md), section 8). The
Oxylabs ceiling is 0 since 2026-11-04T14:43:43Z and no lease is active. Mariano's envelope stays with Mariano's:
its essential tests have not been done. The ledger's Walmart extract is in
[`evidence/live/1.6.x/campaign/shared_ledger/`](../evidence/live/1.6.x/campaign/shared_ledger/).

Per stage (each stage's ceiling is the most it could reserve; "per 1,000" divides the stage's dollars by the run's
own count of valid fresh products):

| Stage | Opened, closed (UTC) | Ceiling: submissions, USD | Settled | Unknown | USD settled + unknown | Valid fresh | USD per 1,000 valid fresh |
|---|---|---|---:|---:|---:|---:|---:|
| W0 | 11-03 16:14:41, 16:15:47 | 1, 0.0015 | 1 (USD 0) | 0 | 0 | none | none |
| L1 | 11-03 17:03:06, 17:09:04 | 6, 0.009 | 4 | 0 | 0.0060 | 32 | 0.188 |
| L2 | 11-03 17:24:50, 18:10:47 | 600, 0.90 | 520 | 4 | 0.7770 | 707 | 1.099 |
| L3 | 11-03 18:19:46, 18:31:37 | 100, 0.15 | 44 | 4 | 0.0690 | 676 | 0.102 |
| L2b | 11-03 18:31:56, 18:58:40 | 130, 0.195 | 125 | 0 | 0.1800 | 120 | 1.500 |
| L4r | 11-03 18:59:01, 19:08:11 | 80, 0.12 | 52 | 0 | 0.0780 | 1,600 | 0.049 |
| L4 | 11-03 19:08:14, 19:17:16 | 660, 0.99 | 35 | 0 | 0.0525 | none (stopped) | none |
| L5 | 11-04 10:26:37, 10:37:29 | 70, 0.105 | 64 | 4 | 0.1020 | 679 | 0.150 |
| L6 | 11-04 10:37:43, 11:14:38 | 100, 0.15 | 69 | 0 | 0.1035 | none (stopped) | none |
| L8 | 11-04 11:56:29, 12:07:27 | 70, 0.105 | 37 | 4 | 0.0600 | 675 | 0.089 |
| L9 | 11-04 12:07:34, 12:11:12 | 12, 0.018 | 4 | 0 | 0.0060 | 2 | 3.000 |
| L7 | 11-04 12:11:35, 12:23:59 | 524, 0.786 | 82 | 0 | 0.1230 | none (stopped) | none |
| L10 | 11-04 12:56:12, 14:18:06 | 442, 0.663 | 441 | 0 | 0.6615 | 7,055 | 0.094 |
| L11 | 11-04 14:24:19, 14:34:55 | 6, 0.009 | 3 | 0 | 0.0045 | 0 | none |
| L11b | 11-04 14:35:04, 14:43:41 | 6, 0.009 | 3 | 0 | 0.0045 | 35 | 0.129 |
| **Total** | | | **1,484** | **16** | **2.2275** | | |

What drives the cost per 1,000: a demonstration that reads product pages (L2: 484 of them) costs about ten times a
listing read; a census with detail off (L10) or a demonstration that reuses saved reads (L8) costs about USD 0.09
per 1,000 valid fresh products at the reserve rate. The small stages (L9, L11b) are dominated by their fixed
requests: robots.txt and the store page for each worker.

## 2. Measured runtime

Per run, from its own page fetches: [`RECOVERY_AND_OPERATIONS.md`](RECOVERY_AND_OPERATIONS.md), section 4, and
[`CONCURRENCY_MEASURED_1_6_5.csv`](../evidence/reconciliation/1.6.5/CONCURRENCY_MEASURED_1_6_5.csv). The figures
the estimates use:
- **L10, two workers, detail off:** 441 pages in 2,596.6 s of active time, **10.19 pages per active minute**; a
  listing page took 8.4 s at the median and 12.9 s at the 90th percentile.
- **Product pages, detail on:** 5.0 s median and 16.0 s at the 90th percentile in L2 (254 pages); 5.0 s and 8.8 s in
  L5 (34 pages).
- **Fixed work:** each execution reads robots.txt and the store page for each worker before it collects; after
  collection, a run checks and exports its rows (about 5 minutes for 10,301 rows in L11 and L11b).
- **Memory** was not measured.

## 3. The outstanding work toward full scope (an estimate)

From the coverage table of W4, computed offline by `continuation_165.py`
([`CONTINUATION_ESTIMATE_1_6_5.json`](../evidence/reconciliation/1.6.5/w4/CONTINUATION_ESTIMATE_1_6_5.json); the
details are in [`TEST_PLAN.md`](TEST_PLAN.md), stage 2): about **2,683 listing pages** (1,236 and 37 of them from
measured totals, about 1,410 estimated for the 407 listings never reached), about **2,711 submissions**, **USD 4.07
at the reserve rate**, about **4.4 active hours** with two workers. Not included: product pages with detail on, the
child categories of 14 listings above the result window, and retries.

## 4. A full run and the twice-weekly cadence (estimates, not measurements)

**One full listing pass** of the scope as W4 knows it today: the pages of the 465 listings with a reported total
(1,760 pages, each listing at most 25 pages) and about 1,410 pages for the 407 listings never reached: about
**3,170 listing pages**, or about 3,178 submissions with two executions. At 10.19 pages per active minute, about
**5.2 active hours** with two workers.

| Rate per 1,000 results | One listing pass | A month of twice-weekly passes (8.67 a month) |
|---|---:|---:|
| USD 0.50 | about USD 1.59 | about USD 13.77 |
| USD 1.00 | about USD 3.18 | about USD 27.54 |
| USD 1.50 (the trial's reserve rate) | about USD 4.77 | about USD 41.31 |

Not included, and each can be larger than the listing pass:
- **Product pages with detail on:** one per distinct product without a saved read of the last 30 days. The first
  full run reads them for every product; a twice-weekly schedule then rereads each product about once in 30 days,
  plus new products. The number of distinct products in scope is not known until the continuation has run.
- **The children of the 14 listings above the result window**, and any second partition level they need.
- **Retries** and requests whose outcome is unknown.

**The twice-weekly fit: UNKNOWN, not met and not refuted.** About 5.2 active hours of listing pages, plus product
pages, fits easily between the Tuesday and Friday starts (72 hours) on paper, but no full run has been timed. The
collector does not drop an occurrence: a late or overlapped one keeps its identity and backlog, and
`schedule-status` reports it (see [`RECOVERY_AND_OPERATIONS.md`](RECOVERY_AND_OPERATIONS.md), section 5).

## 5. Azure (estimates carried from 1.5.2)

The Azure resources did not change since release 1.5.2: the templates are the same, and their example parameters
now name the 1.6.5 image. The estimates are those of the 1.5.2 report, with retail prices read on 2026-10-28 and
not read again: [`COST_AND_RUNTIME_REPORT.md`, section 10, at `review-1.5.2-20261103`](https://github.com/lonadonia/walmart-azure-scraper/blob/review-1.5.2-20261103/review/COST_AND_RUNTIME_REPORT.md#10-azure-estimates).
Its VM hours rested on a modelled full run; the runtime of section 4 above, once measured, replaces that model.
Nothing was deployed to Azure in this delivery.

## 6. What would turn the estimates into measurements

1. Stage 2 of [`TEST_PLAN.md`](TEST_PLAN.md): the continuation, which counts the pages and the distinct products.
2. A written Oxylabs rate for Walmart, and the owner's dashboard reading of this trial.
3. One full run of the configured scope on the final revision, timed by stage, with detail on.
