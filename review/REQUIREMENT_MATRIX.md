# Requirement matrix, release 1.6.6

Release 1.6.6, commit `39cc61f61ee694c0659a611310605bee6ed42d6b` (built as `cbea802`), with the shared Classic
probe 1.7.1. Store: Walmart #3891, 3900 Fountain Square Pl, Waukegan, IL 60085, PICKUP. Written on 2026-11-04 and
2026-11-05 (UTC).

This page gives the state of every requirement of this delivery:
- the work items of Hamza's brief (W1 to W8);
- the client's Classic findings (C1 to C5);
- the earlier 24-item audit (W01 to W24);
- the common data contract.

The 206 rows of the client's acceptance matrix are in [`ACCEPTANCE_MATRIX.csv`](ACCEPTANCE_MATRIX.csv). Its earlier
columns are kept as published: the 1.5.2 columns, and the 1.6.5 columns `state_1_6_5`, `evidence_1_6_x`,
`revision_1_6_x` and `note_1_6_x`. Four columns are new: `state_1_6_6`, `evidence_1_6_6`, `revision_1_6_6` and
`note_1_6_6`. A 1.6.6 note says what changed from 1.6.5 and why, or "unchanged from 1.6.5". Paths in the 1.5.2 and
1.6.5 columns name files of those publications, which are at the tags `review-1.5.2-20261103` and
`review-1.6.5-20261104`. What each correction changed is in [`CORRECTION_MAP.md`](CORRECTION_MAP.md).

Release 1.6.6 is the final revision of this delivery. It answers the client's review of 1.6.5. Two findings of that
review show that 1.6.5's states were not accurate:
- N8-01 said C1 to C5 were corrected, when C2 and C4 were corrected only in part;
- N10-03 passed the operating documentation, when a refused automatic publication raised none of its alerts.

Both are corrected here, and every such 1.6.5 statement is listed in
[`../manifests/DOC_CORRECTIONS.md`](../manifests/DOC_CORRECTIONS.md). Live results stay attributed to the release
that collected them: L10 to 1.6.4, the canaries L11 and L11b to 1.6.5, the canary L12 to 1.6.6.

## The states

Each state names what the evidence is. None of them means "accepted by the client".

| State | Meaning |
|---|---|
| PASS_OFFLINE | Passed with no request to a provider or to Walmart. This covers source inspection, unit and PostgreSQL integration tests, static checks, the clean-extraction verification of the delivered ZIPs, synthetic faults and the offline replay of stored pages. All of it ran on 1.6.6 unless the row names another release. |
| PASS_DEVELOPER_LIVE | Shown by live runs in the developer environment: the user's Oxylabs Web API trial account, from the workstation, on the release the row names. It is neither the client's environment nor client acceptance. |
| PENDING_CLIENT_AZURE | Needs the client's Azure environment. The client confirmed that their VM is deallocated. Access waits for the client's confirmation of a restart and window, and for the new key to be installed with the old one revoked. |
| PENDING_OBSERVATION | Needs something that cannot be manufactured: a natural available-to-unavailable transition, or scheduled runs observed after the client authorizes the schedule. |
| PENDING_CLIENT_DECISION | The client's choice. For example: support and IP terms, a live Classic successor with its entitlement and limits, or the acceptance itself. |
| PENDING_OWNER | Hamza's action. For example: a walkthrough recording, his own test VM, the provider dashboard reading, the developer key's rotation, a summary PDF. |
| BLOCKED_BUDGET | Implemented and tested offline, but its live proof needs more requests than the trial allowance has left. Scrape.do is in this state too: this delivery authorizes no Scrape.do spending. |
| BLOCKED_SOURCE | The source does not offer what the requirement needs. No row has this state in 1.6.6. |
| NOT_APPLICABLE_BY_CLARIFICATION | Superseded by the client's clarification that the four deal fields are always `""`. |
| REPORTED_NOT_VERIFIED | A fact someone else reported that was not checked here: the client's statement that their VM is deallocated. It is used in notes only. |

