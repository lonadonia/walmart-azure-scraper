# W3: the 275 sponsored and variant decisions, recounted (the probe 1.7.4 revision)

RECONCILIATION, offline: no request was made for this recount. It reads the row-level table published with the 1.6.8
delivery and changes nothing in it.

**Why.** The 1.6.8 publication counted 224 of the 275 queued products as excluded and gave "0 failed, blocked or
unresolved". For 59 of them no source evidence supports exclusion. 4 have a page that gives no category path
(`categoryPathId` -1, no breadcrumb). 55 have a page that does not prove local eligibility
(`LOCATION_UNATTESTED` and `ASSORTMENT_UNRESOLVED`; 14 of them also show a marketplace offer, which does not show the
product absent from the store). Missing evidence leaves a product unresolved. A product is excluded only on
affirmative source evidence: here, the item's own page placing it in another category, which is named.

**Result** (from [`W3_275_RECOUNT_SUMMARY.json`](W3_275_RECOUNT_SUMMARY.json)):

| Outcome | Products | 1.6.8's label for them |
|---|---:|---|
| included | 48 | included |
| excluded: its own page places it in another category, named in `other_branch` | 165 | `excluded_alternative_category` |
| duplicate, linked to the original observation | 3 | duplicate |
| **unresolved**: its page gives no category path | 4 | `excluded_category_path_missing` |
| **unresolved**: its page does not prove local eligibility | 55 | `excluded_local_eligibility_not_proven` |
| total | 275 | |

- The client's variant cases in the queue (25 of the 30; the other 5 were closed before 1.5.2): 1 included, 17
  excluded on another category, and 7 unresolved: V25, V27, V28 and V30 (no category path), and V22, V26 and V29 (local
  eligibility not proven).
- **Separate:** the 44 products whose UPC has no read are a different queue (W2), not part of these 275, and unchanged.
- **What settles the 59:** their own pages read again with the store's context. That is a paid request for each (59
  pages, about USD 0.09 at the documented rate before retries). None was made. Until then they stay unresolved:
  BLOCKED_BUDGET in the acceptance matrix's `*_1_6_8_probe_1_7_4` columns.
- **Unchanged:** the live reads (L2, L3 and L2b, on 1.6.0 and 1.6.1), their stored pages, and the published
  [`W3_ROW_LEVEL_1_6_7.csv`](../../1.6.8/w3/W3_ROW_LEVEL_1_6_7.csv) and
  [`W3_ROW_LEVEL_SUMMARY_1_6_7.json`](../../1.6.8/w3/W3_ROW_LEVEL_SUMMARY_1_6_7.json). Collector 1.6.8 still labels these
  products `excluded_*` in its own records. This revision changes no collector code. Naming them unresolved in the
  collector itself is open for a later release.

## Files

| File | What it is |
|---|---|
| [`W3_275_RECOUNT.csv`](W3_275_RECOUNT.csv) | one row per product: its 1.6.8 class, its outcome here, the basis (affirmative or missing evidence), the other category if named, the page's category path, the record's reasons, the run and the stored page's SHA-256 |
| [`W3_275_RECOUNT_SUMMARY.json`](W3_275_RECOUNT_SUMMARY.json) | the counts, the rule, and the source's SHA-256 |
| [`recount_w3_174.py`](recount_w3_174.py) | the recount (Python 3 standard library). It checks the source's SHA-256 first |

## Check it

From the root of a clone:

```
python3 -I evidence/reconciliation/1.6.8-probe174/w3/recount_w3_174.py
```

It recounts from the published 1.6.8 rows, compares the result with the two files here byte for byte, and ends with
`PASS`.
