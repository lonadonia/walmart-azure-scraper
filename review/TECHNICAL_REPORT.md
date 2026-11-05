# Technical report: Walmart release 1.6.6

Release 1.6.6, commit `39cc61f61ee694c0659a611310605bee6ed42d6b` (2026-11-04T22:34:53Z), built as `cbea802`. The
build commit adds only the archives' builder, so the collector and probe trees are the same. It ships with the shared
Classic probe 1.7.1. Prepared by Hamza on 2026-11-04 and 2026-11-05 (UTC). Times are UTC. Store: Walmart #3891,
3900 Fountain Square Pl, Waukegan, IL 60085, PICKUP.

**What this delivery is: a correction delivery.** The corrections are verified, and the named milestones are still
pending. It is not the full catalogue, nothing ran in the client's environment, no client observed a run, and every
schedule is off. Each requirement's state is in [`REQUIREMENT_MATRIX.md`](REQUIREMENT_MATRIX.md).

**What changed since the 1.6.5 delivery** (the client's review of 1.6.5):
- **Classic C2 and C4, completed in probe 1.7.1.** The 1.6.5 delivery said probe 1.7.0 corrected C1 to C5. For C2 and C4 that was not accurate: 1.7.0 corrected them only in part.
  - C2: 1.7.0's recovery, export and cleanup could run past the session's end.
  - C4: an answer written before the next paid step could still be lost by a crash, and a cut body left no record.

  Seven reproduction tests fail on 1.7.0 and pass on 1.7.1 ([`CLASSIC_PROBE_CORRECTIONS.md`](CLASSIC_PROBE_CORRECTIONS.md)).
- **A refused automatic publication is an alert** (collector 1.6.6). Release 1.6.5 logged it at `WARN` and exited 0, so the documented alerts did not fire. It is now an `ERROR`, recorded on the run, and the execution exits 6, also on Azure's retry. Two new tests fail on 1.6.5 and pass on 1.6.6 ([`1.6.6-collector/`](../evidence/offline-tests/1.6.6-collector/)).
- **L12, live on 1.6.6, with product-page collection on:**
  - 40 fresh valid products and 10 product pages read;
  - three UPCs that had never been read;
  - its export re-verified in full.

  It is a canary, not the 500-product demonstration, which the remaining allowance cannot pay for.
- **The 1.6.5 statements that were not accurate** are listed in [`manifests/DOC_CORRECTIONS.md`](../manifests/DOC_CORRECTIONS.md).

## 1. Evidence classes

| Class | What it is here | Where |
|---|---|---|
| Source inspection | each review point traced in the code of the reviewed release and of 1.6.6 | [`CORRECTION_MAP.md`](CORRECTION_MAP.md), [`CLASSIC_PROBE_CORRECTIONS.md`](CLASSIC_PROBE_CORRECTIONS.md) |
| Synthetic tests | fixtures and temporary PostgreSQL databases, with no request: unit 533 and integration 202 on 1.6.6, in each edition; the publication faults; the Classic probe's loopback stub (173 tests in 1.7.1) | `evidence/offline-tests/`, `evidence/verification/1.6.6/`, `classic-probe-1.7.1/offline_results/` |
| Offline checks of stored pages | stored pages read again with no request: 343 listing pages by 1.6.4's reader; all 1,531 stored page copies sorted by price layout; the exports of L10 and L8 checked by 1.6.5's source check against 1,478 and 951 stored pages; L12's export by 1.6.6's against 1,494 | [`1.6.4-collector/`](../evidence/offline-tests/1.6.4-collector/), [`1.6.5-collector/`](../evidence/offline-tests/1.6.5-collector/), [`source_check_l10/`](../evidence/verification/1.6.5/source_check_l10/), L12's run folder |
| New developer-account live collection | fifteen runs on the user's Oxylabs Web API trial, from the workstation, each on the release that ran it | [`data/RUN_SUMMARY.json`](../data/RUN_SUMMARY.json), `evidence/live/1.6.x/` |
| Carried products | rows a run did not observe itself, each with its own run and date; never counted as fresh | each run's `products.json` and `record_map.json` |
| Reused field observations | UPCs and sizes from saved product-page reads, each naming that read's time, run, revision and page | each run's `field_dispositions.json` |
| Client-environment execution | none | [`MILESTONES.md`](MILESTONES.md) |
| Client-observed acceptance | none | [`TEST_PLAN.md`](TEST_PLAN.md), section 4 |

## 2. What was fixed

Seven collector releases and two probe releases. [`CORRECTION_MAP.md`](CORRECTION_MAP.md) gives each with its cause,
its tests (each failing on the release before) and the live run that showed it. In short:
- **1.6.0:** the four deal fields are always `""` (W1). An account-wide spending gate reserves every submission's
  worst case in the shared trial ledger before it is sent.
- **1.6.1:** a run that ends before its detail pass still uses what earlier product-page reads established.
- **1.6.2:** a listing whose total moved while it was read is never `DONE`. A link that serves a category page is
  recorded and the run goes on.
- **1.6.3:** saved reads are used with detail reading off and for carried rows. Walmart's not-found page is
  recognized.
- **1.6.4:** a listing total reported as 0 is a total of 0.
- **1.6.5:** the independent source check reads all three layouts in which Walmart's pages give prices (price lines,
  nested price objects and flat display strings), as the page reader does. Until 1.6.4 it could not read the flat
  strings.
