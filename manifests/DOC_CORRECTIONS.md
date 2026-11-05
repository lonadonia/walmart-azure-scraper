# Corrections made for this publication

Three records follow: this publication's (tag `review-1.6.6-20261105`), then that of the 1.6.5 publication (tag `review-1.6.5-20261104`) and that of the 1.5.2 publication (tag `review-1.5.2-20261103`), each kept as it was published. [`DOC_CORRECTIONS.json`](DOC_CORRECTIONS.json) gives the exact texts of all three.

## This publication: release 1.6.6 (tag `review-1.6.6-20261105`)

The client's review of 1.6.5 found statements of that publication that were not accurate. Its files stay at its tag. This publication's documents replace them, and section 1 lists each such statement with what is true. Section 2 gives the limitations that 1.6.5 stated truly and that 1.6.6 corrects, section 3 the test counts of 1.6.5 counted again, section 4 the errors found in files and a commit message that are not edited, section 5 the files of 1.6.5 replaced with their text kept, and section 6 the corrections made to this publication's own records before its review tag was set.

`source/`, `classic-probe/`, `classic-probe-1.7.0/` and `classic-probe-1.7.1/` are the delivered archives' files, unchanged ([`check_frozen_trees.py`](check_frozen_trees.py)). Historical evidence is not rewritten either: its only changes are the redactions in [`REDACTIONS.csv`](REDACTIONS.csv). [`FILE_MAP.csv`](FILE_MAP.csv) gives every file's origin and its original and published SHA-256.

### 1. Statements of the 1.6.5 publication that were not accurate (at the tag `review-1.6.5-20261104`)

| Where | What it said | What is true | Corrected in |
|---|---|---|---|
| `README.md`, lines 16 to 18 | Every point of the client's two latest reviews is corrected, with its tests and evidence [...] and the Classic findings C1 to C5 (probe 1.7.0, live mode disabled) | Probe 1.7.0 corrected C1, C3 and C5. It corrected C2 and C4 only in part (C2: a request's worker was killed and reaped at its allowance and its body bounded, but the work after an answer was not bound by the session's deadline: a supervisor's recovery ran after the hard end without a limit, the ledger writes after an answer waited the default 30 s whatever time was left, and the export's recovery of captures had no limit. C4: a crash could still lose a paid answer: the transport deleted the worker's synced body before the capture store had kept it; the campaign's JSON writes were not synced; and a body cut at its deadline was discarded with no record.) Seven reproduction tests fail on 1.7.0's code and pass on probe 1.7.1, which completes both. | README.md, Status |
| `README.md`, line 39 | The shared offline Classic probe 1.7.0: the client's findings C1 to C5 corrected | C2 and C4 were corrected only in part (above). | README.md, Contents: 1.7.0 is "unchanged; superseded by 1.7.1" |
| `CHANGELOG.md`, line 35 | the Classic findings C1 to C5 are corrected offline (probe 1.7.0). | C2 and C4 were corrected only in part (above). | CHANGELOG.md: the 1.6.6 entry, and a note added to this line of the 1.6.5 entry |
| `review/DELIVERY_INDEX.md`, line 8 | Every point of the client's two latest reviews is corrected and verified | As for README.md, above: C2 and C4 were corrected only in part. | review/DELIVERY_INDEX.md, "What this is" |
| `review/DELIVERY_INDEX.md`, line 27 | C1 to C5 in the probe 1.7.0 | C2 and C4 were corrected only in part (above). | review/DELIVERY_INDEX.md, "Start here" |
| `review/TECHNICAL_REPORT.md`, line 39 | Probe 1.7.0: C1 to C5. | C2 and C4 were corrected only in part (above). | review/TECHNICAL_REPORT.md, sections 2 and 8 |
| `review/CORRECTION_MAP.md`, line 148 | C1 to C5 are corrected in the shared probe 1.7.0, offline, with live mode disabled | C2 and C4 were corrected only in part (above). | review/CORRECTION_MAP.md, Classic (W7) |
| `review/MILESTONES.md`, line 19 | the shared Classic probe 1.7.0 corrects C1 to C5 offline | C2 and C4 were corrected only in part (above). | review/MILESTONES.md: the row now says so, and later rows give probe 1.7.1 |
| `review/REQUIREMENT_MATRIX.md`, line 48 | C1 to C5 are corrected in probe 1.7.0 with live mode disabled. | C2 and C4 were corrected only in part (above). | review/REQUIREMENT_MATRIX.md, W7 |
| `review/REQUIREMENT_MATRIX.md`, line 56 | PASS_OFFLINE \| One process per request, killed and reaped at its allowance. Bounded bodies, headers and decompression. A session supervisor. | 1.7.0 corrected it in part: a request's worker was killed and reaped at its allowance and its body bounded, but the work after an answer was not bound by the session's deadline: a supervisor's recovery ran after the hard end without a limit, the ledger writes after an answer waited the default 30 s whatever time was left, and the export's recovery of captures had no limit. The state PASS_OFFLINE now rests on probe 1.7.1. | review/REQUIREMENT_MATRIX.md, C2 |
| `review/REQUIREMENT_MATRIX.md`, line 58 | PASS_OFFLINE \| Each answer is written atomically and indexed before the next paid step, and recovered after a crash. | 1.7.0 corrected it in part: a crash could still lose a paid answer: the transport deleted the worker's synced body before the capture store had kept it; the campaign's JSON writes were not synced; and a body cut at its deadline was discarded with no record. The state PASS_OFFLINE now rests on probe 1.7.1. | review/REQUIREMENT_MATRIX.md, C4 |
| `review/CLASSIC_PROBE_CORRECTIONS.md`, line 1 | Classic probe: the corrections C1 to C5 (shared probe 1.7.0) | C2 and C4 were corrected only in part (above). | review/CLASSIC_PROBE_CORRECTIONS.md, written again for probe 1.7.1 |
| `review/CLASSIC_PROBE_CORRECTIONS.md`, line 18 | 1.6.0 with C1 to C5 corrected. It is authoritative from this delivery. | C2 and C4 were corrected only in part (above). Probe 1.7.1 is authoritative from this delivery. | review/CLASSIC_PROBE_CORRECTIONS.md, the versions table |
| `manifests/PUBLICATION.json`, the Classic probe's "corrections" | the client's findings C1 to C5 (review/CLASSIC_PROBE_CORRECTIONS.md) | C2 and C4 were corrected only in part (above). | manifests/PUBLICATION.json of this publication, whose probe is 1.7.1 |
| `review/ACCEPTANCE_MATRIX.csv`, N8-01, note_1_6_x | C1 to C5 corrected offline | C2 and C4 were corrected only in part (above). | review/ACCEPTANCE_MATRIX.csv, N8-01: the 1.6.6 columns (state_1_6_6, note_1_6_6) |
| `review/ACCEPTANCE_MATRIX.csv`, N10-03, state_1_6_5 | PASS_OFFLINE | Not for monitoring. The operating documentation's alert advice (any ERROR line, any non-zero exit) did not catch a refused automatic publication, which 1.6.5 logged as a WARN line with exit 0. The 1.6.5 documents disclosed the gap and advised an extra alert, but the row still passed. Release 1.6.6 makes the refusal an ERROR with exit 6, also on Azure's retry, and its OPERATIONS.md names the case. | review/ACCEPTANCE_MATRIX.csv, N10-03: the 1.6.6 columns (state_1_6_6, note_1_6_6) |
| `review/ACCEPTANCE_MATRIX.csv`, N1A-02, note_1_6_x | every 1.6.x run passed its canary (store, Pickup, seller, parsing) before collecting | Not every run: L11 recorded no product, because its listing was rejected for its identity before a canary page. Every 1.6.x run that recorded products passed its canary. | review/ACCEPTANCE_MATRIX.csv, N1A-02: the 1.6.6 columns (state_1_6_6, note_1_6_6) |

