# Corrections made for this publication

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

## Path changes

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
