# Walmart release 1.5.2: evidence

Everything here is sorted by what kind of evidence it is. `DELIVERY_INDEX.md`, beside this ZIP, explains the delivery as a whole.

**Folders 1 to 6, `accounts/` and `tools/` are the evidence of release 1.5.1, carried byte for byte.** Every file keeps its path and hash, so what they say about 1.5.1 still applies, and text inside them that names `WALMART_EVIDENCE_1.5.1.zip` means these same files here. **Folder 7 is this release.** It holds no live request.

| Folder | Evidence class | What |
| --- | --- | --- |
| `1_new_live/` | LIVE VERIFIED | The owner-funded campaign of 2026-10-31: nine runs on the Oxylabs Web API, Walmart #3891 Waukegan, Pickup. S1 to S5 on release 1.5.0 (`7b6f325`), S6 and S7 on release 1.5.1 (`488a033`) |
| `2_offline_reprocessing/` | OFFLINE REPROCESSING | The 1.4.1 run B3 (`01M60V2DCCWR72BGVVG3EM9R74`, 2026-10-28) read again by 1.5.1 from its saved pages. No request. Not a new collection |
| `3_reconciliation/` | RECONCILIATION, by row | Coverage, sponsored and variant cases, queues, offers, linked examples, blanks, the known limitation. Each row carries its own class. `cost_model_151/` is an ESTIMATE |
| `4_historical_references/` | HISTORICAL | The earlier deliveries by path and SHA-256 (`HISTORICAL_REFERENCES.csv`), byte-identical copies of 1.4.1's `SHA256SUMS.txt` and `SOURCE_AND_RUN_MANIFEST.json`, and the 1.4.1 saved pages that linked examples name (`saved_pages_of_linked_examples/INDEX.csv` gives each page's 1.4.1 evidence ZIP and member) |
| `5_fault_and_publication_tests/` | SYNTHETIC TEST | Publication faults injected against a test fixture, with before and after snapshots. Not a retailer run |
| `6_offline_regressions/` | OFFLINE VERIFIED | The four test files that hold 1.5.1's new cases, run against the frozen 1.5.0 source and against 1.5.1, each from a clean `git archive` installed from the lock: 182 pass on 1.5.1; on 1.5.0, 28 of the 42 new cases fail (the defects), the 14 others are limits that pass on both, and one case whose expectation 1.5.1 changed fails. No request |
| `7_release_1_5_2/` | OFFLINE REPLAY, OFFLINE REPROCESSING, OWNER AZURE TEST, SYNTHETIC TEST, RECONCILIATION, by file | Release 1.5.2 (`627c804`). See the table below |
| `accounts/` | ACCOUNT READING | The free Scrape.do `/info` readings of this task, with the key removed |
| `tools/` | TOOL | The operator's scripts that ran the campaign and made these reconciliations, as they ran, and (`tools/docs151/`) the scripts that wrote the delivery's acceptance matrix, run summary, linked examples and source and run manifest, with the Markdown source of `CLIENT_SUMMARY.pdf`. `tools/workstation/` holds the PDF maker (`render_report_pdf_131.py`, Microsoft Edge headless) and the page renderer the verifier uses (`pdf_pages_png.ps1`). They name workstation folders; they are not part of the collector |

The clean-extraction verification of the delivery is not in this ZIP: it is in `verification/` beside it, and `PACKAGE_VERIFICATION.txt` summarizes it.

## Folder 7: release 1.5.2

