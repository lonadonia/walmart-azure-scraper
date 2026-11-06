# Cost and runtime report: Walmart release 1.6.8

Release 1.6.8, commit `85c29e7b2404500299056973f50c84b84e187a5a`. No live run was made on it, so every live figure below belongs to an earlier release, named. Store: Walmart #3891, 3900 Fountain Square Pl,
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
before it is sent, and an outcome that is not known stays reserved. Read after the last stage closed (L12,
2026-11-04T23:03:49Z; the ledger's state written at 23:04:15Z), and read again unchanged on 2026-11-06T01:10:58Z:

| | USD |
|---|---|
| Cap | 5.00 |
| Headroom kept inside the cap | 0.50 |
| Walmart's envelope | 2.25 |
| Mariano's envelope | 2.25 |
| Walmart: settled, 1,482 billable results | 2.2230 |
| Walmart: unknown outcomes held, 16 reservations | 0.0240 |
| Walmart: committed | 2.2470 |
| Walmart: left in its envelope | 0.0030 |
| Mariano's: committed (0 reservations) | 0 |

Walmart's 1,513 reservations: 1,497 settled (1,482 results; the other 15 were refused or documented free and
settled at 0) and 16 unknown. The collector's own ledger agrees: 1,512 requests, USD 2.2470; the 1,513th reservation
is W0, a request made outside the collector (see [`TECHNICAL_REPORT.md`](TECHNICAL_REPORT.md), section 8). The
Oxylabs ceiling is 0 since 2026-11-04T23:03:52Z and no lease is active. Mariano's envelope stays with Mariano's:
moving any of it to Walmart needs the owner's separate written authorization, which has not been given, and the
shared rule allows it only after Mariano's smallest essential tests are done or shown unable to proceed, and
neither is the case. The ledger's Walmart extract is in
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
| L12 | 11-04 22:52:53, 23:03:49 | 15, 0.0225 | 13 | 0 | 0.0195 | 40 | 0.488 |
| **Total** | | | **1,497** | **16** | **2.2470** | | |

What drives the cost per 1,000: a demonstration that reads product pages (L2: 484 of them) costs about ten times a
listing read; a census with detail off (L10) or a demonstration that reuses saved reads (L8) costs about USD 0.09
per 1,000 valid fresh products at the reserve rate. The small stages (L9, L11b, L12) are dominated by their fixed
requests: robots.txt and the store page for each worker. L12 also read 10 product pages for 40 products: with
detail on, a short run's cost per product is several times a long run's.

## 2. Measured runtime

Per run, from its own page fetches: [`RECOVERY_AND_OPERATIONS.md`](RECOVERY_AND_OPERATIONS.md), section 4, and
[`CONCURRENCY_MEASURED_1_6_6.csv`](../evidence/reconciliation/1.6.6/CONCURRENCY_MEASURED_1_6_6.csv), which stands: no live run since. The figures
the estimates use:
- **L10, two workers, detail off:** 441 pages in 2,596.6 s of active time, **10.19 pages per active minute**; a
  listing page took 8.4 s at the median and 12.9 s at the 90th percentile.
- **Product pages, detail on:** 5.0 s median and 16.0 s at the 90th percentile in L2 (254 pages); 5.0 s and 8.8 s in
  L5 (34 pages); 3.5 s and 5.1 s in L12 (10 pages, on 1.6.6).
- **Fixed work:** each execution reads robots.txt and the store page for each worker before it collects; after
  collection, a run checks and exports its rows (about 5 minutes for 10,301 rows in L11, L11b and L12).
- **Memory** of a live run was not measured. On the owner's Azure test VM (2 vCPU, 3.9 GB of memory), the delivered Oxylabs edition of 1.6.8 replayed L10 from its stored pages, on the host rather than in Docker: 424 pages and 6,880 valid records (the container's replay gave the same), in 511.5 s of wall time and 212 s of CPU. A replay serves the stored pages through one session, so it ran one worker in one process; L10 itself ran two. That process's resident memory peaked at 1.38 GiB by the kernel's count (1.31 GiB in samples every 0.25 s), and the host never had less than 1.75 GiB available ([`memory/`](../evidence/owner-azure-test/1.6.8/memory/)). A replay makes no request, so this is not a live run's measurement. Peak memory of a full run needs that run.

## 3. The outstanding work toward full scope (an estimate)

From the coverage table of W4 and the campaign's records, computed offline by `continuation_168.py`
([`CONTINUATION_ESTIMATE_1_6_8.json`](../evidence/reconciliation/1.6.8/w4/CONTINUATION_ESTIMATE_1_6_8.json); the
details are in [`TEST_PLAN.md`](TEST_PLAN.md), stage 2). Each part has its own basis, and they are not added into one figure:

