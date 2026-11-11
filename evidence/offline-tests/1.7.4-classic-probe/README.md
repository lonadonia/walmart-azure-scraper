# Offline tests of the shared Classic probe 1.7.4 (the probe 1.7.4 revision)

OFFLINE TEST, 2026-11-09 and 2026-11-10 (UTC). These runs answer the client's review of the 1.6.8 delivery's probe
1.7.2, which concerned C2, the session supervisor's process tree, on Windows. Live mode stays disabled. No request was
sent to Oxylabs or to a retailer. Every process in these tests is a local Python process, and the only connections are
to a stub on 127.0.0.1. The archive's own results are in
[`classic-probe-1.7.4/offline_results/`](../../../classic-probe-1.7.4/offline_results/).

| Probe | Commit (development monorepo) | Probe tree |
|---|---|---|
| 1.7.2, the reviewed version, as published in `classic-probe-1.7.2/` under `review-1.6.8-20261106` | `7768514aa1ffbaa7f96ca242d7b64e495fffefa5` | `3ada8871` |
| 1.7.3 (T05, published with Mariano's 1.9.0rc4) | `95f96a02329bd3a92c9c8b07dd53e53ae89fe553` | `912801d0` |
| 1.7.4, this revision. Its code changed in `e0a6679a3a0c9f479e98cb00821260e0856ecf08` (C2 on Windows) and in `a1def53` (the type check for Linux, [below](#the-first-build-and-the-type-check-for-linux)); `db383e0` and `05d8d87` changed only `tests/test_review_of_172.py` and `README.md` | `a1def53747dfabcb2ad9ca97efc421c1e70f0ac6` | `07477cc6` |
| 1.7.4, the archive's first build, from `05d8d87`: never published, because `mypy` failed on Linux | `05d8d87b32c17e339946539e5e2d61fb004f1c21` | `727c9308` |

## Platforms

On Windows, the preparation workstation:

- Windows 11 Pro 10.0.26200 (`Windows-11-10.0.26200-SP0`);
- CPython 3.12.10 and pytest 9.1.1;
- uv with `--frozen`, so each tree was installed from its own lockfile, and `UV_OFFLINE=1`.

Each tree was a clean `git archive` export, never the working copy. The runs were made one after another, never two
at once, because the tests time real processes.

On Linux, the owner's Azure test VM: Ubuntu 24.04.5 LTS (kernel 7.0.0-1017-azure, x86_64), CPython 3.12.3, uv 0.13.1,
from a clean extraction of the archive. See [On Linux](#on-linux-the-owners-test-vm). macOS was not run.

## The files

| File | What it is | Result |
|---|---|---|
| [`REPRODUCTION_ON_1.7.2_WINDOWS.log`](REPRODUCTION_ON_1.7.2_WINDOWS.log) | the 7 tests of `tests/test_review_of_172.py` on the reviewed code: the published `classic-probe-1.7.2/oxylabs-classic-probe` (git archive of `e733d01`, tag `review-1.6.8-20261106`, all 67 files byte-identical to the tag) with only that test file added | **5 failed, 2 passed** in 48.16 s, each failure with its output |
| [`CANDIDATE_1.7.4_WINDOWS.log`](CANDIDATE_1.7.4_WINDOWS.log) | the same 7 tests on 1.7.4 (git archive of `a1def53`) | **7 passed** in 31.27 s, none skipped |
| [`FULL_1.7.4_WINDOWS.log`](FULL_1.7.4_WINDOWS.log), [`FULL_1.7.4_WINDOWS.junit.xml`](FULL_1.7.4_WINDOWS.junit.xml) | the whole suite on 1.7.4 | 234 collected: **229 passed, 5 skipped, 0 failed**, 0 errors (177.05 s) |
| [`FULL_1.7.4_WINDOWS_checks.log`](FULL_1.7.4_WINDOWS_checks.log) | `uv sync --frozen`, `ruff check`, `ruff format --check`, `mypy`, and `mypy --platform linux` on 1.7.4 | each exit 0: "All checks passed!", "43 files already formatted", and "Success: no issues found in 25 source files" for Windows and for Linux |
| [`TYPES_FOR_LINUX_WINDOWS.log`](TYPES_FOR_LINUX_WINDOWS.log) | `mypy --platform win32`, `linux` and `darwin` on 1.7.2, on the first build (`05d8d87`) and on this build (`a1def53`), each a clean export | 1.7.2 and this build: no issue for any of the three. The first build: no issue for Windows, **3 errors** for Linux and for macOS |
| [`STABILITY_REFUSAL_TESTS_1.7.4_WINDOWS.log`](STABILITY_REFUSAL_TESTS_1.7.4_WINDOWS.log) | the two refusal tests (assignment failure and verification failure) run 15 times in a row | **15 of 15** exit 0; in each round, just before the refused process was ended, it had one thread with a suspend count of 1, no kernel or user time, and 0 resumes |
| [`linux-owner-vm/`](linux-owner-vm/) | the archive run on Linux, twice: the first build, then this one, each folder with its script and every output | see [On Linux](#on-linux-the-owners-test-vm) |
| [`EARLIER_FAILED_RUN_db383e0.txt`](EARLIER_FAILED_RUN_db383e0.txt) | the first offline run of the package, on `db383e0`. It failed in one test and is kept as found | see [The earlier failure](#the-earlier-failure) |
| [`experiments/`](experiments/) | the two Windows experiments behind the change from `db383e0` to `05d8d87`, with their outputs | see [The earlier failure](#the-earlier-failure) |
| [`CLASSIC_PROBE_1.7.2_TO_1.7.3.diff`](CLASSIC_PROBE_1.7.2_TO_1.7.3.diff) | `git diff 7768514..95f96a0 -- headless/oxylabs-classic-probe` (T05; no process code) | 7 files, +280/-23 |
| [`CLASSIC_PROBE_1.7.3_TO_1.7.4.diff`](CLASSIC_PROBE_1.7.3_TO_1.7.4.diff) | `git diff 95f96a0..a1def53 -- headless/oxylabs-classic-probe` (C2 on Windows, and the type check for Linux) | 8 files, +1,091/-74 |
| [`CLASSIC_PROBE_1.7.4_FIRST_BUILD_TO_THIS_BUILD.diff`](CLASSIC_PROBE_1.7.4_FIRST_BUILD_TO_THIS_BUILD.diff) | `git diff 05d8d87..a1def53 -- headless/oxylabs-classic-probe`: what changed after the first build | 2 files, +48/-41; with whitespace ignored (`git diff -w`), +10/-3 |
| [`DIFFSTAT.txt`](DIFFSTAT.txt) | the diffs file by file, and 1.7.3 to 1.7.4 by commit | |
| [`REPRODUCE.md`](REPRODUCE.md) | how to run the reproduction and the candidate from a clone, on Windows, and the same tests on Linux | |

The archive's own run is in `classic-probe-1.7.4/offline_results/` (2026-11-10T02:48:58Z to 02:53:27Z). Its 22
commands all ended as expected (`commands.csv`):

- step 01 is the whole suite: JUnit counts 234 tests, 0 failures, 0 errors, 5 skipped;
- step 04b checks the types for Linux (`mypy --platform linux`): no issue;
- step 15 is the refused live command: exit 3;
- step 16b runs the review tests on 1.7.2's `src/` inside the 1.7.4 tree. It exits 1 with 5 failed and 2 passed, and
  its output shows each failure;
- step 17 runs them on 1.7.4: 7 passed.

The archive was built twice from the same clean export, with the same SHA-256
(`cb5dc070792cd48caa866defe864a12964fe6d30587a734c5a252ed2a9898276`, 194 entries).

## The commands

Run in each tree on Windows (Git Bash, `uv` 0.13.1, Python 3.12.10):

```
uv sync --frozen
uv run --frozen python -m pytest -p no:cacheprovider -rA -v tests/test_review_of_172.py                  # reproduction and candidate
uv run --frozen python -m pytest -p no:cacheprovider -rs -v --junitxml=FULL_1.7.4_WINDOWS.junit.xml      # whole suite
uv run --frozen ruff check src tests
uv run --frozen ruff format --check src tests
uv run --frozen python -m mypy
uv run --frozen python -m mypy --platform linux
uv run --frozen python -m pytest -p no:cacheprovider -rA tests/test_review_of_172.py -k does_not_hold    # 15 times
```

Each run also had `--basetemp` set to a folder of its own. `python -m mypy` was used instead of the `mypy` launcher
because the workstation's Smart App Control blocked the launcher that `uv` installs. The module is the same.

## What the 7 tests show (the client's case)

Five of the tests use a small Python session program. It writes a handshake file, starts a child process and exits
as soon as the child runs. The child writes its own handshake file (its process id and creation time, so a reused id
is never mistaken for it). It then waits 3 s and, if it is still alive, connects to a stub on 127.0.0.1. The first
control runs that program directly; the other four run it through the supervisor's entry point,
`supervisor.run_session`. The last two tests run the probe's campaign drill through `supervisor.run_session`
against a stub on 127.0.0.1. Faults are forced only at the kernel32
boundary (`CreateJobObjectW`, `AssignProcessToJobObject`, `IsProcessInJob`, the job's accounting). Whether a process
is alive is checked independently of the code under test (`OpenProcess` and its creation time). The five tests built on the session program end every
process they saw in a fixture that runs on failure too, so none of them leaves a process behind.

| Test | On 1.7.2 (reproduction) | On 1.7.4 |
|---|---|---|
| `test_control_a_child_outlives_its_exited_parent_and_taskkill_tree_cannot_reach_it` (control, Windows only) | passed: the parent exited with code 0 while its child kept running; `taskkill /F /T /PID <parent>` answered 128, "ERROR: The process ... not found.", and the child was still alive. This is the old limitation, reproduced. The test then ends the child itself and checks that it has gone | passed, the same |
| `test_w_no_job_object_means_a_refusal_and_nothing_of_the_session_runs` (Windows only) | **failed**: with `CreateJobObjectW` failing, the session ran (`"held_by": "taskkill /T (no job object could be made)"`), its child outlived the supervisor and connected to the stub (`"connections_to_the_stub": 1`), and the result said `"left_running": false`, `"problems": []` | passed: `"refused": true`, `"status": "refused"`, stage `create`, 0 processes created, nothing ran, 0 connections |
| `test_w_a_process_the_job_does_not_hold_is_ended_suspended_and_refused[assign]` (Windows only) | **failed**: with `AssignProcessToJobObject` failing, 1.7.2 resumed the process anyway (`"resumed": 1`) under the `taskkill /T` fallback, and the child outlived the supervisor and connected | passed: refused at stage `assign`. Just before its end the process had one thread suspended once, 0 kernel and 0 user time, and no resume was asked for. It was terminated and reaped, and no child started |
| `test_w_a_process_the_job_does_not_hold_is_ended_suspended_and_refused[verify]` (Windows only) | **failed**: with `IsProcessInJob` answering "not a member", 1.7.2 never asked it (`"forced": []`) and ran the session (`"resumed": 1`) | passed: refused at stage `verify`, the same proof as above |
| `test_control_a_child_whose_parent_exited_first_is_ended_with_the_tree` (control, all systems) | passed: with a working job object the parent exited first, the child was alive before the cleanup and gone afterwards, within the deadline | passed: the same, with `"cleanup": "verified"` |
| `test_w_a_cleanup_that_cannot_be_told_is_never_reported_as_done` (all systems) | **failed**: with the job's accounting unreadable, 1.7.2 reported `"left_running": false` with `"gone": null`, no problem and no cleanup verdict (`assert None == 'unknown'`), and took the session's evidence | passed: `"cleanup": "unknown"`, `"left_running": null`, `"gone": null`, `"status": "cleanup-unknown"`, the evidence not taken, and a recovery ran whose manifest names the cleanup |
| `test_w_a_session_is_ok_only_once_its_tree_is_counted_gone` (all systems) | **failed**: 1.7.2 has no status (`assert (None == 'ok')`) | passed: `"status": "ok"` only with the tree verified gone |

On Linux the three tests marked "all systems" run; the other four are skipped as Windows-only. There, on 1.7.2's code,
the last two fail by their output and the control passes; on 1.7.4 all three pass
([On Linux](#on-linux-the-owners-test-vm)).

## The skips

On Windows, 5:

| Skipped test | Why |
|---|---|
| `test_vendored.py`, twice | a probe-only extraction: the Walmart and Mariano's collectors' sources are not beside the probe. Each vendored copy is still checked against its recorded Git object |
| the FIFO tests in `test_review_of_171.py` and `test_supervisor_evidence.py` | Windows has no FIFO at a file's path |
| the symbolic-link test in `test_supervisor_evidence.py` | making a link needs a privilege a normal Windows account lacks |

None of the 7 tests of `tests/test_review_of_172.py` was skipped on Windows.

On Linux, 7: `test_vendored.py` twice (as above); the write-through rename in `test_c2_c4_reproduction.py`, which is
the Windows form of a synced rename; and the 4 Windows-only tests of `tests/test_review_of_172.py` (job objects and
`taskkill /T` exist only on Windows).

## The earlier failure

The package's first offline run, on `db383e0`, failed in one test ([`EARLIER_FAILED_RUN_db383e0.txt`](EARLIER_FAILED_RUN_db383e0.txt)).
`test_w_a_process_the_job_does_not_hold_is_ended_suspended_and_refused[verify]` asserted that the refused process's
user time, read after its end, was 0, and it read 156,250 (100 ns units: one clock tick of 15.625 ms). The supervisor
had refused the process as it should, so the assertion was the problem. Windows samples CPU time by clock tick, and
it can charge a tick of user time to a process that is terminated without ever having run.

[`experiments/susp_times.py`](experiments/susp_times.py) creates 300 processes suspended and ends each without
resuming it, half through a job object and half with `TerminateProcess`
([`susp_times_300.out`](experiments/susp_times_300.out)):

- before the end, all 300 had 0 kernel and 0 user time;
- after the end, 6 had a tick of user time.

The test's docstring cites an earlier run of the same script, whose output was not kept: 10 of 300.
[`experiments/susp_count.py`](experiments/susp_count.py) reads each thread's suspend count without changing it
([`susp_count_200.out`](experiments/susp_count_200.out)). A process never resumed showed one thread suspended once in
100 of 100 cases; a process resumed 50 ms earlier showed four threads, none suspended, in 100 of 100.

So `05d8d87` takes the proof before the end, from Windows' own state. Just before the supervisor ends a refused
process, the test reads:

- its threads' suspend counts, which must be `[1]`;
- its kernel and user time, which must both be 0;
- the number of times the supervisor asked to resume it, which must be 0.

The same tests then pass in the archive's run and in 15 of 15 rounds. The supervisor's code did not change between
`e0a6679` and `05d8d87`.

## The first build and the type check for Linux

The archive was first built from `05d8d87` (SHA-256 `d689e62091a68acc4f716e9a0bd1fe3cc81073a5136f2934fe4232a4a267df98`)
and run on the owner's Linux VM on 2026-11-10, 02:27:39Z to 02:30:18Z
([`linux-owner-vm/first-build-05d8d87/`](linux-owner-vm/first-build-05d8d87/)). Its tests passed there, but `mypy`
exited 1 ([`04_mypy.txt`](linux-owner-vm/first-build-05d8d87/04_mypy.txt)):

```
src/classic_probe/proctree.py:342: error: Name "_Job" is not defined  [name-defined]
src/classic_probe/proctree.py:344: error: Name "CREATE_SUSPENDED" is not defined  [name-defined]
src/classic_probe/proctree.py:367: error: Name "_resume" is not defined  [name-defined]
Found 3 errors in 1 file (checked 25 source files)
```

`ProcessTree._start_held`, the Windows-only start, used three names that exist only under
`if sys.platform == "win32":`. Nothing failed when it ran, because `start()` calls it only on Windows. But `mypy` reads
the code for one platform at a time, the one it runs on unless `--platform` names another, so the checks run on Windows
said "Success" for code that does not type-check for Linux or macOS. On Windows, `mypy --platform linux` and
`--platform darwin` on the first build give the same 3 errors, and 1.7.2 gives none
([`TYPES_FOR_LINUX_WINDOWS.log`](TYPES_FOR_LINUX_WINDOWS.log)).

`a1def53` puts the method's body under `if sys.platform == "win32":`, followed by an explicit refusal (`TreeRefused`,
stage `create`) that nothing reaches. On Windows the code that runs is the same: with whitespace ignored, the diff adds
those two lines and wraps one line that the indent made too long
([`CLASSIC_PROBE_1.7.4_FIRST_BUILD_TO_THIS_BUILD.diff`](CLASSIC_PROBE_1.7.4_FIRST_BUILD_TO_THIS_BUILD.diff) shows the
indent too). The probe's README now runs `mypy` for both platforms, and the archive's step 04b checks the types for
Linux. Every Windows run above was then made again on `a1def53`, the archive was built again, and it was run on Linux
again. The first build was never published; its Linux run is kept as found.

## On Linux (the owner's test VM)

Both runs used the same script form (kept beside its outputs). It checks the SHA-256 of the 1.7.4 archive and of the
1.6.8 delivery's 1.7.2 archive, extracts both, checks each with its own `FILE_SHA256.txt`, installs each with
`uv sync --frozen`, and then sends HTTP(S) to a closed local port, with no credential variable. Each command's output
is a file of its own, and `commands.csv` gives its exit code and, where a step must fail, the line its output must
show. The replays use the inputs packed in `offline_results/`, as steps 10 and 11b on Windows write them with helper
scripts the archive does not hold. The VM's home folder (which names its user) and its host name are replaced in ten of
the published files, five of each run (`manifests/REDACTIONS.csv`).

| | [`first-build-05d8d87/`](linux-owner-vm/first-build-05d8d87/) | [`build-a1def53/`](linux-owner-vm/build-a1def53/), this revision's archive |
|---|---|---|
| Archive | SHA-256 `d689e620…` (frozen revision `05d8d87`) | SHA-256 `cb5dc070…` (frozen revision `a1def53`) |
| Run (UTC, 2026-11-10) | 02:27:39Z to 02:30:18Z | 02:54:29Z to 02:57:09Z |
| Commands as expected | 18 of 19: `04_mypy` exited 1 | **20 of 20** (with `04b`, the type check for Windows) |
| The whole suite (JUnit) | 234 tests, 0 failures, 0 errors, 7 skipped | 234 tests: **227 passed, 7 skipped, 0 failed**, 0 errors |
| `ruff check`, `ruff format --check` | exit 0 | exit 0 |
| `mypy` | **3 errors** (above) | "Success: no issues found in 25 source files", and the same with `--platform win32` |
| Review tests on 1.7.4 | 3 passed, 4 skipped | **3 passed, 4 skipped** |
| Review tests on 1.7.2's archive, the test file added | 2 failed, 1 passed, 4 skipped (by their output) | **2 failed, 1 passed, 4 skipped** (by their output) |
| The live command | refused, exit 3 | refused, exit 3 |
| Test processes left afterwards | 0 | 0 |

On 1.7.2 the two that fail on Linux are:

- `test_w_a_cleanup_that_cannot_be_told_is_never_reported_as_done`. With the process group's state forced unreadable
  (`os.killpg(pid, 0)` raising `EIO`), 1.7.2's supervisor returned no result at all: the error escaped `run_session`
  (`OSError: [Errno 5] forced: the process group cannot be asked`, raised from `proctree.py`'s `members_left`). On
  Windows the same test showed an unreadable count reported as nothing left running; on 1.7.4 it gives
  `"cleanup": "unknown"` and `"status": "cleanup-unknown"` on both systems;
- `test_w_a_session_is_ok_only_once_its_tree_is_counted_gone`: no status (`assert (None == 'ok')`).

The control passes on both builds and on 1.7.2.

The Linux run was first planned for 2026-11-09. The VM's SSH port did not answer from the workstation at 22:04:22Z or
at 22:27:20Z that day; the VM itself was running (its uptime on 2026-11-10 was 14 days). It answered at 02:22:13Z on
2026-11-10, and both runs were made then.
