# Walmart collector, release 1.6.8: summary

Store: Walmart #3891, 3900 Fountain Square Pl, Waukegan, IL 60085, fulfillment PICKUP. Collector release 1.6.8 (commit `85c29e7`, 2026-11-05T20:51:52Z) and the shared Classic probe 1.7.2 (commit `7768514`), published under the tag `review-1.6.8-20261106` (prepared by Hamza on 2026-11-05 and 2026-11-06, UTC). **Corrected by the probe 1.7.4 revision** (tag `review-1.6.8-probe174-20261111`, 2026-11-11): the shared Classic probe is now 1.7.4 (commit `a1def53`), and two statements below are corrected where marked. The collector, its data and its live results are unchanged.

**How to read the evidence.** OFFLINE: tests on fixture or stored pages, no request. OWNER AZURE: Hamza's own Azure test VM (Linux), no provider request; it is not the client's environment. LIVE: earlier runs against Walmart through the Oxylabs Web API on the owner's free trial credit. **No live run was made on 1.6.7 or 1.6.8**, and nothing ran in the client's environment.

## What 1.6.8 corrects

| Finding of the review of 1.6.6 | Correction | Shown by |
|---|---|---|
| C4: a body shorter than its declared length was taken as complete (probe 1.7.1) | probe 1.7.2 keeps it as partial, with its declared and received lengths and its hash; it is never parsed and its money stays held | the review's tests fail on 1.7.1 (13 on Windows, 14 on Linux) and pass on 1.7.2 |
| C2: a manifest read past the hard deadline; an earlier campaign's evidence accepted | evidence only from a bounded regular file that names the current execution; the session's process tree is ended whole; the supervisor returns within its hard end plus 0.5 s. **Corrected by the 1.7.4 revision:** on Windows 1.7.2 held the tree only when a job object could be made and joined, and fell back to `taskkill /T` otherwise. 1.7.4 runs a session only under a verified job object, refuses it with no fallback otherwise, and keeps a cleanup it cannot verify as unknown | the same tests, among them an immediate restart in the same folder; for 1.7.4, 5 tests fail on 1.7.2 by their output and pass on 1.7.4 on Windows (whole suite 229 passed, 5 skipped); on Linux, the 3 that run there pass on 1.7.4 and 2 fail on 1.7.2 (whole suite 227 passed, 7 skipped) |
| The Linux drip test expected a forced kill | it asserts the deadline, the outcome and the worker's end; a separate test forces a hung worker and checks a real kill and reap | probe 1.7.2 from its archive on Linux: 201 passed, 3 skipped, 0 failed |
| Completeness was called too early | a partition is complete only through its children; a row read in part is never complete; a filtered view never completes a listing; a category page of its own is read for the listings it names | the new tests fail on the code before them (1.6.6, 1.6.7 and two earlier 1.6.8 candidates); the controls beside them pass |
| "Fabric Softener" against "Fabric Softeners" | a record takes the name the row's category page gives its exact view, on fresh and carried records | the L12 replay renames 52 records, 40 of them L12's own fresh records |
| A size conflict withheld a verified UPC | UPC and size are decided apart | the 3 UPCs it withheld are filled from saved reads, with no request |

The 275 sponsored and variant decisions, row by row: 48 included; 165 excluded because the item's own page places it in another category; 3 duplicates, linked to their original observations; and **59 unresolved**: 4 whose page states no category path, so the category cannot be proven, and 55 whose page does not prove local eligibility. **Corrected by the 1.7.4 revision:** the 1.6.8 text counted these 59 as excluded and said none is unresolved; no source evidence supports their exclusion. Settling them needs their pages read again with the store's context. The queue of UPCs with no read is 44 (not the 45 reported for 1.6.6), a separate queue.

## Where it was verified