| Path under `7_release_1_5_2/` | Class | What |
| --- | --- | --- |
| `replay_campaign/` | OFFLINE REPLAY | The nine runs replayed in their order by 1.5.2 on a new copy: `runs/<stage>/exports/`, `logs/`, `replay_runs.json` |
| `repeat_replay/` | OFFLINE REPLAY | The same nine on a second copy (`a2/`), and `A1_A2_COMPARISON.json` |
| `replay_b3/` | OFFLINE REPROCESSING | B3 read again by 1.5.2: `export_replay_1_5_2/`, `RUNS_OF_THE_COPY.json` |
| `correction_maps/` | OFFLINE REPLAY | Every difference from the delivered files, per run. `b3_1_4_1_to_1_5_2/` compares B3 with the 1.4.1 file |
| `agreement/` | OFFLINE REPLAY | The check of `provenance.json`, `record_map.json` and `field_dispositions.json` against each other and the stored bytes: 0 problems on ten exports |
| `defects_before_the_fix/` | OFFLINE VERIFIED | The output of the two defects found here, before their fixes |
| `private_label/` | OFFLINE REPROCESSING | What the saved product pages say about the brands |
| `classic_documentation_recheck/` | HISTORICAL | The saved Oxylabs pages compared with the live documentation on 2026-11-01: 12 of 12 identical |
| `load/workstation/` | SYNTHETIC TEST | The load test against a local fixture |
| `sponsored_and_variant_reconciliation/` | RECONCILIATION | The 651 rows, the exact read queue and the summary |
| `accounts/` | ACCOUNT READING | The free Scrape.do `/info` reading of 2026-11-01, with the key removed |
| `owner_vm/` | OWNER AZURE TEST | Hamza's test VM: the driver log, `commands.csv`, the suites' JUnit XML, each step's log, the publication faults (SYNTHETIC), the load test, the container's exports and their comparison with the workstation's (`CONTAINER_COMPARISON.txt`), the Classic probe ZIP tested there against the delivered one (`PROBE_ZIP_TESTED_VS_DELIVERED.json`), and the cleanup log |
| `walkthrough/` | OWNER AZURE TEST | The recording of the terminal walkthrough, and its commands |
| `tools/` | TOOL | The scripts that made this folder, and the sources of the delivery's documents. They name workstation folders; they are not part of the collector |

A replay's run id is new, and it is not the id of the live run. A stored page used by a replay stays in the live run's folder, under `1_new_live/runs/`: a replay fetches nothing.

## The nine live runs

Each run has its folder `1_new_live/runs/<run id>/`. `STAGE.txt` names the stage.

| Stage | Run | Release | Ledger rows | Listing pages | Detail + follow-up pages | Valid fresh products | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| S1 | `01M69X9XHZR83KZ2FNWBJYJKA7` | 1.5.0 | 4 | 1 | 1 + 0 | 35 | rejected |
| S2 | `01M69XM9RZN3C8D0K7W2NSXR3D` | 1.5.0 | 28 | 6 | 10 + 10 | 203 | rejected |
| S3 | `01M69Y1J6YWFEZ1DJHAC2MT17M` | 1.5.0 | 9 | 4 | 3 + 0 | 116 | rejected |
| S4 | `01M69Y882GTVYRJZM0CXQ44MXN` | 1.5.0 | 39 | 19 | 10 + 0 | 677 | rejected |
| S5b serial | `01M69YPZTFCP7AWJ5B78AXEA2N` | 1.5.0 | 4 | 2 | 0 | 80 | rejected |
| S5b parallel | `01M69YS2X0YG5JSEMCGKK8BHE5` | 1.5.0 | 6 | 2 | 0 | 80 | rejected |
| S5a | `01M6A0JWYHTVK7XFH34P235F9Q` | 1.5.0 | 4 | 2 | 0 | 67 | rejected |
| S6 | `01M6A2VQAA5VXJHJHMZPCTZTD4` | 1.5.1 | 22 | 15 | 1 + 0 | 580 | rejected |
| S7 | `01M6A52HA6XYCEDS6DBE5N5RQ7` | 1.5.1 | 3 | 1 | 0 | 32 | rejected |

`rejected` is the correct outcome of a pilot: no capped run reconciles every listing, so the coverage gate fails and nothing is published. The campaign database holds no publication.

The ledger counted 119 rows of the 120 allowed: 115 answered, 3 abandoned when a run was killed or stopped, 1 free provider failure. The last request was at 2026-10-31T23:35:31Z. `1_new_live/plan/CAMPAIGN_BUDGET.json` holds the limits and the worst-case reconciliation of the account's earlier use they were sized against. The Oxylabs balance itself was not read: the Web API documents no balance endpoint, and the owner's dashboard was not opened.

## What is in a run's folder

