# Walmart 1.5.0: staged live validation plan

Written 2026-10-31T17:55Z, before any billable request of this task. The limits and the reconciliation behind
them are in `CAMPAIGN_BUDGET.json`.

## Order

1. Offline corrections and regressions on `walmart-1.5`, from `016dd23`. Lint, strict types, tests.
2. Offline reprocessing of the 1,441 saved product pages. No request.
3. Freeze the revision. Install from the lock into a new virtual environment. Isolated PostgreSQL and data folder
   under `C:/w7/live`. Schedules off. Nothing on Azure.
4. S1, then decide. S2, S3, S4, S5a, S5b, each only if the previous stage's context checks passed.
5. If a live finding changes collection behaviour: new version, new commit, the affected stages repeated if the
   budget allows, and no earlier record attributed to the new commit.

## Limits

| Stage | Purpose | Submissions | Workers | Minutes |
|---|---|---:|---:|---:|
| S1 | Canary: store 3891, ZIP 60085, PICKUP, seller, source response, parsing | 6 | 1 | 10 |
| S2 | Targeted product pages: blanks without a saved page, open sponsored and variant cases | 30 | 1 | 20 |
| S3 | One category with several real pages | 12 | 1 | 15 |
| S4 | >=500 distinct valid fresh products, detail path on, forced kill, resume of the same run | 42 | 2 | 45 |
| S5a | Repeat slice, at least 30 minutes after S4 | 6 | 1 | 10 |
| S5b | Serial against parallel on one slice | 12 | 1, then 2 | 15 |
| margin | Documented transient retries and recovery, each recorded | 12 | - | - |
| **Total** | | **120** (USD 0.18 at the reserve rate, USD 0.12 at the published rate) | | **115** |

The ceiling in the campaign database is raised stage by stage and is cumulative across runs, workers and resumes.

### Amendment A1, written 2026-10-31T22:31Z, before any S6 request

S3, S4 and S5a showed three defects of 1.5.0 (`CAMPAIGN_BUDGET.json`, `amendments`): a multipack lost when the size
is in a comma segment, `store_brand` "no" after a bracketed multipack, and a pilot's page budget stopping the reuse of
pages already saved. Release 1.5.1 changes what is exported, so step 5 above applies and one more stage runs.

| Stage | Purpose | Submissions | Workers | Minutes |
|---|---|---:|---:|---:|
| S6 | On the 1.5.1 commit: >=500 again, multipack weights and `store_brand` live, reuse behind a page budget | 20 expected, 22 limit | 1 | 30 |

Scope: Fresh Vegetables, Laundry, Shampoo, Cold and Flu, Dry Dog Food; 3 pages each; 3 product pages; no follow-up
pages. Used before S6: 94. After S6: at most 116 of 120, about 114 expected. The total of 120 and USD 0.18 is
unchanged; the 22 come from the 14 that S1 to S5b left unused and 8 of the margin, which keeps 4 for documented
transient retries. Below 500 valid products, the result is reported as it is and no further run follows.

S1 to S5b stay attributed to 1.5.0 at `7b6f325`; S6 is attributed to the 1.5.1 commit only.

### Amendment A2, written 2026-10-31T22:32Z, before any S6 request

The brief asks for the stop/resume and repeat-run checks on the same final version where affordable. They ran on
1.5.0 (S4, S5a); 1.5.1 is the final version and both fit. Recovery did not change in 1.5.1: the checks are repeated
because of that requirement, not because of a defect.

| Stage | Purpose | Submissions | Workers | Minutes |
|---|---|---:|---:|---:|
| S6 | As A1, with 1 product page, a forced kill after 8 collected pages, a resume of the same run, and two overlap refusals (exit 9, no request) | 21 expected, 22 limit | 1 | 30 |
| S7 | Repeat of Fresh Vegetables page 1, at least 30 minutes after S6 ends | 3 expected, 4 limit | 1 | 10 |

Used before S6: 94. S6 and S7 together: at most 26, so at most 120 and USD 0.18, about 118 expected. This uses up the
margin: a transient failure in either stage is reported as an unfinished stage, not retried beyond these limits.

### Outcome, written 2026-11-01T00:20Z, after the last stage (no limit changed)

115 answered, 3 abandoned at forced kills, 1 provider failure not charged: 119 of 120 rows, USD 0.1785 at the reserve
rate, last request 2026-10-31T23:35:31Z.

| Stage | Rows used | Limit | How it ended |
|---|---:|---:|---|
| S6 | 22 | 22 | One uncharged provider 500 (67.7 s) on a product page and its retry used the last room; the follow-up task paused at SPENDING_CEILING; `finalize` closed the run with no request. The limit was not raised and the run was not resumed. |
| S7 | 3 | 4 | Robots, store page, Fresh Vegetables page 1; paused at SPENDING_CEILING with 1 row of room, before its detail and reuse step; `finalize` closed the run with no request. |

Step 65 was an operator error: `--max-credits 2` is below the minimum of 5, so it stopped at exit 2 before the lock
check and tested nothing. Step 66 repeated the check correctly (exit 9, no request).

## Stop rules

Stop on a challenge or block, a wrong or unverified store or fulfillment, a page that does not advance, a limit, or
unresolved correctness. There is no provider switch, identity rotation or challenge solving. A retry needs a
documented transient condition or a materially corrected hypothesis. Partial evidence stays.

## Questions each stage answers

- **S1:** does the frozen revision read store 3891, Pickup and the Walmart seller from a real response?
- **S2:** can a product page fill a blank UPC or size for the right identity, and how often is the field truly absent?
- **S3:** do real later pages bring new identities, and do the counts reconcile?
- **S4:** does the corrected pipeline bring >=500 valid products on one revision with the detail path on, and does a
  forced kill leave no loss, duplicate or reset counter?
- **S5a:** what does a time-separated repeat change? A stock transition is reported only if one occurs.
- **S5b:** what does a second worker change in the real pipeline, measured on the same slice?
- **S6:** does the final commit reach >=500 valid products by itself, with the multipack kept beside the size, the
  Walmart brand found after a bracketed pack, and saved pages reused however small the page budget? Does a forced
  kill on that commit leave no loss, duplicate or reset counter?
- **S7:** what does a time-separated repeat change on the final commit? A stock transition is reported only if one
  occurs.

## Not covered

Full store size, full-run runtime, Scrape.do on the final revision (10 credits remain), Classic (no credentials and
no approval), client-observed acceptance, Azure and Docker.
