LAST GOOD PUBLICATION, release 1.6.8 (W6). SYNTHETIC: fixture pages and a temporary local PostgreSQL; no request
reached a provider or Walmart.

What ran (2026-11-05, 21:22:13Z to 21:25:33Z, on the workstation): a clean extraction of
WALMART_OXYLABS_SOURCE_1.6.8.zip (sha256 eacf76e90320dbb1e1795913c4e0736d6297ca54645653764fae212eec6093ea,
commit 85c29e7b2404500299056973f50c84b84e187a5a, which its BUILD_INFO.json names), installed with
`uv sync --frozen` from uv's local cache (UV_OFFLINE=1; CPython 3.12.10), its own frozen
tests/integration/test_publication_safety.py and tests/integration/test_publish.py, and one added file,
test_last_good_corrupt_evidence.py (this folder, the same file as 1.6.4's, 1.6.5's and 1.6.6's: sha256
5da68a0345de86288d976d6b72243478929aa3f638d014b452ab4012a83b9675), copied beside them. Result: 19 passed in
182.94 s, exit 0 (pytest_run.log; pytest_run.junit.xml, whose host name is replaced by "(workstation)").
lastgood168d.sh is the script as it ran, in one attempt (its usage line still names lastgood166.sh, the script it
was made from).

The same check ran on releases 1.6.1, 1.6.4, 1.6.5 and 1.6.6 (../../1.6.6/last_good_publication/ and the folders it
names). Compared with 1.6.6's files, all thirteen cases end with the same status, stop code and exit code and leave
the published state as they did then; only the run identifiers and what derives from them (the manifest keys) differ.
Releases 1.6.7 and 1.6.8 changed nothing under src/walmart_headless/publishing/ (`git diff 39cc61f 85c29e7` is empty
there); their changes are in collection/ and the version strings.

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
| corrupt evidence: one byte of products.json changed  | validated, not published, exit 6  | unchanged       |
| corrupt evidence: products.json truncated            | validated, not published, exit 6  | unchanged       |
| corrupt evidence: manifest.json changed              | validated, not published, exit 6  | unchanged       |
| run interrupted, then resumed (publication_interrupted_run_then_resumed) | exit 75; a manual publish of the interrupted run refused (exit 6); the resume completes it (exit 0) | unchanged until the resume publishes the completed run |
| publication interrupted, then retried (publication_interrupted_then_retried) | the retry publishes in one step (exit 0) | the old dataset until the retry |
| control: one product page refused of many (publication_allowed_one_failed_detail) | published | moves, as it should |

The three corrupt-evidence cases: the run's exports are written and verified, the run validates, and then one file
is changed on disk before the automatic publication. The publication's own integrity check (verify_manifest,
called by publish_run before the pointer moves) finds "products.json hash mismatch" or "manifest hash mismatch",
the publication is refused, and the run stays "validated", never "published".

This check records the exit code and the published state. It does not read the log. The refused automatic
publication as an ERROR line and an ERROR event, exit 6 on the original attempt and on Azure's retry, is asserted by
the two tests of tests/integration/test_operations.py added in 1.6.6, which ran in the clean verification of the
Oxylabs edition (../package/: test_operations.py, 32 passed) and in the whole Linux suites on the owner's VM
(../../../owner-azure-test/1.6.8/linux-suite/ and qualification/), and by the operator drill there
(qualification/logs/<edition>.drill.jsonl, both editions): the run's automatic publication refused,
PUBLICATION_REFUSED at ERROR, exit 6; a manual publish of the same run refused again, exit 6; the last-good
pointer unchanged.
