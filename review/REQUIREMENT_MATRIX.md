# Requirement matrix, release 1.6.8

Release 1.6.8, commit `85c29e7b2404500299056973f50c84b84e187a5a`, with the shared Classic probe 1.7.4 (commit `a1def53747dfabcb2ad9ca97efc421c1e70f0ac6`; 1.7.2, commit `7768514aa1ffbaa7f96ca242d7b64e495fffefa5`, in the 1.6.8 delivery). Store: Walmart #3891, 3900 Fountain Square Pl,
Waukegan, IL 60085, PICKUP. Written on 2026-11-05 and 2026-11-06 (UTC); W3, W7 and C2 corrected by the probe 1.7.4 revision (tag `review-1.6.8-probe174-20261111`, 2026-11-11).

This page gives the state of every requirement of this delivery:
- the work items of Hamza's brief (W1 to W8);
- the client's Classic findings (C1 to C5);
- the earlier 24-item audit (W01 to W24);
- the common data contract.

The 206 rows of the client's acceptance matrix are in [`ACCEPTANCE_MATRIX.csv`](ACCEPTANCE_MATRIX.csv). Its earlier
columns are kept as published: the 1.5.2 columns, the 1.6.5 columns and the 1.6.6 columns. Four columns are new: `state_1_6_8`,
`evidence_1_6_8`, `revision_1_6_8` and `note_1_6_8`. A 1.6.8 note says what changed from 1.6.6 and why, or "unchanged from 1.6.6". Paths in the
earlier columns name files of those publications, which are at the tags `review-1.5.2-20261103`, `review-1.6.5-20261104` and
`review-1.6.6-20261105`. What each correction changed is in [`CORRECTION_MAP.md`](CORRECTION_MAP.md).

**The probe 1.7.4 revision** appends four more columns, `state_1_6_8_probe_1_7_4`, `evidence_1_6_8_probe_1_7_4`,
`revision_1_6_8_probe_1_7_4` and `note_1_6_8_probe_1_7_4`, and changes none of the columns before them. A row it does not
touch copies its 1.6.8 state, evidence and revision, with the note "as in the 1.6.8 column".

Release 1.6.8 answers the client's review of 1.6.6, and carries release 1.6.7, which was never delivered. It is the revision of this
delivery, not a final release: a final tag is kept for a release that passes the applicable gates, and the live demonstration is not funded. The review showed that
some 1.6.6 statements were not accurate. Among them:
- that 1.6.6 was the final revision of the delivery;
- N8-01, that probe 1.7.1 completed C2 and C4;
- W2, that 45 UPCs remained;
- W4, that the coverage tables gave the exact outstanding queue.

Each is corrected here, and every such statement is listed in
[`../manifests/DOC_CORRECTIONS.md`](../manifests/DOC_CORRECTIONS.md). Live results stay attributed to the release
that collected them: L10 to 1.6.4, the canaries L11 and L11b to 1.6.5, the canary L12 to 1.6.6. **No live run was made on 1.6.7 or 1.6.8.**

## The states

Each state names what the evidence is. None of them means "accepted by the client".

| State | Meaning |
|---|---|
| PASS_OFFLINE | Passed with no request to a provider or to Walmart. This covers source inspection, unit and PostgreSQL integration tests, static checks, the clean-extraction verification of the delivered ZIPs, synthetic faults and the offline replay of stored pages. All of it ran on 1.6.8 unless the row names another release. |
| PASS_DEVELOPER_LIVE | Shown by live runs in the developer environment: the owner's Oxylabs Web API trial account (free credit), from the workstation, on the release the row names. It is neither the client's environment nor client acceptance. |
| PASS_OWNER_AZURE | Passed on Hamza's own Azure test VM, on the release the row names, with no request to a provider or to Walmart. It is neither the client's environment nor client acceptance. |
| PENDING_CLIENT_AZURE | Needs the client's Azure environment. The client confirmed that their VM is deallocated. Access waits for the client's confirmation of a restart and window, and for the new key to be installed with the old one revoked. |
| PENDING_OBSERVATION | Needs something that cannot be manufactured: a natural available-to-unavailable transition, or scheduled runs observed after the client authorizes the schedule. |
| PENDING_CLIENT_DECISION | The client's choice. For example: support and IP terms, a live Classic successor with its entitlement and limits, or the acceptance itself. |
| PENDING_OWNER | Hamza's action. For example: deallocating the owner's test VM, the provider dashboard reading, the developer key's rotation. |
| BLOCKED_BUDGET | Implemented and tested offline, but its live proof needs more requests than the trial allowance has left. Scrape.do is in this state too: this delivery authorizes no Scrape.do spending. |
| BLOCKED_SOURCE | The source does not offer what the requirement needs. No row has this state in 1.6.8. |
| NOT_APPLICABLE_BY_CLARIFICATION | Superseded by the client's clarification that the four deal fields are always `""`. |
| REPORTED_NOT_VERIFIED | A fact someone else reported that was not checked here: the client's statement that their VM is deallocated. It is used in notes only. |

