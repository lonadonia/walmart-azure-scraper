# Authentic Walmart pages, replayed offline

Captured from Walmart through Scrape.do's Walmart store endpoint (`storeid=3891`, `zipcode=60085`) on
2026-10-21 by run W1 (`01M5F0864ZTDB3GPHH85HK6EAK`) of the application this collector derives from, and
stored by that run after sanitization (session identifiers removed, product and store data untouched). Release 1.3.1 found that the earlier sanitizer kept Walmart's camelCase session keys (`isomorphicSessionId`, `adSessionId`) and the request trace IDs (`traceId`, `spanId`, `renderViewId`) in the page data; these copies went through the 1.3.1 sanitizer, which replaced those values with `[REDACTED]`; the
three pages' SHA-256 changed accordingly, nothing else in them did:

| File | Page | Fetch id |
|---|---|---|
| `robots.txt` | https://www.walmart.com/robots.txt | `01M5F08F6BVSQJ2BBDEMXXY7K0` |
| `store_page.html.gz` | https://www.walmart.com/store/3891-waukegan-il | `01M5F08GFQHJ7VPBA2RPZQX94M` |
| `diapering_page1.html.gz` | Diapering listing, result page 1 | `01M5F0KC63DT2N3T78QEBZAZWC` |
| `diapering_page2.html.gz` | Diapering listing, result page 2 | `01M5F0KJMNRWVDXYGZ3QQCZ4T0` |

`w1_exported_records.json` holds the records W1 exported for the products these two pages list as organic
results (Walmart's own `isSponsoredFlag` false; a product shown only as a sponsored tile here was recorded by W1
from another category's page). The records are W1's own export, unchanged.
`tests/integration/test_captures_replay.py` serves these pages through the Scrape.do mock and checks that this
collector exports the same products with the same values.

These are earlier captures, not new evidence: no test reaches Walmart or Scrape.do.
