# Technical report: Walmart release 1.6.8

Release 1.6.8, commit `85c29e7b2404500299056973f50c84b84e187a5a` (2026-11-05T20:51:52Z). It ships with the shared Classic probe 1.7.2, commit
`7768514aa1ffbaa7f96ca242d7b64e495fffefa5`, whose tree is the same at the collector's commit. Prepared by Hamza on 2026-11-05 and 2026-11-06 (UTC). Times are UTC.
Store: Walmart #3891, 3900 Fountain Square Pl, Waukegan, IL 60085, PICKUP.

**What this delivery is: a correction delivery.** The corrections are verified offline and on the owner's Azure test VM,
and the named milestones are still pending. **No live run was made on 1.6.7 or 1.6.8.** It is not the full catalogue,
nothing ran in the client's environment, no client observed a run, and every schedule is off. Each requirement's
state is in [`REQUIREMENT_MATRIX.md`](REQUIREMENT_MATRIX.md).

**What changed since the 1.6.6 delivery** (the client's review of 1.6.6):
- **Classic C4 and C2, completed in probe 1.7.2.** The 1.6.6 delivery said probe 1.7.1 completed them. That was not accurate.
  - C4: a server that declares `Content-Length: 100`, sends the two bytes `{}` and closes got `ok=True`, `truncated=False` and a final `.body`.
  - C2: on Linux the supervisor waited 1.10 s for a FIFO manifest past a 0.30 s hard deadline, and it accepted an earlier campaign's `complete=true` file when a new command exited 0 without writing any.
  - The published suite failed one test on Linux (169 passed, 1 failed, 3 skipped): the drip test required a forced kill when the worker had ended by itself.

  The review's tests fail on 1.7.1 (13 on Windows, 14 on Linux) and pass on 1.7.2 ([`CLASSIC_PROBE_CORRECTIONS.md`](CLASSIC_PROBE_CORRECTIONS.md)).
- **What "complete" means** (collector 1.6.7 and 1.6.8). A partition is complete only through its children, a row read in part is never complete, and a read of a filtered view never completes a listing. 252 of 1,104 listings are complete under these rules, and no CSV row is (0 of 11).
- **Scope that was skipped** (collector 1.6.8). A subcategory that is a category page of its own is read for the listings it names. A link that shows a listing filtered has the listing itself read, in full, once. Two shelves that share listing ID 0 are two listings.
- **The category mapping** (1.6.7 and 1.6.8). A listing takes the name the row's category page gives that exact view, on fresh and carried rows. "Fabric Softeners" is that name for listing `1115193_1071967_1630538`.
- **UPC and size decided apart** (1.6.7). A size conflict withholds the size only. The queue of UPCs with no read is 44, not 45.
- **The 275 sponsored and variant decisions at row level**: 48 included, 165 excluded with another category identified, 4 with no category path, 55 with no proof of local eligibility, 3 duplicates linked to their originals.
- **A container gate on the owner's Azure test VM.** The actual images from the delivered source, with digests, migrations on an isolated PostgreSQL, a replay of stored pages, a kill and resume, a rollback and persistence across a restart. An owner test, not the client's environment.
- **The 1.6.6 statements that were not accurate** are listed in [`manifests/DOC_CORRECTIONS.md`](../manifests/DOC_CORRECTIONS.md).

## 1. Evidence classes

| Class | What it is here | Where |
|---|---|---|
| Source inspection | each review point traced in the code of the reviewed release and of 1.6.6 | [`CORRECTION_MAP.md`](CORRECTION_MAP.md), [`CLASSIC_PROBE_CORRECTIONS.md`](CLASSIC_PROBE_CORRECTIONS.md) |
| Synthetic tests | fixtures and temporary PostgreSQL databases, with no request: unit 554 and integration 222 on 1.6.8, in each edition; the publication faults; the operator drill; the Classic probe's loopback stub (204 tests in 1.7.2) | `evidence/owner-azure-test/1.6.8/qualification/`, `evidence/offline-tests/`, `evidence/verification/1.6.8/`, `classic-probe-1.7.2/offline_results/` |
| Offline checks of stored pages | stored pages read again with no request: 343 listing pages by 1.6.4's reader; all 1,531 stored page copies sorted by price layout; the exports of L10 and L8 checked by 1.6.5's source check against 1,478 and 951 stored pages; L12's export by 1.6.6's against 1,494; L12 and L10 replayed by 1.6.8 in the container, each record checked against its stored page; the 1,505 links the stored category pages record; the 275 decisions and S6's blank fields rechecked | [`1.6.4-collector/`](../evidence/offline-tests/1.6.4-collector/), [`1.6.5-collector/`](../evidence/offline-tests/1.6.5-collector/), [`source_check_l10/`](../evidence/verification/1.6.5/source_check_l10/), L12's run folder, [`container/`](../evidence/owner-azure-test/1.6.8/container/), [`reconciliation/1.6.8/`](../evidence/reconciliation/1.6.8/) |
| New developer-account live collection | fifteen runs on the owner's Oxylabs Web API trial (free credit), from the workstation, each on the release that ran it, 1.6.0 to 1.6.6. **None on 1.6.7 or 1.6.8** | [`data/RUN_SUMMARY.json`](../data/RUN_SUMMARY.json), `evidence/live/1.6.x/` |
| Owner Azure test | on Hamza's Azure test VM (Linux), with no provider request: both editions from their ZIPs, the container gate, the operator drill, the probe, the walkthrough. Not the client's environment | [`evidence/owner-azure-test/1.6.8/`](../evidence/owner-azure-test/1.6.8/) |
| Carried products | rows a run did not observe itself, each with its own run and date; never counted as fresh | each run's `products.json` and `record_map.json` |
| Reused field observations | UPCs and sizes from saved product-page reads, each naming that read's time, run, revision and page | each run's `field_dispositions.json` |
| Client-environment execution | none | [`MILESTONES.md`](MILESTONES.md) |
| Client-observed acceptance | none | [`TEST_PLAN.md`](TEST_PLAN.md), section 4 |

## 2. What was fixed

Nine collector releases and three probe releases. [`CORRECTION_MAP.md`](CORRECTION_MAP.md) gives each with its cause,
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
- **1.6.7** (never delivered; carried into 1.6.8): a partition is complete only through its children; a row read in part is
  never complete; the report gives each listing its effective outcome and each CSV row its verdict; the agreed category
  mapping, on fresh and carried rows; a carried row's UPC and size decided apart.
- **1.6.8:** a subcategory page of its own is read for the listings it names; one view linked twice is read once under its
  first name; a filtered link has the listing itself read; a filtered view of the row's own category is recorded and not
  read; two shelves are two listings; the mapping is per view; a read of a filtered view never completes a listing.
- **Probe 1.7.0:** C1, C3 and C5, and C2 and C4 in part.
- **Probe 1.7.1:** more of C2 and C4, not all of them (the 1.6.6 delivery said "completed"; see below).
  - The ledger writes after an answer wait no longer than the write window. It closes 30 s before the session's end
    by default: a third of the export reserve, at most 30 s.
  - After one refusal of the lock, the session does not wait for it again.
  - The supervisor's kill, reap and recovery all end by the hard end; the recovery runs in its own process, killed if
    it is still running then.
  - Each answer is kept as received under its dispatch's number, its body renamed durably after its status
    (write-through on Windows), so a crash before the kept copy loses nothing.
  - A body cut at its deadline is kept and recorded (`PARTIAL_RESPONSE`), and every evidence file is synced before it
    is renamed into place.
- **Probe 1.7.2:** C2 and C4 completed.
  - A body shorter than its declared length, zero bytes included, or a chunked body cut short, is kept as partial with its
    declared and received lengths and SHA-256. It is never parsed, and its money stays held.
  - Each worker status names its dispatch, and a recovery refuses a status of another dispatch or without that identity.
  - Evidence is read only from a regular file, bounded in size and time. A session's evidence must name its execution, so an
    earlier campaign's complete file is not taken.
  - The session's process tree is ended whole when it ends, the recovery's bound is monotonic, and the supervisor returns
    within its hard end plus 0.5 s.
  - The drip test asserts the deadline, the outcome, the partial and the worker's end, and a separate test forces a hung worker
    and checks a real kill and reap.

Four of these (1.6.2 to 1.6.5) correct a defect that a live run met: L4, L6, L7 and L10. 1.6.6 and 1.7.1 correct what the
client's review of 1.6.5 found, and 1.6.7, 1.6.8 and 1.7.2 what its review of 1.6.6 found, with what this delivery's own
checks found on the way. Each live release was frozen before a stage ran on it, and no earlier run is attributed to a later release.

## 3. What ran on the final revision, and where

No row below sent a request to a provider, to Walmart or to Classic. All on 2026-11-05 unless a row names another date.

| What | Where | When (UTC) | Result |
|---|---|---|---|
| Each new test on the code before it: 1.6.8's on 1.6.7, `7a96218` and `9c14425`; 1.6.7's on 1.6.6 | the workstation (Windows) and the owner's VM (Linux) | 10:35:39Z to 10:36:31Z (1.6.7's tests on 1.6.6, Linux); 17:31:13Z to 17:33:15Z and 21:16:57Z to 21:20:56Z (Windows); 21:20:03Z to 21:24:30Z (Linux) | they fail by the messages [`docs/VERIFICATION.md`](../source/walmart-oxylabs-1.6.8/docs/VERIFICATION.md) quotes ([`1.6.8-collector/`](../evidence/offline-tests/1.6.8-collector/)) |
| The whole Linux suite on the commit | the owner's Azure test VM, Ubuntu 24.04.5, one process per integration file | 2026-11-05, 20:55:56Z to 21:20:02Z | unit 554, integration 222 in 23 files, all passed |
| Both editions from their ZIPs, Linux: lock, ruff, format, mypy, `--version`, `validate-config`, migrations on PostgreSQL 16, unit and integration suites, the operator drill, a rollback to 1.6.6 | the owner's VM | 2026-11-05, 22:09:17Z to 22:55:26Z | 44 steps, 0 not as expected; each edition unit 554, integration 222 ([`qualification/`](../evidence/owner-azure-test/1.6.8/qualification/)) |
| The operator drill: start, status, pause, resume, export, storage, a refused publication (`PUBLICATION_REFUSED` at `ERROR`, exit 6, and exit 6 again on a manual `publish`, the last-good pointer unchanged), a run stopped by its credits that kept the published dataset, store isolation | the same, on synthetic pages | within the row above | passed in both editions ([transcripts](../evidence/owner-azure-test/1.6.8/qualification/logs/)) |
| The container gate: both images built from the ZIPs, smoke tests, migrations, L12 and L10 replayed from stored pages, a replay killed and resumed, every record checked against its page, rollback to a 1.6.6 image and forward, a daemon restart with data compared | the owner's VM, Docker unpacked into the gate's own folder | 2026-11-05, 21:24:30Z to 22:09:14Z | 89 steps, 1 not as expected: `after` (exit 1), the gate's databases still present, dropped afterwards ([`container/`](../evidence/owner-azure-test/1.6.8/container/)). The gate's walkthrough recording failed by its output (`command not found`). Image ids and digests are in [`IMAGES.md`](../evidence/owner-azure-test/1.6.8/container/IMAGES.md) |
| 1.6.8's coverage report of each of the fifteen live runs | that gate | within the row above | the input of the W4 tables below |
| Both editions from clean extractions of `WALMART_SOURCE_1.6.8.zip`, Windows | the workstation, with HTTP(S) sent to a closed local port | 2026-11-05, 21:00:57Z to 21:55:59Z | 37 steps, 0 not ok ([`package/`](../evidence/verification/1.6.8/package/)): in each edition the lock, ruff, format and mypy clean; 554 unit tests passed; the integration files the change touches, each in its own process: 151 and 73 passed |
| Bicep build and lint of both editions' `azure/main.bicep` | the same extraction; no deployment | 2026-11-05, 21:00:59Z to 21:01:09Z | exit 0; the lint reported nothing |
| The last-good publication against every listed fault | a clean extraction of the 1.6.8 Oxylabs edition ZIP, the workstation | 2026-11-05, 21:22:13Z to 21:25:33Z | 19 passed ([`last_good_publication/`](../evidence/verification/1.6.8/last_good_publication/)) |
| The probe 1.7.2 from its delivered ZIP | the owner's VM | 2026-11-06, 01:02:36Z to 01:05:06Z | 201 passed, 3 skipped ([`probe-1.7.2/`](../evidence/owner-azure-test/1.6.8/probe-1.7.2/)) |
| The probe 1.7.2 from its own clean export | the workstation | 2026-11-05, 15:58:16Z to 16:02:05Z | 199 passed, 5 skipped; the review tests fail on 1.7.1's `src/` (13) and pass on 1.7.2 (22 passed, 1 skipped) ([`offline_results/`](../classic-probe-1.7.2/offline_results/)) |
| The walkthrough recording | the owner's VM, in a session of its own after the gate | 2026-11-05, 23:00:16Z to 23:14:13Z | 163 s, English on-screen narration, no audio ([`walkthrough/`](../walkthrough/)) |