States of the 206 rows (unchanged in number from 1.6.5; 43 rows have a new note, and the others keep their state
with their evidence made again on 1.6.6 where it was 1.6.5's): PASS_OFFLINE 90, PASS_DEVELOPER_LIVE 66,
BLOCKED_BUDGET 22, PENDING_CLIENT_AZURE 8, PENDING_OWNER 7, NOT_APPLICABLE_BY_CLARIFICATION 6,
PENDING_CLIENT_DECISION 4, PENDING_OBSERVATION 3, BLOCKED_SOURCE 0.

## The work items of this delivery (W1 to W8)

| Item | State | What was done, and where |
|---|---|---|
| **W1** The four deal fields `""` | PASS_OFFLINE, PASS_DEVELOPER_LIVE | Release 1.6.0 enforces the rule at the final export boundary (`publishing/exports.py`) and in every path before it. The tests start from nonempty deal data. Every row of every 1.6.x export has `""` ([`manifests/check_data.py`](../manifests/check_data.py)), L12's 10,301 rows included. No credit was spent on offers. [`CORRECTION_MAP.md`, W1](CORRECTION_MAP.md#the-four-deal-fields-w1) |
| **W2** UPC, size and provenance | PASS_DEVELOPER_LIVE; BLOCKED_BUDGET for 45 UPCs never read; PENDING_OWNER for the key rotation | A per-row, per-field correction table, from S6's 706 rows to their state in L8, with its aggregates. 48 UPCs had never been read; L12 on 1.6.6 read 3 of them live (leading zeros kept), so 45 remain. [W2](CORRECTION_MAP.md#upc-size-and-provenance-w2) |
| **W3** Sponsored and variant decisions | PASS_DEVELOPER_LIVE | All 275 queued products were read live and decided. The client's 11 and 30 cases are traced. [W3](CORRECTION_MAP.md#sponsored-and-variant-products-w3) |
| **W4** Full production scope | BLOCKED_BUDGET | Two censuses: L7 on 1.6.3 and L10 on 1.6.4. Together they read page 1 of 451 listings in the 11 CSV rows; 395 listings their category pages named were not reached before L10's ceiling. Coverage tables by row, root, child and page give the exact outstanding queue (1.6.6: L12's one page added, no state changed). No CSV row is complete (0 of 11). [`TEST_PLAN.md`](TEST_PLAN.md) prices the remaining work. [W4](CORRECTION_MAP.md#coverage-partitions-and-the-census-w4) |
| **W5** Final-revision live qualification | PASS_DEVELOPER_LIVE (the canary L12 on 1.6.6, detail on; L10 on 1.6.4, detail off); BLOCKED_BUDGET for 500 or more with detail on | Fifteen staged runs, each on a frozen release. L12 on the final 1.6.6, detail on: 40 fresh valid, 10 product pages, UPC 27 of 40, its export of 10,301 records verified. L10 on 1.6.4 gave 7,055 fresh valid products with detail off; with detail on, the last run of 500 or more is L8 on 1.6.3 (675). A run of 500 or more on 1.6.6 needs at most about USD 0.07; USD 0.003 is left. [`data/RUN_SUMMARY.json`](../data/RUN_SUMMARY.json), [`MILESTONES.md`](MILESTONES.md) |
| **W6** Retention, recovery, publication, capacity | PASS_DEVELOPER_LIVE / PASS_OFFLINE; PENDING_CLIENT_AZURE (container); BLOCKED_BUDGET (full-run capacity); PENDING_OBSERVATION (cadence) | Recovery ran live on 1.6.1 to 1.6.3. The last-good publication was tested synthetically on a clean 1.6.6. A refused automatic publication is an `ERROR` with exit 6 since 1.6.6, and the alert advice names it. Concurrency ran live with two workers. The schedule is kept disabled, with a written daylight-saving policy. [`RECOVERY_AND_OPERATIONS.md`](RECOVERY_AND_OPERATIONS.md) |
| **W7** Classic findings, Mariano's adapter | PASS_OFFLINE; a live successor is PENDING_CLIENT_DECISION | C1, C3 and C5 are corrected in probe 1.7.0; C2 and C4 are completed in probe 1.7.1, with live mode disabled. The adapter's identity is explicit and unchanged. [`CLASSIC_PROBE_CORRECTIONS.md`](CLASSIC_PROBE_CORRECTIONS.md) |
| **W8** The earlier 24-item audit | as below | See the next table. |

## The Classic findings (C1 to C5)

| Finding | State | Correction |
|---|---|---|
| C1 Redirect policy absent | PASS_OFFLINE | 1.7.0: `http.client` in a worker process. Redirects are never followed, and the worker accepts one target only. |
| C2 A timeout leaves the worker alive; body, processing and export unbounded | PASS_OFFLINE | 1.7.0: one process per request, killed and reaped at its allowance; bounded bodies, headers and decompression; a session supervisor. **1.7.1** completes it: the ledger writes after an answer wait no longer than the write window, which ends 30 s before the session's end by default (a third of the export reserve, at most 30 s); after one refusal of the lock, the session does not wait for it again; the export's checks and manifest run until the true end; the supervisor's kill, reap and recovery all end by the hard end, the recovery in its own process, killed if it is still running then. |
| C3 Stale clock across the ledger lock and dispatch | PASS_OFFLINE | 1.7.0: the time is read under the lock, the lock wait is bounded, and every stop is checked again just before sending. |
| C4 Responses only in memory | PASS_OFFLINE | 1.7.0: each answer written atomically and indexed before the next paid step, and recovered after a crash. **1.7.1** completes it: each answer is kept as received, privately, under its dispatch's number; the worker writes its status first, then renames the body durably (a write-through rename on Windows, a synced folder on Linux and macOS), so a crash before the kept copy loses nothing; a body cut short is kept and recorded once (`PARTIAL_RESPONSE`); every evidence file, the manifest included, is synced before it is renamed into place. |
| C5 The default retry sleep is a no-op | PASS_OFFLINE | 1.7.0: a real bounded backoff that never runs past the deadline, with `Retry-After` honoured up to 60 s. |

The 1.6.5 delivery gave C2 and C4 as corrected in 1.7.0. Seven reproduction tests show what 1.7.0 left open: they
fail on 1.7.0's code and pass on 1.7.1. The tests, the pinned diffs and what is not established (power loss, among
others) are in [`CLASSIC_PROBE_CORRECTIONS.md`](CLASSIC_PROBE_CORRECTIONS.md). No Classic scraping request has ever
been sent. The only request with Classic-style credentials was W0, refused with HTTP 401
([`TECHNICAL_REPORT.md`](TECHNICAL_REPORT.md), section 8). A live successor needs its own version, a Classic username
and password with an entitlement, and the account owner's authorization.

