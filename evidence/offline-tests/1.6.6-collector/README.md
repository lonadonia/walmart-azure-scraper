# Collector 1.6.6: offline tests of the correction

No request reached a provider or Walmart. The tests run the collector against a scripted local stub on `127.0.0.1`.

## What 1.6.6 changes

In release 1.6.5, a complete, validated run whose automatic publication was refused was logged as
`PUBLICATION_REFUSED` at `WARN`, and the execution exited 0. So none of the alerts suggested in `docs/OPERATIONS.md` fired:
- any `ERROR` line;
- `RUN_FINISHED` with `exit_code != 0`.

A scheduled run that was refused could go unnoticed while the last published dataset grew older.

Release 1.6.6 (`39cc61f`, built as `cbea802`) changes three things:
- `PUBLICATION_REFUSED` is an `ERROR` event and log line, recorded on the run;
- the execution exits 6 (`Exit.REJECTED`);
- when Azure retries a scheduled execution whose run is already done, the retry (`_done_occurrence`) also exits 6. Before, it reported the occurrence as done with exit 0.

The documents changed with it:
- `docs/OPERATIONS.md`: the alert advice adds `OCCURRENCE_DONE` with `exit_code != 0` and names the case.
- `docs/CLI.md`: the exit-code table and the event list.
- `README.md`: a paragraph on 1.6.6.
- `docs/VERIFICATION.md`: how the change was tested.

Collection, the page reader, the records, the gates and the exports are unchanged from 1.6.5. Only the release number changed in the other files (`Dockerfile`, `pyproject.toml`, `uv.lock`, `__init__.py`, `core/paths.py`, the Azure parameters example).

| File | What it holds |
|---|---|
| `COLLECTOR_1.6.5_TO_1.6.6.diff`, `DIFFSTAT.txt` | the whole change from release 1.6.5 (`67d216e`) to 1.6.6 (`39cc61f`), collector folder only: 12 files, 144 lines added, 22 removed |
| `COLLECTOR_1.5.2_TO_1.6.6.diff`, `DIFFSTAT_1.5.2_TO_1.6.6.txt` | the pinned correction diff, collector folder only: from release 1.5.2 (`627c804`), the one the client reviewed, to 1.6.6. Each release's own step is in its folder, `../1.6.0-collector/` to `../1.6.6-collector/` |
| `REPRODUCTION_ON_1.6.5.log` | the two new tests against release 1.6.5's code: they fail (three runs, below) |
| `RETRY_GAP_BEFORE_THE_FULL_FIX.log` | an intermediate state of the fix that the second test caught (below) |
| `STATIC_1.6.6.log`, `UNIT_1.6.6.log`, `TESTS_ON_1.6.6.log` | on the committed 1.6.6 tree (`cbea802`, clean): ruff, format and mypy clean; the unit suite (533 passed); the two new tests and the unchanged publication test (3 passed) |

The full integration suite is not repeated here. It ran on clean extractions of both 1.6.6 editions, with the unit suite, ruff, format and mypy (`../../verification/1.6.6/package/`).

## The two new tests (`tests/integration/test_operations.py`)

| Test | What it requires |
|---|---|
| `test_a_refused_automatic_publication_is_an_error_with_a_non_zero_exit` | the target is not a test target, so the publication of the stub's pages is refused. The test requires: a validated run; exactly one `PUBLICATION_REFUSED` line, at `ERROR`, with its reason; exit 6 and `RUN_FINISHED` with `exit_code` 6; one `ERROR` event recorded on the run; nothing published |
| `test_a_scheduled_run_whose_publication_was_refused_exits_6_also_on_azures_retry` | the same through a scheduled execution, which exits 6. A second execution of the same occurrence 10 minutes later (Azure's retry) must also exit 6, send no request and create no run; nothing published |

No test was removed or weakened. The existing publication test (`test_a_complete_run_is_published_and_a_partial_run_never_replaces_it`) is unchanged and passes.

## The tests fail on 1.6.5 for the right reason

`REPRODUCTION_ON_1.6.5.log` holds three runs against release 1.6.5's collector code (src tree `4ff40b10…`, the tree of commits `67d216e` to `68ff3d8`):

1. 22:27:40Z, the first test: `PUBLICATION_REFUSED` came at `WARN`, not `ERROR`. Fail.
2. 22:28:13Z, the same test with pytest's local values (`-l`): the exit code was 0, not 6.
3. 22:32:58Z, both tests, with `operations.py` restored from `68ff3d8`: 2 failed. The first fails on `WARN`; the second fails on `0 == 6`, its scheduled execution's exit.

`RETRY_GAP_BEFORE_THE_FULL_FIX.log` (22:30:22Z) is the second test against an uncommitted first version of the fix. That version changed only `after_run`. The scheduled run itself ended with `RUN_FINISHED` exit 6, but Azure's retry of the same occurrence still returned 0 through `_done_occurrence`. The committed fix covers that path as well.

On the 1.6.6 commit both pass (`TESTS_ON_1.6.6.log`).
