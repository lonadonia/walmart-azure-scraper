# Requirement matrix, release 1.6.5

Release 1.6.5, commit `67d216eb8ee2ec839a437b0b5bf2d594324b6982`, with the shared Classic probe 1.7.0. Store:
Walmart #3891, 3900 Fountain Square Pl, Waukegan, IL 60085, PICKUP. Written on 2026-11-04 (UTC).

This page gives the state of every requirement of this delivery: the work items of Hamza's brief (W1 to W8), the
client's Classic findings (C1 to C5), the earlier 24-item audit (W01 to W24) and the common data contract. The 206
rows of the client's acceptance matrix are in [`ACCEPTANCE_MATRIX.csv`](ACCEPTANCE_MATRIX.csv). Their 1.5.2 columns
are kept as published then, and four columns are new: `state_1_6_5`, `evidence_1_6_x`, `revision_1_6_x` and
`note_1_6_x`. The paths `source/walmart-oxylabs-1.5.2/...` in the 1.5.2 `evidence` column name files of the 1.5.2
tree, which is at the tag `review-1.5.2-20261103`; this publication's `source/` holds 1.6.5. What each correction changed is in [`CORRECTION_MAP.md`](CORRECTION_MAP.md).

Release 1.6.5 is the final revision of this delivery. It changes only the independent source check, after the live
census L10 (release 1.6.4) showed that the check could not read one of the three price layouts Walmart's pages use.
Live results stay attributed to the release that collected them: L10 to 1.6.4, the canaries L11 and L11b to 1.6.5.

## The states

Each state names what the evidence is. None of them means "accepted by the client".

| State | Meaning |
|---|---|
| PASS_OFFLINE | Passed with no request to a provider or to Walmart. This covers source inspection, unit and PostgreSQL integration tests, static checks, the clean-extraction verification of the delivered ZIPs, synthetic faults and the offline replay of stored pages. All of it ran on 1.6.5 unless the row names another release. |
| PASS_DEVELOPER_LIVE | Shown by live runs in the developer environment: the user's Oxylabs Web API trial account, from the workstation, on the release the row names. It is neither the client's environment nor client acceptance. |
| PENDING_CLIENT_AZURE | Needs the client's Azure environment. The client confirmed that their VM is deallocated. Access waits for the client's confirmation of a restart and window, and for the new key to be installed with the old one revoked. |
| PENDING_OBSERVATION | Needs something that cannot be manufactured: a natural available-to-unavailable transition, or scheduled runs observed after the client authorizes the schedule. |
| PENDING_CLIENT_DECISION | The client's choice. For example: support and IP terms, a live Classic successor with its entitlement and limits, or the acceptance itself. |
| PENDING_OWNER | Hamza's action. For example: a walkthrough recording, his own test VM, the provider dashboard reading, the developer key's rotation, a summary PDF. |
| BLOCKED_BUDGET | Implemented and tested offline, but its live proof needs more requests than the trial allowance has left. Scrape.do is in this state too: this delivery authorizes no Scrape.do spending. |
| BLOCKED_SOURCE | The source does not offer what the requirement needs. No row has this state in 1.6.5. |
| NOT_APPLICABLE_BY_CLARIFICATION | Superseded by the client's clarification that the four deal fields are always `""`. |
| REPORTED_NOT_VERIFIED | A fact someone else reported that was not checked here: the client's statement that their VM is deallocated. It is used in notes only. |

States of the 206 rows: PASS_OFFLINE 90, PASS_DEVELOPER_LIVE 66, BLOCKED_BUDGET 22, PENDING_CLIENT_AZURE 8,
PENDING_OWNER 7, NOT_APPLICABLE_BY_CLARIFICATION 6, PENDING_CLIENT_DECISION 4, PENDING_OBSERVATION 3,
BLOCKED_SOURCE 0.

## The work items of this delivery (W1 to W8)