- **1.6.6:** a refused automatic publication is an `ERROR` (`PUBLICATION_REFUSED`), recorded on the run, and its
  execution, and Azure's retry of it, exits 6. Until 1.6.5 it was a `WARN` and exit 0.
- **Probe 1.7.0:** C1, C3 and C5, and C2 and C4 in part.
- **Probe 1.7.1:** C2 and C4 completed.
  - The ledger writes after an answer wait no longer than the write window. It closes 30 s before the session's end
    by default: a third of the export reserve, at most 30 s.
  - After one refusal of the lock, the session does not wait for it again.
  - The supervisor's kill, reap and recovery all end by the hard end; the recovery runs in its own process, killed if
    it is still running then.
  - Each answer is kept as received under its dispatch's number, its body renamed durably after its status
    (write-through on Windows), so a crash before the kept copy loses nothing.
  - A body cut at its deadline is kept and recorded (`PARTIAL_RESPONSE`), and every evidence file is synced before it
    is renamed into place.

Four of these (1.6.2 to 1.6.5) correct a defect that a live run of this delivery met: L4, L6, L7 and L10. 1.6.6 and
1.7.1 correct what the client's review of 1.6.5 found. Each release was frozen before the next stage ran on it, and
no earlier run is attributed to a later release.

## 3. What ran on the final revision, and where

| What | Where | When (UTC), 2026-11-04 | Result |
|---|---|---|---|
| The two new tests on 1.6.5's code | the development tree, `operations.py` of 1.6.5 restored | 22:27:40Z to 22:33:23Z | 2 failed, as intended: `WARN`, not `ERROR`; exit 0, not 6 |
| Unit suite, ruff, ruff format, mypy (strict); the publication tests | development tree at `cbea802` (clean), the workstation | 22:59:12Z to about 23:00:20Z | 533 passed; clean; 3 passed |
| **L12, a canary with product-page collection on, live** | the workstation, the user's Oxylabs Web API trial | 22:52:55Z to 22:59:46Z | canary passed; 40 fresh valid; 10 product pages; UPC 27 of 40 |
| L12's export checked (`validate-export --run`) | the 1.6.6 Oxylabs edition | 23:00:43Z to 23:01:59Z | exit 0: 10,301 of 10,301 records verified against 1,494 stored pages of 15 runs, no mismatch |
| Both editions from clean extractions of `WALMART_SOURCE_1.6.6.zip` | the workstation, with HTTP(S) sent to a closed local port | 22:48:48Z to 23:35:44Z | 23 steps, 0 not ok ([`evidence/verification/1.6.6/package/`](../evidence/verification/1.6.6/package/)): in each edition the lock, ruff, format and mypy clean; 533 unit and 202 integration tests passed, none skipped |
| Bicep build and lint of both editions' `azure/main.bicep` | the same extraction; no deployment | 23:33:56Z to 23:34:08Z | exit 0; the lint reported nothing; the build output is the same as 1.6.5's |
| The last-good publication against every listed fault | a clean extraction of the 1.6.6 Oxylabs edition ZIP | 23:40:08Z to 23:43:12Z | 19 passed; the three corrupt-evidence cases now exit 6 (1.6.5: 0). A first attempt at 23:36:05Z ran no test: offline, `uv` could not fetch its build backend; the rerun used `uv`'s cache, as the verifier does |
| The probe 1.7.1 from its own clean export | the workstation | 22:43:25Z to 22:48:29Z | 173 tests: 171 passed, 2 skipped; the 7 reproductions fail on 1.7.0's `src/` and pass on 1.7.1 |

