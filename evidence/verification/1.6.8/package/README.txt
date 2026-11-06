CLEAN-EXTRACTION VERIFICATION of release 1.6.8 (commit 85c29e7b2404500299056973f50c84b84e187a5a), both editions, on
the workstation (Windows 11).
SYNTHETIC tests: fixture pages, stored authentic pages and a temporary local PostgreSQL. No request reached a provider
or Walmart: every step but the installs ran with HTTP(S) sent to a closed local port (127.0.0.1:9) and without any
provider key, database URL or collector setting of the workstation; the installs used uv's local cache only.

What ran (2026-11-05): verify168d_clean.py (this folder, as it ran: sha256
b7a2001b2e4036575085c213699c7b66e20520ecaf06c804e6d9e2f2edf174f6) on WALMART_SOURCE_1.6.8.zip
(sha256 0cd1d4c07cbd25ead47080794efde39e7d309e4a09e670008908b893e0f9923e, 472 entries), extracted into an empty
folder at 21:00:57Z. The checks then ran from 21:25:33Z to 21:55:59Z, each in its own process, one after the other,
driven by verify168d_driver.sh (this folder: sha256 e2caa6944a6eb1b4f385ef3cf9faf6cb0a28de0322ef684f4b6995bbb6ec1a6a);
in between, the last-good publication check ran (../last_good_publication/). The ZIP holds both editions; each was
checked on its own copy:

  edition    tree (235 files)        lock   install           ruff, format, mypy   unit         integration
  oxylabs    bb0e35e3743d9746...     ok     uv sync --frozen  ok, ok, ok           554 passed   151 passed: 12 files
  scrapedo   1f6fdc3d505fc59e...     ok     uv sync --frozen  ok, ok, ok           554 passed   73 passed: 4 files

  "tree": the edition's 235 files match its EDITION.json and the ZIP's BUILD_MANIFEST.json (count and tree digest),
  its BUILD_INFO.json names the commit 85c29e7, and it holds no env file. Compared afterwards with the commit itself
  (git archive 85c29e7:headless/walmart-azure-headless, 233 files) member by member: in each edition, 231 files equal
  the commit's byte for byte, 2 are the edition's own (.env.example and config/collector.yaml), and the other 2 are
  BUILD_INFO.json and EDITION.json; no file of the commit's collector folder is missing. "lock":
  `uv lock --check --offline`; also `walmart-collector --version` (walmart-azure-headless 1.6.8), `--help` and
  `validate-config` in each edition, through python (the "-m" steps: this workstation's Application Control refuses
  the uv launchers). No test was skipped, failed or errored (junit/). Result: 37 steps, 0 not ok (REPORT.txt).

  The integration files: those the change from 1.6.6 touches. In both editions, the four that read category pages:
  test_category_mapping.py (14), test_scrapedo_walmart.py (19), test_coverage_and_assortment.py (32) and
  test_workers_and_oxylabs.py (8). In the Oxylabs edition also test_lineage_retention.py (8), test_replay.py (9),
  test_operations.py (32), test_followups.py (9), test_publication_safety.py (10), test_deal_fields_policy.py (4),
  test_retained_masking.py (4) and test_yield_baseline.py (2). Each file ran in its own pytest process.
  The other integration files were NOT run here on Windows. A Windows run of the whole integration suite from an
  earlier 1.6.8 candidate's ZIP was stopped by the session's memory protection when the workstation ran low on
  memory (56 passed, none failed, when it stopped; ../../../offline-tests/1.6.8-collector/candidates/7a96218/) and
  was not repeated. The whole suite ran on Linux on the owner's Azure test VM: on the commit itself (unit 554,
  integration 222 in 23 files, one process per file; ../../../owner-azure-test/1.6.8/linux-suite/), and from the two
  edition ZIPs below, whose files equal this ZIP's (unit 554 and integration 222 in each edition;
  ../../../owner-azure-test/1.6.8/qualification/).

The edition ZIPs built beside it, whose 235 files each equal the corresponding files of WALMART_SOURCE_1.6.8.zip:
  WALMART_OXYLABS_SOURCE_1.6.8.zip  sha256 eacf76e90320dbb1e1795913c4e0736d6297ca54645653764fae212eec6093ea
  WALMART_SCRAPEDO_SOURCE_1.6.8.zip sha256 18642dd6fd1de8db6d43eea16bc11e11ffa780cc791a67dd75b4ce316d63db52
The builder made the same three ZIPs twice from the commit, byte for byte.

From 21:00:59Z to 21:01:09Z, right after the extraction, the Azure templates of both editions were built and linted
with the Bicep CLI from the same extraction, without any deployment (BICEP_CHECKS.txt, bicep168d.sh;
logs/<edition>.bicep-build.log, logs/<edition>.bicep-lint.log): exit 0, and the lint reported nothing. The templates
are only read; the build output is 21,691 bytes in each edition, as for 1.6.6.

  REPORT.txt           the verifier's summary
  steps.jsonl          one line per step: command, exit code, seconds, note, end time (UTC)
  logs/<step>.log      each step's full output (no step was run twice: there is no earlier attempt)
  junit/<step>.xml     the JUnit XML of the test steps; the host name is replaced by "(workstation)"
  BICEP_CHECKS.txt     the Bicep build and lint of azure/main.bicep in both editions

The offline tests of 1.6.8 (the diffs and the fail-befores) are ../../../offline-tests/1.6.8-collector/. Release 1.6.6's
record is ../../1.6.6/package/.
