# Classic probe: the corrections C1 to C5 (shared probe 1.7.2)

The client's second review found five defects in the frozen Walmart Classic probe 1.5.2. This page shows where each
defect was, that the newer shared probe 1.6.0 (published with Mariano's) inherited all five, what releases 1.7.0 and
1.7.1 corrected, and what release 1.7.2 completes. It also lists the offline tests that prove each correction.

**A correction of this page.** The 1.6.5 publication said that release 1.7.0 corrects all five findings, and the 1.6.6 publication that release 1.7.1
completes C2 and C4. Neither was accurate. The client's review of 1.7.1 reproduced what was left open:
- **C4:** a local server that declares `Content-Length: 100`, writes the two bytes `{}` and closes got `ok=True`, `truncated=False` and a final `.body`.
- **C2:** on Linux the supervisor waited 1.10 s for a FIFO manifest past a 0.30 s hard deadline, and it accepted an earlier campaign's recent `complete=true` file when a new command exited 0 without writing evidence.
- **The Linux test:** the published suite gave 171 passed and 2 skipped on Windows, and 169 passed, 1 failed and 3 skipped on Linux. The drip test required a forced kill when the worker had ended by itself.

Release 1.7.2 corrects all three, each first reproduced by a test that fails on 1.7.1 (below). The corrected sentences are listed in
[`manifests/DOC_CORRECTIONS.md`](../manifests/DOC_CORRECTIONS.md).

**Live mode stays disabled.** No Classic scraping request has ever been sent. The only request made with Classic-style
credentials was W0: one usage-statistics query that sent the Web API key as Basic credentials and was refused (HTTP
401, [`TECHNICAL_REPORT.md`](TECHNICAL_REPORT.md), section 8). The credential on file is an Oxylabs **Web API**
Bearer key, not a Classic username and password, so no live Classic test is possible with it.

## The probes and their identities

| Probe | What it is | Identity | Where it is published |
|---|---|---|---|
| **1.5.2**, Walmart only | The probe the client reviewed. Frozen with collector `627c804d66aa33fc423fd2296c8896c5d5c2c3d4`; its code last changed at `2ed64b70809a67c49c68ebda5e3c3420f079073b`. Its Mariano's reservation is not an adapter. | delivered archive SHA-256 `d4785ccb…` (see `manifests/FILE_MAP.csv`) | [`classic-probe/`](../classic-probe/) in this repository, unchanged |
| **1.6.0**, shared | Adds store 53100502/PICKUP and the Mariano's steps. It plans **no** Mariano's page-2 request. | commit `1f568b8d367ee90e0f4a87879a44873ae649e906`; `classic-probe` tree `33c2d786fa793e2e588746f219eb9118cc789c38`; adapter [`src/classic_probe/marianos.py`](https://github.com/lonadonia/marianos-azure-scraper/blob/1f568b8d367ee90e0f4a87879a44873ae649e906/classic-probe/src/classic_probe/marianos.py) in that tree, blob `9de6510bddbb0cae7fd86e09dac5ed32fc3487a4` | [lonadonia/marianos-azure-scraper](https://github.com/lonadonia/marianos-azure-scraper/tree/1f568b8d367ee90e0f4a87879a44873ae649e906/classic-probe), unchanged |
| **1.7.0**, shared | 1.6.0 with C1, C3 and C5 corrected, and C2 and C4 in part. Published with collector 1.6.5; superseded by 1.7.1. | the probe's source tree is Git tree `8305ffe25665b404347954dad38d501cbba70640`, at `1780349e522d771a3642fe88bfb7b542044ec844`, where its archive was built, and at `67d216eb8ee2ec839a437b0b5bf2d594324b6982` (collector 1.6.5) | [`classic-probe-1.7.0/`](../classic-probe-1.7.0/) in this repository, unchanged |
| **1.7.1**, shared | 1.7.0 with C2 and C4 advanced, not completed. Published with collector 1.6.6; superseded by 1.7.2. | the probe's source tree is Git tree `7adfea8fbd8e562fd72444891e62e3029d544a5f`, at `68ff3d8518b38a3792792ed6ffb8e73c2756245f`, where its code changed, and at `cbea802891d4e66b74a0abc33e0af0af74c89708`, where its archive was built; archive `OXYLABS_CLASSIC_OFFLINE_PROBE_1.7.1.zip`, SHA-256 `89558e533d3d5b9c2fc2981a6caf168c481ba637a02eb5cb46eec3bce467c4f9` | [`classic-probe-1.7.1/`](../classic-probe-1.7.1/) in this repository, unchanged |
| **1.7.2**, shared, current | 1.7.1 with C2 and C4 completed, and the Linux test corrected. It is authoritative from this delivery (collector 1.6.8). | the probe's source tree is Git tree `3ada8871cf159d27a6afb49ff8ca854e16c5d657`, at `7768514aa1ffbaa7f96ca242d7b64e495fffefa5`, where its code changed, unchanged at `7ee2fa1e00512a3ce7a9481268f4e5302294f94f`, where its archive was built, and at the collector's `85c29e7b2404500299056973f50c84b84e187a5a`; archive `OXYLABS_CLASSIC_OFFLINE_PROBE_1.7.2.zip`, SHA-256 `fe25579154b9cac70628fa8b7e3a61a85858b01f6900ff0aded04b3d6da76e1e` (built again before publication with the workstation's user name replaced in one of its offline results; its first build, `79f32db3457ff069…`, was not delivered: [`PACKAGE_REBUILD.txt`](../evidence/offline-tests/1.7.2-classic-probe/PACKAGE_REBUILD.txt)); the adapter blob is still `9de6510bddbb0cae7fd86e09dac5ed32fc3487a4`, unchanged | [`classic-probe-1.7.2/`](../classic-probe-1.7.2/) in this repository |

The published 1.6.0 tree `33c2d786…` is the development tree `28ae3603…` plus one added file, `CLASSIC_PROBE.md`.
The 1.7.0 code was committed at `2c08585` (tree `0ac0bdb1…`); the next commit, `48307cf`, corrected three of its
documents, which gives the tree `8305ffe2…`. The 1.7.1 code was committed at `68ff3d8`. The 1.7.2 code was committed at `7768514`; the later commits of
this delivery, up to `85c29e7` (collector 1.6.8), change nothing in the probe.
The Mariano's adapter is byte-for-byte the same in 1.6.0, 1.7.0, 1.7.1 and 1.7.2, so every correction is in the shared
layer: transport, worker, ledger, campaign, deadline, captures, supervisor and, new in 1.7.2, the process tree (`proctree.py`).

The Mariano's repository is not changed by this delivery. Its pin to probe 1.7.1 stands until its owner moves it to 1.7.2.

## The defects and their corrections

The line numbers refer to the files of each release.

| Finding | In 1.5.2 (reviewed) | Inherited by 1.6.0 | Correction in 1.7.0 | In 1.7.1 |
|---|---|---|---|---|
| **C1** Redirect policy absent | `transport.py:82` sends with `urllib.request.urlopen`, whose default opener follows redirects | yes, `transport.py:82` | Nothing follows a redirect. The request runs in a separate worker process (`networker.py`) through `http.client`, which never follows one. The worker refuses any target other than `https://realtime.oxylabs.io:443/v1/queries` (`networker.py:33`). A 3xx answer is recorded, with its location, and stops the campaign (`checks.py:77`). The credentials are sent once, to the documented endpoint only. The original dispatch stays charged at "unknown". | Unchanged: complete in 1.7.0. |
| **C2** A timeout leaves the worker alive; body, processing and export are unbounded | `campaign.py:226` bounds a request with `bounded_send`, a thread and queue timeout that does not stop the thread | yes, `campaign.py:228` | Each request runs in its own process, which is killed and reaped at the request's allowance (`transport.py:116`, `:196` to `:201`). The body is bounded on success and on error alike, and so are the headers and the decompressed size (`ResponseLimits`, `decode_body` at `transport.py:99`). A truncated body is never parsed. A session supervisor kills the whole session, with every process it started, at the session's hard end. An "unknown" reservation stays held: nothing claims the remote side was cancelled. **Left open (reproduced):** the supervisor's recovery ran after the session's hard end with no bound of its own, so a ledger lock held elsewhere kept it waiting 30 s, after which it raised. The ledger writes after an answer (its index, its settlement, a stop) waited up to 30 s for the lock whatever time was left. A killed session that could not be reaped raised out of the supervisor with nothing recovered. | The session's ledger writes after an answer wait no longer than its write window, which ends 30 s before the session's end by default (a third of the export reserve, at most 30 s: `deadline.recovery_reserve`, `SessionClock.write_remaining`; `ledger.bind_time_left`). After one refusal of the lock, the session does not wait for it again (`campaign._ledger_write`). The export's checks and manifest run until the true end. The supervisor's kill, reap and recovery all end by the hard end (`supervisor.run_session`). The recovery runs in its own process (`python -I -m classic_probe.supervisor recover … --until`), its lock waits end by the same end, and a recovery still running then is killed. What a recovery could not do is listed (`completed`: false, with the reasons). A row it could not mark keeps its money held for the next recovery. |
| **C3** A stale clock across the ledger lock and dispatch | `ledger.py:401` reads the clock before taking the write lock, and `mark_sent` checks no time | yes, `ledger.py:401` and `:479` | The time is read under the lock (`ledger.py:514`). The wait for the lock is bounded, and a wait that runs out reserves nothing (`LockNotObtained`, `ledger.py:130`). `mark_sent` checks the time and every stop again just before sending (`ledger.py:591`), and records a late request as never sent. A `SessionClock` takes the earlier of the monotonic and wall-clock ends and keeps the export and cleanup time in reserve. It clamps each allowance and each backoff to the time left (`deadline.py:20` to `:52`). A restart keeps the campaign's durable deadline. | Unchanged: complete in 1.7.0. 1.7.1 also bounds the ledger writes that follow an answer (C2). |
| **C4** Responses held only in memory until the final export | `campaign.py:174` and `:234` keep responses in a list that only `_export` writes | yes, `campaign.py:176` and `:236` | Each bounded answer is written atomically (a private `.part` file, then `fsync` and `os.replace`) and indexed in the ledger before the next paid step (`captures.py:134`, `campaign.py:281`). The index rows cannot be changed. On restart, the captures are recovered: indexed, or removed if they were never completed (`captures.py:164`). A truncated answer is never presented as complete. The export is written from the durable index. The original and sanitized hashes are both kept. **Left open (reproduced):** the transport deleted the worker's synced file as soon as it had read it, before the kept copy was written, so a crash between the two lost a paid answer. The evidence manifest was renamed into place without being synced. On Windows a kept file's rename was not written through to the disk. A body cut at its deadline left no record. | Each answer is kept as received, privately, under its dispatch's number in the ledger (`private/raw/dispatch_NNN.body` with its `.status.json`, never exported). The worker writes the status first, then renames the body durably: a write-through rename on Windows (`MoveFileExW`), a synced folder on Linux and macOS (`durable.replace`). A crash before the kept copy loses nothing: the recovery keeps the copy from those files, without a paid refetch, once the body matches the SHA-256 in its status (`captures.recover`). A body cut short is kept (`dispatch_NNN.partial`) and recorded once in the ledger (`PARTIAL_RESPONSE`, with its length and SHA-256), never as an answer. Every evidence file, the manifest included, is synced before it is renamed into place (`durable.write`). |
| **C5** The default retry sleep is a no-op | `campaign.py:171`: `sleep or (lambda _s: None)` | yes, `campaign.py:173` | The default is the real `time.sleep` (`campaign.py:182`). A backoff is a real wait. It never runs past the deadline, and the session stops during it when time runs out. A `Retry-After` in either documented form is honoured up to 60 s. A longer wait ends the step (`campaign.py:328`). Every retry is a new dispatch with its own reservation. | Unchanged: complete in 1.7.0. |

**What 1.7.2 completes** (each line reproduced by a test that fails on 1.7.1):

| Finding | Left open by 1.7.1 | In 1.7.2 |
|---|---|---|
| **C4**, a body shorter than declared | `http.client` reports a premature end as an empty read. A server that declares `Content-Length: 100`, writes `{}` and closes gave a whole answer, on a success status or an error status alike, and the campaign parsed it | The worker compares what arrived with what was declared. A body shorter than its declared length, zero bytes included, and a chunked body cut short, are kept as `dispatch_NNN.partial` with their status (`IncompleteBody`, the declared and received lengths, the SHA-256), recorded once in the ledger (`PARTIAL_RESPONSE`), never parsed, and their reservation stays held. The transport and the recovery check the declared length again. A body of exactly its declared length, a response without a body (204, 304, `Content-Length: 0`) and a body of exactly the byte limit stay whole; a body above the limit is still cut there, marked truncated and never decoded. A crash and an immediate restart in the same folder keep the partial, its hash and its accounting, with no paid refetch |
| **C4**, a worker killed after it named its file | The transport looked only for the unrenamed `.part` file, so it reported a whole answer as lost and a kept partial as absent | The transport reads the worker's own status first: a whole answer stays the answer, a partial is described with its length and hash, and a status the worker wrote is never overwritten |
| **C4**, whose answer it is | A raw file was kept by its name | Each worker status names its dispatch (campaign, ledger genesis id, sequence number, step, attempt and the payload's SHA-256). A recovery keeps a raw answer or a partial only when its status names the ledger row it is recovered into. Anything else is refused, listed with the reason and left on disk as found |
| **C2**, one deadline | On Linux the supervisor waited 1.10 s for a FIFO at the evidence path past a hard end of 0.30 s. It took the complete evidence a previous run had left in the same folder when a new command exited 0 without writing any | Evidence is read only from a regular file, in bounded chunks and within the time left: a FIFO, a link, a folder or a file above 16 MiB is refused at once. Each session has an execution id (`CLASSIC_PROBE_EXECUTION_ID`) that its manifest must name, with this campaign and this ledger, and be marked complete. The session's command runs as a process tree (a process group on Linux and macOS, a job object on Windows) that is ended whole whenever the session ends, so nothing it started can dispatch later. The recovery's bound is a monotonic time, so a wall-clock jump cannot extend it. The supervisor returns within its hard end plus 0.5 s (`supervisor.TOLERANCE_S`), and a charge whose outcome is unknown keeps its reservation |
| **The Linux test** | `test_a_body_dripped_past_the_deadline_is_cut_off` expected a forced kill when the worker had stopped by itself at its own deadline, which it does first on Linux | The test asserts the deadline, the outcome, the partial that was kept and the worker's end, whichever ended it. A separate test makes a worker hang past its deadline and checks a real kill and reap |

C1's redirect and credential protections, C3's checks under the ledger lock and just before dispatch, C5's bounded backoff and the shared accounting are unchanged, and their tests pass on 1.7.2. Live mode stays disabled, and the steps, the response checks, the payloads and the campaign limits are those of 1.7.1.

## Offline proof

**Release 1.7.2.** The probe's own [`offline_results/`](../classic-probe-1.7.2/offline_results/) come from a clean
export, installed with `uv sync --frozen`, on Windows (2026-11-05, 15:58:16Z to 16:02:05Z):
- 204 tests: 199 passed, 5 skipped (`01_pytest_standalone.txt`, `junit_standalone.xml`).
- ruff, format and mypy clean; the plan, both offline replays, the offline ledger, its export, and live mode refused (exit 3).
- `16a` and `16b`: the review tests of 1.7.2 run against the `src/` of 1.7.1, in a second clean export: **13 failed, 9 passed, 1 skipped**. `17`: the same tests on 1.7.2: **22 passed, 1 skipped** (the FIFO test, which Windows cannot run). A step counts as expected only when its output says so, not by its exit code alone (`commands.csv`).

On Linux, the owner's Azure test VM ([`linux-owner-vm/`](../evidence/offline-tests/1.7.2-classic-probe/linux-owner-vm/), and from the delivered ZIP in [`probe-1.7.2/`](../evidence/owner-azure-test/1.6.8/probe-1.7.2/)):
- the published 1.7.1, as extracted: 1 failed, 169 passed, 3 skipped, the failure the client saw;
- the review tests on 1.7.1's code: **14 failed, 11 passed**, the 14th being the FIFO test: a FIFO at the evidence path held 1.7.1's supervisor past its hard end;
- the same tests on 1.7.2: **25 passed**;
- the whole suite on 1.7.2: 201 passed, 3 skipped; ruff, format and mypy clean.

In the development tree on Windows, [`1.7.2-classic-probe/`](../evidence/offline-tests/1.7.2-classic-probe/) holds the same tests on 1.7.1's code: **13 failed, 11 passed, 1 skipped**, and the whole suite on 1.7.2: 199 passed, 5 skipped.

**The skips, and why they differ by system.**
- Both systems: `test_vendored.py`, twice. The Walmart and Mariano's collectors' sources are not beside a probe-only extraction, so the vendored copies cannot be compared with them there; each copy is still checked against its recorded Git object.
- Windows only: the FIFO tests (`test_review_of_171.py`, `test_supervisor_evidence.py`), because Windows has no FIFO at a file's path, so nothing there can hold an open; and a symbolic-link test, because making a link needs a privilege a normal Windows account lacks. Windows links are refused by the same `lstat` test.
- Linux only: the write-through rename (`test_c2_c4_reproduction.py`), which is the Windows form of a synced rename.

**Release 1.7.1**, for the record: 173 tests, 171 passed, 2 skipped, from a clean export on Windows
([`classic-probe-1.7.1/offline_results/`](../classic-probe-1.7.1/offline_results/)); [`evidence/offline-tests/1.7.1-classic-probe/`](../evidence/offline-tests/1.7.1-classic-probe/) holds its 7 tests failing on 1.7.0's code.


**Release 1.7.0**, for the record: 158 tests, 156 passed, 2 skipped, from a clean export
([`classic-probe-1.7.0/offline_results/`](../classic-probe-1.7.0/offline_results/)); 157 passed and 1 skipped in its
development tree
([`evidence/offline-tests/1.7.0-classic-probe/DEV_TREE_TESTS_1.7.0.log`](../evidence/offline-tests/1.7.0-classic-probe/DEV_TREE_TESTS_1.7.0.log)).

Every test talks to a scripted HTTP stub on `127.0.0.1` (`tests/loopback_stub.py`). This build can make a transport
only for a loopback stub. Its worker refuses the real endpoint and any other target. A test checks that no
credential reaches the worker's arguments or environment. The C2 tests use separate processes, a ledger lock held by
another connection and killed sessions.

| Finding | Tests (in `tests/`) |
|---|---|
| C1 | `test_a_redirect_is_reported_and_never_followed`: 301, 302, 303, 307 and 308, each to the same host, another host, plain HTTP and a relative loop (20 cases). Each opens one connection, and the credentials are sent once. `test_a_redirect_chain_stops_the_campaign_after_one_request` covers a chain of five hops. Also `test_a_request_for_any_other_url_is_refused_before_a_worker_starts` and `test_the_worker_itself_refuses_the_real_endpoint_and_any_other_target`. |
| C2 | 1.7.0: `test_a_server_that_never_answers_is_killed_and_reaped_at_the_deadline`, `test_a_body_dripped_past_the_deadline_is_cut_off`, `test_a_body_above_its_limit_is_truncated_on_success_and_error_alike`, `test_a_truncated_answer_stops_the_campaign_and_is_never_read` and `test_a_compression_bomb_is_refused_within_its_decoded_limit` (all in `test_isolated_transport.py`); `test_a_session_past_its_hard_end_is_killed_with_its_worker_and_recovered` (`test_supervisor.py`). 1.7.1, failing on 1.7.0: `test_c2_the_recovery_after_a_kill_ends_by_the_sessions_end_even_with_the_ledger_locked`, `test_c2_the_writes_after_an_answer_wait_for_the_lock_no_longer_than_the_session_allows` and `test_c2_a_session_that_cannot_be_reaped_after_its_kill_is_still_recovered` (`test_c2_c4_reproduction.py`). 1.7.1, new: `test_after_one_refusal_of_the_lock_the_session_does_not_wait_for_it_again`, `test_a_session_that_exits_cleanly_without_its_evidence_is_recovered` and `test_a_recovery_that_overruns_is_killed_by_the_sessions_end` (`test_durable_evidence.py`). 1.7.2, failing on 1.7.1: `test_c2_a_fifo_at_the_evidence_path_cannot_hold_the_supervisor_past_its_hard_end`, `test_c2_a_previous_runs_complete_evidence_is_not_taken_for_this_sessions`, `test_c2_a_process_a_session_leaves_behind_is_killed_before_it_can_dispatch`, `test_c2_the_recovery_keeps_its_bound_when_the_wall_clock_jumps` and `test_c2_an_immediate_restart_in_the_same_folder_keeps_each_sessions_evidence_its_own` (`test_review_of_171.py`). 1.7.2, new: the seven tests of `test_supervisor_evidence.py`, the drip test as corrected, and the forced hung-worker test (`test_isolated_transport.py`); the control `test_c2_control_a_stalled_request_ends_within_the_tolerance_and_nothing_dispatches_later`. |
| C3 | `test_the_time_is_read_only_while_the_write_lock_is_held`, `test_a_reservation_that_waited_for_the_lock_is_checked_against_the_time_left_when_it_gets_it`, `test_the_wait_for_the_lock_is_bounded_and_reserves_nothing`, `test_the_last_check_before_sending_refuses_a_late_request_and_records_it_as_never_sent` and `test_a_stop_recorded_by_another_invocation_is_seen_at_the_last_check` (`test_ledger.py`). Wall-clock jumps and clamped allowances are in `test_deadline.py`. |
| C4 | 1.7.0: `test_each_answer_is_kept_and_indexed_before_the_next_paid_step`, `test_an_answer_that_cannot_be_kept_stops_the_campaign_before_another_request` and `test_the_export_says_when_a_capture_was_not_checked_in_time` (`test_campaign.py`); `test_a_capture_index_row_is_never_changed_or_deleted` (`test_ledger.py`); `test_a_crash_at_each_point_leaves_the_money_held_and_the_evidence_recoverable` (`test_supervisor.py`). 1.7.1, failing on 1.7.0: `test_c4_an_answer_received_before_a_crash_is_kept_without_a_paid_refetch`, `test_c4_the_evidence_manifest_is_synced_before_it_is_renamed_into_place`, `test_c4_on_windows_a_kept_file_is_renamed_through_to_the_disk` and `test_c4_a_body_cut_at_its_deadline_is_recorded_as_partial_never_as_an_answer` (`test_c2_c4_reproduction.py`, with a new drill mode in `session_drill.py`, `loopback-crash-after-send`). 1.7.1, new: `test_an_answer_whose_worker_died_before_its_final_rename_is_kept_without_a_refetch`, `test_a_raw_body_that_does_not_match_its_status_is_refused_and_never_indexed`, `test_a_partial_body_found_at_a_recovery_is_recorded_once_and_never_indexed`, `test_a_dispatch_name_is_used_once_and_its_files_are_never_overwritten` and `test_a_body_cut_by_the_workers_kill_is_kept_as_partial_with_its_length_and_hash` (`test_durable_evidence.py`). 1.7.2, failing on 1.7.1: `test_c4_a_body_shorter_than_its_declared_length_is_never_an_answer` (200 and 500), `test_c4_a_declared_body_of_which_nothing_came_is_never_an_answer`, `test_c4_a_body_cut_short_below_its_byte_limit_is_partial_not_an_answer`, `test_c4_a_campaign_keeps_a_short_body_as_partial_and_holds_its_money`, `test_c4_a_short_body_survives_a_crash_and_an_immediate_restart_without_a_refetch`, `test_c4_a_raw_answer_shorter_than_its_declared_length_is_never_kept_as_whole`, `test_c4_a_whole_answer_whose_worker_is_killed_before_its_final_rename_is_kept_whole` and `test_c4_a_partial_the_worker_kept_before_its_kill_is_still_described` (`test_review_of_171.py`). Controls, passing on both: exact length, no body, exactly the byte limit, above the byte limit, a chunked body cut short. |
| C5 | `test_a_backoff_is_a_real_wait_by_default`, `test_retry_after_is_honoured_and_a_longer_wait_ends_the_step` and `test_retry_after_past_the_deadline_is_not_waited_for` (`test_campaign.py`). `test_a_backoff_really_waits_and_never_past_the_deadline`, `test_the_default_sleeper_is_the_real_one` and `test_retry_after_is_read_in_both_documented_forms` (`test_deadline.py`). |

On 1.7.2 no test of C1, C3 or C5 was removed or changed. The only lines the diff removes from tests are the drip test's single forced-kill assertion (replaced as above), a stub of `Popen.communicate` that 1.7.2's transport no longer calls, and a test helper's signature, whose callers changed with it.

No test of 1.7.0 was changed or removed in 1.7.1. One of them,
`test_the_export_says_when_a_capture_was_not_checked_in_time`, first failed against an early draft of 1.7.1; the
code was corrected (the export's checks keep running until the session's true end), not the test.

## The pinned diffs

- **1.6.0 to 1.7.0.** The diff from 1.6.0 (`5454e9c`) to 1.7.0 as delivered (`1780349`) is in
  `evidence/offline-tests/1.7.0-classic-probe/CLASSIC_PROBE_1.6.0_TO_1.7.0.diff`, with `DIFFSTAT.txt` beside it
  (24 files): source 11 files, 1,186 lines added and 229 removed; tests 8 files, 1,027 added and 11 removed;
  documents 3 files, 7 added and 5 removed; version only, `pyproject.toml` and `uv.lock`. C2 and C4 needed new
  parts: a worker process (`networker.py`), a supervisor (`supervisor.py`), a session clock (`deadline.py`) and a
  capture store (`captures.py`).
- **1.7.0 to 1.7.1.** The diff from 1.7.0 (`6b9be92`, tree `8305ffe2…`) to 1.7.1 (`68ff3d8`) is in
  `evidence/offline-tests/1.7.1-classic-probe/CLASSIC_PROBE_1.7.0_TO_1.7.1.diff`, with `DIFFSTAT.txt` beside it
  (16 files, 1,492 lines added and 167 removed):
  - source: 9 files, 940 added and 159 removed, one of them new (`durable.py`: synced writes and write-through
    renames);
  - tests: 3 files, 528 added and 1 removed (two new test files, and the drill mode above);
  - documents: `README.md` and `CLASSIC_TEST_PLAN.md`, which had described C2 and C4 as corrected in 1.7.0;
  - version only: `pyproject.toml` and `uv.lock`.
- **1.7.1 to 1.7.2.** The diff from 1.7.1 (`68ff3d8`, tree `7adfea8f…`) to 1.7.2 (`7768514`, tree `3ada8871…`) is in
  `evidence/offline-tests/1.7.2-classic-probe/CLASSIC_PROBE_1.7.1_TO_1.7.2.diff`, with `DIFFSTAT.txt` beside it
  (19 files, 1,917 lines added and 188 removed), one source file new (`proctree.py`: a session's process tree).

The Mariano's adapter and the vendored page readers are unchanged. The documented contract (endpoint, payloads,
prices) is unchanged.

## What this does not establish

- No Classic scraping request has been sent, by any release; the only request with Classic-style credentials was W0,
  refused. Each correction is proven on a loopback stub, not on Oxylabs. Classic stays disabled.
- A crash while the operating system itself fails (power loss with a disk that does not honour a flush) is outside
  what an application can prove; the tests show the order of syncs and renames, and the recovery from each crash
  point a process can reach.
- A future live-enabled build needs:
  - its own version;
  - the exact documented route;
  - a Classic username and password with a real entitlement;
  - the account owner's authorization.
- Mariano's page 2 stays unplanned. The recorded Classic contract does not establish it, and neither the adapter nor
  any credential settles it.
