# Classic probe: the corrections C1 to C5 (shared probe 1.7.0)

The client's second review found five defects in the frozen Walmart Classic probe 1.5.2. This page shows where each
defect was, that the newer shared probe 1.6.0 (published with Mariano's) inherited all five, and how release 1.7.0
corrects them. It also lists the offline tests that prove each correction.

**Live mode stays disabled.** No Classic scraping request has ever been sent. The only request made with Classic-style
credentials was W0: one usage-statistics query that sent the Web API key as Basic credentials and was refused (HTTP
401, [`TECHNICAL_REPORT.md`](TECHNICAL_REPORT.md), section 8). The credential on file is an Oxylabs **Web API**
Bearer key, not a Classic username and password, so no live Classic test is possible with it.

## The three probes and their identities

| Probe | What it is | Identity | Where it is published |
|---|---|---|---|
| **1.5.2**, Walmart only | The probe the client reviewed. Frozen with collector `627c804d66aa33fc423fd2296c8896c5d5c2c3d4`; its code last changed at `2ed64b70809a67c49c68ebda5e3c3420f079073b`. Its Mariano's reservation is not an adapter. | delivered archive SHA-256 `d4785ccb…` (see `manifests/FILE_MAP.csv`) | [`classic-probe/`](../classic-probe/) in this repository, unchanged |
| **1.6.0**, shared | Adds store 53100502/PICKUP and the Mariano's steps. It plans **no** Mariano's page-2 request. | commit `1f568b8d367ee90e0f4a87879a44873ae649e906`; `classic-probe` tree `33c2d786fa793e2e588746f219eb9118cc789c38`; adapter [`src/classic_probe/marianos.py`](https://github.com/lonadonia/marianos-azure-scraper/blob/1f568b8d367ee90e0f4a87879a44873ae649e906/classic-probe/src/classic_probe/marianos.py) in that tree, blob `9de6510bddbb0cae7fd86e09dac5ed32fc3487a4` | [lonadonia/marianos-azure-scraper](https://github.com/lonadonia/marianos-azure-scraper/tree/1f568b8d367ee90e0f4a87879a44873ae649e906/classic-probe), unchanged |
| **1.7.0**, shared, corrected | 1.6.0 with C1 to C5 corrected. It is authoritative from this delivery. | the probe's source tree is Git tree `8305ffe25665b404347954dad38d501cbba70640`, both at `1780349e522d771a3642fe88bfb7b542044ec844`, where its archive was built, and at the delivery's final revision `67d216eb8ee2ec839a437b0b5bf2d594324b6982` (collector 1.6.5); the adapter blob is still `9de6510bddbb0cae7fd86e09dac5ed32fc3487a4`, unchanged | [`classic-probe-1.7.0/`](../classic-probe-1.7.0/) in this repository |

The published 1.6.0 tree `33c2d786…` is the development tree `28ae3603…` plus one added file, `CLASSIC_PROBE.md`.
The 1.7.0 code was committed at `2c08585` (tree `0ac0bdb1…`); the next commit, `48307cf`, corrected three of its
documents (README, test plan, documented contract: each named the release 1.6.0 or the old transport), which gives
the tree `8305ffe2…`. No later commit of this delivery changed the probe.
The Mariano's adapter is byte-for-byte the same in 1.6.0 and 1.7.0, so every correction is in the shared layer:
transport, ledger, campaign, deadline and captures.

## The defects and their corrections

The line numbers refer to the files of each release.

| Finding | In 1.5.2 (reviewed) | Inherited by 1.6.0 | Correction in 1.7.0 |
|---|---|---|---|
| **C1** Redirect policy absent | `transport.py:82` sends with `urllib.request.urlopen`, whose default opener follows redirects | yes, `transport.py:82` | Nothing follows a redirect. The request runs in a separate worker process (`networker.py`) through `http.client`, which never follows one. The worker refuses any target other than `https://realtime.oxylabs.io:443/v1/queries` (`networker.py:33`). A 3xx answer is recorded, with its location, and stops the campaign (`checks.py:77`). The credentials are sent once, to the documented endpoint only. The original dispatch stays charged at "unknown". |
| **C2** A timeout leaves the worker alive; body, processing and export are unbounded | `campaign.py:226` bounds a request with `bounded_send`, a thread and queue timeout that does not stop the thread | yes, `campaign.py:228` | Each request runs in its own process, which is killed and reaped at the request's allowance (`transport.py:116`, `:196` to `:201`). The body is bounded on success and on error alike, and so are the headers and the decompressed size (`ResponseLimits`, `decode_body` at `transport.py:99`). A truncated body is never parsed. A session supervisor kills the whole session, with every process it started, at the session's hard end, then recovers it into an incomplete manifest (`supervisor.py`). An "unknown" reservation stays held: nothing claims the remote side was cancelled. |
| **C3** A stale clock across the ledger lock and dispatch | `ledger.py:401` reads the clock before taking the write lock, and `mark_sent` checks no time | yes, `ledger.py:401` and `:479` | The time is read under the lock (`ledger.py:514`). The wait for the lock is bounded, and a wait that runs out reserves nothing (`LockNotObtained`, `ledger.py:130`). `mark_sent` checks the time and every stop again just before sending (`ledger.py:591`), and records a late request as never sent. A `SessionClock` takes the earlier of the monotonic and wall-clock ends and keeps the export and cleanup time in reserve. It clamps each allowance and each backoff to the time left (`deadline.py:20` to `:52`). A restart keeps the campaign's durable deadline. |
| **C4** Responses held only in memory until the final export | `campaign.py:174` and `:234` keep responses in a list that only `_export` writes | yes, `campaign.py:176` and `:236` | Each bounded answer is written atomically (a private `.part` file, then `fsync` and `os.replace`) and indexed in the ledger before the next paid step (`captures.py:134`, `campaign.py:281`). The index rows cannot be changed. On restart, the captures are recovered: indexed, or removed if they were never completed (`captures.py:164`). A truncated answer is never presented as complete. The export is written from the durable index. The original and sanitized hashes are both kept. |
| **C5** The default retry sleep is a no-op | `campaign.py:171`: `sleep or (lambda _s: None)` | yes, `campaign.py:173` | The default is the real `time.sleep` (`campaign.py:182`). A backoff is a real wait. It never runs past the deadline, and the session stops during it when time runs out. A `Retry-After` in either documented form is honoured up to 60 s. A longer wait ends the step (`campaign.py:328`). Every retry is a new dispatch with its own reservation. |

## Offline proof

Test results: the probe's own [`offline_results/`](../classic-probe-1.7.0/offline_results/) (the clean export:
`01_pytest_standalone.txt`, `junit_standalone.xml`, and the other commands of `commands.csv`) and
[`evidence/offline-tests/1.7.0-classic-probe/DEV_TREE_TESTS_1.7.0.log`](../evidence/offline-tests/1.7.0-classic-probe/DEV_TREE_TESTS_1.7.0.log)
(the development tree). From a clean export of the delivery's revision, installed with `uv sync --frozen`: 158
tests, 156 passed, 2 skipped. Both skips are the vendored-file check, which compares
the page readers copied from the Walmart and Mariano's collectors with those collectors' sources; a probe-only
extraction has neither beside it. In the development tree (157 passed, 1 skipped) the Walmart check passes, and the
Mariano's check is skipped because the Mariano's collector beside the probe there is a different release.

Every test talks to a scripted HTTP stub on `127.0.0.1` (`tests/loopback_stub.py`). This build can make a transport
only for a loopback stub. Its worker refuses the real endpoint and any other target. A test checks that no
credential reaches the worker's arguments or environment.

| Finding | Tests (in `tests/`) |
|---|---|
| C1 | `test_a_redirect_is_reported_and_never_followed`: 301, 302, 303, 307 and 308, each to the same host, another host, plain HTTP and a relative loop (20 cases). Each opens one connection, and the credentials are sent once. `test_a_redirect_chain_stops_the_campaign_after_one_request` covers a chain of five hops. Also `test_a_request_for_any_other_url_is_refused_before_a_worker_starts` and `test_the_worker_itself_refuses_the_real_endpoint_and_any_other_target`. |
| C2 | `test_a_server_that_never_answers_is_killed_and_reaped_at_the_deadline`, `test_a_body_dripped_past_the_deadline_is_cut_off`, `test_a_body_above_its_limit_is_truncated_on_success_and_error_alike`, `test_a_truncated_answer_stops_the_campaign_and_is_never_read` and `test_a_compression_bomb_is_refused_within_its_decoded_limit` (all in `test_isolated_transport.py`). `test_a_session_past_its_hard_end_is_killed_with_its_worker_and_recovered` (`test_supervisor.py`). |
| C3 | `test_the_time_is_read_only_while_the_write_lock_is_held`, `test_a_reservation_that_waited_for_the_lock_is_checked_against_the_time_left_when_it_gets_it`, `test_the_wait_for_the_lock_is_bounded_and_reserves_nothing`, `test_the_last_check_before_sending_refuses_a_late_request_and_records_it_as_never_sent` and `test_a_stop_recorded_by_another_invocation_is_seen_at_the_last_check` (`test_ledger.py`). Wall-clock jumps and clamped allowances are in `test_deadline.py`. |
| C4 | `test_each_answer_is_kept_and_indexed_before_the_next_paid_step`, `test_an_answer_that_cannot_be_kept_stops_the_campaign_before_another_request` and `test_the_export_says_when_a_capture_was_not_checked_in_time` (`test_campaign.py`). `test_a_capture_index_row_is_never_changed_or_deleted` (`test_ledger.py`). `test_a_crash_at_each_point_leaves_the_money_held_and_the_evidence_recoverable` (`test_supervisor.py`). |
| C5 | `test_a_backoff_is_a_real_wait_by_default`, `test_retry_after_is_honoured_and_a_longer_wait_ends_the_step` and `test_retry_after_past_the_deadline_is_not_waited_for` (`test_campaign.py`). `test_a_backoff_really_waits_and_never_past_the_deadline`, `test_the_default_sleeper_is_the_real_one` and `test_retry_after_is_read_in_both_documented_forms` (`test_deadline.py`). |

## The pinned diff

The diff from 1.6.0 (`5454e9c`) to 1.7.0 as delivered (`1780349`) is in
`evidence/offline-tests/1.7.0-classic-probe/CLASSIC_PROBE_1.6.0_TO_1.7.0.diff`. `DIFFSTAT.txt` beside it gives the
per-file summary (24 files):
- source: 11 files, 1,186 lines added and 229 removed;
- tests: 8 files, 1,027 lines added and 11 removed;
- documents: 3 files, 7 lines added and 5 removed (the release and the transport named correctly);
- version only: `pyproject.toml` and `uv.lock`.

The diff is not small, because C2 and C4 needed new parts:
- a worker process (`networker.py`);
- a supervisor (`supervisor.py`);
- a session clock (`deadline.py`);
- a capture store (`captures.py`).

The Mariano's adapter and the vendored page readers are unchanged. The documented contract changed in one sentence,
which named the old transport; the contract itself (endpoint, payloads, prices) is unchanged.

## What this does not establish

- No Classic scraping request has been sent, by any release; the only request with Classic-style credentials was W0,
  refused. Each correction is proven on a loopback stub, not on Oxylabs.
- A future live-enabled build needs:
  - its own version;
  - the exact documented route;
  - a Classic username and password with a real entitlement;
  - the account owner's authorization.
- Mariano's page 2 stays unplanned. The recorded Classic contract does not establish it, and neither the adapter nor
  any credential settles it.
