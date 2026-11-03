# Payload matrix (what a future approved campaign could send)

This is the output of `classic-probe plan --targets config/targets.json`, which sends nothing and writes nothing, set out with the checks each response must pass.

Every payload is checked against the documented contract before it can be planned (`contract.assert_documented`; [DOCUMENTED_CONTRACT.md](DOCUMENTED_CONTRACT.md)). Nothing here has been sent: this build's live mode is disabled.

## Walmart: store 3891 (Waukegan), Pickup

| # | Step | Sent when | Request | Most billable results | Goes on only if the response shows |
| --- | --- | --- | --- | --- | --- |
| 1 | `walmart-search-p1` | always first | `POST https://realtime.oxylabs.io/v1/queries?type=raw,parsed` with `{"source": "walmart_search", "query": "milk", "store_id": "3891", "fulfillment_type": "pickup", "parse": true}` | 2 | HTTP 200 and a retailer 2xx. A raw page with Walmart's page data and no challenge. `pageMetadata.location` is store 3891 with intent PICKUP. The parsed `location.store_id` is 3891 or absent. `parse_status_code` is 12000, 12004 or 12005. The page holds products, and the parsed products are all on the page |
| 2 | `walmart-search-p2` | only if step 1's `page_details.last_visible_page` ≥ 2 | the same with `"start_page": 2` | 2 | The same as step 1. Also, the parsed `page_details.page` and the page data's own page are both 2, and the page holds a product that page 1 did not |
| 3 | `walmart-product` | only if page 1 holds a non-sponsored Walmart.com product with a Pickup line | `{"source": "walmart_product", "product_id": "<that product>", "store_id": "3891", "fulfillment_type": "pickup", "parse": true}` with `?type=raw,parsed` | 2 | HTTP 200 and a retailer 2xx. No challenge. `initialData.data.product.usItemId` is the requested item, and the parsed URL's item agrees. `product.location` is store 3891 with intent PICKUP. The parsed store is 3891 or absent. The UPC is read as the collector reads it |
| 4 | `walmart-category-url` | last, only if steps 1 to 3 went on | `POST https://realtime.oxylabs.io/v1/queries` with `{"url": "https://www.walmart.com/browse/food/fresh-fruits/976759_976793_9756351"}` | 1 | HTTP 200 and a retailer 2xx. No challenge. The page's own `pageMetadata.location` is store 3891 with intent PICKUP. No store parameter is documented for this form |

Anything else stops the campaign at that response, and nothing more is sent:

- the retailer refuses;
- the context is wrong or missing;
- the product page is another item's;
- page 2 does not advance or is empty;
- the response is outside the documented structure;
- the parser status is a failure;
- the account answers HTTP 400, 401, 403 or 422;
- a limit is reached;
- a request is unanswered at its deadline.

The [README](../README.md) lists the stop codes.

## Upper bounds

| | Bound | Where it is enforced |
| --- | --- | --- |
| Dispatches for Walmart | 4 steps × at most 2 attempts (one retry, only for a documented temporary error) = **8 of its 10** | `Campaign.max_attempts`. The ledger refuses an 11th whatever the code above it does |
| Setup, authentication, qualification calls | **none**: the probe makes no automatic call of any kind | there is no code that makes one. Any future one would be reserved like any request |
| Dispatches for Mariano's | **0**: no adapter. Its 10 stay reserved | `Target.live_problems`. The ledger keeps its share |
| Reserved charge per dispatch | the higher of the confirmed plain and rendered rate × the most billable results (2, 2, 2, 1) | `RateCard.worst_case`. It is reserved before sending and kept until a confirmed charge replaces it |
| Walmart's worst case | (2 + 2 + 2 + 1) × 2 attempts = 14 results × the highest confirmed rate | the dispatch that would pass Walmart's USD 2.25 share is not reserved (`STOP_RETAILER_FUNDS`) |
| Time | 8 × 120 s request timeout + at most 4 retry waits of ≤ 5 s ≈ 16.3 minutes, within the campaign's 27 minutes (30 less 3 kept for export and cleanup) | each reservation must end before the export's reserve starts (`STOP_DEADLINE`) |

These bounds can be stated only as formulas: no rate ships with the probe. With a confirmed rate card, `plan --rates FILE` prints each step's reserved amount in dollars.
