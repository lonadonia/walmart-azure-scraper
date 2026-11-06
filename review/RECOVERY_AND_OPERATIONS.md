# Recovery and operations (W6), release 1.6.8

Release 1.6.8, commit `85c29e7b2404500299056973f50c84b84e187a5a`. Store: Walmart #3891, 3900
Fountain Square Pl, Waukegan, IL 60085, PICKUP. Times are UTC.

Each line says where it was shown:
- **LIVE:** the Oxylabs Web API and Walmart, from the workstation, with the owner's trial account (free credit). This is
  developer-environment evidence, not the client's.
- **OWNER AZURE:** the owner's Azure test VM, Linux, with no provider request: stored pages or synthetic pages. Not the client's environment.
- **SYNTHETIC:** fixture pages and a temporary local database, with no request.
- **DOCUMENTED:** the shipped documents and configuration, not exercised here.

Nothing in this file ran in the client's Azure environment, and the schedule was never enabled. **No live run was made on 1.6.7 or 1.6.8.**
Releases 1.6.7 and 1.6.8 change what a run reads, how its listings and rows are judged and named, and which saved values a carried row takes. Release 1.6.6
changed only how a refused automatic publication is reported (section 3), release 1.6.5 only the independent source
check, and release 1.6.4 only how a listing's total is read: the retention, recovery, concurrency and schedule code
is that of 1.6.3, with a carried row's renaming and its UPC and size decided apart since 1.6.7, and the publication step's own checks are too.

## 1. Retention

