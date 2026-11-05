# Authentic listing pages of the Azure run, replayed offline

Four result pages saved by run `01M5X364ZR83MZ9M60QGPFR7TX` (release 1.3.0 on the user's Azure VM,
Oxylabs Web API, store #3891 Pickup) on 2026-10-26. They are the collector's stored page copies
(sanitized at capture: scripts other than the page data removed, identifiers in the page data redacted),
recompressed here. Release 1.3.1 found that the earlier sanitizer kept Walmart's camelCase session keys (`isomorphicSessionId`, `adSessionId`) and the request trace IDs (`traceId`, `spanId`, `renderViewId`) in the page data; these copies went through the 1.3.1 sanitizer, which replaced those values with `[REDACTED]` (`MANIFEST.json`: `resanitized_1_3_1`, with the
content SHA-256 before that step). They are sanitized copies, not byte-for-byte originals. `MANIFEST.json`
gives each page's fetch id, URL, fetch time, the SHA-256 of the stored copy and of the content kept here, and
the SHA-256 of the raw answer kept privately with the run's other raw answers.

| File | Listing | What the page data shows |
|---|---|---|
| `citrus_page1.html.gz` | Citrus, `976759_976793_9756351_4914029` | 21 results in the result grid (stack 0), and an "Available for shipping" carousel (stack 1) with 7 more products; 21 results reported. Release 1.3.0 read both stacks: 28 "organic" products for 21 reported, an overcount it took for completion |
| `apples_page1.html.gz` | Apples, `976759_976793_9756351_7796396` | 39 products in the result grid, 6 of them sponsored placements; 39 results reported, one page. Release 1.3.0 counted the 33 organic products only and recorded the listing as a result-window end |
| `bath_body_page1.html.gz` | Bath & Body, `1005862_1071969` (added in release 1.3.1) | The product 625527254 (eos body lotion) appears twice in the result grid; the first tile names no options, the second names its 2-pack (15357773865) and 3-pack (15349802259), neither of them a tile of its own. Release 1.3.0 kept the options of the first tile only and never followed the two |
| `fresh_vegetables_page1.html.gz` | Fresh Vegetables, `976759_976793_8910423` (added in release 1.4.0) | Page 1 of 7 (284 results reported, 45 products in the result grid, 5 of them sponsored). 10 tiles are charged by weight: 9 state the price as an estimate ("each (est.)" next to the price); the jalapeños (44391018) show their price for a stated weight ("$0.25 / 0.14lb") with no estimate wording. Release 1.4.0 excludes the 9 for the estimated-weight wording and keeps 44391018 |

`tests/unit/test_listing_reconciliation.py` reads the first three pages with the 1.3.1 parser and completion
rule; `tests/unit/test_weight_priced.py` reads the Apples and Fresh Vegetables pages with the 1.4.0 weight
rule.
The Bath & Body page was copied in release 1.3.1 by `add_capture_bath_body_131.py` (an operator tool, in the
evidence package's `tools/`) through the 1.3.1 sanitizer; the Fresh Vegetables page in release 1.4.0 by
`add_capture_vegetables_140.py`, the same steps for its fetch.
They are earlier captures, not new evidence: no test reaches Walmart or a provider.
