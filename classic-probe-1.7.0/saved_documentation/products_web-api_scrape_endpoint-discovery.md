> For the complete documentation index, see [llms.txt](https://developers.oxylabs.io/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://developers.oxylabs.io/products/web-api/scrape/endpoint-discovery.md).

# Endpoint Discovery

Discover all up-to-date Web API scrape endpoints and their parameters at runtime instead of hardcoding a list.

Get the most up-to-date Web API scraper endpoint and parameter list programatically from `GET /v1/scrapers` plus `OPTIONS` instead of hardcoding a list to avoid outdated endpoint names or their requests schemas.

## Find all available scrapers

{% tabs %}
{% tab title="HTTP" %}

```http
GET /v1/scrapers
```

{% endtab %}

{% tab title="cURL" %}

```bash
curl https://webapi.oxylabs.io/v1/scrapers \
  -H "Authorization: Bearer $OXYLABS_WEB_API_KEY"
```

{% endtab %}
{% endtabs %}

Returns every `/scrape` endpoint, including all dedicated scrapers (realtime and async):

```json
{
  "scrapers": [
    "/v1/scrape",
    "/v1/scrape/amazon",
    "/v1/scrape/amazon/product",
    "/v1/scrape/google/search",
    "/v1/async/scrape",
    "/v1/async/scrape/amazon/product"
    ...
  ]
}
```

Most scrapers appear twice:&#x20;

* Once under `/v1/scrape/` (synchronous)
* Once under `/v1/async/scrape/` (async job)

Some scrapers only support async delivery, while some also have a `/v1/async/scrape/batch/`  batch delivery option. See [Delivery Modes](/products/web-api/scrape/delivery-modes.md).

## Find all endpoint parameters

{% tabs %}
{% tab title="HTTP" %}

```http
OPTIONS /v1/{endpoint}
```

{% endtab %}

{% tab title="cURL" %}

```bash
curl -X OPTIONS https://webapi.oxylabs.io/v1/scrape/amazon/product \
  -H "Authorization: Bearer $OXYLABS_WEB_API_KEY"
```

{% endtab %}
{% endtabs %}

`OPTIONS` request returns a response with every accepted parameter of the provided endpoint and their:

* Type (`"string"`, `"bool"`, `"int"`, nested objects, single-element arrays as "array of \[type]")
* `required/optional` flags
* Allowed values (e.g. `enum` lists, `min`/`max` values, etc.)
* Default value (if assigned)
* Description

```json
{
    "url": "[string] [required] [max_len: 8192]. The url of the page to scrape.",
    "output": [
        "[string] [optional] [enum: html, screenshot, markdown, json] [default: html]. `html` is the page source, `markdown` it converted, `screenshot` a png, and `json` the parsed data."
    ],
    "json": {
        "schema": "[json] [min_len: 10] [max_len: 65535]. The json schema the scraped page is parsed into for `json` output. Cannot be used together with `json.prompt`.",
        "prompt": "[string] [max_len: 8192]. The prompt naming the data the scraped page is parsed into for `json` output. Cannot be used together with `json.schema`."
    },
    "location": "[string] [optional]. Country the scrape is made from, as an ISO 3166-1 alpha-2 code, e.g. `US`.",
    "device": "[string] [optional] [enum: desktop, mobile] [default: desktop]. Device the scraped page is rendered for.",
    "run_js": "[bool] [optional]. Renders the page using javascript before scraping it, needed for `screenshot` output."
}
```

**This is the recommended source for up-to-date parameters and what type each takes. For parameter descriptions, check** [**API Reference**](https://developers.oxylabs.io/api-reference)**.**

{% hint style="info" %}
**Async alternative** of each scraper (e.g. `OPTIONS /v1/async/scrape/...`) returns the same list as realtime, plus `storage` and `callback_url`.
{% endhint %}

## Implementation example

```python
import os, requests

API = "https://webapi.oxylabs.io"
HEADERS = {"Authorization": f"Bearer {os.environ['OXYLABS_WEB_API_KEY']}"}

listing = requests.get(f"{API}/v1/scrapers", headers=HEADERS, timeout=60).json()

for path in listing["scrapers"]:
    if path.startswith("/v1/async/scrape/batch"):
        continue  # same parameters as the job it wraps
    spec = requests.options(f"{API}{path}", headers=HEADERS, timeout=60).json()
    print(path, sorted(spec))
```

{% hint style="info" %}
Cache the result for the life of a process rather than calling it per request. it changes on deploys, not on traffic.
{% endhint %}


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation by asking a question.

Perform an HTTP GET request on the following URL with the `ask` and `goal` query parameters:

```
GET https://developers.oxylabs.io/products/web-api/scrape/endpoint-discovery.md?ask=<question>&goal=<user_goal>
```

`ask` is the immediate question: it should be specific, self-contained, and written in natural language.
`goal` is what the user is ultimately trying to achieve, the reason they need the answer. Sharing it helps GitBook give you a better, more relevant answer. A goal is most helpful when it describes the outcome the user wants rather than restating the question. For example, with `ask=how do I create an API token`, a goal like `automate deployments from our CI pipeline` lets GitBook tailor the answer to that use case.

The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
