# Test plan and the next live work: Walmart release 1.6.8

Status on 2026-11-06: **nothing below has been run, and nothing below is approved.** Every figure is an estimate
from this delivery's measurements, not a quote. Money is at the shared trial's reserve rate, USD 0.0015 per result
(a list price, not an invoice). Times are UTC. Store: Walmart #3891, 3900 Fountain Square Pl, Waukegan, IL 60085,
PICKUP.

## Why the live work stops here

| Account | Limit | Used (committed) | Left | Needed for the smallest useful stage |
|---|---|---:|---:|---|
| The owner's Oxylabs Web API trial (free credit), Walmart's envelope | USD 2.25 | USD 2.247 (1,513 reservations) | USD 0.003 (2 submissions) | Stage 1: at most 45 submissions, retries included, USD 0.0675 |
| The same trial, Mariano's envelope | USD 2.25 | 0 | USD 2.25 | not available to Walmart: moving any of it needs the owner's separate written authorization, which has not been given; the shared rule also allows it only after Mariano's smallest essential tests are done or shown unable to proceed, and neither is the case |
| Scrape.do | no access authorized in this delivery | 0 | none | Stage 3 |
| Oxylabs Classic (the client's) | no access | 0 | not known | credentials, entitlement, rates, written approval |

The trial's cap is USD 5 in total across Walmart and Mariano's, with USD 0.50 kept as headroom inside it. The
ledger was not reset, nothing was bought, and nothing was charged to the client. The Oxylabs ceiling is 0 since
2026-11-04T23:03:52Z: no run sends anything until a new ceiling is set with its own approved basis. The last
USD 0.0225 of Walmart's envelope paid for L12, a canary of 1.6.6 with detail on (13 submissions, USD 0.0195). L12 proves 40
fresh products and 10 product pages on 1.6.6; its 10,301 exported records include 10,261 carried. It is not Stage 1. Figures:
[`COST_AND_RUNTIME_REPORT.md`](COST_AND_RUNTIME_REPORT.md).

Each stage below runs the frozen release 1.6.8 (`85c29e7`). No live run has been made on it: everything that shows 1.6.8 itself ran offline or on the owner's Azure test VM, on stored and synthetic pages. Its ceiling is set with `set-ceiling` before its first
request, every submission's worst case is reserved before it is sent, a retry or a restart counts against the same
ceiling, and an unknown outcome stays charged. A stage that meets a block, a wrong store, repeated pages or its
ceiling stops, and reports what remains.

## Stage 1: a detail-on demonstration on the final revision (the smallest next proposal)

What it closes: N1A-05 and the detail-on part of W5 (at least 500 genuine distinct fresh valid products from one run
of the final revision, with the detail path on). It is also the first live run of 1.6.8.

| Step | Submissions | What it shows |
|---|---:|---|
| Preflight of each worker: robots.txt and the store page | 4 | store 3891, ZIP 60085, PICKUP, on Walmart's own store page |
| The six listings of L2, L3, L5 and L8, three result pages each, two workers, one execution | 18 | about 675 fresh products, as L8 read; the automated canary and the 1.6.8 source check on the first recorded page |
| Product pages, detail on, for the products with no saved read of the last 30 days | about 6 to 23 | L8 needed 6 (with 667 UPCs from saved reads); more if Walmart's listings changed. L12 read 10 such pages on 1.6.6, 10 of 10 matched to their products |
| **Total** | **about 28 to 45, capped at 45** | **at most USD 0.0675** (45 × USD 0.0015) |

Ceiling: `set-ceiling --provider oxylabs --submissions 45 --usd 0.0675`, retries included. It stops at the ceiling, even below 500, and
reports how many pages it read itself. Afterwards: `export`, `validate-export --run`, `field-dispositions`, `coverage-report`. The saved reads it
relies on date from 2026-11-03 and 2026-11-04, so they serve until 2026-12-03; later, more product pages are needed.

An optional addition of about 6 submissions: reach Beauty's "New Arrivals" listing through Beauty's category page,
as L10 did, so that the source check (1.6.5 and later) also meets the flat price layout live. L11 named that listing directly and
it was rejected for its identity (see [`TECHNICAL_REPORT.md`](TECHNICAL_REPORT.md), section 8).

## Stage 2: the continuation toward full scope (W4), priced from the coverage table

Computed offline by `continuation_168.py` from
[`W4_LISTINGS_1_6_8.csv`](../evidence/reconciliation/1.6.8/w4/W4_LISTINGS_1_6_8.csv) and the campaign's own records
([`CONTINUATION_ESTIMATE_1_6_8.json`](../evidence/reconciliation/1.6.8/w4/CONTINUATION_ESTIMATE_1_6_8.json)): 40 results per page, at
most 25 pages per listing (the result window). Each part has its own basis, and no total is given, because an estimate
and an assumption do not add up to a quote.

| Part | Results | USD at the reserve rate | Basis |
|---|---:|---:|---|
| **Known listing pages** | about 3,087 | about 4.63 | 1,305 pages after those read (213 `PARTIAL` listings) and 61 read again (15 `INCOMPLETE`): measured, from reported totals. About 1,659 for 464 listings never reached and about 34 for 7 read only through a filtered view: **estimates**, each row's mean. Plus robots.txt and the store page for each worker of about 7 executions |
| **Category pages of their own, never read** | 95 | 0.14 | a count: one result each. Reading them replaces the assumption below with a measured count |
| **The listings those pages name** | 2,636 / 7,908 / 15,815 | 3.95 / 11.86 / 23.72 | an **assumption**, not a measurement: 5, 15 or 30 new listings per page, each at its row's mean pages. No such page has been read live |
| **Pages beyond the result window** | 182, and 1,475 for one listing | 0.27, and 2.21 | from reported totals, read through child categories: 15 listings above the window. "Special Kitty" reports 60,000, which is priced apart until its children are named |
| **Product pages of the products known today** | 9,307 | 13.96 | a count, from L12's 10,301 records: 9,344 lack a UPC or a size, 37 of those have a saved read of the last 30 days |
| **Product pages of products not yet seen** | about 50,321 to 101,956 | 75.48 to 152.93 | an **estimate**: the known listing pages times the fresh valid products per page of L10 (low) and L4r (high). Listings overlap more as they are read further, so even the low figure can be high. USD 1.50 per 1,000 products |
| **Retries** | 14 attempts after the first in 686 on product pages; 0 in 734 on listing pages | about 1.47 to 2.74 on product pages | measured in the 15 live runs: 11 of 672 billed product-page results were retries. A failure the provider documents as free costs time, not money; an unknown outcome stays reserved |

**The USD 4.07 of the 1.6.6 plan** priced the 2,683 known listing pages of the 1.6.5 table, and nothing else. On the 1.6.8 table
the same part is about 3,059 pages, mainly because the links the census did not choose now count for their rows,
as the review asked. Product pages are the largest part by far: in the two large reads measured, no result page stated a UPC (L4r: 1,600 of 1,600
fresh valid products left it to their own page; L10: 6,686 of 7,055, the rest answered by saved reads), so nearly every product needs
its page once.

- **Time:** about 5.0 active hours of known listing pages with two workers, at L10's measured
  10.19 pages per active minute; about 59.9 to 111.7
  active hours of product pages, at the measured 7.23 s each with
  two workers. A first full run may not fit between two starts with two workers; more workers or a longer first run is the client's
  decision once it has been measured.
- **A later run:** about 3,828 listing pages (about 6.3 active hours, about USD 5.80),
  new branches excluded. A saved read serves 30 days, so at two runs a week the product pages are paid about once per product in each
  30 days, not per run.
- **A child above the window** needs the second partition level (A18).
- **Then:** a timed full run of the whole scope, which measures what a twice-weekly run costs and whether it fits
  between two starts (A52, A53, N5-06): requests, unique fresh, retained and invalid products, wall time, peak memory, workers and cost. It
  is not proposed here: the continuation decides its size.

## Stage 3: a Scrape.do canary

Needs separately supplied Scrape.do access; this delivery authorizes no Scrape.do spending. The Scrape.do edition is
built from the same revision and passes the same offline suites, on Windows and on Linux. Its request code (`acquisition/scrapedo.py`) has
not changed since 1.5.2, so the estimates of the 1.5.2 plan stand: a canary of about 21 credits, and a 19-page
demonstration of about 192 credits. The canary is run as L11b and L12 were: robots.txt, the store page and one listing page,
with the store, Pickup and source checks.

## Stage 4: a sequence the client observes

In the client's environment once access is restored, or shared on screen from the workstation; never certified on
the client's behalf:
1. the offline checks of [`ACCEPTANCE_RUNBOOK.md`](ACCEPTANCE_RUNBOOK.md), sections 1 to 6, on the client's copy;
2. `validate-config --check-db --require-credentials` and `status` on the client's database;
3. a live canary of one listing page (3 submissions), a pause, a refused second run, `resume`, `status`, then
   `export`, `validate-export --run` and `coverage-report`;
4. the published dataset unchanged afterwards (a pilot is never published).

At most 30 results, USD 0.045, on the account the client chooses.

## Order and dependencies

| # | Who | What | Cost, an estimate |
|---|---|---|---:|
| 1 | Hamza or the client | Approve Stage 1 in writing: the account, the ceiling, the date | at most USD 0.0675 |
| 2 | the client | Approve Stage 2 on an account the client chooses, known listing pages and category pages first | about USD 4.63 and 0.14; the listings those pages name, then product pages, priced above |
| 3 | Hamza or the client | Supply Scrape.do access for Stage 3 | about 21 credits, then about 192 |
| 4 | the client | Restore access to the VM (restart, window, `scraper_client_test_v2.pub` with the old key revoked); then Stage 4 | at most USD 0.045 |
| 5 | the client | After Stage 2: the timed full run, the schedule, Classic, the support and IP terms | decided then |

The dated milestones are in [`MILESTONES.md`](MILESTONES.md).
