# Corrections made for this publication

Two records follow: this publication's (tag `review-1.6.5-20261104`), then that of the 1.5.2 publication (tag `review-1.5.2-20261103`), kept as it was published. [`DOC_CORRECTIONS.json`](DOC_CORRECTIONS.json) gives the exact texts of both.

## This publication: release 1.6.5 (tag `review-1.6.5-20261104`)

The review documents of 1.6.5 were written for this publication, so no delivered document was corrected. What follows is everything else: errors found in files that are not edited, the files of the 1.5.2 publication that this one replaces while keeping their text, and the corrections made to this publication's own records before its review tag was set.

`source/`, `classic-probe/` and `classic-probe-1.7.0/` are the delivered archives' files, unchanged ([`check_frozen_trees.py`](check_frozen_trees.py)). Historical evidence is not rewritten either: its only changes are the redactions in [`REDACTIONS.csv`](REDACTIONS.csv). [`FILE_MAP.csv`](FILE_MAP.csv) gives every file's origin and its original and published SHA-256.

### 1. Errata: files that are not edited

| Where | What it says | What is true | Basis |
|---|---|---|---|
| `source/README.md`, line 7 | Live runs on this release: none: release 1.6.5 changes only the independent source check [...] The live runs L1 to L10 ran releases 1.6.0 to 1.6.4 | Written when the source ZIP was built, before release 1.6.5's two live canaries ran: L11 (2026-11-04T14:24:22Z to 14:30:08Z; its listing was rejected for its identity, so there was no canary page) and L11b (14:35:08Z to 14:40:23Z; passed). The rest of the cell is true. | data/RUN_SUMMARY.json; evidence/live/1.6.x/campaign/commands.csv |
| `source/walmart-oxylabs-1.6.5/tests/captures/listing_pages_20261104_flat/README.md`, line 12 (the same in walmart-scrapedo-1.6.5) | It is the only page with flat price strings among the 1,526 pages stored by the collector's 21 live runs of 2026-10-31 to 2026-11-04 | The 21 runs of releases 1.5.0 to 1.6.4 stored 1,527 page copies. 1,526 leaves out the challenge page of L6 (fetch 01M6K2F80M1AFY26P6BMN56F4C), which has no page data. The sentence's claim, that this is the only page with flat price strings, is true. | evidence/offline-tests/1.6.5-collector/FLAT_LAYOUT_SCAN.json and README.md |
| `source/walmart-oxylabs-1.6.5/tests/unit/test_flat_price_layout.py`, line 73 (the same in walmart-scrapedo-1.6.5) | # The other page gives its prices in price lines, as every other stored page of the live runs; one of its | A comment. It is true of the listing pages: every one with a result grid gives its prices in price lines, except the two copies of the flat page. Product pages give theirs as nested objects (675) or show none (10). No test depends on the comment. | evidence/offline-tests/1.6.5-collector/FLAT_LAYOUT_SCAN.json and README.md |
| `evidence/live/1.6.x/campaign/checks/L11_close_outcome.txt` (the same note is in logs/182_l11_close.jsonl and in the shared ledger's stages.csv) | gates G12, G14, G3, G4 FAIL; rejected | The run's own checks also fail G8 (FIELD_INCOMPLETE): its failed gates are G3, G4, G8, G12, G14. | evidence/live/1.6.x/campaign/checks/L11_CHECKS.json; data/RUN_SUMMARY.json (gates_failed) |
| `evidence/live/1.6.x/campaign/checks/L11b_close_outcome.txt` (the same note is in logs/194_l11b_close.jsonl and in the shared ledger's stages.csv) | Gates G3 and G4 FAIL, so the run is rejected, as a pilot always is. | The run's own checks also record G14 (CONTEST_NOT_READY), the readiness marker, which never blocks a publication: its failed gates are G3, G4, G14. | evidence/live/1.6.x/campaign/checks/L11b_CHECKS.json; data/RUN_SUMMARY.json (gates_failed); the collector's NON_BLOCKING_GATES (source/walmart-oxylabs-1.6.5/src/walmart_headless/publishing/publish.py) |
| `manifests/PUBLICATION.json` (of the 1.5.2 publication, at the tag review-1.5.2-20261103: checks_before_commit, scans, names_and_markers) | no workstation user name, host name, key fingerprint or client-message draft name | It searched for the twelve-character key fingerprints only. Five files of that publication, carried here unchanged, show the earlier Oxylabs key's fingerprint shortened to its last six characters after an ellipsis, the form the collector's validate-config prints: 11 times in evidence/historical/1_4_1/SOURCE_AND_RUN_MANIFEST.json and once in each of four validate-config logs in evidence/live/campaign/logs/ (01, 03, 16 and 61). A fingerprint is not a credential. This publication redacts that form in every file it adds or replaces (REDACTIONS.csv, rule "provider key fingerprint, shortened"); the five files are kept byte for byte, as they are at that tag. | this publication's scans of its whole tree (manifests/PUBLICATION.json, checks_before_commit, scans) |

### 2. Files of the 1.5.2 publication replaced, with their text kept

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

### 3. Corrections made to this publication's own records before its review tag was set

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