| What | Where | Result |
|---|---|---|
| The whole suite on the commit | OWNER AZURE, Linux | unit 554, integration 222 in 23 files, all passed |
| Both editions from their ZIPs: lock, lint, types, migrations on PostgreSQL 16, the whole suites, the operator drill, rollback to 1.6.6 and forward again | OWNER AZURE, Linux | 44 steps, 0 not as expected |
| Docker: both images built from the ZIPs; smoke tests; replays of stored live pages; a replay killed and resumed; rollback; data across a daemon restart | OWNER AZURE, Linux | 89 steps; 1 not as expected by its exit code (the gate's databases were still present; dropped afterwards). The resumed replay's export equals the uninterrupted one byte for byte |
| Both editions from a clean extraction of the source ZIP | OFFLINE, Windows | 37 steps, 0 not ok: unit 554 per edition and the integration files the change touches (Oxylabs 151, Scrape.do 73); the Azure templates build and lint, nothing deployed |
| A refused automatic publication | OFFLINE and OWNER AZURE | `PUBLICATION_REFUSED` at ERROR, exit 6, on the first attempt and on Azure's retry (tests); in the drill, exit 6 and again exit 6 on a manual publish; the last-good dataset unchanged |
| The walkthrough | OWNER AZURE | a 163 s screen recording with its English narration on screen, on stored pages only |
| A replay of L10 (stored pages), timed and its memory measured | OWNER AZURE, Linux host | 424 pages in 511.5 s, one worker in one process, resident memory at most 1.38 GiB; a replay, not a live measurement |

## Coverage today, row by row

The 11 rows of the client's CSV name 1,104 known listings. Under the 1.6.8 rules: 252 complete, 213 partial, 464 not attempted, 15 incomplete (a moving total or a missing page), 12 stopped at the site's result window, 7 read only through a filtered view, 95 category pages of their own not read yet, 1 category page and 1 not found; 44 are out of scope. **No CSV row is complete (0 of 11).**

| CSV row | Listings known | Complete | Partial | Not attempted | Other open | Out of scope | Row complete |
|---|---|---|---|---|---|---|---|
| Food | 215 | 7 | 29 | 124 | 50 | 5 | no |
| Household Essentials | 114 | 19 | 14 | 65 | 13 | 3 | no |
| Personal Care | 123 | 46 | 53 | 1 | 16 | 7 | no |
| Beauty | 123 | 44 | 42 | 10 | 25 | 2 | no |
| Diapering | 1 | 0 | 1 | 0 | 0 | 0 | no |
| Feeding | 127 | 72 | 37 | 7 | 10 | 1 | no |
| Health & Wellness | 11 | 2 | 3 | 0 | 6 | 0 | no |
| Pets | 87 | 43 | 25 | 1 | 9 | 9 | no |
| Balloons | 1 | 0 | 1 | 0 | 0 | 0 | no |
| Art Supplies | 8 | 2 | 6 | 0 | 0 | 0 | no |
| Office Supplies | 294 | 17 | 2 | 256 | 2 | 17 | no |

The last live runs: L12 on 1.6.6 (detail on) proves 40 fresh products and 10 product pages; its 10,301 exported records include 10,261 carried. L10 on 1.6.4 read 7,055 fresh valid products with detail off. L8 on 1.6.3 read 675 with detail on.

## Money

The live runs used the owner's Oxylabs free trial credit, counted at the documented rate of USD 0.0015 per result. The trial is USD 5 in total, shared with the Mariano's project. Walmart's envelope of USD 2.25 has USD 2.247 committed and USD 0.003 left. The Oxylabs ceiling is 0 since 2026-11-04. Mariano's envelope is not moved to Walmart without the owner's written authorization. **The ledger was read again for the probe 1.7.4 revision on 2026-11-09 (read-only): Walmart's part is the same, 1,513 reservations and USD 2.2470 committed, its last reservation on 2026-11-04, and this revision made no request. The database's SHA-256 has changed since 2026-11-06 because Mariano's own stages have drawn on Mariano's envelope, outside this revision.**

| Next work | Size | Cost at that rate |
|---|---|---|
| 500 or more fresh products in one run, detail on, on 1.6.8 | at most 45 submissions, retries included | at most USD 0.0675 |
| The known listing pages left | about 3,059 pages | about USD 4.63 |
| The category pages not read yet | 95 pages | USD 0.14 |
| The listings those pages name | not known until read | USD 3.95 to 23.72, if each page names 5 to 30 |
| Pages beyond the result window | 1,657 pages, 1,475 of them one listing | USD 2.49 |
| Product pages of the products known today | 9,307 pages | USD 13.96 |
| Product pages of products not yet seen | 50,321 to 101,956 pages (estimate) | USD 75.48 to 152.93 |
| Retries of product pages (1.6% measured) | | USD 1.47 to 2.74 |

## What is pending, and on whom

| Item | State | What it needs |
|---|---|---|
| The 59 unresolved sponsored and variant products | BLOCKED_BUDGET | their product pages read again with the store's context: 59 pages, about USD 0.09 at that rate before retries |
| The 500-product demonstration on 1.6.8 | BLOCKED_BUDGET | a written ceiling of 45 submissions and USD 0.0675 on an account the owner or the client names |
| The full catalogue and a timed full run | BLOCKED_BUDGET | funding of the continuation, on the account the client chooses |
| A run in the client's Azure environment, observed by the client | PENDING_CLIENT_AZURE | the access window, the VM restarted, the new public key installed and the old one revoked |
| Two scheduled runs, Tuesday and Friday at 06:00 Chicago | PENDING_OBSERVATION | the client's approval to enable the schedule, and funds for the runs |
| A real product going unavailable, or missing later, between two runs | PENDING_OBSERVATION | live runs that observe one; none is manufactured (the retention rules are tested offline) |
| Deallocate the owner's test VM; read the provider's usage page; replace the owner's Web API key | PENDING_OWNER | Hamza, in the owner's Azure portal and Oxylabs dashboard |
| Classic live mode; Scrape.do | PENDING_CLIENT_DECISION | the client's choice, entitlement and access |
| The support period and the transfer of intellectual property | PENDING_CLIENT_DECISION | an agreement between the owner and the client |

The acceptance matrix's 206 rows on 1.6.8: PASS_OFFLINE 91, PASS_DEVELOPER_LIVE 66, BLOCKED_BUDGET 22, NOT_APPLICABLE_BY_CLARIFICATION 6, PASS_OWNER_AZURE 5, PENDING_CLIENT_AZURE 5, PENDING_CLIENT_DECISION 4, PENDING_OWNER 4, PENDING_OBSERVATION 3. With the probe 1.7.4 revision: PASS_OFFLINE 91, PASS_DEVELOPER_LIVE 64, PASS_OWNER_AZURE 5, BLOCKED_BUDGET 24, PENDING_CLIENT_AZURE 5, PENDING_OWNER 4, NOT_APPLICABLE_BY_CLARIFICATION 6, PENDING_CLIENT_DECISION 4, PENDING_OBSERVATION 3; A25 and P4-02 move from PASS_DEVELOPER_LIVE to BLOCKED_BUDGET (the 59 unresolved).