The basis of the Classic rows: evidence/offline-tests/1.7.1-classic-probe/REPRODUCTION_ON_1.7.0.log and REPRODUCTION_ON_1.7.1.log; classic-probe-1.7.1/offline_results/16b_reproductions_on_1.7.0_source.txt and 17_reproductions_on_1.7.1.txt. Of the other points that the 1.6.5 publication called corrected (the four deal fields, UPC and size provenance, the sponsored and variant decisions, coverage and partitions, retention and recovery) stand as 1.6.5 corrected them: this delivery does not change them.

### 2. Limitations that 1.6.5 stated truly and that 1.6.6 corrects

| Where | What it said | Now |
|---|---|---|
| `review/DELIVERY_INDEX.md`, lines 92 to 93 (known limitation 10) | 10. A refused automatic publication exits 0 (found on 2026-11-03, not changed): alert on `PUBLICATION_REFUSED` (`RECOVERY_AND_OPERATIONS.md`, section 3). | Release 1.6.6 corrects it: a refused automatic publication is an ERROR line and event and exits 6, also on Azure's retry. DELIVERY_INDEX.md says so after its limitations. |
| `review/RECOVERY_AND_OPERATIONS.md`, lines 108 to 112 (section 3) | Found on 2026-11-03 and not changed. When the automatic publication is refused (the corrupt-evidence cases), the run exits 0. CLI.md defines 0 as "the run validated (or published)", and the refusal is a WARN line, `PUBLICATION_REFUSED`. The published ... | True when written, the query included (source/walmart-oxylabs-1.6.5/docs/OPERATIONS.md, line 305, at the tag review-1.6.5-20261104). Release 1.6.6 corrects the limitation; RECOVERY_AND_OPERATIONS.md, section 3, describes it. |
| `evidence/verification/1.6.5/last_good_publication/README.txt`, line 46 | Still true in 1.6.5 (found on 2026-11-03 and not changed): when the AUTOMATIC publication is refused, the run exits | True of 1.6.5. The file is 1.6.5's evidence and is carried unchanged; the same check on 1.6.6 is evidence/verification/1.6.6/last_good_publication/, where the three corrupt-evidence cases exit 6. |

