# An authentic listing page of live run L7, replayed offline

One result page saved by run `01M6K7HT3XVV8R8CX79P31KMB4` (stage L7, the census on release 1.6.3, Oxylabs Web API,
store #3891 Pickup) on 2026-11-04. It is the collector's stored copy of the page, byte for byte (sanitized at
capture by release 1.6.3: scripts other than the page data removed, session, trace and key values in the page data
replaced with `[REDACTED]`); it is not the raw answer. `MANIFEST.json` gives its fetch id, URL, fetch time, the
SHA-256 of the stored copy and of its content, and the SHA-256 of the raw answer kept privately with the run's
other raw answers.

| File | Listing | What the page data shows |
|---|---|---|
| `bidets_page1.html.gz` | Bidets, `1072864_1045879_5533759_6108305`, a link of the Household Essentials category page | `aggregatedCount` 0 and an empty result grid (stack 0, "Results for \"bidets\"", count 0, fulfillment Pickup, named the results by `primaryStacksToMatch`), next to an "Available for shipping" carousel (stack 1, fulfillment Shipping) with 10 products of its 838; `searchResult.count` 10 (the carousel's products), `maxPage` 0; the page location names store 3891, ZIP 60085 and PICKUP. Release 1.6.3 read the listing's total as `aggregatedCount or count`, took the 0 for a missing value and the 10 for the total, and stopped the run: "the page reports results but shows no product" (ABNORMAL_RESULT, store held). Release 1.6.4 reads the 0 |

`tests/unit/test_empty_pickup_grid.py` reads it with the 1.6.4 parser. It is an earlier capture, not new
evidence: no test reaches Walmart or a provider.
