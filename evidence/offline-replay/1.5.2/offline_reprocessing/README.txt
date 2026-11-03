OFFLINE REPLAY and OFFLINE REPROCESSING by release 1.5.2. Not a new collection: no request was made, and no page here
was fetched by release 1.5.2.

Revision: release 1.5.2, commit 627c804d66aa33fc423fd2296c8896c5d5c2c3d4. The delivered live files in live/ are unchanged and
stay the record of what the live runs exported. Nothing here replaces them.

What was read again
  S6    run 01M6A2VQAA5VXJHJHMZPCTZTD4 (Oxylabs Web API, store 3891, PICKUP, release 1.5.1, 2026-10-31), by replay
        01M6CBBKK60YBBVN6G7KVH2C9A. The campaign's nine runs were replayed in their original order on a new copy of the
        campaign's database and stored pages, so each run carries from the replay before it.
  B3    run 01M60V2DCCWR72BGVVG3EM9R74 (Oxylabs Web API, store 3891, PICKUP, release 1.4.1, 2026-10-28), by replay
        01M6CAYDES6RF52M6PCNY2V560, with the 1,441 saved product pages of ten earlier live runs imported first.
  Each row keeps its own observation: its time, its stored page and its crawl_date. A value from a product page names the run,
  page, time and revision that read it.

Files
  S6_products_fresh_OFFLINE_REPLAY.json, .csv            580 rows, byte for byte the replay's products_fresh export
  S6_products_retained_OFFLINE_REPLAY.json, .csv         706 rows, byte for byte the replay's products export
  S6_field_dispositions_OFFLINE_REPLAY.json, .csv        the UPC and size outcome of each of the 706 rows
  S6_CORRECTION_MAP.csv, S6_CORRECTION_SUMMARY.json      every difference from the delivered live S6 files, each with its class
  B3_products_fresh_OFFLINE_REPROCESSING.json, .csv      662 rows
  B3_products_retained_OFFLINE_REPROCESSING.json, .csv   862 rows
  B3_field_dispositions_OFFLINE_REPROCESSING.json, .csv  the outcome of each of the 862 rows
  B3_FIELD_DISPOSITIONS_662.csv, .json                   for each of the 662, the outcome before and after
  B3_CORRECTION_MAP.csv                                  every field that differs from the delivered 1.4.1 file
                                                         (deliverables/walmart_oxylabs/products_retained.json)
  B3_1_5_1_TO_1_5_2_CORRECTION_MAP.csv                   every difference from 1.5.1's replay of B3
  The maps of the other seven runs: WALMART_EVIDENCE_1.5.2.zip: 7_release_1_5_2/correction_maps/

How to read a correction map
  change_class says what kind of change a row is. store_brand_value, size_value and upc_value change an exported value. The
  others change only the explanation of an unchanged value: missing_kind_corrected, field_source_corrected, class_renamed and
  similar. Two kinds that every replay shows are counted in the summary and not listed: the replay's own read id of the same
  stored page, and a capture hash added where 1.5.0 left it empty.

What changed in S6 (compared with the delivered S6 files; 706 retained rows)
  store_brand   26 values, each no to yes, for brands confirmed in the USPTO's records (docs/PRIVATE_LABEL.md in the source)
  weight        6 values: the five carried rows below, and 13388557389
  upc           none
  No value was blanked. Titles, prices, PPM, URLs, images and dates are unchanged.

The five carried sizes
  S6 carried five Dry Dog Food rows with the size release 1.5.0 gave them. Run S3 observed them at 2026-10-31T21:33:20Z on page 4
  of the listing. (The 1.5.1 delivery index said S4: its own record_map.json says S3.) The observation is kept as it was: same
  run, time, page, title and date. Only the reading of the title changed, because a replay of S3 by 1.5.2 reads the pack beside
  the size.

    Item          As delivered in S6    Read by 1.5.2
    18472720019   30 lb                 2 pack, 30 lb
    18468708077   24 lbs                3 pack, 24 lbs
    18511760810   15 lbs                4 pack, 15 lbs
    20636621408   30 lbs                4 pack, 30 lbs
    18529653937   15 lbs                5 pack, 15 lbs

  13388557389, "(2 pack) Ol' Roy Natural Large Beef Femur Dog Chew ..., 1 Pack": "2 pack, 1 Pack" is now "2 pack".
  LINKED_EXAMPLES.csv links all six to their stored pages (E049 to E054).

What S6 says now (580 fresh rows)
  UPC     353 filled, 226 page not read, 1 absent from the page that was read. S6 fetched 1 of the 353 live and recovered 352 from
          saved pages. A replay fetches nothing, so its export calls all 353 recovered and names the run that read each page.
  Size    567 filled (555 from the listing, 12 recovered), 9 page not read, 3 absent, 1 conflict.
  A blank whose page was not read says not_attempted, never absent. The 226 and the 9 still need a live read.

What changed in B3
  Compared with the delivered 1.4.1 file (862 rows): upc filled 314; weight filled 35, changed 9; store_brand changed 24.
  Compared with 1.5.1's replay: store_brand 22, weight 1. UPCs of the 662: 419 filled, 243 blank (242 page not read, 1 absent).

The provenance correction
  In 1.5.1, provenance.json named the listing title as the source of a size recovered from a saved product page, while
  field_dispositions.json named the page. In 1.5.2 provenance.json, record_map.json and field_dispositions.json name the same
  capture, place in the response, time, product, run and revision. A separate check compared the three files with each other and
  with the stored bytes for every row of the nine replays and B3: 0 problems
  (WALMART_EVIDENCE_1.5.2.zip: 7_release_1_5_2/agreement/).

  The check found one more defect, fixed in 627c804: a row carried from a run that was itself a replay said the replay had observed
  it and fetched its product page. It now names the live run that fetched the page and the replay that read it again.

Repeat
  The nine replays were run twice on separate copies. The data files are identical once each replay's own run and fetch ids are
  numbered, and only the replay's own clock differs (WALMART_EVIDENCE_1.5.2.zip: 7_release_1_5_2/repeat_replay/A1_A2_COMPARISON.json).

What this does not show
  How release 1.5.2 behaves on Walmart's pages today, or anything about products no stored page holds. TEST_PLAN.md gives the next
  live step.