| Path | What |
| --- | --- |
| `exports/products_fresh.json`, `.csv` | The products this run observed. The 22 fields |
| `exports/products.json`, `.csv` | The fresh products plus those carried from earlier runs of the campaign (`observation_kind` in `record_map.json` says which) |
| `exports/record_map.json` | For each row: its run, time, code revision, stored page with SHA-256, store checks, each field's source and the UPC's outcome |
| `exports/field_dispositions.json`, `.csv` | Why each UPC and weight is filled or empty |
| `exports/provenance.json`, `validation_report.json`, `offers.json`, `memberships.json`, `manifest.json` | The rest of the run's export |
| `coverage/` | The run's coverage reconciliation and follow-up outcomes |
| `pages/<fetch id>.html.gz` | The stored page of each fetch |
| `robots/` | The robots.txt read at the start of each segment |
| `db/` | The run's database tables as CSV: `page_fetches`, `provider_usage`, `collection_segments`, `tasks`, `events`, `validation_findings`, `node_coverage`, `artifacts` |
| `RAW_ORIGINALS_MANIFEST.csv` | The SHA-256 of each provider answer kept on the workstation (see `SANITIZATION.md`) |

`1_new_live/campaign/` holds what spans the runs: `commands.csv` (each command, its exit code and time), `logs/` (each command's output), `compare/` (run-to-run comparisons), `summary/` (stages and measures), `db/` (the campaign's tables, including the whole ledger `provider_usage_all.csv`), and the records of the kills and the overlap attempts.

## To follow one product to its page

1. Take the row from `exports/products_fresh.json`. The item id is the last number of its `url`.
2. Find the row with that `url` in `exports/record_map.json`. `page.stored_page` ends in the page's file name, `page.stored_page_sha256` is its hash, and `fields.product_title.selector_or_path` gives the tile's position.
3. Open `pages/<that file>` of the run named by `observed_by_run` (a carried row names its own earlier run). The page data is in the `__NEXT_DATA__` script.
4. A UPC recovered from a saved page: `upc_detail` in the record map and `field_dispositions.json` name the source run, the page and its SHA-256. Those runs are in the 1.4.1 evidence ZIPs; `2_offline_reprocessing/capture_index/detail_capture_index_150.json` lists each saved page, with its path in those ZIPs, and `1_new_live/campaign/db/detail_observations_imported.csv` what was read from it.

`3_reconciliation/linked_examples/LINKED_EXAMPLES.csv` does this for 48 chosen rows, as its tool wrote it. The copy beside this ZIP (`LINKED_EXAMPLES.csv`) is the one to read: its `page_file` names each page as `WALMART_EVIDENCE_1.5.1.zip: <path>`, including the 1.4.1 saved pages now copied to `4_historical_references/saved_pages_of_linked_examples/`. In the tool's copy, `page_file` of E015 and E019 (and `source_path` of E033 and E040) is the page's path in the workstation's extraction of the 1.4.1 evidence ZIPs: without its first folder (ox for the Oxylabs ZIP, sd for the Scrape.do ZIP) it is the ZIP member. Where `page_sha256` comes from a detail reading (E030, E036, E037) it is the hash of the page's content after decompression, which the collector records as `body_sha256`; otherwise it is the hash of the stored `.html.gz` file. `INDEX.csv` gives both for each 1.4.1 page.

## Known limitations of the 1.5.1 files

These are limits of the delivered 1.5.1 exports, which stay as they were. The first two are corrected in the replays of folder 7.

- For a size recovered from a saved page, `provenance.json` (`fields.weight`) still names the listing tile with rule `none`, and `missing.weight` keeps the listing's text. `field_dispositions.json` and `upc_detail` hold the true lineage and are the authority. The 22 exported fields are not affected. `3_reconciliation/known_limitations_151/PROVENANCE_RECOVERED_SIZES.json` lists the rows.
- Five carried Dry Dog Food rows in S6's `products.json` keep the weight 1.5.0 gave them: carried rows are never rewritten, and S6 did not read page 4 of that listing. Items 18472720019, 18468708077, 18511760810, 20636621408, 18529653937.
- S7 stopped at its limit before its detail step, so its 32 products show blank UPCs that S6 filled. They were not read, and the disposition says so (`budget_deadline_interruption`).

`EVIDENCE_MANIFEST.csv` lists every file with its class, source and hashes. `SANITIZATION.md` says what was changed.
