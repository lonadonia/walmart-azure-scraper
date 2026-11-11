> For the complete documentation index, see [llms.txt](https://developers.oxylabs.io/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://developers.oxylabs.io/api-reference/jobs-and-discovery.md).

# Jobs & Discovery

Reference for submitting, batching, and collecting async scrape jobs, and for listing endpoints and parameters at runtime.

<table><thead><tr><th width="112.5">Section</th><th>Endpoints</th></tr></thead><tbody><tr><td>Requests</td><td><code>POST /v1/async/scrape/{path}</code>, <code>POST /v1/async/scrape/batch/{path}</code>, <code>GET /v1/async/scrape/{request_id}</code></td></tr><tr><td>Discovery</td><td><code>GET /v1/scrapers</code>, <code>OPTIONS /v1/{endpoint}</code></td></tr></tbody></table>

## Async requests

### `POST /v1/async/scrape/{path}`

Submits one async scrape request. `{path}` is any scrape path with `/v1/async/scrape/` in place of `/v1/scrape/`.

**Modes:** `async`

<table><thead><tr><th width="151">Name</th><th width="98">Type</th><th width="106.5">Required</th><th>Description</th></tr></thead><tbody><tr><td><code>callback_url</code></td><td>string</td><td>no</td><td>Webhook URL for the finished request. Malformed URLs are rejected with <code>400</code></td></tr><tr><td><code>storage</code></td><td>object</td><td>no</td><td>Delivers the result to a bucket instead of the response</td></tr><tr><td><code>storage.type</code></td><td>string</td><td>yes, with <code>storage</code></td><td><code>s3</code>, <code>s3_gzip</code>, <code>s3_compatible</code>, <code>gcs</code>, or <code>tos</code>. Validated</td></tr><tr><td><code>storage.url</code></td><td>string</td><td>yes, with <code>storage</code></td><td>Destination for the result. Validated for <code>s3</code>, <code>s3_gzip</code>, <code>s3_compatible</code>, and <code>tos</code>. Invalid values return <code>400</code> before the request is created</td></tr></tbody></table>

All other parameters are those of the endpoint being submitted.

#### **Response** – `202 Accepted`

<table><thead><tr><th width="207">Field</th><th width="95">Type</th><th>Description</th></tr></thead><tbody><tr><td><code>state</code></td><td>string</td><td><code>pending</code></td></tr><tr><td><code>params</code></td><td>object</td><td>The request as executed, defaults filled in</td></tr><tr><td><code>metadata.timestamp</code></td><td>integer</td><td>Unix timestamp in seconds</td></tr><tr><td><code>metadata.request_id</code></td><td>string</td><td>The request ID. Use it to collect the result</td></tr></tbody></table>

### `POST /v1/async/scrape/batch/{path}`

Submits one request per value in a list. `{path}` is any scrape path that has a batch mode.

**Modes:** `batch`

<table><thead><tr><th width="131.5">Name</th><th width="93">Type</th><th width="158.5">Required</th><th>Description</th></tr></thead><tbody><tr><td><code>query</code></td><td>array of strings</td><td>yes, if the endpoint takes <code>query</code></td><td>Values, one request per value</td></tr><tr><td><code>url</code></td><td>array of strings</td><td>yes, if the endpoint takes <code>url</code></td><td>URLs, one request per value</td></tr><tr><td><code>callback_url</code></td><td>string</td><td>no</td><td>Webhook URL for each finished request</td></tr><tr><td><code>storage</code></td><td>object</td><td>no</td><td>Bucket delivery for each request. Same fields as above</td></tr></tbody></table>

All other parameters are those of the endpoint being submitted and apply to every request. Use the singular `query` or `url` field with an array value. `queries` and `urls` are not accepted.

#### **Response** – `202 Accepted`

<table><thead><tr><th width="261">Field</th><th width="141.5">Type</th><th>Description</th></tr></thead><tbody><tr><td><code>data[]</code></td><td>array</td><td>One object per accepted request. Omitted when no requests are accepted</td></tr><tr><td><code>errors[]</code></td><td>array</td><td>One error object per rejected item. Omitted when no items are rejected</td></tr><tr><td><code>data[].state</code></td><td>string</td><td><code>pending</code></td></tr><tr><td><code>data[].params</code></td><td>object</td><td>The request as executed</td></tr><tr><td><code>data[].metadata.request_id</code></td><td>string</td><td>The request ID</td></tr></tbody></table>

There is no batch collection route: collect each request by its `request_id`. `/v1/scrape/batch` returns `404`.

### `GET /v1/async/scrape/{request_id}`

Returns the state and result of a submitted request. Send `metadata.request_id` from the submit response as the `request_id` path parameter.

#### **Response** – `200 OK`

<table><thead><tr><th width="118">Field</th><th width="76">Type</th><th>Description</th></tr></thead><tbody><tr><td><code>state</code></td><td>string</td><td><code>pending</code> while the request is queued or running, <code>done</code> when finished</td></tr><tr><td><code>results[]</code></td><td>array</td><td>Same shape as the realtime response. Populated when <code>state</code> is <code>done</code></td></tr></tbody></table>

An unknown or expired `request_id` returns `404`.

## Discovery

### `GET /v1/scrapers`

Lists implemented realtime scrape paths for the client.

#### **Response** – `200 OK`

```json
{
  "scrapers": [
    "/v1/scrape",
    "/v1/scrape/amazon",
    "/v1/scrape/amazon/product",
    "/v1/scrape/google/search"
    ...
  ]
}
```

<table><thead><tr><th width="113">Field</th><th width="86.5">Type</th><th>Description</th></tr></thead><tbody><tr><td><code>scrapers</code></td><td>array of strings</td><td>Implemented realtime scrape paths available to the client</td></tr></tbody></table>

### `OPTIONS /v1/{endpoint}`

Returns a parameter specification for an endpoint. The response is not an executable request body. It lists accepted parameters, annotated with their type, requirement, allowed values, default, length limits, and description.

`OPTIONS /v1/search` is not available.

#### **Response** (`OPTIONS /v1/scrape`)

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

#### **Output format**

Each parameter's value: `[type] [required or optional] [constraints]. Description.`

<table><thead><tr><th width="297">Token</th><th>Meaning</th></tr></thead><tbody><tr><td><code>[string], [bool], [int], [json]</code></td><td>Parameter type</td></tr><tr><td><code>[required], [optional]</code></td><td>Whether the parameter must be sent. Not shown on every parameter</td></tr><tr><td><code>[enum: a, b]</code></td><td>Allowed values</td></tr><tr><td><code>[default: x]</code></td><td>Value used when the parameter is omitted</td></tr><tr><td><code>[min_len: n], [max_len: n]</code></td><td>Minimum and maximum length</td></tr></tbody></table>

Arrays shown as a single-element array holding the element's annotation. Nested objects are shown as objects. Async paths also list `storage` and `callback_url`.


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation by asking a question.

Perform an HTTP GET request on the following URL with the `ask` and `goal` query parameters:

```
GET https://developers.oxylabs.io/api-reference/jobs-and-discovery.md?ask=<question>&goal=<user_goal>
```

`ask` is the immediate question: it should be specific, self-contained, and written in natural language.
`goal` is what the user is ultimately trying to achieve, the reason they need the answer. Sharing it helps GitBook give you a better, more relevant answer. A goal is most helpful when it describes the outcome the user wants rather than restating the question. For example, with `ask=how do I create an API token`, a goal like `automate deployments from our CI pipeline` lets GitBook tailor the answer to that use case.

The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
