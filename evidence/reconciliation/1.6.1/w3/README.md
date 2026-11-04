# W3: the 275 queued products and the client's 41 cases, decided live

Release 1.5.2 left 275 products whose own page had to be read before they could be included or excluded: 250 variant
siblings and 25 tile-only variant siblings (`EXACT_LIVE_READ_QUEUE_1_5_2.csv` of the 1.5.2 publication). This
delivery read each one's own page live, for store 3891 Pickup, and decided it.

| File | What it holds |
|---|---|
| [`W3_DECISIONS_1_6_1.csv`](W3_DECISIONS_1_6_1.csv) | one row per queued product (275): the decision, the reason, the run and page fetch that decided it, the HTTP status, the stored page's SHA-256, the store context and category evidence the page showed, the record's status and UPC |
| [`W3_CLIENT_CASES_1_6_1.csv`](W3_CLIENT_CASES_1_6_1.csv) | the 41 cases the client named (S01 to S11 sponsored-only, T01 to T30 tile-only siblings): each case's state in 1.5.2 and its decision now |
| [`W3_SUMMARY_1_6_1.json`](W3_SUMMARY_1_6_1.json) | the counts, computed from the two tables |

## Result (LIVE VERIFIED)

All 275 are decided: **48 included, 224 excluded, 3 duplicates**. None is left open.

| Decided by | Run | Release | Products |
|---|---|---|---|
| L2 | `01M6H72J86K5TF7A1874N7BJ2R` | 1.6.0 | 176 |
| L2b | `01M6HAXEP6495EGWT91JQS09SS` | 1.6.1 | 98 |
| L3 | `01M6HA74X4QYMW45SVD62JQDSQ` | 1.6.1 | 1 |

The exclusions have two reasons, each stated by the product's own page:

- 169: the page files the product under another category than the listing's ("required category not established");
- 55: the page shows no eligible local offer or assortment for the store (its `LOCATION` state).

An included product is a valid record of its run, with its own UPC from its page. A duplicate is the same identity as
a product already recorded.

## The client's 41 cases

- The 11 sponsored-only cases (S01 to S11) and 5 of the tile-only cases were already decided by a live read before
  1.5.2 and were not in the 1.5.2 queue; their earlier decision and its run are in the table.
- The other 25 tile-only cases were read in this delivery: 24 excluded and 1 included.

## Limits

A decision holds for the time its page was read (2026-11-03). A later run reads the store again and may decide a
product differently if Walmart changes its category or its local offer. The pages behind the decisions are in the run
evidence of L2, L2b and L3 (`evidence/live/1.6.x/runs/`), sanitized, with the SHA-256 of the private original of each.
