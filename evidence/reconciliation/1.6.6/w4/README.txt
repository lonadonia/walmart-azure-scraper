W4 COVERAGE TABLES, release 1.6.6 of the tables (offline; no request was sent to make them)

These are the tables of ../../1.6.5/w4/ with run L12 added: one page of Household Essentials' Fabric Softeners
listing, read on release 1.6.6 at 22:52Z to 22:59Z on 2026-11-04. They were made by w4_coverage_166.py
(evidence/live/1.6.x/campaign/tools/), which is w4_coverage_165.py with the 1.6.6 file names and state column
(make_w4_166.py). The inputs are the 1.6.5 inputs and L12's own coverage report; W4_SUMMARY_1_6_6.json names each
input with its SHA-256.

The same tool, given the 1.6.5 inputs alone, reproduces the published 1.6.5 tables byte for byte (with 1_6_5 read
as 1_6_6 in the names). Adding L12 changes two rows:

  W4_PAGES_1_6_6.csv     one page row added: L12, listing 1115193_1071967_1630538, page 1: products 49
                         (organic 40, sponsored 9), reported total 77, grid filter Pickup. Pages: 714 -> 715.
  W4_LISTINGS_1_6_6.csv  the Fabric Softeners row: L12's read is added to reads_1_6_x ("L12 (1.6.6) CAPPED, end
                         PAGE_LIMIT, pages 1, reported 77, placed 40"). Its best read stays L6 (pages 1-2), its
                         state stays OUT_OF_SCOPE and its outstanding work is unchanged. As in 1.6.5, the latest
                         run that names a listing gives its name, link and found_via: L12 named the listing from
                         its configured path, so this row now reads "Fabric Softener", found_via "configured",
                         and the link without its navigation parameter. The site's name ("Fabric Softeners") and
                         the category-page link are in the 1.6.5 table.

W4_ROWS_1_6_6.csv, W4_REVISITS_1_6_6.csv and every state count are unchanged. No CSV row is complete, and no
full-scope run has been made (full_scope_complete: false).
