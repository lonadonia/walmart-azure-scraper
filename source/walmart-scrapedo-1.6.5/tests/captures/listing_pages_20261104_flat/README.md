# Two authentic listing pages of live run L10, replayed offline

Two result pages saved by run `01M6KA3CKYJSD6WDY4TDAAV73Y` (stage L10, the census on release 1.6.4, Oxylabs Web
API, store #3891 Pickup) on 2026-11-04. Each is the collector's stored copy of the page, byte for byte (sanitized
at capture by release 1.6.4: scripts other than the page data removed, session, trace and key values in the page
data replaced with `[REDACTED]`); it is not the raw answer. `MANIFEST.json` gives each page's fetch id, URL, fetch
time, the SHA-256 of the stored copy and of its content, and the SHA-256 of the raw answer kept privately with the
run's other raw answers.

| File | Listing | What the page data shows |
|---|---|---|
| `flat_layout_page.html.gz` | Beauty, "New Arrivals" (`1085666_4427759`), page 1 | 50 placements of 42 products. Every price is a flat display string (`priceInfo.linePriceDisplay` and `linePrice`, `priceInfo.unitPrice`, an empty `priceInfo.wasPrice`), with no price line. It is the only page with flat price strings among the 1,526 pages stored by the collector's 21 live runs of 2026-10-31 to 2026-11-04 (releases 1.5.0 to 1.6.4; 33,736 placements) |
| `price_lines_page.html.gz` | Personal Care, "Men's Hair & Beard Care" (`1005862_1056884_2965909`), page 1 | 58 of its 59 placements give their prices in price lines (`priceInfo.priceDetails.priceLines`), and one shows no price; it also shows Head & Shoulders `20409871453`, with another image size |

`l10_records.json` holds the 26 records of the run's export (`products.json`, byte-identical values) that the run
read from `flat_layout_page.html.gz`, as its `record_map.json` names each record's page.

Release 1.6.4's source check read only the price lines and the nested price objects. It found no price on the flat
page, so it reported 21 of the run's 10,301 records as mismatches (it verified the other 5 records read from this
page on another stored page that shows the same values), and `validate-export` exited 6.
`tests/unit/test_flat_price_layout.py` reads these pages with the 1.6.5 source check. They are earlier captures,
not new evidence: no test reaches Walmart or a provider.
