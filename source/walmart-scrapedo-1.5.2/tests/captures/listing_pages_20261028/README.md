# Authentic Strawberries pages of the two provider editions, replayed offline

The same listing, Strawberries (`976759_976793_9756351_3521037`, store #3891, Pickup), saved half an hour
apart on 2026-10-28 by the two phase B2 runs of release 1.4.0 on the user's Azure VM. They are the collector's
stored page copies (sanitized at capture: scripts other than the page data removed, identifiers in the page
data redacted), copied unchanged: the current sanitizer leaves them as stored. They are sanitized copies, not
byte-for-byte originals. `MANIFEST.json` gives each page's run, fetch id, URL, fetch time, the SHA-256 of the
stored copy and of the content kept here, and the SHA-256 of the raw answer kept privately with the run's
other raw answers.

| File | Run | What the page data shows |
|---|---|---|
| `strawberries_scrapedo_page1.html.gz` | `01M60ESB2201KQ56K9GRTMY0V7`, Scrape.do store endpoint (`storeid`, `zipcode`) | The store's unfiltered grid: 5 results reported and shown, 3 of them out of stock; the grid's `meta.fulfillmentIntent` is null, and the page's search request carried an empty `facet` |
| `strawberries_oxylabs_page1.html.gz` | `01M60GKSSDDC2FPGSE9F0NNGWH`, Oxylabs Web API (`store_id`, `fulfillment_type` pickup) | Walmart's Pickup grid: 2 results reported and shown; `meta.fulfillmentIntent` "Pickup", the page's own facet `fulfillment_method:Pickup` |

Release 1.4.1 requests the Scrape.do edition's result pages with Walmart's own facet
`fulfillment_method:Pickup` and records each grid's filter; `tests/unit/test_grid_filter.py` reads both
pages. The pages were copied by `add_capture_strawberries_141.py` (an operator tool, in the evidence package's `tools/`). They are
earlier captures, not new evidence: no test reaches Walmart or a provider.