## The earlier 24-item audit (W01 to W24)

| Items | State | In this delivery |
|---|---|---|
| W01, W02: client VM and key | PENDING_CLIENT_AZURE | The VM is deallocated (the client's statement). No SSH attempt was made. The new public key waits for the client. Locally, both edition ZIPs were installed from their locks and tested. The container was not built: there is no container runtime here. |
| W03: the developer key's action | PENDING_OWNER | The key on file is not the earlier flagged key. Whether that key is revoked cannot be verified from here. No key value is disclosed. |
| W04 to W10: stage bounds, field and identity reconciliation, roots, children and pages, the outstanding queue | PASS_DEVELOPER_LIVE; BLOCKED_BUDGET for full scope | One shared trial ledger bounds every stage (see [`COST_AND_RUNTIME_REPORT.md`](COST_AND_RUNTIME_REPORT.md)). W2, W3 and W4 are above. |
| W11: a fresh demonstration on the final revision | PASS_DEVELOPER_LIVE (a canary with detail on); BLOCKED_BUDGET for 500 or more | L12 on 1.6.6: 40 fresh valid, detail on, its export verified. 500 or more on 1.6.6 with detail on is not funded; the largest runs stay attributed to their releases (L10 on 1.6.4, 7,055 with detail off; L8 on 1.6.3, 675 with detail on). S6 is not relabelled. |
| W12: a live offer example | NOT_APPLICABLE_BY_CLARIFICATION | The four fields are always `""`. No offer example was sought. |
| W13 to W20: retention, recovery, last-good, concurrency, full costs, cadence, provider decision, client acceptance | each at its own level | Retention: PASS_DEVELOPER_LIVE. Recovery: PASS_DEVELOPER_LIVE (1.6.1 to 1.6.3) and PASS_OFFLINE (1.6.6). Last-good: PASS_OFFLINE (synthetic), with a refused publication now an alert. Concurrency: PASS_DEVELOPER_LIVE, with full-run sizing BLOCKED_BUDGET. Full costs: BLOCKED_BUDGET (estimates only). Cadence: PENDING_OBSERVATION. Provider and client acceptance: PENDING_CLIENT_DECISION. |
| W21: both editions | PASS_OFFLINE; BLOCKED_BUDGET live | Both editions are built from one revision, and both were tested from their ZIPs. Scrape.do live qualification needs separately supplied access. |
| W22: stale rows, versions, settings, milestones | PASS_OFFLINE | This page, the four new matrix columns and [`MILESTONES.md`](MILESTONES.md). |
| W23: developer compute cleanup | PENDING_OWNER | Hamza's own resources. The client's VM was not touched, and no evidence was deleted. |
| W24: support and IP terms | PENDING_CLIENT_DECISION | A commercial decision, not a code item. |

## The common data contract

| Rule | State | Where it is enforced, and shown |
|---|---|---|
| The 22 fields in order, all strings, `""` when missing; `gupc` and `unit_price` always `""`; no 23rd field; `url` not renamed | PASS_OFFLINE, PASS_DEVELOPER_LIVE | `core/schema.py` and `publishing/exports.py`; `check_data.py` checks every published 1.6.x export |
| Store and PICKUP proved from the returned page, never from the request | PASS_DEVELOPER_LIVE | every page of every 1.6.x run (each run's store attestations), L12 included |
| Eligible products retained indefinitely; a carried row keeps its own `crawl_date` | PASS_DEVELOPER_LIVE | L8: 675 fresh and 1,840 carried; L10: 7,057 fresh and 3,244 carried; L12: 40 fresh and 10,261 carried; each carried row with its own run and date |
| The approximate-weight exclusion; faithful pack sizes | PASS_OFFLINE, PASS_DEVELOPER_LIVE | the weight-wording tests; W2 gives each size's source |
| Sponsored status alone decides nothing | PASS_DEVELOPER_LIVE | W3 |
| `not_attempted`, `blocked`, `request_failed`, `readable_source_absent` and `conflict` kept apart | PASS_OFFLINE, PASS_DEVELOPER_LIVE | each run's `field_dispositions.csv`; 1.6.3 records Walmart's not-found page as `request_failed` |
| Every exported record checked against the stored page it was read from | PASS_OFFLINE, PASS_DEVELOPER_LIVE | the source check of 1.6.5 and 1.6.6 reads all three price layouts; L10's and L8's exports verified in full ([`evidence/verification/1.6.5/source_check_l10/`](../evidence/verification/1.6.5/source_check_l10/)), and L12's on 1.6.6 (10,301 of 10,301) |
| At least 500 genuine distinct fresh valid products from one run | PASS_DEVELOPER_LIVE | L10 on 1.6.4 (7,055, detail off, re-validated on 1.6.5); L8 on 1.6.3 (675, detail on). Not on 1.6.6: its one run is the canary L12 (40) |
| Production: every root, child, partition and page | BLOCKED_BUDGET | W4 |
| Checkpoints, bounded retries, deduplication, recovery, overlap protection, last-good publication | PASS_DEVELOPER_LIVE, PASS_OFFLINE | [`RECOVERY_AND_OPERATIONS.md`](RECOVERY_AND_OPERATIONS.md) |
