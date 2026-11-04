LAST GOOD PUBLICATION, release 1.6.1 (W6). SYNTHETIC: fixture pages and a temporary local PostgreSQL; no request
reached a provider or Walmart.

What ran (2026-11-03, 18:38:56Z to 18:41:54Z): a clean extraction of WALMART_OXYLABS_SOURCE_1.6.1.zip (sha256
805f6921..., revision 1780349e522d771a3642fe88bfb7b542044ec844), installed with `uv sync --frozen`, its own frozen
tests/integration/test_publication_safety.py and tests/integration/test_publish.py, and one added file,
test_last_good_corrupt_evidence.py (this folder), copied beside them. Result: 19 passed (pytest_run.log).

A first attempt (pytest_first_attempt_invalid_all_skipped.log) is NOT evidence: it forced the pure-Python PostgreSQL
driver, which needs a library this workstation does not have, so the database fixture skipped all 19 tests. It
was rerun without that setting.

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

Found while doing this, and not changed in 1.6.1: when the AUTOMATIC publication is refused, the run exits 0
(CLI.md: 0 is "the run validated (or published)") and the refusal is a WARN line, PUBLICATION_REFUSED. The
published dataset is protected, but an operator who alerts only on non-zero exits and ERROR lines (the suggestions
in OPERATIONS.md) would not see it. Until a later release exits non-zero there, add an alert on PUBLICATION_REFUSED
(the Log Analytics query in OPERATIONS.md already selects it). A manual `publish` that is refused exits 6.
