> For the complete documentation index, see [llms.txt](https://developers.oxylabs.io/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://developers.oxylabs.io/api-reference/overview.md).

# Overview

Base URL, authentication, request conventions, delivery modes, and response envelope shapes for the Web API.

## Base URL

```
https://webapi.oxylabs.io
```

## Authentication

```http
Authorization: Bearer YOUR_API_KEY
```

Bearer token on every request. Full detail: [Authentication](/products/web-api/authentication.md).

## Request format

<table data-header-hidden><thead><tr><th width="160">Item</th><th>Value</th></tr></thead><tbody><tr><td>Method</td><td><code>POST</code>, unless stated on the endpoint</td></tr><tr><td>Content type</td><td><code>application/json</code></td></tr><tr><td>Body</td><td>JSON object. Unrecognized fields are rejected with <code>400</code></td></tr></tbody></table>

## Endpoints

<table><thead><tr><th width="231">Type</th><th>Path</th></tr></thead><tbody><tr><td>Search</td><td><code>POST /v1/search</code></td></tr><tr><td>Generic scrape</td><td><code>POST /v1/scrape</code></td></tr><tr><td>Dedicated scrapers</td><td><code>POST /v1/scrape/{target}/{collection}</code></td></tr><tr><td>Dedicated scraper list</td><td><code>GET /v1/scrapers</code></td></tr><tr><td>Endpoint parameter list</td><td><code>OPTIONS /v1/{endpoint}</code></td></tr></tbody></table>

Full endpoint list: [Full Endpoint Index](/api-reference/full-endpoint-index.md).

## Delivery modes

{% hint style="info" %}
`/v1/search` is synchronous (realtime) only.
{% endhint %}

<table><thead><tr><th>Mode</th><th width="222">Response</th><th>Notes</th></tr></thead><tbody><tr><td><a href="/products/web-api/scrape/delivery-modes.md#realtime">Synchronous</a><br><code>/v1/scrape/...</code></td><td><code>200</code>, result in body</td><td>Holds the connection open</td></tr><tr><td><a href="/products/web-api/scrape/delivery-modes.md#single-job-delivery-async">Async (single job)</a><br><code>/v1/async/scrape/...</code></td><td><code>202</code>, poll/callback/storage</td><td>Job ID is <code>metadata.request_id</code></td></tr><tr><td><a href="/products/web-api/scrape/delivery-modes.md#batch-delivery-async">Async (batch)</a><br><code>/v1/async/scrape/batch/...</code></td><td><code>202</code>, array of jobs</td><td><code>query</code>/<code>url</code> becomes a list</td></tr></tbody></table>

Select endpoint support only `async` jobs. Delivery mode support per endpoint: [Full Endpoint Index](/api-reference/full-endpoint-index.md).


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation by asking a question.

Perform an HTTP GET request on the following URL with the `ask` and `goal` query parameters:

```
GET https://developers.oxylabs.io/api-reference/overview.md?ask=<question>&goal=<user_goal>
```

`ask` is the immediate question: it should be specific, self-contained, and written in natural language.
`goal` is what the user is ultimately trying to achieve, the reason they need the answer. Sharing it helps GitBook give you a better, more relevant answer. A goal is most helpful when it describes the outcome the user wants rather than restating the question. For example, with `ask=how do I create an API token`, a goal like `automate deployments from our CI pipeline` lets GitBook tailor the answer to that use case.

The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
