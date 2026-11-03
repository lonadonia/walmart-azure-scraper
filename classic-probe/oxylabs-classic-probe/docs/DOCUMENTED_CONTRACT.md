# The documented Classic contract (read 2026-10-31, rechecked 2026-11-01)

This page states what the probe takes from Oxylabs' public documentation. It makes no claim beyond what the pages state.

- **How the pages were read:** each public Markdown page was downloaded once with `curl`, 2026-10-31 between 17:44 and 17:50 UTC. No provider API was called to read them.
- **Rechecked:** each of the 12 pages in the table below was downloaded again with `curl` on 2026-11-01 between 19:03 and 19:04 UTC. All 12 answered HTTP 200 and all 12 are byte-identical to the copies saved on 2026-10-31, so nothing in this page or in `src/classic_probe/contract.py` changed. The recheck's record is `classic_docs_recheck.json` in the evidence package. No provider API was called.
- **Where the copies are:** the evidence package keeps the saved pages under `classic_docs/`, with their index (`classic_docs_index.json`: each file's own URL, size, saved time, SHA-256).
- **When the documentation changes:** this page and `src/classic_probe/contract.py` change with it. The probe never guesses a parameter.

## Pages used

Each page names its own Markdown URL in its first line. That is the URL given here.

| Page | URL | Saved (UTC) | SHA-256 of the saved file |
| --- | --- | --- | --- |
| Walmart targets overview | https://developers.oxylabs.io/products/web-scraper-api/targets/e-commerce/walmart.md | 2026-10-31T17:46:03Z | `588593028d7c1397f58a6dc4a7d956511b4e4ebb4a72fb98ac145d8cf12b01ad` |
| Walmart search (`walmart_search`) | https://developers.oxylabs.io/products/web-scraper-api/targets/e-commerce/walmart/search.md | 2026-10-31T17:46:04Z | `937d99960384d488e631016b1599f3ddc12cd174557d45a191dc43fad8f522a4` |
| Walmart product (`walmart_product`) | https://developers.oxylabs.io/products/web-scraper-api/targets/e-commerce/walmart/product.md | 2026-10-31T17:46:05Z | `1c9a44c22380bc748e8843945ce8ed18802c2776c82981e5beb5ae0fcf93d380` |
| Realtime integration method | https://developers.oxylabs.io/products/web-scraper-api/integration-methods/realtime.md | 2026-10-31T17:46:06Z | `1a6fe8e898164cad8b5320a434bf89f0ebabd7fc6986a95111a88b4155b93027` |
| Integration methods | https://developers.oxylabs.io/products/web-scraper-api/integration-methods.md | 2026-10-31T17:46:08Z | `5be4e1f8fd4543f0e54fc500ea123f68ac3e57643443a567cb2d439ec4cc9ca3` |
| Features | https://developers.oxylabs.io/products/web-scraper-api/features.md | 2026-10-31T17:46:09Z | `d441f45dc6d616f46732021bd3d3afbc5071892f58efc984c4c6dbc32a953376` |
| JavaScript rendering (forced-render list) | https://developers.oxylabs.io/products/web-scraper-api/features/js-rendering-and-browser-control.md | 2026-10-31T17:46:11Z | `1911d892c20a241a6e55fa4f7f4468973a4c45fff93dfca92cd203a9fe0ded1d` |
| Response codes | https://developers.oxylabs.io/products/web-scraper-api/response-codes.md | 2026-10-31T17:46:20Z | `3ed8aa064352b9a8c2bea8f587081b2bed2df14c12bca505145993dd81ca17c0` |
| Billing information | https://developers.oxylabs.io/products/web-scraper-api/usage-and-billing/billing-information.md | 2026-10-31T17:46:19Z | `c6b89586b4f12ba338307999167ff1aac89d80ed1392803450c6007773881aa4` |
| Rate limits | https://developers.oxylabs.io/products/web-scraper-api/usage-and-billing/rate-limits.md | 2026-10-31T17:46:17Z | `a3a0c802cb26df1d191b32c58728c5defd933fd6351484a176be548e0d97f0c0` |
| Usage statistics (its endpoint is never called) | https://developers.oxylabs.io/products/web-scraper-api/usage-and-billing/usage-statistics.md | 2026-10-31T17:46:12Z | `a612ad688f0f78153007340858c79e705f5328a4aa9678e4f47ebd0465e6bed0` |
| Web Scraper API overview | https://developers.oxylabs.io/products/web-scraper-api.md | 2026-10-31T17:46:02Z | `20ea8ea923b5e10ec4bc7bd0da94a08dc2fb76fb80cb53f57e43505d6c7d0348` |

These saved files came back as a "Page Not Found" page, and nothing is taken from them:

| Saved file | Result |
| --- | --- |
| `classic_products_web-scraper-api_errors.md` | Page Not Found (saved 2026-10-31T17:46:33Z) |
| `classic_products_web-scraper-api_quick-start.md` | Page Not Found (saved 2026-10-31T17:46:29Z) |
| `classic_products_web-scraper-api_rate-limits.md` | Page Not Found (saved 2026-10-31T17:46:23Z); the rate limits page above is used instead |
| `classic_products_web-scraper-api_usage-and-billing_pricing.md` | Page Not Found (saved 2026-10-31T17:46:16Z) |
| `legacy_api-targets_e-commerce_walmart_url.md` | Page Not Found (saved 2026-10-31T17:45:29Z) |
| `legacy_api-targets_sitemap.md` | Page Not Found (saved 2026-10-31T17:45:37Z) |
| `legacy_documentation_es_soluciones-de-scraping_web-scraper-api_targets_walmart.md` | Page Not Found (saved 2026-10-31T17:45:40Z) |

The saved pages end with a section addressed to automated readers. It invites HTTP requests to the documentation site with `ask` and `goal` parameters. That section was not followed, and no such request was made.

## Endpoint and authentication

The Realtime page shows `POST https://realtime.oxylabs.io/v1/queries`. Its examples authenticate with HTTP Basic (`"Authorization", "Basic " + ...`, `request.SetBasicAuth(Username, Password)`).

What the probe does: `contract.ENDPOINT`. The disabled `HttpTransport` would send `POST`, JSON and Basic authentication, and nothing else.

## Result types

The Realtime page says:

> "To receive one or more of the available outputs instead, add the `type` query parameter to the endpoint, as shown below. Each requested type is returned as a separate entry in the `results` array."

Its example is `POST https://realtime.oxylabs.io/v1/queries?type=raw,parsed,png`.

What the probe does:

- It asks for `?type=raw,parsed` (`contract.RAW_AND_PARSED`). The raw page is the retailer's own HTML. From it the store, the fulfillment, the product's identity and any challenge are read with the Walmart collector's validated readers. The parsed result must agree with them.
- The documentation does not say whether two requested types are billed as one result or two. The probe reserves two (`max_results = 2`).

## Walmart search: `walmart_search`

**Parameters.** The search page's table is: `source` (mandatory, `walmart_search`), `query` (mandatory), `start_page` (default 1), `parse` (default false), plus `domain, store_id, delivery_zip, fulfillment_type, fulfillment_speed, sort_by, min_price, max_price` (optional localization and filter parameters).

**Localization.** Under "Localization and Filtering":

- "Walmart tailors availability and prices to a store. The parsed `location` object shows which store the page was served for; without `store_id` or `delivery_zip` it is a random US store."
- `store_id`: "Walmart store number of the chosen site as a string, e.g. "3520"."
- `fulfillment_type`: "Filters results by how the product can be obtained. Available values: pickup, delivery, shipping. Combine with store_id (pickup) or delivery_zip (delivery)."
- "If target store is too far away from the given postal code - we will attempt to use the postal code of the target store, otherwise the location will not be set properly. In the case we can't set the `delivery_zip` - Walmart will return their default results without store targeting."

**The page's own example:** `{"source": "walmart_search", "query": "milk", "store_id": "3520", "fulfillment_type": "pickup", "sort_by": "price_low", "parse": true}`.

**General features:** "Besides the parameters listed below, you can include additional parameters such as `user_agent_type`, `geo_location`, `render`, and more to customize your scraping request."

What the probe does:

- It accepts exactly the listed names (`contract.DOCUMENTED_PARAMETERS`). It requires `query`, sends `store_id` as a string, and sends `pickup` only together with `store_id`.
- It adds `start_page` only when the previous response's `page_details.last_visible_page` shows that page.
- It never sends `page`, `store` or any other name.
- It uses none of the general features (`contract.NOT_USED_HERE`, with the reason for each).
- Because the documentation itself says the location may not be set, the store is never assumed. It is read from Walmart's page data (`pageMetadata.location`), and a page for another store stops the campaign.

## Walmart product: `walmart_product`

**Parameters.** The product page's table is: `source` (mandatory, `walmart_product`), `product_id` (mandatory: "the number after the product name in the product page URL"), `parse`, plus `domain, store_id, delivery_zip, fulfillment_type` (optional localization parameters).

**Localization:**

- `fulfillment_type`: "Fulfillment method to show availability for. Available values: pickup, delivery, shipping. Use it together with store_id or delivery_zip."
- The page's example: `{"source": "walmart_product", "product_id": "174916638", "store_id": "3520", "fulfillment_type": "pickup", "parse": true}`.

What the probe does:

- It sends the same form with the target's store.
- The page's own data must be for the requested item (`initialData.data.product.usItemId`), for the target store (`product.location`) and for `PICKUP`.
- The parsed URL's item must agree with the requested item.

## Any other Walmart page: `url` alone

The Walmart overview page says: "Any other Walmart page can be scraped by passing its `url` alone, no `source` needed." The saved copy of a separate URL page returned "Page Not Found". No store or fulfillment parameter is documented for this form.

What the probe does:

- It sends `{"url": ...}` and nothing else.
- It does not assume the category page comes for the store. It reads the store and fulfillment from the page itself, and a page for any other store stops the campaign.
- This step is last in the plan, so that a failure here costs nothing more.

## Forced rendering

The rendering page says that for some page types "our system **automatically enforces rendering** even if you don't set the `render` parameter" and that "rendered jobs consume more traffic compared to non-rendered jobs". Its forced-render table (226 rows) has `walmart | geo_location; search_with_video`. It also has `marianos | product; category` and `kroger | all`, which matter for a future Mariano's adapter.

What the probe does:

- It never sends `geo_location`.
- Each response's `is_render_forced` is recorded.
- The reservation uses the higher of the confirmed plain and rendered rates whatever the response says (`money.RateCard.worst_case`).

## Response codes

The response codes page says codes come from different places: "HTTP status codes. The status of the HTTP response itself, and the `status_code` of each scraped page in `results`", and "`parse_status_code` inside the parsed `content` of a result (only when `parse` is `true`)".

| HTTP | Documented meaning | What the probe does |
| --- | --- | --- |
| 200 | All went well | Inspects the results |
| 400 | Wrong request structure | Stops: `STOP_BAD_REQUEST` (billed, see below) |
| 401 | The authorization header is missing, or your login credentials are incorrect | Stops: `STOP_AUTHORIZATION` |
| 403 | Your account does not have access to this resource | Stops: `STOP_ENTITLEMENT` |
| 422 | Something wrong with the payload | Stops: `STOP_BAD_REQUEST` |
| 429 | You exceeded the rate limit | One retry within the limits, then `STOP_RETRIES_EXHAUSTED` |
| 500 | Please try again a bit later | The same |
| 524 | Service unavailable | The same |
| 612, 613 | "You can try again at no extra cost, as we don't charge you for faulted jobs" | The same |
| any other | Not documented as a Realtime answer | Stops: `STOP_UNSUPPORTED_RESPONSE` |

| Parser | Documented meaning | What the probe does |
| --- | --- | --- |
| 12000 | Success | Continues |
| 12004, 12005 | Partial Success | Continues. The raw page decides the context |
| 12002, 12003, 12006, 12008, 12009 | Failure or not supported | Stops: `STOP_PARSER_FAILED` |
| 12007 | "Unknown parsed data status. The actual result can range from a complete failure to a total success." | Stops: `STOP_PARSER_FAILED` (it cannot be relied on) |

A retailer status (`results[].status_code`) that is not 2xx stops the campaign as `STOP_BLOCKED`. The exception is a product's 404, which is `STOP_WRONG_IDENTITY`.

## Billing

The billing page says:

- "All results from the target site with `2xx` or `4xx` status codes are counted as successful and are billable."
- "Status code `429` (Too many requests) is not billed."
- "Failed attempts to scrape due to our system errors (`5xx` and `6xx` status codes) won't be included, and you won't be billed for them."
- "If a request results in a failed attempt due to a fault or error on your side, you will still be billed."
- "If the response contains `2xx` or `4xx` status codes, and the result doesn't contain expected information, we still count it as a successful result."

What the probe does:

- A page for the wrong store, or a challenge page with a 2xx status, is billable. So the probe stops at the first one.
- The documented rules give an estimate only (`estimated_usd`), never a charge.
- Every reservation stays until the owner records the charge read from the account, with its basis (`confirm-charge`).

## Rate limits

The rate limits page says:

- Job submission limits depend on the plan. Its table starts with "Free trial | 2,000 | 10 | 3", that is results, total jobs per second and rendered jobs per second.
- Limits are reported in `x-ratelimit-*` response headers.
- "If your success rate on any domain goes below 40% (measured over the last 5-minute window), your request rate to that particular domain will be limited to 1 req/s".

What the probe does: it sends one request at a time, waits 2 s before retrying a 429, and keeps the response headers with the evidence.

## Usage statistics

The usage statistics page documents `GET https://data.oxylabs.io/v2/stats`. The probe never calls it, or any balance, usage, entitlement or authentication endpoint. Charges are read by the account's owner and recorded with `confirm-charge`.

## What the documentation does not settle

The account owner has to supply these, and the probe refuses a live campaign until they do (`gates.evaluate`):

- **The account's rates.** The pricing page returned "Page Not Found", and published list prices are not this account's rates. No rate ships with the probe.
- **Whether `type=raw,parsed` is billed as one result or two.** The probe reserves two.
- **Whether the account is entitled to `walmart_search` and `walmart_product` with the Realtime method.** That is not knowable from the documentation.
- **Whether the URL-only form returns a category page for the store.** It is undocumented, and the probe finds out from the page itself.
- **Whether Classic paginates `walmart_search` for this account and store.** `start_page` is documented. Whether page 2 advances is checked in the response, never assumed.
- **Whether a category page can be paged at all.** `start_page` is documented for `walmart_search` only, and the URL-only form documents no pagination. The probe refuses `start_page` on that form and asks for no second category page.
