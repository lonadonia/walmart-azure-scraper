LAST GOOD PUBLICATION, release 1.6.5 (W6). SYNTHETIC: fixture pages and a temporary local PostgreSQL; no request
reached a provider or Walmart.

What ran (2026-11-04, 15:06:30Z to 15:09:51Z, on the workstation): a clean extraction of
WALMART_OXYLABS_SOURCE_1.6.5.zip (sha256 edd60bb8435e7abd8293d7c2b5b76eaaaff0051d18c053d715afc2533070ba6b,
revision 67d216eb8ee2ec839a437b0b5bf2d594324b6982), installed with `uv sync --frozen` (CPython 3.12.10), its own
frozen tests/integration/test_publication_safety.py and tests/integration/test_publish.py, and one added file,
test_last_good_corrupt_evidence.py (this folder, the same file as 1.6.4's: sha256
5da68a0345de86288d976d6b72243478929aa3f638d014b452ab4012a83b9675), copied beside them. Result: 19 passed in
184.96 s, exit 0 (pytest_run.log; pytest_run.junit.xml, whose host name is replaced by "(workstation)").

The same check ran on release 1.6.1 on 2026-11-03 and on release 1.6.4 on 2026-11-04 with the same result
(../../1.6.1/last_good_publication/, ../../1.6.4/last_good_publication/): every case below ends with the same status,
stop code and exit code, and leaves the published state as it did then; only the run identifiers and hashes of the
new runs differ. Releases 1.6.2 to 1.6.5 did not change the publication step (publishing/publish.py,
publishing/exports.py); release 1.6.3 changed one evidence writer (publishing/supporting_log.py); release 1.6.5
changed only the independent source check (checks/source_check.py), which the automated canary and validate-export
apply.

Each JSON file below is written by a test. "before" and "after" are the same snapshot of the published state: the
publication pointer and its version, the number of publication rows, latest.json, the manifest it names and that
manifest's products.json (bytes and hashes), and the first run's observations and records. "unchanged": true means
the second run left all of it as it was.

| Fault (file)                                         | Second run                        | Published state |
|------------------------------------------------------|-----------------------------------|-----------------|
| incomplete (publication_refused_incomplete)          | rejected, CREDITS_EXHAUSTED, exit 4 | unchanged     |
| thin (publication_refused_thin)                      | rejected, exit 6                  | unchanged       |
| empty (publication_refused_empty)                    | rejected, exit 6                  | unchanged       |
| wrong store (publication_refused_wrong_store)        | rejected, STORE_NOT_VERIFIED, exit 7 (CLI.md: the store is then held) | unchanged |
| blocked by the site (publication_refused_site_refusal) | rejected, SITE_REFUSAL, exit 5 (CLI.md: the store is then held) | unchanged |
| product pages stopped (publication_refused_failed_detail) | rejected, exit 6: 3 consecutive product pages refused (a challenge) | unchanged |
| mixed lineage (publication_refused_mixed_lineage)    | publish refused, exit 6           | unchanged       |
| corrupt evidence: one byte of products.json changed  | validated, not published, exit 0  | unchanged       |
| corrupt evidence: products.json truncated            | validated, not published, exit 0  | unchanged       |
| corrupt evidence: manifest.json changed              | validated, not published, exit 0  | unchanged       |
| run interrupted, then resumed (publication_interrupted_run_then_resumed) | exit 75; a manual publish of the interrupted run refused (exit 6); the resume completes it (exit 0) | unchanged until the resume publishes the completed run |
| publication interrupted, then retried (publication_interrupted_then_retried) | the retry publishes in one step (exit 0) | the old dataset until the retry |
| control: one product page refused of many (publication_allowed_one_failed_detail) | published | moves, as it should |

The three corrupt-evidence cases: the run's exports are written and verified, the run validates, and then one file
is changed on disk before the automatic publication. The publication's own integrity check (verify_manifest,
called by publish_run before the pointer moves) finds "products.json hash mismatch" or "manifest hash mismatch",
the publication is refused, and the run stays "validated", never "published".

Still true in 1.6.5 (found on 2026-11-03 and not changed): when the AUTOMATIC publication is refused, the run exits
0 (CLI.md: 0 is "the run validated (or published)") and the refusal is a WARN line, PUBLICATION_REFUSED. The
published dataset is protected, but an operator who alerts only on non-zero exits and ERROR lines (the suggestions
in OPERATIONS.md) would not see it. Add an alert on PUBLICATION_REFUSED (the Log Analytics query in OPERATIONS.md
already selects it). A manual `publish` that is refused exits 6.