The records are in [`evidence/verification/1.6.6/`](../evidence/verification/1.6.6/),
[`evidence/offline-tests/1.6.6-collector/`](../evidence/offline-tests/1.6.6-collector/),
[`evidence/offline-tests/1.7.1-classic-probe/`](../evidence/offline-tests/1.7.1-classic-probe/) and
[`classic-probe-1.7.1/offline_results/`](../classic-probe-1.7.1/offline_results/).

All fifteen live runs, each on the release that ran it (every one is a pilot, rejected at least by G3 because no
run read the whole catalogue, so nothing was published):

| Run | Release | What it was | When (UTC) | Workers | Fresh valid | Export rows (carried) | How it ended | Ledger rows | USD |
|---|---|---|---|---|---|---|---|---|---|
| L1 | 1.6.0 | canary | 11-03 17:03 to 17:05 | 1 | 32 | 709 (677) | rejected: G3, G4, G14 | 4 | 0.0060 |
| L2 | 1.6.0 | demonstration, detail on, with pause, kill and resume | 11-03 17:24 to 18:08 | 2 | 707 | 806 (99) | rejected: G3 | 524 | 0.7770 |
| L3 | 1.6.1 | demonstration, detail on, with pause, kill and resume | 11-03 18:19 to 18:30 | 2 | 676 | 808 (132) | rejected: G3 | 48 | 0.0690 |
| L2b | 1.6.1 | the queued products' own pages (W3) | 11-03 18:32 to 18:57 | 1 | 120 | 928 (808) | rejected: G3, G14 | 125 | 0.1800 |
| L4r | 1.6.1 | revisits of capped listings | 11-03 18:59 to 19:04 | 2 | 1,600 | 1,754 (153) | rejected: G3 | 52 | 0.0780 |
| L4 | 1.6.1 | census | 11-03 19:08 to 19:11 | 2 | none (865 fresh rows) | 865 (0) | stopped: `ABNORMAL_RESULT`, a link served a category page (fixed in 1.6.2) | 35 | 0.0525 |
| L5 | 1.6.2 | demonstration, detail on, with pause, kill and resume | 11-04 10:26 to 10:35 | 2 | 679 | 2,274 (1,595) | rejected: G3, G4 | 68 | 0.1020 |
| L6 | 1.6.2 | partitions: the children of Laundry and Shampoo | 11-04 10:37 to 10:43 | 2 | none (1,101 fresh rows) | 1,101 (0) | stopped: `SITE_REFUSAL`, Walmart's not-found page (fixed in 1.6.3) | 69 | 0.1035 |
| L8 | 1.6.3 | demonstration, detail on, with pause, kill and resume | 11-04 11:56 to 12:05 | 2 | 675 | 2,515 (1,840) | rejected: G3, G4 | 41 | 0.0600 |
| L9 | 1.6.3 | two children L6 had not read | 11-04 12:07 to 12:09 | 1 | 2 | 2,515 (2,513) | rejected: G3, G4, G14 | 4 | 0.0060 |
| L7 | 1.6.3 | census | 11-04 12:11 to 12:19 | 2 | none (2,019 fresh rows) | 2,019 (0) | stopped: `ABNORMAL_RESULT`, an empty listing's total (fixed in 1.6.4) | 82 | 0.1230 |
| L10 | 1.6.4 | census, continued | 11-04 12:56 to 13:43 | 2 | 7,055 | 10,301 (3,244) | `RUN_CREDIT_LIMIT`, finalized; rejected: G3, G4. `validate-export` exit 6 on 1.6.4 (the check's defect, fixed in 1.6.5), exit 0 on 1.6.5 | 441 | 0.6615 |
| L11 | 1.6.5 | canary | 11-04 14:24 to 14:30 | 1 | 0 | 10,301 (10,301) | rejected: G3, G4, G8, G12, G14; no canary page | 3 | 0.0045 |
| L11b | 1.6.5 | canary | 11-04 14:35 to 14:40 | 1 | 35 | 10,301 (10,266) | rejected: G3, G4, G14; canary passed | 3 | 0.0045 |
| L12 | 1.6.6 | canary, detail on (10 product pages) | 11-04 22:52 to 22:59 | 1 | 40 | 10,301 (10,261) | rejected: G3, G14; canary passed | 13 | 0.0195 |

"Fresh valid" is the run's own count from its validation; a run that stopped before its validation has none, and
its export's fresh rows are given instead. G14 (the readiness marker) never blocks. The ledger rows are the shared
ledger's reservations of the run's stage; USD is at the reserve rate. Each run's evidence is in
`evidence/live/1.6.x/runs/<run>_<id>/`, and each stage's command, ceiling, deadline and outcome in
[`evidence/live/1.6.x/campaign/`](../evidence/live/1.6.x/campaign/).

## 4. Counts, field completeness, coverage and recovery

**L12 on 1.6.6** (`01M6MC7YE4PBXV88G3PJ5ENW4B`), the final release with product-page collection on. It read page 1 of
Household Essentials' Fabric Softeners listing (`/browse/household-essentials/fabric-softener/1115193_1071967_1630538`,
77 results reported). It used one worker, at most 10 product pages and no follow-up page, under a ceiling of 15
submissions.
- Store 3891 Pickup was verified on Walmart's store page and at the start and end of the listing work. The automated
  canary passed on the first recorded page: 40 of 40 records verified.
