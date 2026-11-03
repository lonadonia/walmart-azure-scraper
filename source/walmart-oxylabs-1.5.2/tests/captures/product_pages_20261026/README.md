# Authentic product pages of the Azure run, replayed offline

Four product pages read by run `01M5X364ZR83MZ9M60QGPFR7TX` (release 1.3.0 on the user's Azure VM,
Oxylabs Web API, store #3891 Pickup) on 2026-10-26, three by its follow-ups and one (added in release 1.3.1)
by the UPC read of an exported product: the collector's stored page copies
(sanitized at capture: scripts other than the page data removed, identifiers in the page data redacted),
recompressed here. Release 1.3.1 found that the earlier sanitizer kept Walmart's camelCase session keys
(`isomorphicSessionId`, `adSessionId`) and the request trace IDs (`traceId`, `spanId`, `renderViewId`); these
copies went through the 1.3.1 sanitizer, which replaced those values with `[REDACTED]` (`MANIFEST.json`:
`resanitized_1_3_1`). They are sanitized copies, not byte-for-byte originals. `MANIFEST.json` gives each
page's fetch id, URL, fetch time, the SHA-256 of the stored copy and of the content kept here, the SHA-256 of
the raw answer kept privately with the run's other raw answers, and the run's 1.3.0 follow-up outcome.

| File | Item | What the page data shows |
|---|---|---|
| `walmart_seller_15268670678.html.gz` | Spice World Fresh Peeled Ginger 7oz (sponsored only in the run of 2026-10-24) | sold by Walmart.com (`sellerDisplayName`, `sellerType` INTERNAL), `offerType` ONLINE_AND_STORE, a Pickup line for store 3891 (`fulfillmentSummary`), Pickup in stock at Waukegan Supercenter |
| `marketplace_15163163334.html.gz` | Del Monte Golden Sweet Whole Kernel Corn, a variant sibling | sold by DealZone Inc (`sellerDisplayName`, `sellerType` EXTERNAL), `offerType` ONLINE_ONLY, Pickup NOT_AVAILABLE at Waukegan Supercenter, shipping only. Product pages name the seller in `sellerDisplayName`, never in `sellerName`; release 1.3.0 read `sellerName` only and never recognised a marketplace seller on a product page |
| `out_of_stock_994998279.html.gz` | Fresh Red Mango, Each (sponsored only in the run of 2026-10-24) | sold by Walmart.com, out of stock everywhere: no `fulfillmentSummary` line for the store; the Pickup option names Waukegan Supercenter (by name, without a store id) as OUT_OF_STOCK. The store's assortment is not established from this page alone |
| `each_estimated_12852163028.html.gz` | Fresh Pears Bartlett Bulk, Each (an exported product of the run; added in release 1.3.1) | the price shown as "each (est.)" (`priceDisplayCodes.priceDisplayCondition`): $0.77, was $1.02, $1.72/lb; `priceDisplayCodes.finalCostByWeight` true, `salesUnit` EACH_WEIGHT; the specifications "Average sold by weight" and "Maximum sold by weight", 0.6 Pounds. Its result tile stated neither code (sales unit EACH_WEIGHT and a value-less `SOLD_BY_WEIGHT` price line only), so release 1.3.0 exported the estimate as a fixed price |

`tests/unit/test_product_page_offers.py` and `tests/unit/test_weight_priced.py` read these pages with the
1.3.1 parser. They are earlier captures, not new evidence: no test reaches Walmart or a provider. The pear's
page was copied by `add_capture_each_est_131.py` (an operator tool, in the evidence package's `tools/`) through the 1.3.1 sanitizer.