### 3. The test counts of the 1.6.5 publication, counted again

Each test count that the 1.6.5 documents state was counted again from its JUnit file or log, as published at the tag `review-1.6.5-20261104`. Each is accurate. (The skipped probe tests are the vendored-file checks, which need the collectors' sources beside the probe.)

| Statement | Evidence | Counted |
|---|---|---|
| 1.6.5, oxylabs edition, from the clean extraction: 533 unit tests passed | `evidence/verification/1.6.5/package/junit/oxylabs.unit.xml` | tests 533, failures 0, errors 0, skipped 0 |
| 1.6.5, oxylabs edition, from the clean extraction: 200 integration tests passed | `evidence/verification/1.6.5/package/junit/oxylabs.integration.xml` | tests 200, failures 0, errors 0, skipped 0 |
| 1.6.5, scrapedo edition, from the clean extraction: 533 unit tests passed | `evidence/verification/1.6.5/package/junit/scrapedo.unit.xml` | tests 533, failures 0, errors 0, skipped 0 |
| 1.6.5, scrapedo edition, from the clean extraction: 200 integration tests passed | `evidence/verification/1.6.5/package/junit/scrapedo.integration.xml` | tests 200, failures 0, errors 0, skipped 0 |
| the last-good publication on 1.6.5: 19 passed | `evidence/verification/1.6.5/last_good_publication/pytest_run.junit.xml` | tests 19, failures 0, errors 0, skipped 0 |
| probe 1.7.0 from its clean export: 158 tests, 156 passed, 2 skipped | `classic-probe-1.7.0/offline_results/junit_standalone.xml` | tests 158, failures 0, errors 0, skipped 2 |
| probe 1.7.0 in the development tree: 157 passed, 1 skipped | `evidence/offline-tests/1.7.0-classic-probe/DEV_TREE_TESTS_1.7.0.log` | passed 157, skipped 1 |
| the 8 tests of 1.6.5's new test file on 1.6.4: 6 failed and 2 passed | `evidence/offline-tests/1.6.5-collector/REGRESSION_TESTS_ON_1.6.4.junit.xml` | tests 8, failures 6, errors 0, skipped 0 |
| the unit suite on the 1.6.5 commit: 533 passed | `evidence/offline-tests/1.6.5-collector/UNIT_1.6.5.log` | passed 533 |

### 4. Errata: files and a commit message that are not edited

| Where | What it says | What is true | Basis |
|---|---|---|---|
| `source/README.md`, line 7 | none: release 1.6.6 changes only how a refused automatic publication is reported [...] The live runs L1 to L10 ran releases 1.6.0 to 1.6.4 | Written when the source ZIP was built (2026-11-04T22:38:53Z), before release 1.6.6's live canary L12 ran (22:52:55Z to 22:59:46Z, detail on: 40 fresh valid products, a rejected pilot). The cell also leaves out release 1.6.5's two canaries, L11 and L11b. The rest of the cell is true. | data/RUN_SUMMARY.json; evidence/live/1.6.x/campaign/commands.csv |
| `classic-probe-1.7.0/README_FIRST.md`, lines 6 to 7 | Version 1.7.0 corrects the five findings of the client's second review (C1 to C5) in the shared layer | C1, C3 and C5 were corrected in 1.7.0; C2 and C4 only in part, and probe 1.7.1 completes them. The same file of classic-probe-1.7.1/ says so. | evidence/offline-tests/1.7.1-classic-probe/REPRODUCTION_ON_1.7.0.log and REPRODUCTION_ON_1.7.1.log; classic-probe-1.7.1/offline_results/16b_reproductions_on_1.7.0_source.txt and 17_reproductions_on_1.7.1.txt |
| `classic-probe-1.7.0/oxylabs-classic-probe/README.md`, line 11 | Version 1.7.0 corrects the five findings of the client's second review (C1 to C5) | C1, C3 and C5 were corrected in 1.7.0; C2 and C4 only in part, and probe 1.7.1 completes them. The same file of classic-probe-1.7.1/ says so. | evidence/offline-tests/1.7.1-classic-probe/REPRODUCTION_ON_1.7.0.log and REPRODUCTION_ON_1.7.1.log; classic-probe-1.7.1/offline_results/16b_reproductions_on_1.7.0_source.txt and 17_reproductions_on_1.7.1.txt |
| `classic-probe-1.7.0/oxylabs-classic-probe/CLASSIC_TEST_PLAN.md`, line 5 | Release 1.7.0 corrects the transport, the ledger's timing, the session deadline, the keeping of answers and the backoff (the client's findings C1 to C5) | C1, C3 and C5 were corrected in 1.7.0; C2 and C4 only in part, and probe 1.7.1 completes them. The same file of classic-probe-1.7.1/ says so. | evidence/offline-tests/1.7.1-classic-probe/REPRODUCTION_ON_1.7.0.log and REPRODUCTION_ON_1.7.1.log; classic-probe-1.7.1/offline_results/16b_reproductions_on_1.7.0_source.txt and 17_reproductions_on_1.7.1.txt |
| `d2ce076f23ac2787b4b38269de6f8ba8942f520c`, its commit message, lines 5 to 6 | classic-probe-1.7.0/: the shared Classic probe 1.7.0 (findings C1 to C5 corrected, live mode disabled) | C1, C3 and C5 were corrected in 1.7.0; C2 and C4 only in part, and probe 1.7.1 completes them. The commit message of this publication says so. | evidence/offline-tests/1.7.1-classic-probe/REPRODUCTION_ON_1.7.0.log and REPRODUCTION_ON_1.7.1.log; classic-probe-1.7.1/offline_results/16b_reproductions_on_1.7.0_source.txt and 17_reproductions_on_1.7.1.txt |

