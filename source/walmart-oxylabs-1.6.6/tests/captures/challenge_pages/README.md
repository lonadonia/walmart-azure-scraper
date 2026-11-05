# Authentic pages for the challenge detection tests

Saved Walmart answers, used offline by `tests/unit/test_challenge_detection.py`. No test reaches Walmart
or a provider. Every file is a **sanitized copy**, not a byte-for-byte original: `MANIFEST.json` gives,
for each file, the source file it was made from, that file's SHA-256 (`source_sha256`) and the SHA-256 of
the content kept here (`content_sha256`, the decompressed page for `.html.gz`).

| File | What it is | Source |
|---|---|---|
| `store_5402_challenge.html.gz` | Walmart's store page for #5402 after the store change was refused: the page data is there, and PerimeterX's "Robot or human?" dialog with its `px-captcha` container is added at the end of the 400 kB page | live pilot of 2026-10-20 22:31 UTC, run `01M5DQ1YXB7WEXNA7FYJDMR5Z6` (Scrapfly Cloud Browser), fetch `01M5DQ2WMVKVNVHN4Z0Q0JZMB5` |
| `store_3891_page.html.gz` | Walmart's store page for #3891 as first served (no challenge) | live retry of 2026-10-21 03:14 UTC, run `01M5E77WDATTQVD6GB1HW5K0ZK`, `store_page.html` |
| `store_3891_challenge.html.gz` | the same page after the refused store change, with the "Robot or human?" dialog | same run, `after_click.html` |
| `setpickup_412_block_5402.json`, `setpickup_412_block_3891.json` | PerimeterX's block answer (HTTP 412) to the store change of each run | same runs |
| `product_15353921746.html.gz` | a **legitimate** product page (3 pack CeraVe Baby Moisturizing Cream 5 oz, item 15353921746) whose page data holds a brand's reply to a customer review: "… provide the reference #48395435 …". Release 1.3.0 took that sentence for an Akamai reference id and the page for a refusal | Azure run `01M5X364ZR83MZ9M60QGPFR7TX` of 2026-10-26 (Oxylabs Web API), fetch `01M5X4S1M9SV0AXNB9ZD29G8TT`, the collector's stored page copy |

The two store runs were made by the application this collector derives from; their pages were stored
by that application after sanitization (scripts other than the page data removed, session, visitor and
device identifiers in the page data replaced with `[REDACTED]`). They are the pages kept in the
repository's `deploy_validation` folders, where their READMEs describe the runs.

Sanitization applied here:

* every page went through this collector's `walmart_headless.sites.walmart.sanitize.sanitize_html`
  (`sanitizer_changed_bytes` says whether it changed anything);
* in `setpickup_412_block_5402.json`, the `u=` and `v=` visitor values of the block script were replaced
  with `[REDACTED]` (`identifiers_redacted_here`); the `uuid` and `vid` values were already redacted;
* the raw original of the product page is kept privately with the run's other raw answers; its SHA-256 is
  in `MANIFEST.json` (`raw_original_body_sha256`);
* release 1.3.1 found that the earlier sanitizer kept Walmart's camelCase session keys (`isomorphicSessionId`, `adSessionId`) and the request trace IDs (`traceId`, `spanId`, `renderViewId`) in the page data; these copies went through the 1.3.1 sanitizer, which replaced those values with `[REDACTED]` (`MANIFEST.json`: `resanitized_1_3_1`).

What sanitization keeps: the page data (`__NEXT_DATA__`), the markup, and the challenge dialog's own
elements (`<div id="px-captcha">`, its heading). It removes script bodies, so a challenge recognised only
from a script would not be recognised from these copies; the tests use the elements that are kept.
