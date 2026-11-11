# Probe 1.7.4 on Linux: the owner's test VM

OFFLINE TEST, 2026-11-10 (UTC), on the owner's Azure test VM: Ubuntu 24.04.5 LTS (kernel 7.0.0-1017-azure, x86_64),
CPython 3.12.3, uv 0.13.1. No request was sent to Oxylabs or to a retailer: after the installs, HTTP(S) went to a
closed local port, the tests close the network themselves, and the live command was refused (exit 3). Nothing ran in
the client's environment.

Each folder holds one run: the script that made it (`vm_probe_174*.sh`), its console output (`vm_probe_174*.out`),
`HOST.txt` (the system, both archives' SHA-256 as checked, the start and end), `file_sha256_check.txt` (each archive's
files checked against its own `FILE_SHA256.txt`), `commands.csv` (each command, its exit code, the expected one, and
the line its output had to show), one output file per command, and the JUnit file of the whole suite.

| Folder | Archive | Run | Result |
|---|---|---|---|
| [`first-build-05d8d87/`](first-build-05d8d87/) | the first build, from `05d8d87`, SHA-256 `d689e620…`; never published | 02:27:39Z to 02:30:18Z | 18 of 19 commands as expected. The tests passed (234: 227 passed, 7 skipped), but `mypy` exited 1 with 3 `name-defined` errors in `proctree.py` |
| [`build-a1def53/`](build-a1def53/) | this revision's archive, from `a1def53`, SHA-256 `cb5dc070…` | 02:54:29Z to 02:57:09Z | **20 of 20 as expected**: 234 tests, 227 passed, 7 skipped, 0 failed; ruff, format and mypy clean, mypy also for Windows; the review tests 3 passed and 4 skipped on 1.7.4, and 2 failed (by their output), 1 passed and 4 skipped on 1.7.2; no test process left |

What the first build's error was, and what `a1def53` changed, is in
[`../README.md`](../README.md#the-first-build-and-the-type-check-for-linux). The VM's home folder (which names its
user) and its host name are replaced in five files of each run (`manifests/REDACTIONS.csv`); nothing else in them was
changed.