### 5. Files of the 1.6.5 publication replaced, with their text kept

| File | Change |
|---|---|
| `CHANGELOG.md` | the 1.6.6 entry added; in the 1.6.5 entry, a note added to the line on the Classic findings says that C2 and C4 were corrected only in part. The 1.6.5 entry and those before it are otherwise unchanged |
| `data/README.md` | in its first part, the paragraph on releases 1.6.5 and 1.6.6, L12's place, the fifteen 1.6.x runs and the current coverage tables (1.6.6/w4/); the 1.5.x part is unchanged |
| `evidence/README.md` | in its first part, the rows for 1.6.6 and probe 1.7.1 and the 1.6.6 verification and reconciliation folders; the 1.5.2 part is unchanged |
| `review/ACCEPTANCE_MATRIX.csv` | four columns added (state_1_6_6, evidence_1_6_6, revision_1_6_6, note_1_6_6); the sixteen columns of the 1.5.2 matrix and the four of 1.6.5 are unchanged in all 206 rows. Their paths name files of those publications, which are at their tags |
| `data/RUN_SUMMARY.json` | L12 added, and "about" names the final release 1.6.6; the 23 entries of the 1.6.5 publication, "campaigns" and "files_delivered" are unchanged |
| `manifests/DOC_CORRECTIONS.md, DOC_CORRECTIONS.json` | this publication's part added first; the records of the 1.6.5 and 1.5.2 publications kept below, as published |

The other files of the 1.6.5 publication are either carried unchanged (its evidence, its data folders, `classic-probe/`, `classic-probe-1.7.0/`, `walkthrough/`, `.gitattributes`, `.gitignore`, `review/LINKED_EXAMPLES.csv`, `review/THIRD_PARTY_LICENSES.csv`, `manifests/SOURCE_AND_RUN_MANIFEST.json` and `manifests/check_data.py`, which checks every 1.6.x run that RUN_SUMMARY.json lists, L12 included) or replaced by this delivery's file of the same name (`README.md`, `source/`, the review documents and the manifests: `check_frozen_trees.py`, `PUBLICATION.json`, `FILE_MAP.csv`, `REDACTIONS.csv`, `EXCLUDED.csv` and `SHA256SUMS.txt`). Each replaced file's earlier version is at the tag `review-1.6.5-20261104`, and [`FILE_MAP.csv`](FILE_MAP.csv) names it.

### 6. Corrections made to this publication's own records before its review tag was set