- 40 fresh valid products. The page placed 49 products: 40 organic and 9 sponsored. The 9 sponsored are duplicates of
  organic tiles.
- UPC: 27 of 40.
  - 17 from saved reads of the products' own pages, reused with no request;
  - 10 from the 10 product pages read live, each matched to its product;
  - 13 not read, because the pilot's 10-page budget stopped them. They stay queued (`budget_deadline_interruption`).
- Size: 39 of 40 from the listing; the other one's page was among those not read.
- The four deal fields are `""` in every one of the 10,301 rows. Sale prices: 3 (each below its regular price). Store
  brand: 3 "yes".
- Three of the UPCs W2 counted as never read were read: items `14561172064` (`072613474844`), `1398092439`
  (`827854009580`) and `14620357163` (`072613474912`). The fourth of those items on this listing, `20242472444`, was
  not on page 1. 45 of W2's never-read UPCs remain ([`CORRECTION_MAP.md`](CORRECTION_MAP.md), W2).
- `validate-export --run`: 10,301 of 10,301 records verified against 1,494 stored pages of 15 runs, no mismatch.
- Gates: G3 failed (a pilot covers no category in full) and G14 (the readiness marker, non-blocking). Every other
  gate passed.
- 13 submissions (robots.txt, the store page, 1 listing page, 10 product pages), all settled: 13 results, USD 0.0195.

L12 is a canary, not the demonstration of 500 or more products with detail on that the review asks of the final
revision. That run needs about 28 to 45 submissions, at most about USD 0.07 at the reserve rate. Walmart's envelope
had USD 0.0225, which paid for L12, and now has USD 0.003 ([`TEST_PLAN.md`](TEST_PLAN.md), stage 1).

**L10 on 1.6.4** (`01M6KA3CKYJSD6WDY4TDAAV73Y`). It is a census: page 1 of each listing that the category pages of
CSV rows 2 to 10 name today, and Household Essentials' Bidets listing. Detail reading was off, with no follow-up page
and two workers. It read 8 category pages and 429 listing pages.
- 7,055 fresh valid products: Personal Care 1,834, Beauty 1,766, Feeding 1,395, Pets 1,321,
  Health & Wellness 273, Art Supplies 255, Office Supplies 134, Balloons 40, Diapering 39. The fresh export has 7,057
  rows: the other 2 are products their page showed with no price at all, exported with empty prices and marked
  `exported_not_valid` in `record_map.json`; they are not counted. 3,244 rows were carried from earlier runs.
- UPC of the fresh rows: 367 from saved product-page reads, 6,688 `not_attempted` (detail reading off), 2 absent in
  the source.
- Carried rows: 267 filled from saved reads (UPC 267, weight 15); 12 withheld, because the read's size statements
  conflict.
