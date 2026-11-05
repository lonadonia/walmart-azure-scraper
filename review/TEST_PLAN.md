# Test plan and the next live work: Walmart release 1.6.6

Status on 2026-11-05: **nothing below has been run, and nothing below is approved.** Every figure is an estimate
from this delivery's measurements, not a quote. Money is at the shared trial's reserve rate, USD 0.0015 per result
(a list price, not an invoice). Times are UTC. Store: Walmart #3891, 3900 Fountain Square Pl, Waukegan, IL 60085,
PICKUP.

## Why the live work stops here

| Account | Limit | Used (committed) | Left | Needed for the smallest useful stage |
|---|---|---:|---:|---|
| The user's Oxylabs Web API trial, Walmart's envelope | USD 2.25 | USD 2.247 (1,513 reservations) | USD 0.003 (2 submissions) | Stage 1: about 28 to 45 submissions, at most about USD 0.07 |
| The same trial, Mariano's envelope | USD 2.25 | 0 | USD 2.25 | not available to Walmart: it may be reassigned only after Mariano's smallest essential tests are done or shown unable to proceed, and neither is the case |
| Scrape.do | no access authorized in this delivery | 0 | none | Stage 3 |
| Oxylabs Classic (the client's) | no access | 0 | not known | credentials, entitlement, rates, written approval |

The trial's cap is USD 5 in total across Walmart and Mariano's, with USD 0.50 kept as headroom inside it. The
ledger was not reset, nothing was bought, and nothing was charged to the client. The Oxylabs ceiling is 0 since
2026-11-04T23:03:52Z: no run sends anything until a new ceiling is set with its own approved basis. The last
USD 0.0225 of Walmart's envelope paid for L12, a canary of 1.6.6 with detail on (13 submissions, USD 0.0195): the
smallest live check of the final revision's detail path that the envelope could pay for. It is not Stage 1. Figures:
[`COST_AND_RUNTIME_REPORT.md`](COST_AND_RUNTIME_REPORT.md).

Each stage below runs the frozen release 1.6.6 (`39cc61f`, built as `cbea802`). Its ceiling is set with `set-ceiling` before its first
request, every submission's worst case is reserved before it is sent, a retry or a restart counts against the same
ceiling, and an unknown outcome stays charged. A stage that meets a block, a wrong store, repeated pages or its
ceiling stops, and reports what remains.

## Stage 1: a detail-on demonstration on the final revision (the smallest next proposal)

What it closes: N1A-05 and the detail-on part of W5 (at least 500 genuine distinct fresh valid products from one run
of the final revision, with the detail path on).

| Step | Submissions | What it shows |
|---|---:|---|
| Preflight of each worker: robots.txt and the store page | 4 | store 3891, ZIP 60085, PICKUP, on Walmart's own store page |
| The six listings of L2, L3, L5 and L8, three result pages each, two workers, one execution | 18 | about 675 fresh products, as L8 read; the automated canary and the 1.6.6 source check on the first recorded page |
| Product pages, detail on, for the products with no saved read of the last 30 days | about 6 to 23 | L8 needed 6 (with 667 UPCs from saved reads); more if Walmart's listings changed. L12 read 10 such pages on 1.6.6, 10 of 10 matched to their products |
| **Total** | **about 28 to 45** | **at most about USD 0.07** (45 × USD 0.0015) |

Ceiling: `set-ceiling --provider oxylabs --submissions 45 --usd 0.0675`. Afterwards: `export`, `validate-export
--run`, `field-dispositions`, `coverage-report`. The saved reads it relies on date from 2026-11-03 and 2026-11-04,
so they serve until 2026-12-03; later, more product pages are needed.

An optional addition of about 6 submissions: reach Beauty's "New Arrivals" listing through Beauty's category page,
as L10 did, so that the source check (1.6.5 and later) also meets the flat price layout live. L11 named that listing directly and
it was rejected for its identity (see [`TECHNICAL_REPORT.md`](TECHNICAL_REPORT.md), section 8).

## Stage 2: the continuation toward full scope (W4), priced from the coverage table

Computed offline from [`W4_LISTINGS_1_6_5.csv`](../evidence/reconciliation/1.6.5/w4/W4_LISTINGS_1_6_5.csv) (L12's one
page, in the 1.6.6 tables, changes no listing's state, so the estimate stands) by
`continuation_165.py`
([`CONTINUATION_ESTIMATE_1_6_5.json`](../evidence/reconciliation/1.6.5/w4/CONTINUATION_ESTIMATE_1_6_5.json)): 40
results per page, at most 25 pages per listing (the result window).

| Listings | How many | Listing pages | Basis |
|---|---:|---:|---|
| `PARTIAL`: the pages after those read | 203 | 1,236 | measured: each listing's reported total |
| `INCOMPLETE`: read again from page 1 | 9 | 37 | measured: each listing's last reported total |
| `NOT_ATTEMPTED`: named, never reached | 407 | about 1,410 | **an estimate**: no total is known; each row's mean from the listings reached in that row (row 0: 124 listings, about 956 pages; row 10: 256 listings, about 377 pages) |
| `RESULT_WINDOW`, `CATEGORY_PAGE`, `NOT_FOUND` | 11 | 0 | read through their child categories, or not a listing |
| **Total** | | **about 2,683** | |

- **Submissions:** about 2,711 (the listing pages, and robots.txt and the store page for each worker of each of
  about 7 executions of about 440 pages, the size of L10).
- **Money:** about **USD 4.07** at the reserve rate.
- **Time:** about **4.4 active hours** with two workers, at L10's measured 10.19 pages per active minute.
- **Not included:** product pages with detail on (one per distinct product without a saved read of the last 30
  days: priced once the continuation has counted the products); retries; and the listings found only by reading
  child categories. 14 `PARTIAL` listings report more results than the window serves (from 1,001 to 2,943, and
  "Special Kitty" 60,000): they are read through their child categories, at a cost known only once those are named.
  A child that also exceeds the window needs the second partition level (A18).
- **Then:** a timed full run of the whole scope, which measures what a twice-weekly run costs and whether it fits
  between two starts (A52, A53, N5-06). It is not proposed here: the continuation decides its size.

## Stage 3: a Scrape.do canary

Needs separately supplied Scrape.do access; this delivery authorizes no Scrape.do spending. The Scrape.do edition is
built from the same revision and passes the same offline suites. Its request code (`acquisition/scrapedo.py`) has
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
| 1 | Hamza or the client | Approve Stage 1 in writing: the account, the ceiling, the date | at most about USD 0.07 |
| 2 | the client | Approve Stage 2 on an account the client chooses | about USD 4.07, plus product pages |
| 3 | Hamza or the client | Supply Scrape.do access for Stage 3 | about 21 credits, then about 192 |
| 4 | the client | Restore access to the VM (restart, window, `scraper_client_test_v2.pub` with the old key revoked); then Stage 4 | at most USD 0.045 |
| 5 | the client | After Stage 2: the timed full run, the schedule, Classic, the support and IP terms | decided then |

The dated milestones are in [`MILESTONES.md`](MILESTONES.md).