| What | Correction |
|---|---|
| review/MILESTONES.md: the probe 1.7.0 row | The row carried from 1.6.5 said that probe 1.7.0 corrected C1 to C5. Before publication it was corrected to say that C2 and C4 were corrected only in part, and completed in 1.7.1. |
| review/RECOVERY_AND_OPERATIONS.md: the corrupt-evidence row of the last-good table | A draft credited the last-good check with showing PUBLICATION_REFUSED at ERROR. That check records the exit code and the published state only; the ERROR level is asserted by 1.6.6's two new tests (tests/integration/test_operations.py). The row now says so. |
| review/DELIVERY_INDEX.md: L12's export | A draft said that L12's export carries L10's rows. Compared row by row, its 10,301 retained rows are L10's except the products that L11b (35) and L12 (40) read again; against L11b's retained export, only L12's 40 products differ. |
| classic-probe-1.7.1/offline_results/: the reproduction on 1.7.0 | The first run of the probe's results tool counted the reproduction step on 1.7.0 as expected from its exit code alone; its install had failed, because that extraction lacked a file. The tool now builds the whole tree and checks each step's output as well. Only the rerun (7 failed on 1.7.0, 7 passed on 1.7.1) is delivered (TECHNICAL_REPORT.md, section 8). |
| evidence/verification/1.6.6/package/BICEP_CHECKS.txt | Its first version said the Bicep checks ran after the verifier's steps; they ran while the Scrape.do integration step was running. They were run again with the header corrected, and only that run is delivered. |
| review/ wording found in the review before publication | "the client's review of 1.6.5 rejected that" became "advised an extra alert, but still gave its operating documentation a pass (N10-03)", which is what the 1.6.5 documents did; "a pilot, so no publication was attempted" became "a rejected pilot, never published"; a sentence that no live command ran in a gap now cites commands.csv; the reason for the probe's two skipped tests replaced "skipped by design"; the C2 and C4 rows of REQUIREMENT_MATRIX.md and TECHNICAL_REPORT.md now follow CLASSIC_PROBE_CORRECTIONS.md. |
| review/RECOVERY_AND_OPERATIONS.md, section 2, and review/ACCEPTANCE_MATRIX.csv, B26 | Found in the last review before publication. Section 2 carried 1.6.5's sentence "Releases 1.6.4 and 1.6.5 did not change the recovery path"; it now names 1.6.4 to 1.6.6. B26's note said that the Mariano's repository's pin had moved to probe 1.7.1; that pin needs this publication's commit, so it can only follow it, and the note now says so. |
| the commit message of d2ce076 (section 4) | Found in the last review before publication: the 1.6.5 publication's first commit message also said that probe 1.7.0 corrected C1 to C5. It is added to section 4, and this publication's commit message says what is true. |
| evidence/offline-tests/1.6.6-collector/RETRY_GAP_BEFORE_THE_FULL_FIX.log | Found by the names scan made before the commit: this new test log named the workstation's user folder and its pytest temporary folder, 3 times each. The redaction step had skipped it without a word, because 4 of its bytes are not UTF-8 (the Windows console wrote the collector's breadcrumb separator as cp1252 0x9B). The step now reads such a file losslessly and refuses, never skips, a text file it cannot read. The log is redacted (REDACTIONS.csv, rules "Windows user folder" and "pytest temporary folder user"), its 4 bytes kept; no other file had been skipped (manifests/PUBLICATION.json, checks_before_commit, scans). |

## The 1.6.5 publication (tag `review-1.6.5-20261104`), as published

Kept as written for that publication, its headings one level lower. Its exact texts are under `review-1.6.5-20261104` in [`DOC_CORRECTIONS.json`](DOC_CORRECTIONS.json). "This publication" in it is the 1.6.5 publication, and its links to the manifests and the documents meant that publication's files, which are at its tag ([`manifests/` at `review-1.6.5-20261104`](https://github.com/lonadonia/walmart-azure-scraper/blob/review-1.6.5-20261104/manifests/)).

The review documents of 1.6.5 were written for this publication, so no delivered document was corrected. What follows is everything else: errors found in files that are not edited, the files of the 1.5.2 publication that this one replaces while keeping their text, and the corrections made to this publication's own records before its review tag was set.

`source/`, `classic-probe/` and `classic-probe-1.7.0/` are the delivered archives' files, unchanged ([`check_frozen_trees.py`](check_frozen_trees.py)). Historical evidence is not rewritten either: its only changes are the redactions in [`REDACTIONS.csv`](REDACTIONS.csv). [`FILE_MAP.csv`](FILE_MAP.csv) gives every file's origin and its original and published SHA-256.

#### 1. Errata: files that are not edited