States of the 206 rows, on 1.6.8: PASS_OFFLINE 91, PASS_DEVELOPER_LIVE 66, PASS_OWNER_AZURE 5, BLOCKED_BUDGET 22, PENDING_CLIENT_AZURE 5, PENDING_OWNER 4, NOT_APPLICABLE_BY_CLARIFICATION 6, PENDING_CLIENT_DECISION 4, PENDING_OBSERVATION 3, BLOCKED_SOURCE 0. In the probe 1.7.4 revision's columns: PASS_OFFLINE 91, PASS_DEVELOPER_LIVE 64, PASS_OWNER_AZURE 5, BLOCKED_BUDGET 24, PENDING_CLIENT_AZURE 5, PENDING_OWNER 4, NOT_APPLICABLE_BY_CLARIFICATION 6, PENDING_CLIENT_DECISION 4, PENDING_OBSERVATION 3. There, 2 rows change state, A25 and P4-02 (PASS_DEVELOPER_LIVE to BLOCKED_BUDGET: the 59 unresolved sponsored and variant products), and 17 rows have a new note: those two, A24, B16 and N5-04 (the 275 corrected), the 11 rows of the Classic probe (their evidence is now probe 1.7.4's, tested on Windows and on Linux) and B26 (Mariano's pin). On 1.6.8, 6 rows changed state from 1.6.6: A61 (PENDING_CLIENT_AZURE to PASS_OWNER_AZURE), A64 (PENDING_OWNER to PASS_OWNER_AZURE), B22 (PENDING_CLIENT_AZURE to PASS_OWNER_AZURE), N10-02 (PENDING_CLIENT_AZURE to PASS_OWNER_AZURE), N10-04 (PENDING_OWNER to PASS_OWNER_AZURE), N10-08 (PENDING_OWNER to PASS_OFFLINE). 74 rows have a new note written for this delivery, and the others keep their state with their evidence made again on 1.6.8 where it was 1.6.6's.

## The work items of this delivery (W1 to W8)

| Item | State | What was done, and where |
|---|---|---|
| **W1** The four deal fields `""` | PASS_OFFLINE, PASS_DEVELOPER_LIVE | Release 1.6.0 enforces the rule at the final export boundary (`publishing/exports.py`) and in every path before it. The tests start from nonempty deal data. Every row of every 1.6.x export has `""` ([`manifests/check_data.py`](../manifests/check_data.py)), L12's 10,301 rows included, and so does the export of each 1.6.8 replay in the container gate. No credit was spent on offers. [`CORRECTION_MAP.md`, W1](CORRECTION_MAP.md#the-four-deal-fields-w1) |
| **W2** UPC, size and provenance | PASS_DEVELOPER_LIVE; BLOCKED_BUDGET for 44 UPCs with no read; PENDING_OWNER for the key rotation | A per-row, per-field correction table, from S6's 706 rows to their state in L8, and a recheck of every blank against every saved read. Of the 52 UPCs missing after 1.6.3: L12 filled 3 live (leading zeros kept); 3 are stated by saved reads that 1.6.6 withheld only for a size conflict, and 1.6.7 recovers them; 44 have no read in any run; 1 is absent from its own page; 1 page was of another item. UPC and size are decided apart since 1.6.7. [W2](CORRECTION_MAP.md#upc-size-and-provenance-w2) |
| **W3** Sponsored and variant decisions | PASS_DEVELOPER_LIVE for the reads and the 216 products with a source-supported outcome; BLOCKED_BUDGET for the 59 unresolved | All 275 queued products were read live and are reconciled at row level: 48 included; 165 excluded because their own page places them in another category, identified; 3 duplicates linked to their originals and page hashes; **59 unresolved**: 4 whose page gives no category path (`categoryPathId` -1, no breadcrumb) and 55 whose page does not prove local eligibility. *(Corrected by the probe 1.7.4 revision: the 1.6.8 text counted these 59 as excluded and gave 0 unresolved, but no source evidence supports their exclusion. [Recount](../evidence/reconciliation/1.6.8-probe174/w3/).)* Settling them needs their pages read again with the store's context (paid requests). The client's 11 and 30 cases are traced; 7 of the 30 (V22, V25 to V30) are among the 59. The 44 unread UPCs are a separate queue. [W3](CORRECTION_MAP.md#sponsored-and-variant-products-w3) |
| **W4** Full production scope | BLOCKED_BUDGET | Coverage tables by row, root, child and page, made again from 1.6.8's own reports of the fifteen live runs. 252 of 1,104 listings are complete and no CSV row is (0 of 11). Open: 213 partial, 464 not attempted, 95 category pages of their own not read, 15 incomplete, 12 at the result window, 7 read only through a filtered view. 1.6.8 reads what earlier releases skipped; no live run has shown it. [`TEST_PLAN.md`](TEST_PLAN.md) prices the remaining work part by part. [W4](CORRECTION_MAP.md#coverage-partitions-and-the-census-w4) |
| **W5** Final-revision live qualification | BLOCKED_BUDGET on 1.6.8; PASS_DEVELOPER_LIVE on earlier releases (the canary L12 on 1.6.6, detail on; L10 on 1.6.4, detail off) | Fifteen staged runs, each on a frozen release; none on 1.6.7 or 1.6.8. L12 on 1.6.6, detail on: 40 fresh valid, 10 product pages, UPC 27 of 40, its export of 10,301 records verified (10,261 of them carried). L10 on 1.6.4 gave 7,055 fresh valid products with detail off; with detail on, the last run of 500 or more is L8 on 1.6.3 (675). A run of 500 or more on 1.6.8 is capped at 45 submissions, USD 0.0675; USD 0.003 is left and the ceiling is 0. On 1.6.8, L12 and L10 were replayed from stored pages in the container: a replay, not new collection. [`data/RUN_SUMMARY.json`](../data/RUN_SUMMARY.json), [`MILESTONES.md`](MILESTONES.md) |
| **W6** Retention, recovery, publication, capacity | PASS_DEVELOPER_LIVE / PASS_OFFLINE; PASS_OWNER_AZURE (container); BLOCKED_BUDGET (full-run capacity); PENDING_OBSERVATION (cadence) | Recovery ran live on 1.6.1 to 1.6.3, and on 1.6.8 in the suites, the container and the operator drill. The last-good publication was tested synthetically on a clean 1.6.8. A refused automatic publication is an `ERROR` with exit 6, on its first attempt and on the retry, and the last-good pointer stays. Concurrency ran live with two workers. The schedule is kept disabled, with a written daylight-saving policy. [`RECOVERY_AND_OPERATIONS.md`](RECOVERY_AND_OPERATIONS.md) |
| **W7** Classic findings, Mariano's adapter | PASS_OFFLINE; a live successor is PENDING_CLIENT_DECISION | C1, C3 and C5 are corrected in probe 1.7.0; C2 and C4 were advanced in 1.7.1 and completed in probe 1.7.2, with live mode disabled, on Windows and on Linux, except that on Windows C2's process tree was held only when a job object could be made and joined: probe 1.7.4 corrects that (tested on Windows and on Linux). The adapter's identity is explicit and unchanged. [`CLASSIC_PROBE_CORRECTIONS.md`](CLASSIC_PROBE_CORRECTIONS.md) |
| **W8** The earlier 24-item audit | as below | See the next table. |

## The Classic findings (C1 to C5)

| Finding | State | Correction |
|---|---|---|
| C1 Redirect policy absent | PASS_OFFLINE | 1.7.0: `http.client` in a worker process. Redirects are never followed, and the worker accepts one target only. |
| C2 A timeout leaves the worker alive; body, processing and export unbounded | PASS_OFFLINE | 1.7.0: one process per request, killed and reaped at its allowance; bounded bodies, headers and decompression; a session supervisor. 1.7.1: the ledger writes after an answer wait no longer than the write window; the supervisor's kill, reap and recovery end by the hard end, the recovery in its own process. **1.7.2 completes it:** evidence is read only from a regular file, bounded in size and time (a FIFO, a link or a folder is refused at once); a session's evidence must name its execution, so an earlier campaign's complete file is not taken; the session's process tree is ended whole when it ends (on Windows only when a job object could be made and joined: see 1.7.4); the recovery's bound is monotonic; the supervisor returns within its hard end plus 0.5 s; an unknown charge stays reserved. **1.7.4 (the client's review of 1.7.2):** on Windows a session runs only once a verified job object holds it, created suspended and confirmed before it runs; a failure refuses it with no fallback, and the suspended process is ended and reaped; a cleanup that cannot be verified stays `unknown` or `failed` in the status and the recovery's manifest. The 5 new tests fail on 1.7.2 by their output and pass on 1.7.4, on Windows; the whole suite gives 229 passed, 5 skipped. On Linux, from the archive: 227 passed, 7 skipped, and the 3 review tests that run there pass on 1.7.4 and 2 fail on 1.7.2. |
| C3 Stale clock across the ledger lock and dispatch | PASS_OFFLINE | 1.7.0: the time is read under the lock, the lock wait is bounded, and every stop is checked again just before sending. |
| C4 Responses only in memory | PASS_OFFLINE | 1.7.0: each answer written atomically and indexed before the next paid step, and recovered after a crash. 1.7.1: each answer kept as received under its dispatch's number; the body renamed durably after its status; a body cut at its deadline recorded (`PARTIAL_RESPONSE`). **1.7.2 completes it:** a body shorter than its declared length, zero bytes included, or a chunked body cut short, is kept as partial with its declared and received lengths and SHA-256, is never parsed, and its money stays held; the transport and the recovery check the declared length again; a worker killed after it named its file no longer loses a whole answer or a kept partial; a recovery refuses a status of another dispatch or without that identity; no recovery sends a request. Exact-length bodies, bodiless responses and the byte limit are controlled by tests. |
| C5 The default retry sleep is a no-op | PASS_OFFLINE | 1.7.0: a real bounded backoff that never runs past the deadline, with `Retry-After` honoured up to 60 s. |

The 1.6.5 delivery gave C2 and C4 as corrected in 1.7.0, and the 1.6.6 delivery as completed in 1.7.1. Neither was accurate. The client's review reproduced what 1.7.1 left open: the review's tests fail on 1.7.1's code (13 on Windows; 14 on Linux, where the FIFO test runs) and pass on 1.7.2. The drip test that failed on Linux now asserts what happened, and a separate test forces a hung worker. The 1.6.8 delivery gave C2 as completed in 1.7.2; on Windows it was not, in two cases the client's review of 1.7.2 found: a job object that could not be made or joined, and a count that could not be read. Probe 1.7.4 corrects both, each first reproduced on 1.7.2's code on Windows. The tests, the pinned diffs and what is not established (power loss, among others) are in [`CLASSIC_PROBE_CORRECTIONS.md`](CLASSIC_PROBE_CORRECTIONS.md). No Classic scraping request has ever been sent. The only request with Classic-style credentials was W0, refused with HTTP 401 ([`TECHNICAL_REPORT.md`](TECHNICAL_REPORT.md), section 8). A live successor needs its own version, a Classic username and password with an entitlement, and the account owner's authorization.

## The earlier 24-item audit (W01 to W24)

| Items | State | In this delivery |
|---|---|---|
| W01, W02: client VM and key | PENDING_CLIENT_AZURE | The VM is deallocated (the client's statement). No SSH attempt was made. The new public key waits for the client. The container was built and tested on the owner's Azure test VM instead: an owner test, not the client's environment. |
| W03: the developer key's action | PENDING_OWNER | The key on file is not the earlier flagged key. Whether that key is revoked cannot be verified from here. No key value is disclosed. |
| W04 to W10: stage bounds, field and identity reconciliation, roots, children and pages, the outstanding queue | PASS_DEVELOPER_LIVE; BLOCKED_BUDGET for full scope | One shared trial ledger bounds every stage (see [`COST_AND_RUNTIME_REPORT.md`](COST_AND_RUNTIME_REPORT.md)). W2, W3 and W4 are above. |
| W11: a fresh demonstration on the final revision | BLOCKED_BUDGET on 1.6.8 | 500 or more on 1.6.8 with detail on is not funded. The largest runs stay attributed to their releases (L10 on 1.6.4, 7,055 with detail off; L8 on 1.6.3, 675 with detail on; the canary L12 on 1.6.6, 40 with detail on). S6 is not relabelled. |
| W12: a live offer example | NOT_APPLICABLE_BY_CLARIFICATION | The four fields are always `""`. No offer example was sought. |
| W13 to W20: retention, recovery, last-good, concurrency, full costs, cadence, provider decision, client acceptance | each at its own level | Retention: PASS_DEVELOPER_LIVE. Recovery: PASS_DEVELOPER_LIVE (1.6.1 to 1.6.3) and PASS_OFFLINE (1.6.8). Last-good: PASS_OFFLINE (synthetic), with a refused publication an alert. Concurrency: PASS_DEVELOPER_LIVE, with full-run sizing BLOCKED_BUDGET. Full costs: BLOCKED_BUDGET (estimates only). Cadence: PENDING_OBSERVATION. Provider and client acceptance: PENDING_CLIENT_DECISION. |
| W21: both editions | PASS_OFFLINE; PASS_OWNER_AZURE (container); BLOCKED_BUDGET live | Both editions are built from one revision, and both were tested from their ZIPs, on Linux and Windows, and built as images. Scrape.do live qualification needs separately supplied access. |
| W22: stale rows, versions, settings, milestones | PASS_OFFLINE | This page, the four new matrix columns and [`MILESTONES.md`](MILESTONES.md). |
| W23: developer compute cleanup | PENDING_OWNER | Hamza's own resources: this delivery's gates removed what they made on that VM ([`HOST_STATE.md`](../evidence/owner-azure-test/1.6.8/HOST_STATE.md)), and deallocating it is Hamza's task. The client's VM was not touched, and no evidence was deleted. |
| W24: support and IP terms | PENDING_CLIENT_DECISION | A commercial decision, not a code item. |

## The common data contract

| Rule | State | Where it is enforced, and shown |
|---|---|---|
| The 22 fields in order, all strings, `""` when missing; `gupc` and `unit_price` always `""`; no 23rd field; `url` not renamed | PASS_OFFLINE, PASS_DEVELOPER_LIVE | `core/schema.py` and `publishing/exports.py`; `check_data.py` checks every published 1.6.x export |
| Store and PICKUP proved from the returned page, never from the request | PASS_DEVELOPER_LIVE | every page of every 1.6.x run (each run's store attestations), L12 included |
| Eligible products retained indefinitely; a carried row keeps its own `crawl_date` | PASS_DEVELOPER_LIVE | L8: 675 fresh and 1,840 carried; L10: 7,057 fresh and 3,244 carried; L12: 40 fresh and 10,261 carried; each carried row with its own run and date. A rename under the agreed mapping keeps the earlier name in the row's lineage |
| The approximate-weight exclusion; faithful pack sizes | PASS_OFFLINE, PASS_DEVELOPER_LIVE | the weight-wording tests; W2 gives each size's source |
| Sponsored status alone decides nothing | PASS_DEVELOPER_LIVE | W3 |
| `not_attempted`, `blocked`, `request_failed`, `readable_source_absent` and `conflict` kept apart | PASS_OFFLINE, PASS_DEVELOPER_LIVE | each run's `field_dispositions.csv`; 1.6.3 records Walmart's not-found page as `request_failed` |
| Every exported record checked against the stored page it was read from | PASS_OFFLINE, PASS_DEVELOPER_LIVE | the source check of 1.6.5 and later reads all three price layouts; L10's and L8's exports verified in full ([`evidence/verification/1.6.5/source_check_l10/`](../evidence/verification/1.6.5/source_check_l10/)), and L12's on 1.6.6 (10,301 of 10,301) |
| At least 500 genuine distinct fresh valid products from one run | PASS_DEVELOPER_LIVE on earlier releases; BLOCKED_BUDGET on 1.6.8 | L10 on 1.6.4 (7,055, detail off, re-validated on 1.6.5); L8 on 1.6.3 (675, detail on). Not on 1.6.6: its one run is the canary L12 (40). Not on 1.6.8: no live run |
| Production: every root, child, partition and page | BLOCKED_BUDGET | W4 |
| Checkpoints, bounded retries, deduplication, recovery, overlap protection, last-good publication | PASS_DEVELOPER_LIVE, PASS_OFFLINE | [`RECOVERY_AND_OPERATIONS.md`](RECOVERY_AND_OPERATIONS.md) |
