# Milestones: Walmart collector 1.6.6

Every time here is UTC and written with its offset. Conversions use the IANA time-zone database (tzdata 2026.5,
read 2026-11-04): on 2026-11-04 and 2026-11-05, America/Chicago (the store's zone) is UTC−06:00 (CST, daylight-saving time ended
2026-11-01) and Africa/Casablanca is UTC+00:00. Chicago returns to UTC−05:00 (CDT) on 2027-03-14.

The 2026-11-03T23:00Z time the VM extension was requested for was a request, not a granted window. No date below
depends on the client's VM, and none is promised where it would.

## 1. Done in this delivery

Command times are from `evidence/live/1.6.x/campaign/commands.csv`; each run's own start and end are in
[`data/RUN_SUMMARY.json`](../data/RUN_SUMMARY.json).

| When (UTC) | Milestone | Evidence |
|---|---|---|
| 2026-11-03T16:03Z | work starts from the reviewed publication `c4e665c` (tag `review-1.5.2-20261103`; the remote's `main` was still at it at 16:04Z) | this file; `manifests/PUBLICATION.json` |
| 2026-11-03T16:14Z | **mistake W0:** one GET to Oxylabs' statistics endpoint sent the Web API key as Basic credentials and was refused (HTTP 401, empty body; no result billed). Disclosed in the shared ledger | `evidence/live/1.6.x/campaign/shared_ledger/` |
| 2026-11-03T16:58:50Z | the shared Classic probe 1.7.0, offline (`2c08585`; its documents `48307cf`, 18:16:47Z): C1, C3 and C5 corrected; C2 and C4 only in part (completed in 1.7.1) | [`CLASSIC_PROBE_CORRECTIONS.md`](CLASSIC_PROBE_CORRECTIONS.md) |
| 2026-11-03T16:59:04Z | collector 1.6.0 committed (`56f078e`): the four deal fields always `""` (W1) | `evidence/offline-tests/1.6.0-collector/` |
| 2026-11-03T17:03:12Z to 17:04:56Z | L1, canary on 1.6.0 | `evidence/live/1.6.x/runs/L1_*` |
| 2026-11-03T17:24:52Z to 18:07:52Z | L2, high-value queue on 1.6.0, with pause, kill and resumes | `runs/L2_*` |
| 2026-11-03T18:18:22Z | collector 1.6.1 committed (`1780349`) | `offline-tests/1.6.1-collector/` |
| 2026-11-03T18:19:49Z to 18:29:40Z | L3, demonstration on 1.6.1, with pause, overlap refusal, kill and resume | `runs/L3_*` |
| 2026-11-03T18:31:59Z to 18:56:46Z | L2b, the rest of the sponsored and variant queue (W3), on 1.6.1 | `runs/L2b_*` |
| 2026-11-03T18:59:05Z to 19:04:09Z | L4r, the five capped listings, Strawberries and Dry Dog Food, on 1.6.1 | `runs/L4r_*` |
| 2026-11-03T19:08:17Z to 19:11:23Z | L4, census on 1.6.1: stopped (`ABNORMAL_RESULT`) at a link that serves a category page (Fresh Flowers) | `runs/L4_*` |
| 2026-11-03T19:24Z to 2026-11-04T09:59Z | **no work** (the session stopped); nothing ran and the ledger did not move | `campaign/commands.csv` has no command from L4's close (2026-11-03T19:17:16Z) to 2026-11-04T10:26:25Z, and `campaign/shared_ledger/events.json` no event from 19:17:16Z to 10:26:37Z |
| 2026-11-04T10:24:46Z | collector 1.6.2 committed (`1274056`): category pages and the moving-total window | `offline-tests/1.6.2-collector/` |
| 2026-11-04T10:26:39Z to 10:35:31Z | L5, demonstration on 1.6.2 (679 fresh valid), with pause, overlap refusal, kill and resume | `runs/L5_*` |
| 2026-11-04T10:37:45Z to 10:43:15Z | L6, partition check on 1.6.2: stopped (`SITE_REFUSAL`) at Walmart's not-found page | `runs/L6_*` |
| 2026-11-04T11:54:09Z | collector 1.6.3 committed (`def55e5`): saved reads with detail off, carried blanks recovered, the not-found page | `offline-tests/1.6.3-collector/` |
| 2026-11-04T11:56:31Z to 12:04:56Z | L8, demonstration on 1.6.3 (675 fresh valid), with pause, overlap refusal, kill and resume | `runs/L8_*` |
| 2026-11-04T12:07:37Z to 12:09:31Z | L9, L6's two unread children on 1.6.3 | `runs/L9_*` |
| 2026-11-04T12:11:40Z to 12:19:31Z | L7, census on 1.6.3: stopped (`ABNORMAL_RESULT`) at the Bidets listing (a reported total of 0 read as 10) | `runs/L7_*` |
| 2026-11-04T12:32:58Z | collector 1.6.4 committed (`28ac7d3`): a reported total of 0 is a total | `offline-tests/1.6.4-collector/` |
| 2026-11-04T12:56:14Z to 13:42:47Z | L10, census continued on 1.6.4 (7,055 fresh valid): stopped at its run credit limit and finalized | `runs/L10_*` |
| 2026-11-04T13:43:21Z to 13:44:45Z | L10's `validate-export --run` on 1.6.4 exits 6: 21 correct records reported as mismatches, because the source check could not read one page's flat price strings | `campaign/logs/162_l10_validate_export.jsonl` |
| 2026-11-04T14:15:19Z | collector 1.6.5 committed (`67d216e`): the source check reads all three price layouts | `offline-tests/1.6.5-collector/` |
| 2026-11-04T14:16:48Z to 15:04:59Z | both 1.6.5 editions verified from clean extractions of `WALMART_SOURCE_1.6.5.zip`: 23 steps, 0 not ok | `verification/1.6.5/package/` |
| 2026-11-04T14:18:06Z | L10's stage closed in the shared ledger | `campaign/` |
| 2026-11-04T14:19:47Z to 14:22:48Z | L10's and L8's exports pass `validate-export --run` on 1.6.5 (10,301 and 2,515 records verified) | `verification/1.6.5/source_check_l10/` |
| 2026-11-04T14:24:22Z to 14:30:08Z | L11, canary on 1.6.5: its listing was rejected for its identity, so there was no canary page (the delivery engineer's choice of listing) | `runs/L11_*` |
| 2026-11-04T14:35:08Z to 14:40:23Z | L11b, canary on 1.6.5: passed, 35 of 35 records verified | `runs/L11b_*` |
| 2026-11-04T14:43:41Z | L11b's stage closed; at 14:43:43Z the Oxylabs ceiling was set to 0 submissions and USD 0 | `campaign/` |
| 2026-11-04T14:56:45Z | the 1.6.5 tests run on the unchanged 1.6.4: 6 fail and 2 pass, as intended | `offline-tests/1.6.5-collector/` |
| 2026-11-04T15:06:30Z to 15:09:51Z | the last-good publication on a clean 1.6.5: 19 passed | `verification/1.6.5/last_good_publication/` |
| 2026-11-04T15:09:33Z to 15:09:45Z | the Bicep build and lint of both editions' Azure templates, no deployment: exit 0 | `verification/1.6.5/package/BICEP_CHECKS.txt` |
| 2026-11-04, at the time of its commit | the 1.6.5 publication, tag `review-1.6.5-20261104` (`d2ce076`, then `bcb53e8`) | the tag's `manifests/PUBLICATION.json` |
| 2026-11-04T21:22Z | the client's review of 1.6.5 is taken up: Classic C2 and C4, the refused publication's alert, the statements to correct | [`CORRECTION_MAP.md`](CORRECTION_MAP.md) |
| 2026-11-04T21:37:46Z to 22:22:46Z | the 7 reproduction tests of C2 and C4 fail on probe 1.7.0's code | `evidence/offline-tests/1.7.1-classic-probe/` |
| 2026-11-04T22:25:51Z | the shared Classic probe 1.7.1 committed (`68ff3d8`): C2 and C4 completed | [`CLASSIC_PROBE_CORRECTIONS.md`](CLASSIC_PROBE_CORRECTIONS.md) |
| 2026-11-04T22:27:40Z to 22:33:23Z | the two new publication tests fail on 1.6.5's code (`WARN`, not `ERROR`; exit 0, not 6) | `evidence/offline-tests/1.6.6-collector/` |
| 2026-11-04T22:34:53Z | collector 1.6.6 committed (`39cc61f`): a refused automatic publication is an `ERROR` and exits 6 | `offline-tests/1.6.6-collector/` |
| 2026-11-04T22:38:53Z | the builder of the 1.6.6 archives committed (`cbea802`), and the archives built from it | `evidence/live/1.6.x/builds/`; `classic-probe-1.7.1/` |
| 2026-11-04T22:43:25Z to 22:48:29Z | the probe 1.7.1 from its own clean export: 173 tests, 171 passed, 2 skipped; the reproductions fail on 1.7.0 and pass on 1.7.1 | `classic-probe-1.7.1/offline_results/` |
| 2026-11-04T22:48:48Z to 23:35:44Z | both 1.6.6 editions verified from clean extractions of `WALMART_SOURCE_1.6.6.zip` | `verification/1.6.6/package/` |
| 2026-11-04T22:52:55Z to 22:59:46Z | L12, a canary on 1.6.6 with product-page collection on: 40 fresh valid, 10 product pages, UPC 27 of 40 | `runs/L12_*` |
| 2026-11-04T23:00:43Z to 23:01:59Z | L12's export passes `validate-export --run` on 1.6.6: 10,301 of 10,301 records verified | `campaign/logs/205_l12_validate_export.jsonl` |
| 2026-11-04T23:03:49Z | L12's stage closed; at 23:03:52Z the Oxylabs ceiling was set to 0 submissions and USD 0 | `campaign/` |
| 2026-11-04T23:40:08Z to 23:43:12Z | the last-good publication on a clean 1.6.6: 19 passed; the three corrupt-evidence cases now exit 6 (1.6.5: 0). A first attempt at 23:36:05Z ran no test: offline, `uv` could not fetch its build backend | `verification/1.6.6/last_good_publication/` |
| 2026-11-05, at the time of the commit the tag names | this publication, tag `review-1.6.6-20261105` (a file cannot hold the time of the commit that adds it) | `manifests/PUBLICATION.json` |

## 2. Open, with their conditions

No date is given where a milestone waits on someone else's action. Where a duration is measured, it is given as a
duration after the condition.

| Milestone | State | Condition | After the condition |
|---|---|---|---|
| The client's review of 1.6.6 | PENDING_CLIENT_DECISION | the client reads this delivery | none from us |
| A demonstration of 500 or more with detail on, on 1.6.6 | BLOCKED_BUDGET | approval of stage 1 of [`TEST_PLAN.md`](TEST_PLAN.md): at most about USD 0.07, on a named account (USD 0.003 of the trial share is left) | about 10 minutes of running (L8 took 6 minutes of active time) and an hour of checks and reporting |
| Offline checks on the client's VM: install from the source ZIP, `uv sync --frozen`, migration on an isolated test database, the unit suite, a container build, `--version` | PENDING_CLIENT_AZURE | the client confirms the VM is running and the window, and installs `scraper_client_test_v2.pub` with the old key revoked. No SSH attempt is made before that | about 2 hours of work, by the access already agreed with the client |
| A live run in the client's environment | PENDING_CLIENT_AZURE | the offline checks above, and the client's approval of a paid budget on their own account | the bounded proposal in [`TEST_PLAN.md`](TEST_PLAN.md) |
| The full catalogue (all 11 CSV rows, every child and page) | BLOCKED_BUDGET | funding of the continuation in [`TEST_PLAN.md`](TEST_PLAN.md), stage 2 (about USD 4.07 for its listing pages, plus product pages) | about 4.4 active hours of listing pages with two workers at L10's measured rate, plus the product pages and the child listings found on the way |
| A timed full-scope run, and the twice-weekly fit | BLOCKED_BUDGET | the full catalogue above | measured by that run |
| The twice-weekly schedule enabled and observed | PENDING_OBSERVATION | the client's authorization (it ships disabled) and two observed scheduled runs | the first slots after an authorization: Tuesday and Friday 06:00 America/Chicago = 12:00Z (UTC−06:00) until 2027-03-12; from 2027-03-16 = 11:00Z (UTC−05:00). For example Friday 2026-11-06T12:00Z and Tuesday 2026-11-10T12:00Z |
| Scrape.do edition live on 1.6.6 | BLOCKED_BUDGET | Scrape.do access with credits (no Scrape.do spend is authorized in this delivery) | the canary of [`TEST_PLAN.md`](TEST_PLAN.md), stage 3 |
| A live Classic successor probe | PENDING_CLIENT_DECISION | the client's choice of Classic, a corrected live-enabled revision, a real Classic entitlement and the client-account limits proposed earlier (10 requests per retailer, 20 combined, 30 minutes, USD 5 combined) | not planned before that decision |
| The earlier Web API key (fingerprint `<key-fingerprint>`) revoked | PENDING_OWNER | the account owner's credential workflow | none from us |
| A walkthrough recording of 1.6.6; a summary PDF | PENDING_OWNER | Hamza's decision | none from us |
| The defect-support period and the transfer of intellectual property | PENDING_CLIENT_DECISION | a commercial agreement | none: not a code item |