- Bidets, which stopped L7 on 1.6.3, ended `EMPTY` as 1.6.4 intends.
- It stopped at its run credit limit (about 441 of its 442 credits) and was finalized; the 155 listings it had not
  reached are `SKIPPED`. Gates G3 and G4 failed; a pilot is never published either way.
- `validate-export --run` on 1.6.4 exited 6: its source check reported 21 records as mismatches. All 21 were read
  from one page that gives its prices as flat strings, and all 21 equal that page. The check could not read that
  layout; release 1.6.5 corrects it, and on 1.6.5 the export passes: 10,301 of 10,301 records verified against 1,478
  stored pages of 13 runs ([`source_check_l10/`](../evidence/verification/1.6.5/source_check_l10/)).

**L11b on 1.6.5** (`01M6KFRFEX31W014SW9ZTT4Y54`), that release's canary: page 1 of Food's Fresh Fruits listing, one
worker, detail off. Store 3891 Pickup verified on Walmart's store page. The automated canary passed on the first
recorded page (14:35:40Z): 40 records, 35 valid, the source check 35 of 35. Their 35 UPCs come from saved reads.
That page, and L12's, gives its prices in price lines: no live run of 1.6.5 or 1.6.6 checked a page in the flat
layout, which is verified offline on the authentic stored page.

**L8 on 1.6.3** (`01M6K6P21BW509BMRTN1FSB9H7`), the last demonstration of 500 or more with detail reading on:
- 675 fresh valid, and an export of 2,515 rows (1,840 carried);
- UPC of the fresh rows: 667 from saved reads, 5 from the 6 product pages it fetched, 2 absent in the source, 1
  identity mismatch;
- 155 carried rows filled from saved reads (UPC 155, weight 5), and 4 withheld because the read's size statements
  conflict;
- its export passes `validate-export --run` on 1.6.5 too: 2,515 of 2,515 verified against 951 stored pages.

**Fields of S6's 706 rows** (W2), and **the 275 queued products** (W3): see [`CORRECTION_MAP.md`](CORRECTION_MAP.md).