**The Windows integration suite was not run in full on this commit.** A full Windows pass of an earlier candidate was stopped by the
workstation's low-memory protection, after 56 integration tests had passed, and it was not forced. So Windows ran the unit suite and the files the change touches, each in its own
process, and the full integration suite ran on Linux, from the edition ZIPs, whose files equal those of `WALMART_SOURCE_1.6.8.zip`.

All fifteen live runs, each on the release that ran it (every one is a pilot, rejected at least by G3 because no
run read the whole catalogue, so nothing was published). **None ran on 1.6.7 or 1.6.8:**

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

**L12 on 1.6.6** (`01M6MC7YE4PBXV88G3PJ5ENW4B`), the last live run, with product-page collection on. It read page 1 of
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
  not on page 1. 44 UPCs of S6's rows have no read in any run ([`CORRECTION_MAP.md`](CORRECTION_MAP.md), W2; the 1.6.6 report said 45).
- `validate-export --run`: 10,301 of 10,301 records verified against 1,494 stored pages of 15 runs, no mismatch.
- Gates: G3 failed (a pilot covers no category in full) and G14 (the readiness marker, non-blocking). Every other
  gate passed.
- 13 submissions (robots.txt, the store page, 1 listing page, 10 product pages), all settled: 13 results, USD 0.0195.

