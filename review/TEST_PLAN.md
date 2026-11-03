# Test plan and consolidated request: Walmart release 1.5.2

Status on 2026-11-01: **nothing below has been run, and nothing below is approved.** This is the one request that
remains for the live work. Every figure is an estimate from the measurements in [`COST_AND_RUNTIME_REPORT.md`](COST_AND_RUNTIME_REPORT.md), not a
quote. Money is at USD 0.50 to 1.50 per 1,000 results, the readings of Oxylabs' price page, which names no rate for
Walmart. The upper figure is what a ceiling would be set to. Times are UTC. Store: Walmart #3891, 3900 Fountain Square
Pl, Waukegan, IL 60085, PICKUP.

Release 1.5.2 has not run live. Its corrections are verified offline, against the pages the live runs stored. The last
live evidence is run S6 on release 1.5.1 (`488a033`).

## Why no live run was made in this release

| Account | Limit | Used | Left | Needed for the smallest useful run |
|---|---|---:|---:|---|
| Oxylabs Web API (the owner's) | 120 rows, [`evidence/live/plan/CAMPAIGN_BUDGET.json`](../evidence/live/plan/CAMPAIGN_BUDGET.json) | 119 | 1 | at least 3 rows for any session; about 300 for Stage 1 |
| Scrape.do (the owner's free plan) | 1,000 credits a month | 990 | 10 | about 213 credits: canary about 21, a 19-page run about 192 |
| Oxylabs Classic (the client's) | no access | 0 | not known | credentials, entitlement, rates, written approval |

The ledger was not reset, nothing was bought, and nothing was charged to the client.

## The request

| # | Who | What | Cost, an estimate |
|---|---|---|---:|
| 1 | Hamza | Replace the owner's Web API key in the Oxylabs dashboard before the next live run | none |
| 2 | Hamza or the client | Approve Stage 1 in writing: the account, about 300 rows, the date | USD 0.15 to 0.45 |
| 3 | Hamza or the client | Approve the rest of [`evidence/reconciliation/1.5.2/sponsored_and_variant_reconciliation/EXACT_LIVE_READ_QUEUE_1_5_2.csv`](../evidence/reconciliation/1.5.2/sponsored_and_variant_reconciliation/EXACT_LIVE_READ_QUEUE_1_5_2.csv) (250 items left after Stage 1) | USD 0.13 to 0.38 |
| 4 | the client | Approve Stage 2, the census: about 615 rows | USD 0.31 to 0.92 |
| 5 | the client | After the census, choose a plan and approve Stage 3, one timed full run | see below |
| 6 | Hamza | Scrape.do: wait for the monthly renewal or take a paid plan, for at least about 213 credits | none, or the plan |
| 7 | the client | Azure access and paid Classic: an Azure access request (drafted separately; not published here) and [`classic-probe/oxylabs-classic-probe/CLASSIC_TEST_PLAN.md`](../classic-probe/oxylabs-classic-probe/CLASSIC_TEST_PLAN.md) | as the request and that plan say |
| 8 | the client | Observe a run: [`ACCEPTANCE_RUNBOOK.md`](ACCEPTANCE_RUNBOOK.md), section 7 | at most 30 rows, USD 0.045 |
| 9 | the client | The support period and the transfer of intellectual property | an agreement |

Items 2 to 4 together come to about 1,165 rows, USD 0.58 to 1.75.

## Stage 1: qualification of the final revision (about 300 rows)

| Step | Rows | What it shows | Stop if |
|---|---:|---|---|
| Canary: store page, store checks, one listing page, one product page | 4 | store 3891, ZIP 60085, PICKUP, seller, the corrected fields on live pages | any store check fails |
| Demonstration: at least 500 fresh products with their product pages read, a kill and a resume | about 255 | the corrected collector end to end, on live pages: about 235 product pages, plus setup and the restart | a block, a wrong store, repeated pages or the ceiling |
| Repeat of one page, later | 4 | the same revision read twice, live | as above |
| The 25 tile-only siblings of the earlier reviews | 29 | each sibling's own page: identity, category, Pickup | as above |
| Serial and parallel on the same pages | 10 | 1 and 2 workers through the real pipeline, on the final revision | as above |

The rows are estimates: Walmart's pages change. The ceiling is set with `set-ceiling` before the first request and a
retry or a restart counts against it.

## Stage 2: census (about 615 rows)

One Pickup result page per root listing (613 roots) reads each root's Pickup total. The sum bounds the store's
assortment from above and fixes the number of result pages of a full run. It replaces the assumed N of the cost
report with a measurement. The 945 listings of the earlier inventory are a baseline, not an assumed current truth.

## Stage 3: one timed full run

No figure here is a measurement yet. For N of 20,000 to 40,000 the model gives 31,769 to 99,418 results for a first
run on Oxylabs, and more for N of 80,000. That is beyond a free balance and needs a paid plan, so it is a decision
for after the census. The plan and the amount are not proposed here because the census decides them. The run has no
demonstration cap: its limits stop it safely, keep its checkpoints and report what remains, and a run stopped by a
limit is never reported as complete. If accessible pages run out with a gap left, the report says "accessible pages
exhausted; coverage incomplete". The twice-weekly fit is known only after this run.

## Milestones

These are the earliest realistic times, and each depends on the approval before it. A later approval moves what
follows by the same delay.

| Earliest | Milestone | Depends on |
|---|---|---|
| 2026-11-03T12:00Z | Key replaced, Stage 1 approved | items 1 and 2 |
| 2026-11-03T14:00Z to 18:00Z | Stage 1 runs | the approval; Oxylabs answering as on 2026-10-31 |
| 2026-11-04T12:00Z | Stage 1 report, with a correction release if Stage 1 finds a defect | Stage 1 |
| 2026-11-05T18:00Z | Census report | item 4 |
| Set after the census | Stage 3, and the twice-weekly answer | item 5 |
| Set by the client | The client-observed run, Azure and Classic | items 7 and 8 |
