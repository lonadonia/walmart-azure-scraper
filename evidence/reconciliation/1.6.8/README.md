# Reconciliation for release 1.6.8: W2, W3 and W4

These tables answer the client's review of 1.6.6. They were made without any request: the tools read the live runs'
stored pages and records, either in the campaign database (read-only session) or as published under
`evidence/live/1.6.x/`. Every row names the run, page and SHA-256 its decision rests on.

The W2 and W3 tools were written for release 1.6.7. They read only saved captures, through the collector's page
reader (`page_data.py`, `challenge.py` and `sanitize.py`). Those files are byte-identical in 1.6.7 and 1.6.8, so the
tables stand for 1.6.8. The W4 tables are made from the coverage reports that release 1.6.8 itself gives for the live
runs: its Docker image made them on the owner's Azure test VM (2026-11-05). `l12/` compares the 1.6.8 replay of L12 with
the export 1.6.6 published.

| Folder | What it holds |
|---|---|
| `w2/` | the blank UPCs and sizes of S6, rechecked against every saved read (`W2_RECHECK_1_6_7.csv`, 66 rows; `W2_RECHECK_SUMMARY_1_6_7.json`) |
| `w3/` | the 275 queued sponsored and variant products at row level (`W3_ROW_LEVEL_1_6_7.csv`, 275 rows; `W3_ROW_LEVEL_SUMMARY_1_6_7.json`) |
| `w4/` | coverage per listing, page and CSV row under the 1.6.8 rules, each listing's change from the 1.6.6 tables, and the price of the outstanding work |
| `l12/` | L12's published export against its 1.6.8 replay, field by field (`L12_1.6.6_EXPORT_VS_1.6.8_REPLAY.csv`, `.json`), and why each name changed: the stored links of the category pages (`names_probe_168d.py`, `links_of_168d.py` and their output) |
| `tools/` | the tools of W2, W3 and W4 (`w2_recheck_167.py`, `w3_reconcile_167.py`, `w4_coverage_168.py`) and the price estimate (`continuation_168.py`) |

## W2: the blank UPCs and sizes

After release 1.6.3, S6's rows lacked 52 UPCs: 51 still blank and 1 cleared. For 49 of the 52, 1.6.3 recorded "not
attempted".

| UPC class | Count | What it means |
|---|---|---|
| `filled_in_l12_export` | 3 | L12 (release 1.6.6) read the item's own page and filled the UPC |
| `recoverable_by_1_6_7` | 3 | a saved read of the item's own page states the UPC; 1.6.6 withheld it only because the same read's sizes conflict. Release 1.6.7 (and 1.6.8) decides UPC and size separately, so it fills these UPCs without a request: items 16664823 (`046500022517`), 314089142 (`024200049423`) and 40347953 (`033383652207`) |
| `never_attempted` | 44 | no read of the item's own page exists in any run; all 44 wait in the detail queue (pending). For 43 no read was ever attempted: in L12, 20 because product detail reading was off in their runs and 23 with no outcome recorded. For 1 (item 338270604) the read was cut by a run's detail limit |
| `absent_at_source` | 1 | the item's own page states no UPC or GTIN (item 10496473297) |
| `wrong_identity` | 1 | the page read was for another item (655257631 read as 195134138) |

The 1.6.8 replay of L12 on the owner's VM (no request) fills all three, among nine UPCs it fills from saved reads
(`l12/`).

So the queue of UPCs with no read is 44, not the 45 that 1.6.6 reported. Reading them needs product pages, which
need provider funds; none is available.

| Size class | Count |
|---|---|
| `conflicting` (the read states more than one size; the size stays blank, the UPC is unaffected) | 4 |
| `absent_at_source` | 8 |
| `never_attempted` | 2 |

No UPC, size or price was guessed. A blank value keeps its reason, its run and, where a page was read, that page's
SHA-256.

## W3: the 275 sponsored and variant products

| Outcome | Count |
|---|---|
| included | 48 |
| excluded: the item's own page places it in another category (that category identified) | 165 |
| excluded: the page states no category path (`categoryPathId` −1, no breadcrumb), so the required category cannot be proven | 4 |
| excluded: the page does not prove local eligibility | 55 |
| duplicate (linked to the original observation and the SHA-256 of the stored page) | 3 |
| failed, blocked or unresolved | 0 |

So 169 exclusions (165 + 4) lack proof of the required category and 55 lack proof of local eligibility. A missing path
(4) is kept apart from a positively identified alternative category (165). The three duplicates are items 122787913,
567228522 and 15565153181.

## W4: coverage under the 1.6.8 rules

See `w4/README.txt`. No CSV row is complete: 0 of 11. Of the 1,104 listings known, 252 are complete, 213 partial,
464 not attempted, 15 incomplete, 12 at the result window and 7 read only through a filtered view; 95 subcategory
pages of their own were never read; 1 is a category page and 1 was not found; 44 are out of scope (35 not category
pages, 6 excluded by the CSV, 3 filtered views of their row's own category). `w4/W4_ROWS_1_6_8.csv` gives each of the
11 rows apart. Reading the known listing pages would cost about USD 4.63; product pages for UPC and size, USD 89 to
167 (`w4/CONTINUATION_ESTIMATE_1_6_8.json`).

## L12: the published export against the 1.6.8 replay

All 10,301 records match by product URL. 9 UPCs are filled from saved reads, and 337 sub_category values change, every
one to the name the row's category page gives the view itself: "Laundry" to "Shop All Laundry Supplies" (184),
"Fabric Softener" to "Fabric Softeners" (52, 40 of them L12's own), "Dry Dog Food" to "Dry dog food" (39), "Laundry
Detergents" to "Laundry Detergent" (38), "Laundry Scent Boosters" to "Scent Boosters" (19), and "Great Value Pantry"
to "Pantry" (5: the Food page links that listing twice, "Pantry" first). Nothing else differs, and the six
always-empty fields stay empty.