| What | Rule (unchanged in 1.6.x unless named) | Where it is set or shown |
|---|---|---|
| The store's verified products | Kept indefinitely. A product a run does not observe is carried forward from its last verified observation, with its own crawl date, its age and the reason. A carried row is never counted as fresh, and its crawl date is never refreshed by a new export. Since 1.6.7 it takes the name the category page gives its exact view, and its lineage keeps the earlier name (`historical.renamed_by_mapping`) | `config/collector.yaml`, `historical:` (`max_age_days` must stay null); `collection/retention.py`. LIVE: L8 (1.6.3) exported 2,515 rows, 675 fresh and 1,840 carried; L10 (1.6.4) exported 10,301 rows, 7,057 fresh and 3,244 carried; each carried row with its own run and date |
| A product later shown only with a shipping or marketplace offer, or with no line for the store | keeps its identity with empty prices, never that offer's price | DOCUMENTED and tested (`tests/integration/test_coverage_and_assortment.py`) |
| A UPC or size read on a product's own page | reused for 30 days (`detail.reuse_days`), always named as that read: its time, run, revision and page. From 1.6.1 also when a run ends before its detail pass; from 1.6.3 also with detail reading off and for carried rows | LIVE: L8 took 667 UPCs from saved reads and fetched 6 product pages; 155 carried rows got their blank UPC from a saved read that each names. L10, with detail off, took 367 UPCs from saved reads and filled 267 carried rows. Carried rows whose read gives conflicting sizes were left as carried (`recovery_withheld`): 4 in L8, 12 in L10. Since 1.6.7 such a read withholds the size only (`historical.size_withheld`), offline; 3 UPCs of S6's rows are recovered so with no request |
| Deal fields (`volume_deals_*`, `digital_deals_*`) | always `""` (the client's clarification, release 1.6.0) | LIVE: `""` in every row of every 1.6.x export |
| Exports and the published dataset | every run's exports under `runs/<store>/<run>/exports/` in the storage (a local folder or the Blob container). `published/<store>/latest.json` is the **last-good pointer**: it names the published run and its manifest, and it is not a product file. The database's publication pointer is authoritative | `docs/OPERATIONS.md`, "Publication" and "Backup" (Blob soft delete and versioning; PostgreSQL point-in-time restore, 7 to 35 days) |

## 2. Recovery

LIVE, three times, each on the release it ran:
- L3 on 1.6.1 (run `01M6HA74X4QYMW45SVD62JQDSQ`);
- L5 on 1.6.2 (`01M6K1HG154683NAAFXQZX33C6`);
- L8 on 1.6.3 (`01M6K6P21BW509BMRTN1FSB9H7`).

Each ran with two workers. Releases 1.6.4 to 1.6.8 did not change the recovery path, and a live repeat on them was not funded; their integration suites,
which include the interruption, kill and resume tests, passed in both editions. Every command, with its start, end and exit code, is in `evidence/live/1.6.x/campaign/commands.csv`, and
each command's own log is beside it.

| Step | L8 on 1.6.3 | L5 on 1.6.2 | L3 on 1.6.1 |
|---|---|---|---|
| Pause: Ctrl+Break to the collector's process group, 45.0 s after the start | exit 75 (interrupted, resumable) at 45.8 s | exit 75 at 47.5 s | exit 75 at 45.5 s |
| A second `run` for the same store while the first is unfinished | refused, exit 9, no request | refused, exit 9 | refused, exit 9: "walmart-3891-pickup has an unfinished run ... (interrupted): resume or finalize it" |
| `resume`, then a forced kill (`taskkill /F`; no signal handler runs), 60.0 s after the resume | exit 1 | exit 1 | exit 1 |
| `status` after the kill | exit 0: the run is shown unfinished | exit 0 | exit 0 |
| `resume` to the end | 381.1 s; exit 6: G3 (a bounded pilot covers no category in full) and G4 (58% of the rows of the listings it read are retained from earlier runs). A pilot is never published either way | 398.0 s; exit 6, the same two gates (54% retained) | 427.7 s; exit 0 (G3 only) |
| Pages read twice | none: 18 listing fetches for 18 listing pages, 6 product pages for 6 | none: 18 for 18, 34 for 34 | none: 18 for 18, 12 for 12 |
| Fresh valid records | 675 | 679 | 676 |
| Active time of the three executions | 42.1 s, 42.6 s, 286.8 s | 44.4 s, 42.3 s, 273.6 s | 42.5 s, 42.1 s, 303.9 s |

Each execution reads robots.txt and the store page again, as a resume must before it collects: 6 each per stage (3
executions, 2 workers). On 1.6.0, L2 (`01M6H72J86K5TF7A1874N7BJ2R`) was paused after 480 s, killed 420 s into its
resume and resumed to the end, with no page read twice (18 listing pages, 254 product pages, 230 follow-up pages).

**OWNER AZURE, on 1.6.8, with no request.** A replay of L10's stored pages in the container, with 120 pages read, was killed with SIGKILL (exit 137). The run stayed unfinished. The ordinary `resume`, started at once, was not refused: it recorded the run interrupted and recovered, closed the killed execution's segment as abandoned, and reclaimed the one task the dead worker held, which went on from its checkpoint. The run finished with 426 pages. Two pages were read again, robots.txt and the store page, because a resumed execution checks the store before it continues; no result page was read twice. Its export equals the uninterrupted replay's byte for byte, and its records were checked against their stored pages ([`KILL_RESUME_COMPARISON.txt`](../evidence/owner-azure-test/1.6.8/container/kill_resume/KILL_RESUME_COMPARISON.txt), [`killresume.log`](../evidence/owner-azure-test/1.6.8/container/logs/killresume.log)). It stays a replay: `rejected`, like its source run, and never published.

**What a stop costs.** In every stage, the pause left 2 requests in flight and the kill left 2 more. Their answers
were not used and their outcome is unknown, so both ledgers keep them as charged. The collector's ledger shows the
paused ones as cancelled and the killed ones as reserved (or abandoned after 600 s). The shared trial ledger marks
each one "unknown" at the reserve rate (USD 0.0015) when the next process takes the stage's lease. Per stage:

| Stage | Settled | Free (documented) | Unknown |
|---|---|---|---|
| L8 | 36 (USD 0.054) | 1 | 4 (USD 0.006) |
| L5 | 64 (USD 0.096) | none | 4 (USD 0.006) |
| L3 | 42 (USD 0.063) | 2 | 4 (USD 0.006) |

**A stop at the credit limit.** L10 on 1.6.4 had a run credit limit of 442. At about 441 credits it stopped
(`RUN_CREDIT_LIMIT`) and was finalized with what it had collected: its checkpoints kept, the 155 listings it had not
reached recorded `SKIPPED`, nothing shown as complete, and the run rejected as a pilot.

**A pause is not a finalize.**
- A pause (Ctrl+Break, SIGTERM or the job's time limit) leaves the run interrupted (exit 75). `resume --run ID`
  continues it from its checkpoints, and no collected page is requested again.
- `stop --run ID` is not a pause. It stops collecting for good: the execution stops at its next checkpoint and the
  run is finalized with what it collected (`collection/control.py`, `request_stop`).
- `finalize --run ID` closes an unfinished run without any request. It checks and exports what was collected, as a
  partial or pilot dataset that is never published. A finalized run has finished and cannot be resumed.
- A run that reaches the spending ceiling (`SPENDING_CEILING`, exit 4) stays resumable once the ceiling is raised.
  A run that reaches its own credit limit (`RUN_CREDIT_LIMIT`) is finalized.

**Rerun.** A new run after a finished one starts from the store's retained products and the saved product-page
reads. L8 needed 6 product pages for its 675 fresh products; L2 needed 484 for its 707.

## 3. The last good dataset is protected

SYNTHETIC, on a clean extraction of the 1.6.8 Oxylabs edition ZIP (sha256 `eacf76e9…`): its own frozen tests plus
one added file, 19 passed on 2026-11-05, 21:22:13Z to 21:25:33Z
([`evidence/verification/1.6.8/last_good_publication/`](../evidence/verification/1.6.8/last_good_publication/)).
The same check passed on 1.6.1, 1.6.4, 1.6.5 and 1.6.6. In each case a first run is published, a second run meets the fault, and
the published state is compared before and after: the pointer, the publication rows, `latest.json`, the manifest and
its `products.json`, and the first run's observations.

| Fault | Second run | Published dataset |
|---|---|---|
| Incomplete (credits ran out) | rejected, `CREDITS_EXHAUSTED`, exit 4 | unchanged |
| Thin | rejected, exit 6 | unchanged |
| Empty | rejected, exit 6 | unchanged |
| Wrong store | rejected, `STORE_NOT_VERIFIED`, exit 7; the store is then held | unchanged |
| Blocked by the site | rejected, `SITE_REFUSAL`, exit 5; the store is then held | unchanged |
| Product pages stopped by a challenge | rejected, exit 6 | unchanged |
| Mixed lineage | the publication refused, exit 6 | unchanged |
| Corrupt evidence after the run validated: one byte of `products.json` changed, `products.json` truncated, or `manifest.json` changed | not published: "products.json hash mismatch" or "manifest hash mismatch"; the run stays `validated`; exit 6 (1.6.5: exit 0). That `PUBLICATION_REFUSED` is at `ERROR` (1.6.5: `WARN`) is asserted by 1.6.6's two tests and the operator drill below, not by this check | unchanged |
| Run interrupted | exit 75; a manual publication of it refused (exit 6) | unchanged until its resume completes and publishes it |
| Publication interrupted | the retry publishes in one step | the old dataset until then |
| Control: one product page refused among many | published | moves, as it should |

**A pilot never replaces the published dataset.** A demonstration or census run is a pilot. Its manifest says
`"dataset": "pilot"` and it is never published. Only a complete, validated, non-pilot run moves the pointer. None of
the 1.6.x runs was published: each is a bounded pilot, and no run read the full catalogue.

**A refused automatic publication is an alert (release 1.6.6).** Until 1.6.5, when the automatic publication was
refused (the corrupt-evidence cases, for example), the run exited 0 and the refusal was a `WARN` line,
`PUBLICATION_REFUSED`. The published dataset was protected, but none of the alerts OPERATIONS.md suggests (any `ERROR`
line, any non-zero exit) fired. The 1.6.5 delivery disclosed this and advised an extra alert, but still gave its operating
documentation a pass (N10-03). Since 1.6.6:
- `PUBLICATION_REFUSED` is an `ERROR` line, and an `ERROR` event recorded on the run, with its reason;
- the execution exits 6, and `RUN_FINISHED` carries `exit_code` 6 and the refusal;
- Azure's retry of a scheduled execution whose run is done exits 6 too (`OCCURRENCE_DONE` with `exit_code` 6), so a
  retry cannot turn the execution into a success;
- the alert advice of OPERATIONS.md adds `OCCURRENCE_DONE` with `exit_code != 0` and names the case.

The two tests that show it fail on 1.6.5 and pass on 1.6.6
([`evidence/offline-tests/1.6.6-collector/`](../evidence/offline-tests/1.6.6-collector/)). A manual `publish` that is
refused exits 6, as before. To act on the alert: read the reason (`status --run ID`), resolve it, then
`publish --run ID`. The last published dataset stays published meanwhile.

**The operator drill (OWNER AZURE, synthetic pages), on 1.6.8, in both editions.** `test_operator_drill_owner.py` runs the ordinary command line against the VM's PostgreSQL 16, with a local stub for the site: `validate-config --check-db`, `sync-config`, `run`, `status`, `export` and the storage location, a pause and `resume`, a publication refused because the run's pages did not come from the network and the store is not a test target, `publish` of that run by hand, a run stopped when its provider credits ran out, and the export of the store's published dataset. Its transcripts are [`oxylabs.drill.jsonl` and `scrapedo.drill.jsonl`](../evidence/owner-azure-test/1.6.8/qualification/logs/). It shows:
- the run's automatic publication refused: `PUBLICATION_REFUSED` at `ERROR`, exit 6; a manual `publish` of the same run refused again, exit 6; the last-good pointer unchanged throughout;
- a run paused by its execution limit (exit 75), then continued by `resume`: the same run, then published;
- a run stopped when its credits ran out (exit 4), partial, which did not replace the published dataset: the store's export is still the last good run;
- store isolation: a second store, configured and enabled beside the first, has no run and no folder, and no request carried its store id (the stub saw only `3891`), while the first ran.

## 4. Concurrency

LIVE, measured from each run's own page fetches and its collector ledger
([`CONCURRENCY_MEASURED_1_6_6.csv`](../evidence/reconciliation/1.6.6/CONCURRENCY_MEASURED_1_6_6.csv), one line per
run and page purpose; no live run since). Workers share one pace per store: leases, checkpoints, deduplication and the shared trial
reservations held under two workers, and no page was read twice.

| Run | Release | Workers | Executions | Active time (s) | Pages answered | Pages per active minute | Listing page, median and p90 (s) | Product page, median and p90 (s) |
|---|---|---|---|---|---|---|---|---|
| L1 | 1.6.0 | 1 | 1 | 99.0 | 4 | 2.42 | 30.0, 30.0 | 34.5, 34.5 |
| L2 | 1.6.0 | 2 | 3 | 2,188.7 | 514 | 14.09 | 7.4, 14.7 | 5.0, 16.0 (detail); 5.1, 11.0 (follow-up) |
| L3 | 1.6.1 | 2 | 3 | 388.5 | 42 | 6.49 | 6.6, 9.8 | 17.5, 69.5 |
| L2b | 1.6.1 | 1 | 1 | 1,483.0 | 120 | 4.85 | 7.0, 7.6 | 6.9, 18.0 |
| L4r | 1.6.1 | 2 | 1 | 299.8 | 52 | 10.41 | 6.5, 9.2 | none |
| L4 | 1.6.1 | 2 | 1 | 174.3 | 35 | 12.05 | 7.4, 11.0 | none |
| L5 | 1.6.2 | 2 | 3 | 360.3 | 64 | 10.66 | 8.3, 14.8 | 5.0, 8.8 |
| L6 | 1.6.2 | 2 | 1 | 317.0 | 69 | 13.06 | 6.9, 9.7 | none |
| L8 | 1.6.3 | 2 | 3 | 371.5 | 36 | 5.81 | 7.0, 13.2 | 11.4, 47.8 |
| L9 | 1.6.3 | 1 | 1 | 111.5 | 4 | 2.15 | 11.0, 19.1 | none |
| L7 | 1.6.3 | 2 | 1 | 449.1 | 82 | 10.96 | 8.1, 11.7 | none |
| L10 | 1.6.4 | 2 | 1 | 2,596.6 | 441 | 10.19 | 8.4, 12.9 | none |
| L11 | 1.6.5 | 1 | 1 | 342.6 | 3 | 0.53 | 13.8 (one page) | none |
| L11b | 1.6.5 | 1 | 1 | 311.3 | 3 | 0.58 | 10.0 (one page) | none |
| L12 | 1.6.6 | 1 | 1 | 407.0 | 13 | 1.92 | 21.8 (one page) | 3.5, 5.1 |

"Pages answered" counts robots.txt and the store page too. The rate of a short run is dominated by its fixed work:
each 1.6.5 canary's three requests ended within its first 20 s, and the rest of its active time (about 5 minutes)
went to checking and exporting its 10,301 rows. L12's 13 requests ended by 22:55:13Z, about 2.3 minutes into its 6.8
minutes of active time. The longest two-worker run, L10, read 441 pages in 2,596.6 s of active time:
10.19 pages per active minute, the rate [`TEST_PLAN.md`](TEST_PLAN.md) uses. Memory of a live run was not measured. On the owner's Azure test VM (2 vCPU, 3.9 GB of memory), the delivered Oxylabs edition of 1.6.8 replayed L10 from its stored pages, on the host rather than in Docker: 424 pages and 6,880 valid records (the container's replay gave the same), in 511.5 s of wall time and 212 s of CPU. A replay serves the stored pages through one session, so it ran one worker in one process; L10 itself ran two. That process's resident memory peaked at 1.38 GiB by the kernel's count (1.31 GiB in samples every 0.25 s), and the host never had less than 1.75 GiB available ([`memory/`](../evidence/owner-azure-test/1.6.8/memory/)). A replay makes no request, so this is not a live run's measurement. The worker
count for a full run needs the full run (A53).

## 5. Schedule (kept disabled)

DOCUMENTED and tested offline. Nothing was scheduled anywhere in this delivery.

- **Shipped state:** `schedule.enabled: false`. `run --scheduled` exits 0 with `SCHEDULE_OFF` until the client
  approves it.
- **When enabled:** Tuesday and Friday (`weekdays: [1, 4]`) at 06:00 store-local time (`America/Chicago`). The Azure
  job fires every 30 minutes (`*/30 * * * *`, UTC), and each firing decides once, in store-local time, and exits.
  - Until 2027-03-14 (CST, UTC−06:00), 06:00 in Chicago is 12:00Z.
  - From 2027-03-14 (CDT, UTC−05:00), it is 11:00Z.
  - A daylight-saving change never moves or doubles a run.
- **Unfinished runs:** a run that outlasts its execution (300 minutes) pauses at its checkpoint (exit 75), and later
  firings continue it (`continue_unfinished: true`). An occurrence that finds the previous scheduled run unfinished
  lets it go on and starts none (`on_overlap: continue`).
- **Backlog:**
  - A start that could not run keeps its identity and starts later, oldest first.
  - `schedule-status` shows it, with its lateness and the missed deadlines.
  - Queuing a start does not by itself meet the twice-weekly cadence.
  - A configuration that narrows the scheduled scope is refused.
- **Tests:**
  - `tests/unit/test_schedule_dst.py` covers both changes, a repeated hour and a missing hour. Also
    `tests/unit/test_continuation.py` and `tests/unit/test_config_and_schedule.py`.
  - The schedule tests of `tests/integration/test_operations.py` cover: the due local occurrence; the winter
    occurrence; an unfinished scheduled run going on; continuation by later firings; a late start; a backlog across a
    clock change; a manual run deferring an occurrence; a closed window deferring it.
  - All passed in the 1.6.8 suites of both editions on Linux (unit 554, integration 222).
- **Not established:** that a full-scope run fits between two starts. No full-scope run has been made.
  [`COST_AND_RUNTIME_REPORT.md`](COST_AND_RUNTIME_REPORT.md) estimates it from the measured page rates. The
  observed cadence is a separate milestone (PENDING_OBSERVATION), after the client's authorization.

## 6. Container

**OWNER AZURE, on 1.6.8** (2026-11-05, 21:24:30Z to 22:09:14Z): 89 steps, 1 not as expected by its exit code: `after` (exit 1), because the gate's four databases were still on the host; they were kept for the checks that followed and then dropped ([`HOST_STATE.md`](../evidence/owner-azure-test/1.6.8/HOST_STATE.md)). The gate's recording of the walkthrough exited 0 but failed by its output (`command not found`); it was recorded again in a session of its own. The record is [`evidence/owner-azure-test/1.6.8/container/`](../evidence/owner-azure-test/1.6.8/container/). This is an owner test, not the client's environment. The client's VM was not touched.

- **The images.** Both editions were built with `docker build` from the delivered ZIPs. Their ids, layers, `docker save` digests and base-image digests are in [`IMAGES.md`](../evidence/owner-azure-test/1.6.8/container/IMAGES.md). Every file of the images' `src` and `config` was compared with the ZIP's: identical.
- **Smoke tests.** With no network and a read-only root: `--version`, `--help` and the default `validate-config`; `validate-config --require-credentials` with no key is refused with exit 3.
- **Migrations.** A new isolated database per edition: the schema check fails (exit 2), `db-upgrade`, the check passes, a second upgrade changes nothing, then `sync-config` and `status`.
- **Stored live pages.** A copy of the campaign database, with L12 and L10 replayed by 1.6.8. A replay makes no request, and HTTP(S) goes to a closed local port. It is a replay, not new collection, and it stays attributed to the release that collected the pages.
- **Kill and resume.** Section 2.
- **Rollback.** The published 1.6.6, built as an image from its ZIP, reads the same database (one schema head, `0006`), and shows and exports the same run. Then 1.6.8 again.
- **Persistence.** The daemon was stopped and started. The images, the volumes, every file the replays wrote (compared by SHA-256) and the database were all still there.
- **The host.** [`HOST_STATE.md`](../evidence/owner-azure-test/1.6.8/HOST_STATE.md) compares it before and after. Docker is not installed on the VM: Ubuntu's packages were unpacked into the gate's own folder, and a daemon from there ran as root during the gate, with no default bridge and no firewall change.

**What this does not establish:** that the images run in the client's environment, that they run against Azure's PostgreSQL or Blob storage, or anything live.
