The regressions of release 1.5.1, run against the frozen 1.5.0 source and against 1.5.1
Class: OFFLINE VERIFIED. Unit tests and PostgreSQL integration tests (pgserver, a temporary local database). No provider request:
HTTP(S) was sent to a closed local port and no provider key, database URL or collector setting of the workstation was set.

What ran (commands.csv, with each step's exit code, start time and duration):
  before_1_5_0/  `git archive` of 7b6f3258e0f4ab755732605eb88717c592d07073 (release 1.5.0, the revision of the live stages S1 to S5),
                 with the four test files of 1.5.1 laid over it and nothing else changed:
                   tests/unit/test_pack_size.py, tests/unit/test_private_label.py, tests/unit/test_walmart.py,
                   tests/integration/test_detail_path.py
  after_1_5_1/   `git archive` of 488a033fc22d09db9f6270feae274d8c77963d6f (release 1.5.1, the revision of S6 and S7), unchanged.
  Each was installed with `uv sync --frozen --offline` from its own lock; version.txt shows the version and the folder it imported from.
  pytest.txt is the full output, junit.xml the per-test record (host name replaced with "(workstation)").

Result (SUMMARY.json, per test in REGRESSIONS_BEFORE_AND_AFTER.csv):
  on 1.5.1: 182 passed.
  on 1.5.0: 29 failed, 153 passed:
    - 28 of the 42 test cases new in 1.5.1 fail: the defects 1.5.1 corrects.
        test_walmart: a multipack lost when the size is in a comma segment (test_a_multipack_outside_the_size_segment_stays_beside_the_size,
          and three cases of test_the_limits_of_keeping_a_multipack_beside_the_size); what a title says about the product taken as the size
          of its package: loads, a dose strength, a weight limit ("Holds Up to 300 lbs", "Up to 50 Pounds"), a dimension
          (test_what_a_title_says_about_the_product_is_not_the_size_of_its_package);
        test_pack_size: a pack the title states, explaining a larger size on the product page;
        test_private_label: store_brand after a bracketed multipack, and the wordings "Organic Marketside" and "Children's Equate";
        test_detail_path: a pilot's page budget that stopped the reuse of pages already saved
          (test_a_page_budget_never_stops_what_earlier_reads_already_established).
    - 14 new cases pass on 1.5.0, as they should: they are limits that pin what the correction must leave unchanged (for example
      "Example 1-Pack Soap, 12 oz" stays "12 oz", "Example Ibuprofen Tablets, 200 mg" stays "200 mg", a title that only mentions a listed
      brand further along stays store_brand "no").
    - 1 existing case fails on 1.5.0 because 1.5.1 changed its expectation deliberately: "(6 pack) StarKist Chicken Creations ... 2.6 oz
      Pouch" is "6 pack, 2.6 oz Pouch" in 1.5.1 (the pack is kept beside the size), "10g Protein, 2.6 oz Pouch" in 1.5.0.

Tool: tools/delivery151/regressions_before_after_151.py (in this ZIP).
