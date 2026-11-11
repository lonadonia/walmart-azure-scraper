# Reproduce the client's case on Windows: probe 1.7.2, then probe 1.7.4

Offline. Every process is a local Python process, and the only connections are to a stub on 127.0.0.1. Live mode
stays disabled, no credential is read, and nothing is sent to Oxylabs or to a retailer.

Sections 1 to 4 are for Windows, in PowerShell: you need Windows 10 or 11, Git, Python 3.12 and
[uv](https://docs.astral.sh/uv/). The recorded runs used Windows 11 Pro 10.0.26200, CPython 3.12.10 and uv 0.13.1.
Section 5 runs the tests that apply to Linux, in bash.

## 1. The clone, at this revision

```
git clone https://github.com/lonadonia/walmart-azure-scraper.git
cd walmart-azure-scraper
git checkout review-1.6.8-probe174-20261111
python manifests/check_frozen_trees.py
```

The last command ends with `PASS`: the published trees `classic-probe-1.7.2/` and `classic-probe-1.7.4/` are the
archives as built, file for file. Run it before creating any environment inside the clone. The steps below work on
copies placed outside the clone.

## 2. The reviewed version: probe 1.7.2, with the new test file added

```
$w = "C:\probe-review"          # any short folder outside the clone
New-Item -ItemType Directory $w | Out-Null
Copy-Item -Recurse classic-probe-1.7.2\oxylabs-classic-probe "$w\p172"
Copy-Item classic-probe-1.7.4\oxylabs-classic-probe\tests\test_review_of_172.py "$w\p172\tests\"
Push-Location "$w\p172"
uv sync --frozen
uv run --frozen python -m pytest -p no:cacheprovider -rA tests/test_review_of_172.py
Pop-Location
```

Expected (recorded in [`REPRODUCTION_ON_1.7.2_WINDOWS.log`](REPRODUCTION_ON_1.7.2_WINDOWS.log)): `5 failed, 2 passed`.
The helpers the test file imports (`tests/loopback_stub.py`, `tests/test_c2_c4_reproduction.py`) are the same in
1.7.2 and 1.7.4. Each test prints a `FACTS` line, and in it:

- the first control shows the old limitation. The parent exited with code 0, and the child was still alive
  afterwards (`"child_alive_after_its_parent_exited": true`). `taskkill /F /T` on the parent answered 128,
  "ERROR: The process ... not found.", and the child was still alive after it (`"child_alive_after_taskkill_tree": true`).
  The test then ends the child itself;
- with no job object, and with a process that could not join the job, 1.7.2 ran the session anyway
  (`"session_ran": true`, `"held_by": "taskkill /T (...)"`). The session's child outlived the supervisor and
  connected to the stub (`"connections_to_the_stub": 1`), while the result said `"left_running": false` and
  `"problems": []`;
- with `IsProcessInJob` answering "not a member", 1.7.2 never asked it (`"forced": []`) and resumed the process
  (`"resumed": 1`);
- with the job's count unreadable, 1.7.2 gave no cleanup verdict (`assert None == 'unknown'`), reported
  `"left_running": false`, and took the session's evidence;
- 1.7.2 gives no session status (`assert (None == 'ok')`).

## 3. The candidate: probe 1.7.4

```
Copy-Item -Recurse classic-probe-1.7.4\oxylabs-classic-probe "$w\p174"
Push-Location "$w\p174"
uv sync --frozen
uv run --frozen python -m pytest -p no:cacheprovider -rA tests/test_review_of_172.py
uv run --frozen python -m pytest -p no:cacheprovider -rs
uv run --frozen python -m mypy --platform linux
Pop-Location
```

Expected:

- the review tests give `7 passed` ([`CANDIDATE_1.7.4_WINDOWS.log`](CANDIDATE_1.7.4_WINDOWS.log));
- the whole suite gives `229 passed, 5 skipped` ([`FULL_1.7.4_WINDOWS.log`](FULL_1.7.4_WINDOWS.log)). The 5 skips
  are named in [`README.md`](README.md);
- the type check for Linux gives `Success: no issues found in 25 source files`
  ([`FULL_1.7.4_WINDOWS_checks.log`](FULL_1.7.4_WINDOWS_checks.log)). The archive's first build, never published,
  gave 3 errors here ([`TYPES_FOR_LINUX_WINDOWS.log`](TYPES_FOR_LINUX_WINDOWS.log)).

In the `FACTS` lines:

- with no job object: `"refused": true`, `"status": "refused"`, `"stage": "create"`, no process created, and
  `"connections_to_the_stub": 0`;
- with a failed assignment or verification: refused at `assign` or `verify`. Just before its end, the process had
  `"threads_suspend_counts": [1]`, `"kernel_100ns": 0`, `"user_100ns": 0` and `"resumed": 0`, so it never ran. It
  was terminated and reaped;
- with a working job object and the parent gone first: the child was alive before the cleanup and gone after it,
  with `"cleanup": "verified"`;
- with the count unreadable: `"cleanup": "unknown"`, `"left_running": null`, `"gone": null` and
  `"status": "cleanup-unknown"`. The evidence was not taken;
- an ordinary session: `"status": "ok"`, only with its tree verified gone.

## 4. An independent check that nothing was left running

After steps 2 and 3, no test process should remain:

```
Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object CommandLine -match 'child\.py|session\.py' | Select-Object ProcessId, CommandLine
```

It prints nothing. A child that outlived every cleanup would also end by itself within about 40 s: the test child's
life is bounded.

## 5. On Linux

The recorded Linux run used the owner's test VM (Ubuntu 24.04.5, CPython 3.12.3, uv 0.13.1) and the script
[`linux-owner-vm/build-a1def53/vm_probe_174b.sh`](linux-owner-vm/build-a1def53/vm_probe_174b.sh), which starts from
the two archives and keeps every output; after each `uv sync --frozen` it runs the installed `.venv/bin/python` where
the block below has `uv run --frozen python`. The same tests from a clone made as in section 1 (the check there is
`python3 manifests/check_frozen_trees.py` on Linux), in bash, on copies placed outside it as in sections 2 and 3:

```
w=~/probe-review                # any folder outside the clone
mkdir -p $w
cp -r classic-probe-1.7.2/oxylabs-classic-probe $w/p172
cp classic-probe-1.7.4/oxylabs-classic-probe/tests/test_review_of_172.py $w/p172/tests/
cp -r classic-probe-1.7.4/oxylabs-classic-probe $w/p174
(cd $w/p172 && uv sync --frozen && uv run --frozen python -m pytest -p no:cacheprovider -rA tests/test_review_of_172.py)
cd $w/p174
uv sync --frozen
uv run --frozen python -m pytest -p no:cacheprovider -rA tests/test_review_of_172.py
uv run --frozen python -m pytest -p no:cacheprovider -rs
uv run --frozen python -m mypy
uv run --frozen python -m mypy --platform win32
```

Expected (recorded in [`linux-owner-vm/build-a1def53/`](linux-owner-vm/build-a1def53/)):

- on 1.7.2: `2 failed, 1 passed, 4 skipped`. The 4 Windows-only tests are skipped; the two `test_w_` tests that run
  on Linux fail by their output, and the control passes;
- on 1.7.4: `3 passed, 4 skipped`;
- the whole suite on 1.7.4: 227 passed, 7 skipped (the run's JUnit file counts 234 tests, 0 failures, 0 errors,
  7 skipped; the 7 skips are named in [`README.md`](README.md#the-skips));
- both type checks: `Success: no issues found in 25 source files`.

Probe 1.7.4 has not been run on macOS.