**Coverage** (W4). The scope is 1,104 listings in the 11 CSV rows: 765 root and 339 child listings
(`W4_LISTINGS_1_6_6.csv` gives each one's level, parent and how it was found). The fifteen runs read 715 listing
pages; L12's one page changed no listing's state:

| State of a listing | Listings |
|---|---|
| `COMPLETE`: every page read and reconciled | 244 |
| `PARTIAL`: page 1 or more read, more pages remain | 203 |
| `NOT_ATTEMPTED`: named, never reached (395 named by today's census, 12 named on 2026-10-24) | 407 |
| `OUT_OF_SCOPE` | 230 |
| `INCOMPLETE`: the read could not be reconciled or trusted | 9 |
| `RESULT_WINDOW`: more results than the site serves, to be read through child categories | 9 |
| `CATEGORY_PAGE`, `NOT_FOUND` | 1 and 1 |

No CSV row is complete (0 of 11). Partitions ran live at depth 1 only (21 child listings: L6 18, L10 3); none of
them exceeds the result window. The tables are in [`evidence/reconciliation/1.6.6/w4/`](../evidence/reconciliation/1.6.6/w4/)
(those of 1.6.5 stay beside them), and the outstanding work is priced in [`TEST_PLAN.md`](TEST_PLAN.md): about 2,683
listing pages and 2,711 submissions, about USD 4.07 at the trial's rate, product pages not included.

**Recovery and publication:** see [`RECOVERY_AND_OPERATIONS.md`](RECOVERY_AND_OPERATIONS.md). Pause, overlap refusal,
forced kill and resume ran live on 1.6.1, 1.6.2 and 1.6.3, and by the integration suites of every later release. The
last-good publication was tested synthetically on clean extractions of 1.6.5 and 1.6.6.

## 5. Provider usage: the shared trial ledger

Hamza authorized USD 5 in total, across Walmart and Mariano's together, on the designated free trial account; no
top-up, overage or client-account charge. One account-wide ledger outside both repositories enforces it
(`.shared-oxylabs-trial-20261103`). Every submission's worst-case cost was reserved in it before it was
sent, and an unknown outcome stays reserved. Its figures, read after the last stage closed (L12, 23:03:49Z; state
written 23:04:15Z):

| | USD |
|---|---|
| Cap | 5.00 |
| Headroom kept inside the cap | 0.50 |
| Allocatable: Walmart's envelope 2.25, Mariano's envelope 2.25 | 4.50 |
| Walmart: settled (1,482 billable results in 1,497 settled reservations) | 2.2230 |
| Walmart: unknown outcomes held (16 reservations: 2 cancelled at the pause and 2 abandoned at the kill in each of L2, L3, L5 and L8) | 0.0240 |
| Walmart: committed | 2.2470 |
| Walmart: left in its envelope | 0.0030 |
| Mariano's: committed (0 reservations) | 0.0000 |
| Uncommitted in all: the headroom, Mariano's envelope and Walmart's remainder | 2.7530 |

Walmart's 1,513 reservations are the fifteen runs' 1,512 and W0 (section 8), which settled at 0. The collector's
own ledger agrees: 1,512 requests, USD 2.2470. Mariano's envelope is not reassigned to Walmart. The rule allows that
only after Mariano's smallest essential tests are done, or shown unable to proceed, and neither is the case. The
Oxylabs ceiling is 0 submissions and USD 0 since 23:03:52Z, and no lease is active. Dollars are at the reserve rate
(USD 0.0015 per result, a list price), not an invoice. The Web API has no usage endpoint, and the provider
dashboard's reading is the owner's (A74). Per-stage figures: [`COST_AND_RUNTIME_REPORT.md`](COST_AND_RUNTIME_REPORT.md).

## 6. What remains, and why

| Milestone | State | What it needs |
|---|---|---|
| The full catalogue: every CSV row, child and page | BLOCKED_BUDGET | the continuation priced in [`TEST_PLAN.md`](TEST_PLAN.md), on an approved budget |
| A demonstration of 500 or more with detail on, on the final revision | BLOCKED_BUDGET | about 28 to 45 submissions, at most about USD 0.07 at the reserve rate (TEST_PLAN.md, stage 1); USD 0.003 is left |
| A timed full run, and the twice-weekly fit | BLOCKED_BUDGET | the full catalogue first |
| A natural available-to-unavailable transition | PENDING_OBSERVATION | it cannot be manufactured |
| Offline checks and a container build on the client's VM | PENDING_CLIENT_AZURE | the client's confirmation and the new key |
| The schedule enabled and observed | PENDING_OBSERVATION | the client's authorization |
| Scrape.do live | BLOCKED_BUDGET | separately supplied Scrape.do access |
| A live Classic successor | PENDING_CLIENT_DECISION | the client's choice, a Classic entitlement and limits |
| A walkthrough of 1.6.6, the owner's test VM, the developer key's rotation, a summary PDF | PENDING_OWNER | Hamza |
| Support and IP terms | PENDING_CLIENT_DECISION | a commercial agreement |

[`MILESTONES.md`](MILESTONES.md) gives the dated milestones and their conditions.

## 7. Client actions

The smallest decisions, each the client's:
1. Confirm the VM's restart and a window, and install `scraper_client_test_v2.pub` with the old key revoked. The
   offline checks on the VM follow.
2. Decide whether to fund the next live work in [`TEST_PLAN.md`](TEST_PLAN.md), and on which account: first the
   detail-on demonstration on 1.6.6 (at most about USD 0.07), then the continuation. Walmart's share of the user's
   trial allowance has USD 0.003 left.
3. Later: authorize the schedule; decide on Classic; agree the support and IP terms.

## 8. Disclosures

- **The 1.6.5 delivery overstated the Classic corrections and the alert advice.** It said C1 to C5 were corrected
  in probe 1.7.0; C2 and C4 were corrected in part. It gave operating documentation (N10-03) and the publication
  rows a pass while a refused automatic publication raised no documented alert. Both are corrected in this delivery,
  and each 1.6.5 statement is listed in [`manifests/DOC_CORRECTIONS.md`](../manifests/DOC_CORRECTIONS.md).
- **L12's rows name the subcategory "Fabric Softener".** The run named its listing by path (`--subcategory`), and the
  collector takes such a listing's name from its path. The site names it "Fabric Softeners", which is the name the
  carried rows of L7 and L10 have. The products, URLs, prices and UPCs are as the page shows them. A listing that a
  category page names keeps the site's name.
- **A false pass, caught before publication.** The first run of the probe 1.7.1's results tool counted the
  reproduction step on 1.7.0 as expected from its exit code alone. Its install had failed, because that extraction
  lacked a file. The tool now builds the whole tree and checks each step's output. The rerun shows 7 failed on 1.7.0
  and 7 passed on 1.7.1. Only the rerun is in the delivery.
- **Mistake W0, 2026-11-03T16:14Z.** One GET to Oxylabs' statistics endpoint sent the Web API key as Basic
  credentials. It was refused (HTTP 401, empty body), and no result was billed. The key went only to Oxylabs' own
  host, and no other guessed endpoint was tried. It is recorded in the shared ledger.
- **The source check of 1.6.4 was wrong for one page layout.** It read prices only from price lines and nested
  objects. On the one stored page that gives them as flat strings, it expected no price. So it reported 21 correct
  L10 records as mismatches. It would also have accepted a record from such a page whose price was missing, and would
  have stopped a run whose first page came in that layout. No delivered record was affected: the only such pages are
  L10's copy (13:15:20Z) and L11's (14:24:41Z), L10's 26 records from it carry the prices it shows, and L11 recorded
  no product. Release 1.6.5 corrects the check; its tests fail on 1.6.4
  ([`1.6.5-collector/`](../evidence/offline-tests/1.6.5-collector/)).
- **L11 chose a listing that could not serve as a canary.** To exercise 1.6.5 on the flat-layout page, L11 named
  Beauty's "New Arrivals" listing directly. Its page does not place it under Beauty (it has no breadcrumb), so the
  collector rejected it (`IDENTITY`), as it is built to, and recorded no product. The stored L10 copy of that page,
  which also has no breadcrumb, was not checked offline first. The choice was the delivery engineer's. It cost 3
  submissions (USD 0.0045); L11b then ran on a listing whose page names its category.
- **A rebuilt harness backup.** On 2026-11-04 at about 12:40Z, the 1.6.4 patch of the live-stage harness overwrote
  the backup `live160_run.before_163.py`. It was rebuilt from the next backup by removing the one line the 1.6.3
  patch had added. Both hashes are in `evidence/live/1.6.x/campaign/` (`live160_run.before_163.REBUILT.txt`). The
  harness only launches the collector's commands, and it does not change what a run collects.
- **Withheld recoveries.** A carried row whose saved read gives conflicting sizes keeps its blank (`recovery_withheld`):
  4 rows in L8, 12 in L10, 9 in L12.
- **The census has detail reading off.** L10's fresh rows have a UPC only where a saved read gives one. Every other
  UPC is `not_attempted`, never absent.
- **Session gaps.** No work was done from 2026-11-03T19:24Z to 2026-11-04T09:59Z, because the session had stopped.
  Nothing ran, and the ledger did not move: the campaign's `commands.csv` has no command from L4's close
  (2026-11-03T19:17:16Z) to 2026-11-04T10:26:25Z, and the ledger's `events.json` no event from 19:17:16Z to
  10:26:37Z. The campaign's `commands.csv` has no command between L11b's last step (14:43:46Z) and L12's first (22:52:22Z).
- **Corrections to this publication's own texts** before it was pushed, and close notes of the campaign record that
  name fewer gates than the runs' checks, are listed in [`manifests/DOC_CORRECTIONS.md`](../manifests/DOC_CORRECTIONS.md).

## 9. Package

| Folder | What it is |
|---|---|
| [`source/`](../source/) | `WALMART_SOURCE_1.6.6.zip`, file for file: both editions of `39cc61f`, built at `cbea802` |
| [`classic-probe-1.7.1/`](../classic-probe-1.7.1/) | `OXYLABS_CLASSIC_OFFLINE_PROBE_1.7.1.zip`, file for file |
| [`classic-probe-1.7.0/`](../classic-probe-1.7.0/) | the probe 1.7.0 of the 1.6.5 delivery, unchanged (superseded) |
| [`classic-probe/`](../classic-probe/) | the Walmart probe 1.5.2, as reviewed, unchanged |
| [`data/`](../data/) | the product files of L10 and L8, and of the 1.5.x runs, unchanged; the run summary with L12 |
| [`evidence/`](../evidence/) | by class; [`evidence/README.md`](../evidence/README.md) gives each folder |
| [`review/`](.) | this report and the other review documents |
| [`manifests/`](../manifests/) | the file map, redactions, exclusions, the checks, and `SHA256SUMS.txt`, written last |
