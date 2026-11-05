LAST GOOD PUBLICATION, release 1.6.6 (W6). SYNTHETIC: fixture pages and a temporary local PostgreSQL; no request
reached a provider or Walmart.

What ran (2026-11-04, 23:40:08Z to 23:43:12Z, on the workstation): a clean extraction of
WALMART_OXYLABS_SOURCE_1.6.6.zip (sha256 0859a2f693527bab073252edf941928bb4f118ea4a63d581078d96ddd2324e22,
revision cbea802891d4e66b74a0abc33e0af0af74c89708, whose collector folder is that of 39cc61f), installed with
`uv sync --frozen` from uv's local cache (UV_OFFLINE=1; CPython 3.12.10), its own frozen
tests/integration/test_publication_safety.py and tests/integration/test_publish.py, and one added file,
test_last_good_corrupt_evidence.py (this folder, the same file as 1.6.4's and 1.6.5's: sha256
5da68a0345de86288d976d6b72243478929aa3f638d014b452ab4012a83b9675), copied beside them. Result: 19 passed in
168.66 s, exit 0 (pytest_run.log; pytest_run.junit.xml, whose host name is replaced by "(workstation)").
lastgood166.sh is the script as it ran.

A first attempt (23:36:05Z to 23:36:44Z, pytest_run.attempt1.log) ran no test: without UV_OFFLINE, `uv sync`
tried to fetch the build backend (hatchling) from PyPI, the closed local proxy (127.0.0.1:9) refused the
connection, and the run stopped with exit 2. The second attempt added UV_OFFLINE=1, as the clean verifier sets
(../package/verify166_clean.py); nothing else changed.

The same check ran on releases 1.6.1, 1.6.4 and 1.6.5 (../../1.6.1/last_good_publication/,
../../1.6.4/last_good_publication/, ../../1.6.5/last_good_publication/). Compared with 1.6.5's files, ten cases
end with the same status, stop code and exit code and leave the published state as they did then. The three
corrupt-evidence cases now exit 6 instead of 0: that is the 1.6.6 change. Only the run identifiers and the hashes
of the new runs differ otherwise.

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
| corrupt evidence: one byte of products.json changed  | validated, not published, exit 6 (1.6.5: exit 0) | unchanged |
| corrupt evidence: products.json truncated            | validated, not published, exit 6 (1.6.5: exit 0) | unchanged |
| corrupt evidence: manifest.json changed              | validated, not published, exit 6 (1.6.5: exit 0) | unchanged |
| run interrupted, then resumed (publication_interrupted_run_then_resumed) | exit 75; a manual publish of the interrupted run refused (exit 6); the resume completes it (exit 0) | unchanged until the resume publishes the completed run |
| publication interrupted, then retried (publication_interrupted_then_retried) | the retry publishes in one step (exit 0) | the old dataset until the retry |
| control: one product page refused of many (publication_allowed_one_failed_detail) | published | moves, as it should |

The three corrupt-evidence cases: the run's exports are written and verified, the run validates, and then one file
is changed on disk before the automatic publication. The publication's own integrity check (verify_manifest,
called by publish_run before the pointer moves) finds "products.json hash mismatch" or "manifest hash mismatch",
the publication is refused, and the run stays "validated", never "published".

Changed in 1.6.6: when the AUTOMATIC publication is refused, the run exits 6, as a refused manual `publish` does,
and PUBLICATION_REFUSED is an ERROR line and an ERROR event recorded on the run; Azure's retry of a scheduled
execution whose run is already done also exits 6. Up to 1.6.5 the run exited 0 with a WARN line, and an operator
who alerted only on non-zero exits and ERROR lines (the suggestions in OPERATIONS.md) would not have seen it. This
check records the exit code and the published state. It does not read the log: test_last_good_corrupt_evidence.py
records the exit code without asserting it, which is why the same file passed on 1.6.5 (exit 0) and on 1.6.6
(exit 6). The ERROR line, the event and the retry are asserted by the two new tests of
tests/integration/test_operations.py (../../../offline-tests/1.6.6-collector/), which fail on 1.6.5's code and
pass on 1.6.6's, and which ran in the clean verification of both editions (../package/).
