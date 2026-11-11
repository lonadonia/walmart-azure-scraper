# Oxylabs Classic offline probe 1.7.4: start here

An offline, reviewable probe for the Oxylabs **Classic** Web Scraper API. **It has never sent a request**: its live
mode is disabled in the code, and no credential is in this package.

This is the shared probe (Walmart and Mariano's on one ledger). Versions 1.7.0 to 1.7.2 corrected the five findings of
the client's second review (C1 to C5) and what the client's review of 1.7.1 reproduced. Version 1.7.3 refuses an
offline replay's unusable saved responses with one line before anything is created (T05); it was published with
Mariano's 1.9.0rc4 and changes no process code.

Version 1.7.4 corrects what the client's review of 1.7.2 found in C2 on Windows. 1.7.2 held a session's process tree
in a job object only when one could be made and the session's process joined it. Otherwise it ran the session anyway
under a `taskkill /T` fallback, which cannot reach a child whose parent has already exited, and it reported a count it
could not read as nothing left running. Now, on Windows, the session's process is created suspended and resumed only
once a job object holds it: the job is made with kill-on-close and without breakaway (both read back), and the
process is confirmed a member by `IsProcessInJob` and by the job's own count. If the job cannot be made, or the
process cannot be assigned, confirmed or resumed, nothing of the session runs: the process is terminated and reaped,
and the supervisor returns an explicit refusal that names the step. There is no fallback. Whether the tree has gone is
read only from the job's count (from the process group on Linux and macOS), never from the leading process's exit or
a `taskkill` result. A cleanup is `verified`, `failed` or `unknown`, an unknown stays unknown, and a session is `ok`
only once its tree is verified gone.

The 7 tests of `tests/test_review_of_172.py` use real local processes, a handshake file and a stub on 127.0.0.1, and
force each job-object failure at the kernel32 boundary only. Run against the `src/` of 1.7.2, the 5 `test_w_...`
tests fail by their output and the 2 control tests pass (Windows leaves a child running when its parent exits, and
`taskkill /T` on the parent cannot reach it; a working job object ends that child within the deadline): step 16b of
`offline_results/`. On 1.7.4 all 7 pass: step 17. The whole suite: step 01.

**Linux.** `offline_results/` were made on Windows. The first build of 1.7.4 (`05d8d87`, never published) was also
run on Linux, on the owner's test VM (Ubuntu 24.04.5): its tests passed there, but `mypy` reported three
`name-defined` errors, because its Windows-only start used names defined only on Windows and a type check run on
Windows reads the code for Windows alone. This build corrects that in `a1def53747dfabcb2ad9ca97efc421c1e70f0ac6`, with no change in what runs on
either system; step 04b checks the types for Linux. This build's own run on Linux is recorded outside the package,
with the Walmart publication that carries it.

The steps, the response checks, the limits and the Mariano's adapter are those of 1.6.0. The Walmart probe 1.5.2 that
the client reviewed is published unchanged beside it.

| What | Value |
| --- | --- |
| Probe version | 1.7.4 |
| Frozen revision | `a1def53747dfabcb2ad9ca97efc421c1e70f0ac6` (a probe-only revision: branch `classic-probe-1.7.4`, on probe 1.7.3 `95f96a02329bd3a92c9c8b07dd53e53ae89fe553`; no collector is released from it) |
| The probe's own code last changed in | `a1def53747dfabcb2ad9ca97efc421c1e70f0ac6` (the type check for Linux; C2 on Windows was corrected in `e0a6679`, its tests in `db383e0` and `05d8d87`); its tree last changed in `a1def53747dfabcb2ad9ca97efc421c1e70f0ac6` (the same commit, with the README) |
| Live mode | disabled: `gates.LIVE_ENABLED = False` in `oxylabs-classic-probe/src/classic_probe/gates.py` |
| Requests sent to Oxylabs or to a retailer | none |

## What is here

| Path | What |
| --- | --- |
| `oxylabs-classic-probe/` | the probe's tree, unchanged from that revision, with its `uv.lock`. Read its `README.md` |
| `oxylabs-classic-probe/CLASSIC_TEST_PLAN.md` | the staged plan for a future approved campaign |
| `oxylabs-classic-probe/docs/PAYLOAD_MATRIX.md` | every request the plan can send, its upper bound and its stops |
| `oxylabs-classic-probe/docs/DOCUMENTED_CONTRACT.md` | what the documentation says, page by page, with each saved page's SHA-256 |
| `offline_results/` | the outputs of the probe's offline run of this tree on Windows: tests, lint, types, plan, both replays, the refused live command, and the review tests on 1.7.2's code and on this one. `offline_results/README.txt` says what each file is |
| `saved_documentation/` | the public Oxylabs pages the contract names: those read on 2026-10-31 (`INDEX.json`), as published with probe 1.5.2, and those read for Mariano's on 2026-11-02 (`classic_docs_20261102/`, with its `index.json`), as published with the Mariano's delivery |
| `FILE_SHA256.txt` | the SHA-256 of every file of the probe's tree at that revision |
| `PACKAGE_MANIFEST.json` | this package's identity |

## Run it (offline)

Python 3.12 and [uv](https://docs.astral.sh/uv/) are the only prerequisites.

```
cd oxylabs-classic-probe
uv sync --frozen
uv run --frozen pytest
uv run --frozen ruff check src tests
uv run --frozen mypy --platform win32
uv run --frozen mypy --platform linux
uv run --frozen classic-probe plan --targets config/targets.json
uv run --frozen classic-probe validate --targets config/targets.json --rates config/rates.example.json
```

The client's case alone, on Windows: `uv run --frozen pytest -rA tests/test_review_of_172.py` (7 passed on 1.7.4).

The tests close the network: an attempt to open a socket or resolve a name fails the test that made it. Run from
this package alone, two tests are skipped on every system: `test_the_vendored_files_are_still_the_collectors_files`,
once for each collector, compares the vendored page readers with the collector's own files, which are not beside the
probe here. Some tests run on one kind of system only and say why when skipped: on Windows the tests that need a FIFO
or a symbolic link (three); on Linux and macOS the test of Windows' write-through rename (one) and the 4 Windows-only
tests of `tests/test_review_of_172.py` (job objects and `taskkill /T` exist only on Windows). On Windows this
package's run gives 229 passed and 5 skipped (step 01). The probe's README lists them.
Every vendored copy is still checked against its recorded Git object (`test_each_vendored_file_is_the_recorded_copy`).

## What is not established

The Walmart tests use SYNTHETIC Classic responses; the Mariano's tests use real saved Mariano's pages inside invented
Classic envelopes (OFFLINE REPLAY). **They show nothing about what Classic returns**: no account, target entitlement,
rate, store context, fulfillment or pagination has been confirmed. The limits in the plan (10 requests per retailer,
20 in total, 30 minutes, USD 5 with USD 0.50 of headroom) are a proposal to the client, not an approval. Running a
campaign needs the account owner's Classic credentials, entitlements, confirmed rates and written approval, and a
later version of this probe with live mode enabled. The credential used for the Walmart delivery's live stages is an
Oxylabs Web API key, not a Classic username and password.

Probe 1.7.4 has not been run on macOS.