L12 is a canary, not the demonstration of 500 or more products with detail on that the review asks of the final
revision. That run is capped at 45 submissions, USD 0.0675 at the reserve rate. Walmart's envelope
had USD 0.0225, which paid for L12, and now has USD 0.003 ([`TEST_PLAN.md`](TEST_PLAN.md), stage 1).

**L12 replayed on 1.6.8** (REPLAY, OWNER AZURE: the 1.6.8 Oxylabs image on the owner's Azure test VM, 2026-11-05, from L12's stored pages, with no request; never published). The replay (`01M6PSR0QX0H8X0HRE3YWNDA8Y`) exits 0 and is rejected as a pilot by G3 alone, with L12's 40 fresh valid records and 10,261 carried. Its export matches the one 1.6.6 published on all 10,301 records, matched by product URL, except in two ways: 9 UPCs filled from saved product pages (`historical.upc_filled`), three of them the UPCs W2 found recoverable; and 337 `sub_category` values that take the name the row's category page gives the view itself, among them "Fabric Softener" to "Fabric Softeners" (52 records: L12's 40 and 12 carried). `validate-export` verified all 10,301 records against their stored pages. A replay is not new collection: L12 stays a run of release 1.6.6 (`evidence/reconciliation/1.6.8/l12/`; `evidence/owner-azure-test/1.6.8/container/IMAGES.md`).

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

**Coverage** (W4). The scope is 1,104 listings in the 11 CSV rows. The fifteen runs read 715 listing
pages. The tables are made from release 1.6.8's own coverage report of each live run
([`W4_LISTINGS_1_6_8.csv`](../evidence/reconciliation/1.6.8/w4/W4_LISTINGS_1_6_8.csv), with each listing's change from 1.6.6 in
[`W4_TRANSITIONS_1_6_6_TO_1_6_8.csv`](../evidence/reconciliation/1.6.8/w4/W4_TRANSITIONS_1_6_6_TO_1_6_8.csv)):

| State of a listing | Listings |
|---|---:|
| `COMPLETE`: every page read and reconciled, never through a filtered view alone | 252 |
| `PARTIAL`: page 1 or more read, more pages remain | 213 |
| `NOT_ATTEMPTED`: named, never reached | 464 |
| `SUBCATEGORY_PAGE_NOT_READ`: a category page of its own (`/cp/`) that names listings; no run read it | 95 |
| `INCOMPLETE`: the read could not be reconciled or trusted | 15 |
| `RESULT_WINDOW`: more results than the site serves, to be read through child categories | 12 |
| `FILTERED_VIEW`: read only through a link that shows it filtered; the listing itself is not read | 7 |
| `CATEGORY_PAGE`, `NOT_FOUND` | 1 and 1 |
| Not in the row's listings: shop, brand, search, product or account pages | 35 |
| Not in the row's listings: excluded by the client's CSV | 6 |
| Not in the row's listings: a filtered view of the row's own category | 3 |

No CSV row is complete (0 of 11). The 1.6.6 tables counted 244 complete and 230 out of scope. Under the 1.6.8 rules, 239 of the 244 stay complete. Four were complete only through a filtered view, read in L10, and one (Cough) had a total that moved while it was read. The 230 out of scope are now told apart. 95 are subcategory pages of their own that no run read, so their rows stay open. 35 are not category pages, 6 are excluded by the CSV, and 1 is a filtered view of its row's own category. The other 93 are listings the census did not choose ([`w4/README.txt`](../evidence/reconciliation/1.6.8/w4/README.txt)).

The outstanding work is priced part by part in [`TEST_PLAN.md`](TEST_PLAN.md): about USD 4.63 for the known listing pages, USD 0.14 for
the 95 category pages of their own, USD 13.96 for the product pages of the products known today and, as an estimate, USD
75.48 to 152.93 for those of products not yet seen. Product pages are by far the largest part. The listings the category pages name
are not known until they are read, and retries are priced apart. The USD 4.07 of 1.6.6 priced the known listing pages of its table only.


**Recovery and publication:** see [`RECOVERY_AND_OPERATIONS.md`](RECOVERY_AND_OPERATIONS.md). Pause, overlap refusal,
forced kill and resume ran live on 1.6.1, 1.6.2 and 1.6.3, and by the integration suites of every later release. On 1.6.8 they
also ran in the container and in the operator drill, on stored and synthetic pages. The last-good publication was tested
synthetically on clean extractions of 1.6.5, 1.6.6 and 1.6.8.

## 5. Provider usage: the shared trial ledger

Hamza authorized USD 5 in total, across Walmart and Mariano's together, on the designated free trial account; no
top-up, overage or client-account charge. One account-wide ledger outside both repositories enforces it
(`.shared-oxylabs-trial-20261103`). Every submission's worst-case cost was reserved in it before it was
sent, and an unknown outcome stays reserved. Its figures, read after the last stage closed (L12, 2026-11-04T23:03:49Z; state
written 23:04:15Z), stand unchanged: the ledger's database was read again on 2026-11-06T01:10:58Z and has the same SHA-256 (`d9e882ae6a0f46e4…`):

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
own ledger agrees: 1,512 requests, USD 2.2470. Mariano's envelope is not reassigned to Walmart. That needs the owner's
separate written authorization, which has not been given, and the shared rule allows it only after Mariano's smallest
essential tests are done, or shown unable to proceed, and neither is the case. The
Oxylabs ceiling is 0 submissions and USD 0 since 2026-11-04T23:03:52Z, and no lease is active. This delivery made no provider request. Dollars are at the reserve rate
(USD 0.0015 per result, a list price), not an invoice. The Web API has no usage endpoint, and the provider
dashboard's reading is the owner's (A74). Per-stage figures: [`COST_AND_RUNTIME_REPORT.md`](COST_AND_RUNTIME_REPORT.md).

## 6. What remains, and why

| Milestone | State | What it needs |
|---|---|---|
| A demonstration of 500 or more with detail on, on 1.6.8 | BLOCKED_BUDGET | at most 45 submissions, USD 0.0675 at the reserve rate (TEST_PLAN.md, stage 1); USD 0.003 is left and the ceiling is 0 |
| The full catalogue: every CSV row, child and page | BLOCKED_BUDGET | the continuation priced in [`TEST_PLAN.md`](TEST_PLAN.md), on an approved budget |
| A timed full run, and the twice-weekly fit | BLOCKED_BUDGET | the full catalogue first |
| A natural available-to-unavailable transition | PENDING_OBSERVATION | it cannot be manufactured |
| Offline checks and a container build on the client's VM | PENDING_CLIENT_AZURE | the client's confirmation and the new key. The same checks passed on the owner's VM |
| The schedule enabled and observed | PENDING_OBSERVATION | the client's authorization |
| Scrape.do live | BLOCKED_BUDGET | separately supplied Scrape.do access |
| A live Classic successor | PENDING_CLIENT_DECISION | the client's choice, a Classic entitlement and limits |
| The owner's VM deallocated, the provider dashboard's reading, the earlier key's revocation | PENDING_OWNER | Hamza |
| Support and IP terms | PENDING_CLIENT_DECISION | a commercial agreement |

[`MILESTONES.md`](MILESTONES.md) gives the dated milestones and their conditions.


## 7. Client actions

The smallest decisions, each the client's:
1. Confirm the VM's restart and a window, and install `scraper_client_test_v2.pub` with the old key revoked. The
   offline checks on the VM follow.
2. Decide whether to fund the next live work in [`TEST_PLAN.md`](TEST_PLAN.md), and on which account: first the
   detail-on demonstration on 1.6.8 (at most 45 submissions, USD 0.0675), then the continuation, part by part. Walmart's share of the
   owner's trial allowance (free credit) has USD 0.003 left.
3. Later: authorize the schedule; decide on Classic; agree the support and IP terms.

## 8. Disclosures

- **The 1.6.6 delivery overstated the Classic corrections.** It said C2 and C4 were completed in probe 1.7.1 and called 1.6.6 the
  final revision. The client's review reproduced what was left open. Each such statement is listed in
  [`manifests/DOC_CORRECTIONS.md`](../manifests/DOC_CORRECTIONS.md), with the 45 UPCs (44), "the exact outstanding queue" (it lacked the category pages of their own)
  and "224 excluded with the page's own reason" (4 pages state no category path, and 55 do not prove local eligibility).
- **Four listings were counted complete from a read of a filtered view.** All four are L10's: Emergency Contraception (reported 4, placed 3), Celebrity Colognes
  and Allergy (0 of 0, `EMPTY`) and Contact solution (30 of 24). The category page links them only with a facet or filter in the query, so the read
  saw part of the listing at most. They are among the 244 that 1.6.6 published as complete. On 1.6.8 they are not complete. One more, Cough, is no longer complete, because its reported total moved while it was read (351, 349, 344 in L4r).
- **L10's rows carry the names of filtered views.** L10's fresh file has 31 rows "Subscription" and 19 "Cough" under Health & Wellness, each from a filtered view of
  listing `976760_4661388_6244277_7158394`, and its retained file has 5 rows "Great Value Pantry", a second link the Food page gives listing
  `976759_976794_2002490`. The published files are as collected. The 1.6.8 replay's names are in [`container/`](../evidence/owner-azure-test/1.6.8/container/).
- **Three 1.6.8 commits were replaced before anything was delivered.** `745607e`: one test kept its old expectation, found by the full Linux suite. `7a96218`: replayed on L12's stored pages, it
  renamed carried records after a second link the same page gives the same listing. `9c14425`: checked against the 1,505 stored links, its key ignored the filters in a link's query and the
  shelf a link names, so it could read a filtered view as the listing. No archive of them was delivered and no live run was made on them
  ([`1.6.8-collector/`](../evidence/offline-tests/1.6.8-collector/)). Release 1.6.7 (`7ee2fa1`) was prepared and never delivered; 1.6.8 carries it.
- **A wrong diagnosis on the owner's VM.** From about 18:16Z to 20:49Z on 2026-11-05 the workstation could not reach the VM, and Hamza was asked to start it. The VM had not stopped: its firewall admits
  SSH from one operator address, and the workstation's public address had changed. The job on the VM finished by itself at 19:25Z. It cost time, and it changed no result.
- **The full Windows integration suite did not run on 1.6.8.** See section 3. Each of its files that the change touches ran, and the whole suite ran on Linux from the same ZIPs.
- **The probe's Linux run differs by two steps.** Steps 10 and 11b write fixtures with helper scripts that the delivered probe does not hold, so the VM's run replays the packaged inputs
  instead ([`probe-1.7.2/`](../evidence/owner-azure-test/1.6.8/probe-1.7.2/)).
- **The owner's VM carries a change we disclose.** The 1.6.7 gate's Docker daemon deleted a `docker0` bridge that the 2026-11-01 test had left on the VM. It was restored after the 1.6.8 gate
  ([`HOST_STATE.md`](../evidence/owner-azure-test/1.6.8/HOST_STATE.md)).
- **No proxy-free or zero-cost route was tried.** None is approved on record, and the only live route is the funded provider, so no retailer request was made.
- **The 1.6.5 delivery overstated the Classic corrections and the alert advice.** It said C1 to C5 were corrected
  in probe 1.7.0; C2 and C4 were corrected in part. It gave operating documentation (N10-03) and the publication
  rows a pass while a refused automatic publication raised no documented alert. Both are corrected in this delivery,
  and each 1.6.5 statement is listed in [`manifests/DOC_CORRECTIONS.md`](../manifests/DOC_CORRECTIONS.md).
- **L12's rows name the subcategory "Fabric Softener".** The run named its listing by path (`--subcategory`), and
  release 1.6.6 took such a listing's name from its own page. The Household Essentials page names it "Fabric Softeners", which is the name
  the carried rows of L7 and L10 have. The products, URLs, prices and UPCs are as the page shows them. **Resolved in 1.6.7 and 1.6.8:** a listing takes the
  name its category page gives it, on fresh and carried rows, and a carried row's lineage keeps the earlier name. L12's published file is not edited.
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
- **Withheld recoveries.** On the releases that ran live, a carried row whose saved read gives conflicting sizes keeps its blank
  (`recovery_withheld`): 4 rows in L8, 12 in L10, 9 in L12. Since 1.6.7 such a read withholds the size only.
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
| [`source/`](../source/) | `WALMART_SOURCE_1.6.8.zip`, file for file: both editions of `85c29e7` |
| [`classic-probe-1.7.2/`](../classic-probe-1.7.2/) | `OXYLABS_CLASSIC_OFFLINE_PROBE_1.7.2.zip`, file for file |
| [`classic-probe-1.7.1/`](../classic-probe-1.7.1/), [`classic-probe-1.7.0/`](../classic-probe-1.7.0/) | the probes of the 1.6.6 and 1.6.5 deliveries, unchanged (superseded) |
| [`classic-probe/`](../classic-probe/) | the Walmart probe 1.5.2, as reviewed, unchanged |
| [`data/`](../data/) | the product files of L10 and L8, and of the 1.5.x runs, unchanged; the run summary |
| [`evidence/`](../evidence/) | by class; [`evidence/README.md`](../evidence/README.md) gives each folder |
| [`walkthrough/`](../walkthrough/) | the 1.6.8 recording on the owner's VM, and the 1.5.2 one, unchanged |
| [`review/`](.) | this report, the [summary PDF](WALMART_1.6.8_SUMMARY.pdf) and the other review documents |
| [`manifests/`](../manifests/) | the file map, redactions, exclusions, the checks, and `SHA256SUMS.txt`, written last |
