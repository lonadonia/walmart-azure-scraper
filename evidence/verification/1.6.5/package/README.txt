CLEAN-EXTRACTION VERIFICATION of release 1.6.5 (revision 67d216eb8ee2ec839a437b0b5bf2d594324b6982), both editions.
SYNTHETIC tests: fixture pages, stored authentic pages and a temporary local PostgreSQL. No request reached a provider
or Walmart: every step but the installs ran with HTTP(S) sent to a closed local port (127.0.0.1:9) and without any
provider key, database URL or collector setting of the workstation.

What ran (2026-11-04, 14:16:48Z to 15:04:59Z, on the workstation): verify165_clean.py (this folder, as it ran:
sha256 7209c96e708d4108cbd061bfda4febb60d6c8ca1615dd477a0e030d28bc8f522) on WALMART_SOURCE_1.6.5.zip
(sha256 1c032d87a2cc95a2c9da7b8e9d0bd29666ffcd23f3c6cd435130ce45795c2c90, 462 entries), extracted into an empty
folder. The ZIP holds both editions; each was checked on its own copy:

  edition    tree (230 files)        lock     install        ruff, format, mypy   unit         integration
  oxylabs    877f36afbf465317...     ok       uv sync --frozen  ok, ok, ok        533 passed   200 passed (1362.9 s)
  scrapedo   b771dcb5e876c80f...     ok       uv sync --frozen  ok, ok, ok        533 passed   200 passed (1353.9 s)

  "tree": the edition's 230 files match its EDITION.json and the ZIP's BUILD_MANIFEST.json (count and tree digest),
  its BUILD_INFO.json names the 1.6.5 commit, and it holds no env file. Compared afterwards with the commit itself:
  in each edition, 226 files equal the collector folder's files at 67d216e byte for byte, 2 are the edition's own
  (.env.example and config/collector.yaml), and the other 2 are BUILD_INFO.json and EDITION.json; no file of the
  commit's collector folder is missing. "lock": `uv lock --check --offline`; also `walmart-collector --version`,
  `--help` and `validate-config` in each edition. No test was skipped, failed or errored (junit/). Result: 23 steps,
  0 not ok (REPORT.txt). The edition ZIPs inside it:
  WALMART_OXYLABS_SOURCE_1.6.5.zip  sha256 edd60bb8435e7abd8293d7c2b5b76eaaaff0051d18c053d715afc2533070ba6b
  WALMART_SCRAPEDO_SOURCE_1.6.5.zip sha256 3551ee0ece09d3609a2504d4f60c3adef714eb424d79185587f7ef574bb25e94

Afterwards (15:09:33Z to 15:09:45Z), the Azure templates of both editions were built and linted with the Bicep CLI,
without any deployment (BICEP_CHECKS.txt; logs/<edition>.bicep-build.log, logs/<edition>.bicep-lint.log): exit 0,
and the lint reported nothing.

  REPORT.txt           the verifier's summary
  steps.jsonl          one line per step: command, exit code, seconds, note, end time (UTC)
  logs/<step>.log      each step's full output (no step was run twice: there is no earlier attempt)
  junit/<step>.xml     the JUnit XML of the four test steps; the host name is replaced by "(workstation)"
  BICEP_CHECKS.txt     the Bicep build and lint of azure/main.bicep in both editions

The last-good publication check of 1.6.5 is ../last_good_publication/; the re-validation of the live L10 and L8
exports with the 1.6.5 source check is ../source_check_l10/ and the live canary L11b is
../../../live/1.6.x/runs/L11b_01M6KFRFEX31W014SW9ZTT4Y54/. Release 1.5.2's own clean-extraction record is the top
of ../../ (evidence/verification/).
