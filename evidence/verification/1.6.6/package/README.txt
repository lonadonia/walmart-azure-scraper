CLEAN-EXTRACTION VERIFICATION of release 1.6.6 (revision cbea802891d4e66b74a0abc33e0af0af74c89708, whose collector
folder is that of 39cc61f61ee694c0659a611310605bee6ed42d6b), both editions.
SYNTHETIC tests: fixture pages, stored authentic pages and a temporary local PostgreSQL. No request reached a provider
or Walmart: every step but the installs ran with HTTP(S) sent to a closed local port (127.0.0.1:9) and without any
provider key, database URL or collector setting of the workstation; the installs used uv's local cache only
(UV_OFFLINE=1).

What ran (2026-11-04, 22:48:48Z to 23:35:44Z, on the workstation): verify166_clean.py (this folder, as it ran:
sha256 4a7c08a726d6f485661fc82ae7fae251a197fc11b5fe757edc5aba92dcd6a1e6) on WALMART_SOURCE_1.6.6.zip
(sha256 d514cc6cff170e61416fad9a6a79a076191f6b2882adf47c336769b0e534756f, 462 entries), extracted into an empty
folder. The ZIP holds both editions; each was checked on its own copy:

  edition    tree (230 files)        lock     install        ruff, format, mypy   unit         integration
  oxylabs    938045b09316f258...     ok       uv sync --frozen  ok, ok, ok        533 passed   202 passed (1327.5 s)
  scrapedo   d7d43d3e3ae0f1a2...     ok       uv sync --frozen  ok, ok, ok        533 passed   202 passed (1330.3 s)

  "tree": the edition's 230 files match its EDITION.json and the ZIP's BUILD_MANIFEST.json (count and tree digest),
  its BUILD_INFO.json names the commit cbea802, and it holds no env file. Compared afterwards with the commit
  itself: in each edition, 226 files equal the collector folder's files at cbea802 byte for byte, 2 are the
  edition's own (.env.example and config/collector.yaml), and the other 2 are BUILD_INFO.json and EDITION.json; no
  file of the commit's collector folder is missing. "lock": `uv lock --check --offline`; also
  `walmart-collector --version`, `--help` and `validate-config` in each edition. No test was skipped, failed or
  errored (junit/). The integration suite has 202 tests, 2 more than 1.6.5's: the two new tests of
  tests/integration/test_operations.py (../../../offline-tests/1.6.6-collector/), which passed in both editions.
  Result: 23 steps, 0 not ok (REPORT.txt). The edition ZIPs built beside it, whose 230 files each equal the
  corresponding files of WALMART_SOURCE_1.6.6.zip:
  WALMART_OXYLABS_SOURCE_1.6.6.zip  sha256 0859a2f693527bab073252edf941928bb4f118ea4a63d581078d96ddd2324e22
  WALMART_SCRAPEDO_SOURCE_1.6.6.zip sha256 d96ef6409c0094b40094b605687c8b72efdfc2414568a020965fc31a5c0e68e2

From 23:33:56Z to 23:34:08Z, while the Scrape.do edition's integration step was still running, the Azure templates
of both editions were built and linted with the Bicep CLI from the same extraction, without any deployment (BICEP_CHECKS.txt;
logs/<edition>.bicep-build.log, logs/<edition>.bicep-lint.log): exit 0, and the lint reported nothing. The templates
are only read; the build output is 21,691 bytes in both editions, as for 1.6.5.

  REPORT.txt           the verifier's summary
  steps.jsonl          one line per step: command, exit code, seconds, note, end time (UTC)
  logs/<step>.log      each step's full output (no step was run twice: there is no earlier attempt)
  junit/<step>.xml     the JUnit XML of the four test steps; the host name is replaced by "(workstation)"
  BICEP_CHECKS.txt     the Bicep build and lint of azure/main.bicep in both editions

The last-good publication check of 1.6.6 is ../last_good_publication/. The live canary of 1.6.6, L12 (detail on), is
../../../live/1.6.x/runs/L12_01M6MC7YE4PBXV88G3PJ5ENW4B/. Release 1.6.5's record is ../../1.6.5/package/.
