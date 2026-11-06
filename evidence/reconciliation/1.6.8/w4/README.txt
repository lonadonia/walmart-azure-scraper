W4 COVERAGE TABLES under the rules of release 1.6.8 (commit 85c29e7; offline: no request was sent to make them)

What they are made from. Release 1.6.8's own coverage report of each of the fifteen live runs of the 1.6.x campaign,
and the 1.6.6 tables (W4_LISTINGS_1_6_6.csv of the 1.6.6 publication) for each listing's earlier state.
w4_coverage_168.py (../tools/) joins them, with the published 1.5.2 table (data/COVERAGE_RECONCILIATION.csv) for the
2026-10-24 navigation. W4_SUMMARY_1_6_8.json names every input with its SHA-256; w4_run.out is the tool's output.

How the reports were made. On the owner's Azure test VM, 2026-11-05 from 21:52:54Z to 21:53:33Z, by the 1.6.8 Oxylabs
Docker image (built from the delivered ZIP; ../../../owner-azure-test/1.6.8/container/IMAGES.md), on a copy of the
campaign database restored from its dump: coverage-report --run for each run (container steps coverage_live_L1 to
coverage_live_L12). coverage-report reads the database only; the container had no provider key and its HTTP(S) went
to a closed local port. The fifteen reports are published there (../../../owner-azure-test/1.6.8/container/
coverage_live/<run>/); each is byte for byte the input W4_SUMMARY_1_6_8.json names (SHA-256 checked, 15 of 15).
The tables were joined on the workstation (2026-11-05, 22:19Z), reading the stored partitions from the local copy of
the campaign database in one read-only session.

The tables:
  W4_LISTINGS_1_6_8.csv               one row per listing known in the 11 CSV rows (1,104): its state under 1.6.8, its
                                      best read, every 1.6.x read, what remains, and its 1.6.6 state
  W4_PAGES_1_6_8.csv                  one row per result page read live (715)
  W4_ROWS_1_6_8.csv                   one row per CSV row: its listings by state, and whether it is complete
  W4_REVISITS_1_6_8.csv               the revisits the review of 1.5.2 asked for, as in 1.6.6
  W4_TRANSITIONS_1_6_6_TO_1_6_8.csv   each listing's 1.6.6 state beside its 1.6.8 state, with what is outstanding
  W4_SUMMARY_1_6_8.json               the counts below, and the inputs
  CONTINUATION_ESTIMATE_1_6_8.json    what the outstanding work would cost, priced part by part (below)

States of the 1,104 listings under 1.6.8:
  COMPLETE 252, PARTIAL 213, NOT_ATTEMPTED 464, SUBCATEGORY_PAGE_NOT_READ 95, OUT_OF_SCOPE_NOT_A_CATEGORY 35,
  INCOMPLETE 15, RESULT_WINDOW 12, FILTERED_VIEW 7, OUT_OF_SCOPE_CSV 6, OUT_OF_SCOPE_FILTERED_ROW 3, CATEGORY_PAGE 1,
  NOT_FOUND 1.

From the 1.6.6 tables (COMPLETE 244, PARTIAL 203, NOT_ATTEMPTED 407, OUT_OF_SCOPE 230, RESULT_WINDOW 9,
INCOMPLETE 9, CATEGORY_PAGE 1, NOT_FOUND 1):
  - 239 of the 244 COMPLETE stay complete. Four were complete only from a filtered view, read in L10 (FILTERED_VIEW:
    the listing itself is still to read): Emergency Contraception, Celebrity Colognes, Allergy and Contact solution.
    One, Cough (976760_4661388_6244277_7158394), is INCOMPLETE: its reported total moved while L4r read it (351, 349,
    344), and L10's complete read of it was a filtered view.
  - Of the 203 PARTIAL, 199 stay partial; two were read only through a filtered view (First aid, Pain relief:
    FILTERED_VIEW), and two are filtered views of their row's own category (Personal Care "Clearance", Pets
    "Under $5": OUT_OF_SCOPE_FILTERED_ROW, closed, since the row's subcategories list their products).
  - Of the 9 RESULT_WINDOW, 8 stay; one was read only through a filtered view (Quit smoking: FILTERED_VIEW).
  - The 230 OUT_OF_SCOPE listings are now told apart: 95 are subcategory pages of their own (/cp/) that no run read,
    so their rows stay open (SUBCATEGORY_PAGE_NOT_READ); 35 are shop, brand, search, product or account pages
    (OUT_OF_SCOPE_NOT_A_CATEGORY); 6 are excluded by the client's CSV (OUT_OF_SCOPE_CSV); 1 is Household Essentials
    "Clearance", a filtered view of the row's own category (OUT_OF_SCOPE_FILTERED_ROW); and 93 are listings of their
    rows that the census did not choose to read: 57 NOT_ATTEMPTED, and 36 read by some run (13 COMPLETE, 14 PARTIAL,
    5 INCOMPLETE, 4 RESULT_WINDOW).
  - NOT_ATTEMPTED 407, INCOMPLETE 9, CATEGORY_PAGE 1 and NOT_FOUND 1 keep their state.

CSV rows complete: 0 of 11 (full_scope_complete: false). Every row has listings that are partial, not attempted or
not read; W4_ROWS_1_6_8.csv gives them by row.

What the rest would cost (CONTINUATION_ESTIMATE_1_6_8.json; at the documented rate of USD 0.0015 per result; each
part with its own basis, never added into one figure that hides an assumption):
  - the known listing pages (PARTIAL, INCOMPLETE read again, FILTERED_VIEW, NOT_ATTEMPTED): about 3,059 pages, USD
    4.63, about 5.0 active hours at L10's rate. NOT_ATTEMPTED and FILTERED_VIEW are estimates (the mean of the
    reached listings of the same row);
  - new branches: the 95 subcategory pages, USD 0.14 (a count); the listings they name, not known until they are
    read (USD 3.95, 11.86 or 23.72 if each page names 5, 15 or 30 new listings: an assumption); and the pages beyond
    the result window of 15 listings, USD 2.49, of which Special Kitty (60,000 reported) is 1,475 pages;
  - product pages, for the UPC and size the listing page does not state: USD 13.96 for the products known today
    (L12's 10,301 records: 9,307 own pages needed), and USD 75.48 to 152.93 for the products not yet seen; USD 89.44
    to 166.90 in all, about 60 to 112 active hours with two workers;
  - retries, measured in the 15 live runs: none on listing pages; 1.6% on product pages (USD 1.47 to 2.74).
  The USD 4.07 of 1.6.6 priced the known listing pages only. One later scheduled run, every listing page once, is
  estimated at USD 5.80 (3,828 listing pages; new branches excluded).

Names. A listing's name in these tables is the one the latest run that named it recorded, as in 1.6.6: listing
1115193_1071967_1630538 is "Fabric Softener" because L12 named it from its configured path. Release 1.6.8 names
carried and newly read records by the agreed mapping (the name the row's category page gives the view itself, its
first link): "Fabric Softeners" for that listing (../l12/).
