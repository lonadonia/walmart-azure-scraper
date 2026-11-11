> For the complete documentation index, see [llms.txt](https://developers.oxylabs.io/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://developers.oxylabs.io/api-reference/core-endpoints.md).

# Core Endpoints

Reference for Web API's two core endpoints, /search and /scrape — parameters, response schema, and examples.

<table><thead><tr><th width="184">Endpoint</th><th>Returns</th></tr></thead><tbody><tr><td><a href="#post-v1-search"><code>/search</code></a></td><td>Ranked organic web results</td></tr><tr><td><a href="#post-v1-scrape"><code>/scrape</code></a></td><td>Extract content from URL</td></tr></tbody></table>

### `POST /v1/search`

Ranked organic web results.

**Modes:** `sync` only

#### **Request Schema**

```bash
curl https://webapi.oxylabs.io/v1/search \
  -H "Authorization: Bearer $OXYLABS_WEB_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "eu ai act compliance deadlines", "max_results": 3, "location": "DE"}'
```

<table><thead><tr><th width="122">Parameter</th><th width="88.5">Type</th><th width="84.5">Required</th><th>Description</th></tr></thead><tbody><tr><td><code>query</code></td><td>string</td><td>Yes</td><td>Keyword search phrase. <code>1</code> to <code>2048</code> chars.</td></tr><tr><td><code>max_results</code></td><td>integer</td><td>No</td><td>Number of results to return. <code>1</code>–<code>20</code>. Default <code>10</code></td></tr><tr><td><code>location</code></td><td>string</td><td>No</td><td>ISO 3166-1 alpha-2 country code, e.g. <code>DE</code>. Default <code>null</code></td></tr></tbody></table>

#### **Response**

{% code expandable="true" %}

```json
{
  "state": "done",
  "results": [
    {
      "title": "Implementation Timeline | EU Artificial Intelligence Act",
      "outline": [
        "Date 2 August 2025 Providers: need to be compliant..."
      ],
      "url": "https://artificialintelligenceact.eu/implementation-timeline/",
      "metadata": {
        "position": 1
      }
    }
  ],
  "related_questions": [
    {
      "question": "When does the EU AI Act take effect?",
      "title": "Implementation Timeline | EU Artificial Intelligence Act",
      "snippet": "The Act applies in stages, beginning in August 2024."
    }
  ],
  "related_searches": [
    { "query": "ai act timeline" }
  ],
  "params": {
    "query": "eu ai act compliance deadlines",
    "location": "DE",
    "max_results": 3
  },
  "metadata": {
    "timestamp": 1787431568,
    "request_id": "1788875675880097469"
  }
}
```

{% endcode %}

<table><thead><tr><th width="265">Field</th><th width="84">Type</th><th>Description</th></tr></thead><tbody><tr><td><code>state</code></td><td>string</td><td><code>done</code>. <code>faulted</code> on a <code>500</code></td></tr><tr><td><code>results[]</code></td><td>array</td><td>Ranked organic results, best first. Empty when nothing matched</td></tr><tr><td><code>results[].title</code></td><td>string</td><td>Page title</td></tr><tr><td><code>results[].outline</code></td><td>array of strings</td><td>Content snippets. Each item is truncated</td></tr><tr><td><code>results[].url</code></td><td>string</td><td>Absolute URL of the result</td></tr><tr><td><code>results[].metadata.position</code></td><td>integer</td><td>Rank, starting at <code>1</code></td></tr><tr><td><code>related_questions[]</code></td><td>array</td><td>"People also ask" entries. Omitted when empty</td></tr><tr><td><code>related_questions[].question</code></td><td>string</td><td>The question. Always present</td></tr><tr><td><code>related_questions[].title</code></td><td>string</td><td>Title of the answering page <em>(Optional)</em></td></tr><tr><td><code>related_questions[].snippet</code></td><td>string</td><td>Extract answering the question. Truncated <em>(Optional)</em></td></tr><tr><td><code>related_searches[]</code></td><td>array</td><td>Related queries, each with a <code>query</code>. Omitted when empty</td></tr><tr><td><code>params</code></td><td>object</td><td>Parameters used for request, defaults filled in</td></tr><tr><td><code>metadata.timestamp</code></td><td>integer</td><td>Unix timestamp in seconds</td></tr><tr><td><code>metadata.request_id</code></td><td>string</td><td>Request identifier</td></tr></tbody></table>

### `POST /v1/scrape`

Extracts data from URL and returns its content in the requested formats.

**Modes:** `sync`, `async`, `batch`

#### **Request Schema**

```bash
curl https://webapi.oxylabs.io/v1/scrape \
  -H "Authorization: Bearer $OXYLABS_WEB_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://artificialintelligenceact.eu/implementation-timeline/", "output": ["markdown"]}'
```

<table><thead><tr><th width="133">Parameter</th><th width="93">Type</th><th width="90">Required</th><th>Description</th></tr></thead><tbody><tr><td><code>url</code></td><td>string</td><td>yes</td><td>Absolute <code>http</code> or <code>https</code> URL. Send it unchanged — query strings and path segments are significant</td></tr><tr><td><code>output</code></td><td>array of strings</td><td>no</td><td>Formats to return: <code>["html"]</code> (default), <code>["markdown"]</code>, <code>["json"]</code>, <code>["screenshot"]</code>. <code>json</code> returns parsed fields. <code>screenshot</code> requires <code>run_js: true</code></td></tr><tr><td><code>json</code></td><td>object</td><td>no</td><td>Required when <code>output</code> includes <code>json</code>: <code>{"prompt": string}</code> or <code>{"schema": object}</code>, never both</td></tr><tr><td><code>json.prompt</code></td><td>string</td><td>no</td><td>Natural-language extraction instructions for <code>output: ["json"]</code>. <code>max_len: 8192</code>, default: <code>null</code>. Cannot be used with <code>json.schema</code>.</td></tr><tr><td><code>json.schema</code></td><td>object</td><td>no</td><td>OpenAPI / JSON Schema object defining required JSON output shape. <code>10</code> to <code>65535</code> chars, default: <code>null</code>. Cannot be used with <code>json.prompt</code></td></tr><tr><td><code>location</code></td><td>string</td><td>no</td><td>Two-letter country code to fetch from, e.g. <code>DE</code></td></tr><tr><td><code>device</code></td><td>string</td><td>no</td><td><code>desktop</code> (default) or <code>mobile</code></td></tr><tr><td><code>run_js</code></td><td>boolean</td><td>no</td><td>Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more</td></tr><tr><td><code>callback_url</code></td><td>string</td><td>no</td><td><strong>Async only.</strong> Webhook URL for the finished job. Malformed URLs are rejected with <code>400</code></td></tr><tr><td><code>storage</code></td><td>object</td><td>no</td><td><strong>Async-only.</strong> Delivers the result to a bucket instead of the response: <code>{"type": string, "url": string}</code>. <code>type</code> is <code>s3</code>, <code>s3_gzip</code>, <code>s3_compatible</code>, <code>gcs</code>, or <code>tos</code>. <code>url</code> is not validated</td></tr></tbody></table>

#### **Response**

{% code expandable="true" %}

```json
{
  "state": "done",
  "results": [
    {
      "html": "107.175.25.67\n",
      "metadata": {
        "page": 1,
        "run_js": false,
        "url": "https://ip.oxylabs.io/",
        "statuses": {
          "http_request": {
            "code": 200,
            "tag": "HTTP_OK"
          }
        }
      }
    }
  ],
  "params": {
    "url": "https://ip.oxylabs.io",
    "output": ["html"],
    "json": { "schema": null, "prompt": null },
    "location": null,
    "device": "desktop",
    "run_js": null,
    "storage": {
      "type": "s3",
      "url": "oxylabs.test/7517848208047890433.json"
    },
    "callback_url": null,
    "client_notes": null
  },
  "metadata": {
    "timestamp": 1792394688,
    "request_id": "7517848208047890433",
    "statuses": {
      "storage_upload": {
        "code": 13000,
        "tag": "UPLOAD_SUCCESS"
      }
    }
  }
}
```

{% endcode %}

<table><thead><tr><th width="215">Field</th><th width="81">Type</th><th>Description</th></tr></thead><tbody><tr><td><code>state</code></td><td>string</td><td><code>done</code>, <code>pending</code>, or <code>faulted</code></td></tr><tr><td><code>status</code></td><td>integer</td><td>Present on error responses. HTTP status code</td></tr><tr><td><code>results[]</code></td><td>array</td><td>One entry for the requested URL. Present when <code>state</code> is <code>done</code></td></tr><tr><td><code>results[].markdown</code></td><td>string</td><td>The page as Markdown. Present when requested</td></tr><tr><td><code>results[].html</code></td><td>string</td><td>The raw markup. Present when requested</td></tr><tr><td><code>results[].json</code></td><td>object</td><td>Parsed fields. Present when requested</td></tr><tr><td><code>results[].screenshot</code></td><td>string</td><td>The screenshot. Present when requested</td></tr><tr><td><code>results[].metadata.url</code></td><td>string</td><td>The URL fetched, after redirects</td></tr><tr><td><code>results[].metadata.statuses</code></td><td>object</td><td>HTTP, parsing, and other tagged processing statuses</td></tr><tr><td><code>params</code></td><td>object</td><td>Parameters used for request, defaults filled in. Null values are retained</td></tr><tr><td><code>metadata.timestamp</code></td><td>integer</td><td>Unix timestamp in seconds</td></tr><tr><td><code>metadata.request_id</code></td><td>string</td><td>Request identifier</td></tr><tr><td><code>metadata.statuses</code></td><td>object</td><td>Tagged request-level statuses, such as storage delivery status</td></tr></tbody></table>


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation by asking a question.

Perform an HTTP GET request on the following URL with the `ask` and `goal` query parameters:

```
GET https://developers.oxylabs.io/api-reference/core-endpoints.md?ask=<question>&goal=<user_goal>
```

`ask` is the immediate question: it should be specific, self-contained, and written in natural language.
`goal` is what the user is ultimately trying to achieve, the reason they need the answer. Sharing it helps GitBook give you a better, more relevant answer. A goal is most helpful when it describes the outcome the user wants rather than restating the question. For example, with `ask=how do I create an API token`, a goal like `automate deployments from our CI pipeline` lets GitBook tailor the answer to that use case.

The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