| Where | What it says | What is true | Basis |
|---|---|---|---|
| `source/README.md`, line 7 | Live runs on this release: none: release 1.6.5 changes only the independent source check [...] The live runs L1 to L10 ran releases 1.6.0 to 1.6.4 | Written when the source ZIP was built, before release 1.6.5's two live canaries ran: L11 (2026-11-04T14:24:22Z to 14:30:08Z; its listing was rejected for its identity, so there was no canary page) and L11b (14:35:08Z to 14:40:23Z; passed). The rest of the cell is true. | data/RUN_SUMMARY.json; evidence/live/1.6.x/campaign/commands.csv |
| `source/walmart-oxylabs-1.6.5/tests/captures/listing_pages_20261104_flat/README.md`, line 12 (the same in walmart-scrapedo-1.6.5) | It is the only page with flat price strings among the 1,526 pages stored by the collector's 21 live runs of 2026-10-31 to 2026-11-04 | The 21 runs of releases 1.5.0 to 1.6.4 stored 1,527 page copies. 1,526 leaves out the challenge page of L6 (fetch 01M6K2F80M1AFY26P6BMN56F4C), which has no page data. The sentence's claim, that this is the only page with flat price strings, is true. | evidence/offline-tests/1.6.5-collector/FLAT_LAYOUT_SCAN.json and README.md |
| `source/walmart-oxylabs-1.6.5/tests/unit/test_flat_price_layout.py`, line 73 (the same in walmart-scrapedo-1.6.5) | # The other page gives its prices in price lines, as every other stored page of the live runs; one of its | A comment. It is true of the listing pages: every one with a result grid gives its prices in price lines, except the two copies of the flat page. Product pages give theirs as nested objects (675) or show none (10). No test depends on the comment. | evidence/offline-tests/1.6.5-collector/FLAT_LAYOUT_SCAN.json and README.md |
| `evidence/live/1.6.x/campaign/checks/L11_close_outcome.txt` (the same note is in logs/182_l11_close.jsonl and in the shared ledger's stages.csv) | gates G12, G14, G3, G4 FAIL; rejected | The run's own checks also fail G8 (FIELD_INCOMPLETE): its failed gates are G3, G4, G8, G12, G14. | evidence/live/1.6.x/campaign/checks/L11_CHECKS.json; data/RUN_SUMMARY.json (gates_failed) |
| `evidence/live/1.6.x/campaign/checks/L11b_close_outcome.txt` (the same note is in logs/194_l11b_close.jsonl and in the shared ledger's stages.csv) | Gates G3 and G4 FAIL, so the run is rejected, as a pilot always is. | The run's own checks also record G14 (CONTEST_NOT_READY), the readiness marker, which never blocks a publication: its failed gates are G3, G4, G14. | evidence/live/1.6.x/campaign/checks/L11b_CHECKS.json; data/RUN_SUMMARY.json (gates_failed); the collector's NON_BLOCKING_GATES (source/walmart-oxylabs-1.6.5/src/walmart_headless/publishing/publish.py) |
| `manifests/PUBLICATION.json` (of the 1.5.2 publication, at the tag review-1.5.2-20261103: checks_before_commit, scans, names_and_markers) | no workstation user name, host name, key fingerprint or client-message draft name | It searched for the twelve-character key fingerprints only. Five files of that publication, carried here unchanged, show the earlier Oxylabs key's fingerprint shortened to its last six characters after an ellipsis, the form the collector's validate-config prints: 11 times in evidence/historical/1_4_1/SOURCE_AND_RUN_MANIFEST.json and once in each of four validate-config logs in evidence/live/campaign/logs/ (01, 03, 16 and 61). A fingerprint is not a credential. This publication redacts that form in every file it adds or replaces (REDACTIONS.csv, rule "provider key fingerprint, shortened"); the five files are kept byte for byte, as they are at that tag. | this publication's scans of its whole tree (manifests/PUBLICATION.json, checks_before_commit, scans) |

#### 2. Files of the 1.5.2 publication replaced, with their text kept

| File | Change |
|---|---|
| `evidence/verification/README.txt` | a label added before the first line; the 1.5.2 text follows, byte for byte |
| `data/README.md` | a new first part for the 1.6.x runs; the 1.5.2 text follows under "The 1.5.x runs (2026-10-31), as published with release 1.5.2", its headings one level lower, and its last two paragraphs replaced by one: they said RUN_SUMMARY.json recorded the nine 1.5.x runs, with the delivery's own paths, and the check is now described in the first part |
| `evidence/README.md` | a new first part for the 1.6.x evidence; the 1.5.2 text follows, unchanged but for its headings, one level lower, under "The evidence of release 1.5.2, as published on 2026-11-03" |
| `CHANGELOG.md` | the 1.6.5 entry added; the link to docs/VERIFICATION.md now names the 1.6.5 tree; the rule for live runs now says that only a delivered run's product files get a data/ folder and that every run's exports are in its evidence folder. The 1.5.2 entry and those before it are unchanged |
| `review/ACCEPTANCE_MATRIX.csv` | four columns added (state_1_6_5, evidence_1_6_x, revision_1_6_x, note_1_6_x); the sixteen columns of the 1.5.2 matrix are unchanged in all 206 rows. Their 50 paths into source/walmart-oxylabs-1.5.2/ (in the evidence column) are files of the 1.5.2 tree, which is at the tag review-1.5.2-20261103: REQUIREMENT_MATRIX.md and DELIVERY_INDEX.md say so |
| `data/RUN_SUMMARY.json` | the fourteen 1.6.x runs added. The nine 1.5.x entries keep their values; their delivered files are named by their repository paths (data/S6-1.5.1/, where the delivery wrote live/S6_1.5.1/), and each adds exports and run_folder_in_repository. The top-level "campaign" is now "campaigns", with the 1.5.x campaign under "1.5.x" |
| `manifests/DOC_CORRECTIONS.md, DOC_CORRECTIONS.json` | this publication's part added first; the 1.5.2 record kept below, as published |

The other files of the 1.5.2 publication are either carried unchanged (its evidence, its data folders and `data/COVERAGE_RECONCILIATION.csv`, `classic-probe/`, `walkthrough/`, `.gitattributes`, `.gitignore`, `review/LINKED_EXAMPLES.csv`, `review/THIRD_PARTY_LICENSES.csv` and `manifests/SOURCE_AND_RUN_MANIFEST.json`, which is release 1.5.2's record) or replaced by this delivery's file of the same name (`README.md`, the review documents and the manifests: `check_data.py`, `check_frozen_trees.py`, `PUBLICATION.json`, `FILE_MAP.csv`, `REDACTIONS.csv`, `EXCLUDED.csv` and `SHA256SUMS.txt`). Each replaced file's earlier version is at the tag `review-1.5.2-20261103`, and [`FILE_MAP.csv`](FILE_MAP.csv) names it.

#### 3. Corrections made to this publication's own records before its review tag was set

| What | Correction |
|---|---|
| data/RUN_SUMMARY.json: valid_fresh | assemble_data_164.py counted the exported fresh rows as valid_fresh, which overstated L10 by 2 (7,057 against 7,055 valid) and L4r by 1 (1,601 against 1,600). In assemble_data_165.py, valid_fresh counts valid fresh records, and fresh_rows_exported was added. A run that validated with no valid record (L11) shows 0; runs stopped before validation show none. |
| evidence/reconciliation/1.6.5/CONCURRENCY_MEASURED_1_6_5.csv: release | concurrency_164.py took each run's release from a table of labels and gave L11 and L11b its default, 1.6.1. concurrency_165.py reads it from the run's own database row (db/runs.csv, parser_version): 1.6.5. |
| review/ documents: the final release | Drafts written while 1.6.4 was the candidate called it the final release. Every document now names 1.6.5, and attributes each run to the release that ran it. |
| the W4 coverage description in the review documents | A draft defined the root and child listings of W4's coverage table wrongly. The published text follows the table (evidence/reconciliation/1.6.5/w4/). |
| L8's product pages | A draft said L8 fetched 5 product pages. It fetched 6 (all HTTP 200), and 5 of them gave the UPCs of fresh rows. |
| review/DELIVERY_INDEX.md: evidence/verification/1.6.1/ and 1.6.4/ | A draft called them those releases' verification records. They hold only the last-good publication check of each. |
| review/MILESTONES.md and review/TECHNICAL_REPORT.md: the session gap | Drafts cited a checkpoint note in the campaign record for the gap of 2026-11-03T19:24Z to 2026-11-04T09:59Z. The record has no such note. They now cite commands.csv (no command from 19:17:16Z to 10:26:25Z) and the ledger's events.json (no event from 19:17:16Z to 10:26:37Z). |
| review/CLASSIC_PROBE_CORRECTIONS.md: the Mariano's adapter | A draft gave the adapter as the backticked path classic-probe/src/classic_probe/marianos.py, which reads as a path of this repository (where classic-probe/ is the Walmart probe 1.5.2). It is now a link to that file in lonadonia/marianos-azure-scraper at 1f568b8, whose blob, 9de6510b, was read again through GitHub's API. |
| data/README.md: the 1.5.x entries of RUN_SUMMARY.json | A draft said they keep the paths the 1.5.2 publication gave them. Their delivered files now have repository paths, and two fields were added (see the replaced files above). |
| review/MILESTONES.md, DELIVERY_INDEX.md, REQUIREMENT_MATRIX.md and ACCEPTANCE_MATRIX.csv: the client's VM | Drafts named the client's VM, and MILESTONES.md also its login and folders. The 1.5.2 publication named none of them, and the disclosure scan made before the commit flagged the login. The documents now say "the client's VM"; nothing else in them changed. |
| the shared ledger's folder | 24 files of the live campaign record (evidence/live/1.6.x/campaign/: commands.csv, stage_steps.json, the harness and its five earlier versions, and 16 logs) and two review documents (COST_AND_RUNTIME_REPORT.md and TECHNICAL_REPORT.md) named the shared ledger's folder by its path from the workstation's projects folder. The campaign files are redacted (REDACTIONS.csv, rule "workstation projects folder, relative"); the two documents now give the folder's own name. |
| review/CLASSIC_PROBE_CORRECTIONS.md (twice) and review/REQUIREMENT_MATRIX.md: the Classic request claim | The publication's first commit, d2ce076f23ac2787b4b38269de6f8ba8942f520c (pushed on 2026-11-04 at 19:17Z, before the review tag was set), said that no Classic request had ever been sent. W0 (TECHNICAL_REPORT.md, section 8) was one usage-statistics query that sent the Web API key as Basic credentials, refused with HTTP 401. The tagged commit says that no Classic scraping request has been sent, and names W0. Nothing else changed in the two documents. |

## The 1.5.2 publication (tag `review-1.5.2-20261103`), as published

Kept as written for that publication. Its exact texts are under `review-1.5.2-20261103` in [`DOC_CORRECTIONS.json`](DOC_CORRECTIONS.json). Its links to `PUBLICATION.json` and to the documents it corrected meant that publication's files, which are at its tag ([`manifests/` at `review-1.5.2-20261103`](https://github.com/lonadonia/walmart-azure-scraper/blob/review-1.5.2-20261103/manifests/)).

The review documents of the delivery are published with the corrections below. [`DOC_CORRECTIONS.json`](DOC_CORRECTIONS.json)
gives the exact text of each one, before and after (52 edits), and the path rewrites listed at the end. Values
withheld from a public repository are shown as `<...>`.

The source and the Classic probe are not corrected. They are the delivered archives' files, unchanged
([`check_frozen_trees.py`](check_frozen_trees.py)). Historical evidence is not rewritten either: its only changes are the
redactions in [`REDACTIONS.csv`](REDACTIONS.csv). [`FILE_MAP.csv`](FILE_MAP.csv) gives every file's original and
published SHA-256.

| Correction | Where | Basis |
|---|---|---|
| **A set of two sizes (erratum).** The delivered documents said that release 1.5.2 still gives "12.5 oz" for "Shampoo and Conditioner Dual Pack, 12.5 oz shampoo + 10.6 oz conditioner", as a known limit. The frozen 1.5.2 keeps both sizes: "12.5 oz shampoo + 10.6 oz conditioner". "12.5 oz" was the result of 1.5.0 and 1.5.1. No stored page of the runs has such a title, so the correction rests on a unit test | `review/TECHNICAL_REPORT.md` §3; `review/DELIVERY_INDEX.md`, known limitation 3; `review/ACCEPTANCE_MATRIX.csv` A07, N4-06 | the source's `docs/VERIFICATION.md` (release 1.5.2, the table) and `tests/unit/test_pack_size.py::test_two_packages_of_a_set_are_both_kept_and_do_not_conflict_with_themselves`. That test passed in the delivery's verification of both editions ([`unit.xml`](../evidence/verification/junit/oxylabs/unit.xml)) and again for this publication, on a copy installed from `uv.lock`. The 1.5.0 and 1.5.1 outputs are in [`pack_fix_151/`](../evidence/reconciliation/1.5.1/pack_fix_151/) (`sizes_old_1_5_0.json`, `sizes_new_worktree.json`) |
| **The verifier's name (erratum).** Row N10-01 named the verifier of 1.5.1. The 1.5.2 delivery was verified by `verify_walmart_152_delivery.py` | `review/ACCEPTANCE_MATRIX.csv` N10-01 | [`steps.jsonl`](../evidence/verification/steps.jsonl) |
| **Files not published here.** Each reference to one of these files now says that it is not published and where its record is, if it has one: the client-message draft, the Azure access-request draft, the client summary PDF, the delivery's `SHA256SUMS.txt`, and its verifier and builder | `review/DELIVERY_INDEX.md`; `review/TECHNICAL_REPORT.md` §7, §9; `review/TEST_PLAN.md`, item 7; `review/ACCEPTANCE_RUNBOOK.md`, introduction and §5; `review/ACCEPTANCE_MATRIX.csv` A63, B24, N10-05, N10-08, N11-01, P10-01, P11-01, P13-01 | [`EXCLUDED.csv`](EXCLUDED.csv). The verifier's record is [`evidence/verification/`](../evidence/verification/), and this repository's checksums replace the delivery's list |
| **Public repository.** A note on the handling of the owner's provider key is withheld. The owner action it led to, replacing the key, stays open | `review/DELIVERY_INDEX.md`, Accounts; `review/ACCEPTANCE_MATRIX.csv` A54, P2-03, P8-01 | not needed to verify any claim of the delivery |
| **Names.** Client documents name Hamza only | `review/ACCEPTANCE_MATRIX.csv` N7-03 | |
| **Publication layout.** `review/DELIVERY_INDEX.md` has a note that it is the published copy. The runbook works from a clone, using `manifests/SHA256SUMS.txt`, `check_frozen_trees.py` and `check_data.py`, with `source/` copied out before anything is installed. Its expected results and test counts are unchanged | `review/DELIVERY_INDEX.md`; `review/ACCEPTANCE_RUNBOOK.md`, introduction, §1 to §7 | [`FILE_MAP.csv`](FILE_MAP.csv) |

**Added for this publication:** `README.md`, `CHANGELOG.md`, `review/CORRECTION_MAP.md`, `evidence/README.md`,
`data/README.md`, `walkthrough/README.md` and the files of `manifests/`. They summarize the delivered evidence and
add no test result. One exception is recorded in [`PUBLICATION.json`](PUBLICATION.json): the focused offline checks
run for this publication.

### Path changes

708 references in 7 documents were rewritten to repository paths. These include references into
the archives (`WALMART_EVIDENCE_1.5.2.zip: <path>`, `WALMART_SOURCE_1.5.2.zip: <path>` and
`OXYLABS_CLASSIC_OFFLINE_PROBE_1.5.2.zip: <path>`) and the bare names of the delivery folder's files. They are links
in Markdown and plain paths in CSV. References to `shared/WALMART_SHARED_EVIDENCE_1.4.1.zip`, the 1.4.1 delivery,
are kept as written. The JSON records and the evidence keep their paths:
[`evidence/README.md`](../evidence/README.md) maps them.

| Document | References rewritten |
|---|---|
| `review/ACCEPTANCE_MATRIX.csv` | 551 |
| `review/ACCEPTANCE_RUNBOOK.md` | 24 |
| `review/COST_AND_RUNTIME_REPORT.md` | 9 |
| `review/DELIVERY_INDEX.md` | 42 |
| `review/LINKED_EXAMPLES.csv` | 49 |
| `review/TECHNICAL_REPORT.md` | 28 |
| `review/TEST_PLAN.md` | 5 |