| Item | State | What was done, and where |
|---|---|---|
| **W1** The four deal fields `""` | PASS_OFFLINE, PASS_DEVELOPER_LIVE | Release 1.6.0 enforces the rule at the final export boundary (`publishing/exports.py`) and in every path before it. The tests start from nonempty deal data. Every row of every 1.6.x export has `""` ([`manifests/check_data.py`](../manifests/check_data.py)). No credit was spent on offers. [`CORRECTION_MAP.md`, W1](CORRECTION_MAP.md#the-four-deal-fields-w1) |
| **W2** UPC, size and provenance | PASS_DEVELOPER_LIVE; BLOCKED_BUDGET for 48 UPCs never read; PENDING_OWNER for the key rotation | A per-row, per-field correction table, from S6's 706 rows to their state in L8, with its aggregates. [W2](CORRECTION_MAP.md#upc-size-and-provenance-w2) |
| **W3** Sponsored and variant decisions | PASS_DEVELOPER_LIVE | All 275 queued products were read live and decided. The client's 11 and 30 cases are traced. [W3](CORRECTION_MAP.md#sponsored-and-variant-products-w3) |
| **W4** Full production scope | BLOCKED_BUDGET | Two censuses: L7 on 1.6.3 and L10 on 1.6.4. Together they read page 1 of 451 listings in the 11 CSV rows; 395 listings their category pages named were not reached before L10's ceiling. Coverage tables by row, root, child and page give the exact outstanding queue. No CSV row is complete (0 of 11). [`TEST_PLAN.md`](TEST_PLAN.md) prices the remaining work. [W4](CORRECTION_MAP.md#coverage-partitions-and-the-census-w4) |
| **W5** Final-revision live qualification | PASS_DEVELOPER_LIVE (L10 on 1.6.4, detail off; its export re-validated and the live canary on 1.6.5); BLOCKED_BUDGET with detail on | Fourteen staged runs, each on a frozen release. L10 on 1.6.4 gave 7,055 fresh valid products with detail off. The final 1.6.5 changed only the source check. It re-validated L10's export offline (10,301 of 10,301 records verified), and its live canary L11b passed (35 of 35). With detail on, the last such run is L8 on 1.6.3 (675). [`data/RUN_SUMMARY.json`](../data/RUN_SUMMARY.json), [`MILESTONES.md`](MILESTONES.md) |
| **W6** Retention, recovery, publication, capacity | PASS_DEVELOPER_LIVE / PASS_OFFLINE; PENDING_CLIENT_AZURE (container); BLOCKED_BUDGET (full-run capacity); PENDING_OBSERVATION (cadence) | Recovery ran live on 1.6.1 to 1.6.3. The last-good publication was tested synthetically on a clean 1.6.5. Concurrency ran live with two workers. The schedule is kept disabled, with a written daylight-saving policy. [`RECOVERY_AND_OPERATIONS.md`](RECOVERY_AND_OPERATIONS.md) |
| **W7** Classic findings, Mariano's adapter | PASS_OFFLINE; a live successor is PENDING_CLIENT_DECISION | C1 to C5 are corrected in probe 1.7.0 with live mode disabled. The adapter's identity is explicit. [`CLASSIC_PROBE_CORRECTIONS.md`](CLASSIC_PROBE_CORRECTIONS.md) |
| **W8** The earlier 24-item audit | as below | See the next table. |

## The Classic findings (C1 to C5)

| Finding | State | Correction in probe 1.7.0 |
|---|---|---|
| C1 Redirect policy absent | PASS_OFFLINE | `http.client` in a worker process. Redirects are never followed, and the worker accepts one target only. |
| C2 A timeout leaves the worker alive; body, processing and export unbounded | PASS_OFFLINE | One process per request, killed and reaped at its allowance. Bounded bodies, headers and decompression. A session supervisor. |
| C3 Stale clock across the ledger lock and dispatch | PASS_OFFLINE | The time is read under the lock, the lock wait is bounded, and every stop is checked again just before sending. |
| C4 Responses only in memory | PASS_OFFLINE | Each answer is written atomically and indexed before the next paid step, and recovered after a crash. |
| C5 The default retry sleep is a no-op | PASS_OFFLINE | A real bounded backoff that never runs past the deadline, with `Retry-After` honoured up to 60 s. |

Tests and the pinned diff are in [`CLASSIC_PROBE_CORRECTIONS.md`](CLASSIC_PROBE_CORRECTIONS.md). No Classic request
has ever been sent. A live successor needs its own version, a Classic username and password with an entitlement, and
the account owner's authorization. The probe's tree is unchanged from 1.6.4 to 1.6.5.

## The earlier 24-item audit (W01 to W24)

| Items | State | In this delivery |
|---|---|---|
| W01, W02: client VM and key | PENDING_CLIENT_AZURE | The VM is deallocated (the client's statement). No SSH attempt was made. The new public key waits for the client. Locally, both edition ZIPs were installed from their locks and tested. The container was not built: there is no container runtime here. |
| W03: the developer key's action | PENDING_OWNER | The key on file is not the earlier flagged key. Whether that key is revoked cannot be verified from here. No key value is disclosed. |
| W04 to W10: stage bounds, field and identity reconciliation, roots, children and pages, the outstanding queue | PASS_DEVELOPER_LIVE; BLOCKED_BUDGET for full scope | One shared trial ledger bounds every stage (see [`COST_AND_RUNTIME_REPORT.md`](COST_AND_RUNTIME_REPORT.md)). W2, W3 and W4 are above. |
| W11: a fresh demonstration on the final revision | PASS_DEVELOPER_LIVE (detail off) | L10 on 1.6.4: 7,055 fresh valid, its export re-validated by the final 1.6.5; 1.6.5's live canary L11b: 35 of 35 verified. A detail-on run of 1.6.5 is BLOCKED_BUDGET. S6 is not relabelled. |
| W12: a live offer example | NOT_APPLICABLE_BY_CLARIFICATION | The four fields are always `""`. No offer example was sought. |
| W13 to W20: retention, recovery, last-good, concurrency, full costs, cadence, provider decision, client acceptance | each at its own level | Retention: PASS_DEVELOPER_LIVE. Recovery: PASS_DEVELOPER_LIVE (1.6.1 to 1.6.3) and PASS_OFFLINE (1.6.5). Last-good: PASS_OFFLINE (synthetic). Concurrency: PASS_DEVELOPER_LIVE, with full-run sizing BLOCKED_BUDGET. Full costs: BLOCKED_BUDGET (estimates only). Cadence: PENDING_OBSERVATION. Provider and client acceptance: PENDING_CLIENT_DECISION. |
| W21: both editions | PASS_OFFLINE; BLOCKED_BUDGET live | Both editions are built from one revision, and both were tested from their ZIPs. Scrape.do live qualification needs separately supplied access. |
| W22: stale rows, versions, settings, milestones | PASS_OFFLINE | This page, the four new matrix columns and [`MILESTONES.md`](MILESTONES.md). |
| W23: developer compute cleanup | PENDING_OWNER | Hamza's own resources. The client's VM was not touched, and no evidence was deleted. |
| W24: support and IP terms | PENDING_CLIENT_DECISION | A commercial decision, not a code item. |

## The common data contract

| Rule | State | Where it is enforced, and shown |
|---|---|---|
| The 22 fields in order, all strings, `""` when missing; `gupc` and `unit_price` always `""`; no 23rd field; `url` not renamed | PASS_OFFLINE, PASS_DEVELOPER_LIVE | `core/schema.py` and `publishing/exports.py`; `check_data.py` checks every published 1.6.x export |
| Store and PICKUP proved from the returned page, never from the request | PASS_DEVELOPER_LIVE | every page of every 1.6.x run (each run's store attestations) |
| Eligible products retained indefinitely; a carried row keeps its own `crawl_date` | PASS_DEVELOPER_LIVE | L8: 675 fresh and 1,840 carried; L10: 7,057 fresh and 3,244 carried; each carried row with its own run and date |
| The approximate-weight exclusion; faithful pack sizes | PASS_OFFLINE, PASS_DEVELOPER_LIVE | the weight-wording tests; W2 gives each size's source |
| Sponsored status alone decides nothing | PASS_DEVELOPER_LIVE | W3 |
| `not_attempted`, `blocked`, `request_failed`, `readable_source_absent` and `conflict` kept apart | PASS_OFFLINE, PASS_DEVELOPER_LIVE | each run's `field_dispositions.csv`; 1.6.3 records Walmart's not-found page as `request_failed` |
| Every exported record checked against the stored page it was read from | PASS_OFFLINE, PASS_DEVELOPER_LIVE | the source check of 1.6.5 reads all three price layouts; L10's and L8's exports verified in full ([`evidence/verification/1.6.5/source_check_l10/`](../evidence/verification/1.6.5/source_check_l10/)) |
| At least 500 genuine distinct fresh valid products from one run | PASS_DEVELOPER_LIVE | L10 on 1.6.4 (7,055, detail off, re-validated on 1.6.5); L8 on 1.6.3 (675, detail on) |
| Production: every root, child, partition and page | BLOCKED_BUDGET | W4 |
| Checkpoints, bounded retries, deduplication, recovery, overlap protection, last-good publication | PASS_DEVELOPER_LIVE, PASS_OFFLINE | [`RECOVERY_AND_OPERATIONS.md`](RECOVERY_AND_OPERATIONS.md) |