| Part | Results | USD at the reserve rate | Basis |
|---|---:|---:|---|
| **Known listing pages** | about 3,087 | about 4.63 | 1,305 pages after those read (213 `PARTIAL` listings) and 61 read again (15 `INCOMPLETE`): measured, from reported totals. About 1,659 for 464 listings never reached and about 34 for 7 read only through a filtered view: **estimates**, each row's mean. Plus robots.txt and the store page for each worker of about 7 executions |
| **Category pages of their own, never read** | 95 | 0.14 | a count: one result each. Reading them replaces the assumption below with a measured count |
| **The listings those pages name** | 2,636 / 7,908 / 15,815 | 3.95 / 11.86 / 23.72 | an **assumption**, not a measurement: 5, 15 or 30 new listings per page, each at its row's mean pages. No such page has been read live |
| **Pages beyond the result window** | 182, and 1,475 for one listing | 0.27, and 2.21 | from reported totals, read through child categories: 15 listings above the window. "Special Kitty" reports 60,000, which is priced apart until its children are named |
| **Product pages of the products known today** | 9,307 | 13.96 | a count, from L12's 10,301 records: 9,344 lack a UPC or a size, 37 of those have a saved read of the last 30 days |
| **Product pages of products not yet seen** | about 50,321 to 101,956 | 75.48 to 152.93 | an **estimate**: the known listing pages times the fresh valid products per page of L10 (low) and L4r (high). Listings overlap more as they are read further, so even the low figure can be high. USD 1.50 per 1,000 products |
| **Retries** | 14 attempts after the first in 686 on product pages; 0 in 734 on listing pages | about 1.47 to 2.74 on product pages | measured in the 15 live runs: 11 of 672 billed product-page results were retries. A failure the provider documents as free costs time, not money; an unknown outcome stays reserved |

The 1.6.6 report's USD 4.07 priced the 2,683 known listing pages of the 1.6.5 table only. The same part is now about
**3,059 listing pages**, about **USD 4.63** at the reserve rate, about
**5.0 active hours** with two workers. Product pages are the largest part: USD
1.50 per 1,000 products at the reserve rate, about 59.9 to
111.7 active hours with two workers at the measured 7.23 s
a page.

## 4. A full run and the twice-weekly cadence (estimates, not measurements)

**One full listing pass** of the scope as W4 knows it today: every listing page once, known totals capped at the window, the row
mean where none is known: about **3,828 listing pages**, about 3,864 submissions. At
10.19 pages per active minute, about **6.3 active hours** with two workers.

| Rate per 1,000 results | One listing pass | A month of twice-weekly passes (8.67 a month) |
|---:|---:|---:|
| USD 0.50 | about USD 1.93 | about USD 16.75 |
| USD 1.00 | about USD 3.86 | about USD 33.50 |
| USD 1.50 (the trial's reserve rate) | about USD 5.80 | about USD 50.25 |

Not included, and each can be larger than the listing pass:
- **Product pages with detail on:** one per exported product lacking a UPC or a size, with no saved read of the last 30 days. In the two large
  reads measured (L4r, L10), no result page stated a UPC. The first full run reads nearly every product; a twice-weekly schedule then rereads each product
  about once in 30 days, plus new products: at the reserve rate, about USD 13.96 for the products known today, and about USD
  75.48 to 152.93 for those the known pages would add (an estimate, section 3), in each 30 days.
- **New branches:** the 95 category pages of their own and the listings they name, the children of the 15 listings above the
  result window, and any second partition level they need.
- **Retries** and requests whose outcome is unknown.

**The twice-weekly fit: UNKNOWN, not met and not refuted.** About 6.3 active hours of listing pages fits between the
Tuesday and Friday starts (72 hours) on paper. A first full run's product pages, about 59.9 to
111.7 active hours with two workers, may not; later runs read only the pages whose reads have expired or
are new. No full run has been timed. The collector does not drop an occurrence: a late or overlapped one keeps its identity and backlog, and
`schedule-status` reports it (see [`RECOVERY_AND_OPERATIONS.md`](RECOVERY_AND_OPERATIONS.md), section 5).

## 5. Azure (estimates carried from 1.5.2)

The Azure resources did not change since release 1.5.2: the templates are the same, and their example parameters
now name the 1.6.8 image. The estimates are those of the 1.5.2 report, with retail prices read on 2026-10-28 and
not read again: [`COST_AND_RUNTIME_REPORT.md`, section 10, at `review-1.5.2-20261103`](https://github.com/lonadonia/walmart-azure-scraper/blob/review-1.5.2-20261103/review/COST_AND_RUNTIME_REPORT.md#10-azure-estimates).
Its VM hours rested on a modelled full run; the runtime of section 4 above, once measured, replaces that model.
Nothing was deployed to the client's Azure in this delivery. The owner's existing Azure test VM ran the container and qualification gates (its compute is the owner's; no resource was added).

## 6. What would turn the estimates into measurements

1. Stage 2 of [`TEST_PLAN.md`](TEST_PLAN.md): the continuation, which counts the pages and the distinct products.
2. A written Oxylabs rate for Walmart, and the owner's dashboard reading of this trial.
3. One full run of the configured scope on the final revision, timed by stage, with detail on.
