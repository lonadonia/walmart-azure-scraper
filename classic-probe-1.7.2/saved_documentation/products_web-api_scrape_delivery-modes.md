> For the complete documentation index, see [llms.txt](https://developers.oxylabs.io/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://developers.oxylabs.io/products/web-api/scrape/delivery-modes.md).

# Delivery Modes

Discover how Web API delivers results: realtime responses, async jobs with polling or callbacks, cloud storage delivery, and batch requests.

The Web API provides three delivery modes for different workload requirements and execution volumes.&#x20;

<table><thead><tr><th width="315">Delivery</th><th width="92">Max items</th><th width="143">Targets</th><th width="215">Used for...</th></tr></thead><tbody><tr><td><a href="#realtime"><strong>Realtime</strong></a> (Synchronous)<br><code>POST /v1/scrape/{source}</code></td><td>1</td><td>All endpoints</td><td>Low-latency requests, testing</td></tr><tr><td><a href="#single-job-delivery-async"><strong>Async Single</strong></a> (Polling)<br><code>POST /v1/async/scrape/{source}</code></td><td>1</td><td>All endpoints</td><td>High concurrency and volume</td></tr><tr><td><a href="#batch-delivery-async"><strong>Async Batch</strong></a> (Bulk queue)<br><code>POST /v1/async/scrape/batch/{source}</code></td><td>5,000</td><td>Select endpoints</td><td>Bulk ingestion</td></tr></tbody></table>

Most `/scrape` endpoints are offered as options for **Realtime** and **Async** result delivery, with the path deciding when and how you get the result.

```http
POST /v1/scrape/...          # realtime: the result is the response
POST /v1/async/scrape/...    # async: create a job and retrieve the result separately
```

## Realtime

```http
POST /v1/scrape/{source}
```

Realtime delivery processes the scrape on the initial HTTP connection. The request blocks until rendering, access resolution, and parsing is complete, returning the content payload in the response body. Set a client timeout of at least 150 seconds.

```bash
curl -X POST https://webapi.oxylabs.io/v1/scrape/amazon/product \
  -H "Authorization: Bearer $OXYLABS_WEB_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "B0CX23V2ZK",
    "domain": "com",
    "output": ["json"]
  }'
```

{% hint style="info" %}
Some endpoints do not support realtime delivery (e.g. YouTube downloads, ChatGPT, Gemini, Perplexity). Confirm your target eligibility with [Endpoint Discovery](/products/web-api/scrape/endpoint-discovery.md) or check the [API Reference](https://developers.oxylabs.io/api-reference).
{% endhint %}

## Single job delivery (Async)

```http
POST /v1/async/scrape/{source}
```

Asynchronous single-job delivery queues a scrape request and immediately returns an HTTP `202 Accepted` status containing the job identifier.

```bash
curl https://webapi.oxylabs.io/v1/async/scrape/media/youtube/metadata \
  -H "Authorization: Bearer $OXYLABS_WEB_API_KEY" \
  -H 'Content-Type: application/json' \
  -d '{"query": "a1cWkClBXLI", "output": ["json"]}'
```

When a job is accepted, the job ID is returned inside `metadata.request_id`.

```json
{
  "status": "pending",
  "params": { "query": "a1cWkClBXLI", "output": ["json"] },
  "metadata": { "timestamp": 1787599164, "request_id": "7497734325668954113" }
}
```

The status of the submitted job can be referenced through the `status` results:

<table data-header-hidden><thead><tr><th width="172"></th><th></th></tr></thead><tbody><tr><td><code>status: "pending"</code></td><td>The job is queued or executing. The <code>results</code> array remains empty (<code>[]</code>).</td></tr><tr><td><code>status: "done"</code></td><td>Job completed. The <code>results</code> array contains the parsed output.</td></tr><tr><td><code>status: "faulted"</code></td><td>Extraction failed. Inspect <code>results[].metadata.status_code</code> for details.</td></tr></tbody></table>

### Output retrieval

Results are retrieved via [polling](#option-a-polling-endpoint-get-v1-async-scrape-jobid), [webhooks](#option-b-webhooks-callback_url) (callback URL), or direct [cloud storage uploads](#option-c-cloud-bucket-upload-storage).

#### **Polling endpoint (`GET /v1/async/scrape/{jobId}`)**

Pass the numeric `metadata.request_id` to the polling endpoint.

```bash
curl -X GET https://webapi.oxylabs.io/v1/async/scrape/7497971512142465025 \
  -H "Authorization: Bearer $OXYLABS_WEB_API_KEY"
```

#### **Webhooks (`callback_url`)**

Include `callback_url` in the initial request body. Once execution transitions to `done` or `faulted`, the API issues an HTTP `POST` payload containing the job results to your specified endpoint.

```json
{
  "query": "B0CX23V2ZK",
  "output": ["json"],
  "callback_url": "https://your-api.example.com/webhooks-oxylabs"
}
```

The URL is validated at submission time and malformed ones are rejected with error `400`.

#### **Cloud storage upload (`storage`)**

`storage` writes the result to a bucket instead of the response body. Async paths only.

```json
{
  "query": "B0CX23V2ZK",
  "output": ["json"],
  "storage": {
    "type": "s3",
    "url": "s3://your-bucket-name/scraped-data/B0CX23V2ZK.json"
  }
}
```

| Field          | Values                                         |
| -------------- | ---------------------------------------------- |
| `storage.type` | `s3`, `s3_gzip`, `s3_compatible`, `gcs`, `tos` |
| `storage.url`  | Destination for the result                     |

{% hint style="danger" %}
**`storage.url` is not validated.** A malformed or misspelled destination is accepted, the job is executed and billed with failed delivery.

**`storage.type` is checked against the list above.** A bad type gives you `400`. Test the destination once with single request before using a batch.
{% endhint %}

## Batch delivery (Async)

{% hint style="warning" %}
Batch routing is available only for select `/scrape` sources. Confirm your target eligibility with [Endpoint Discovery](/products/web-api/scrape/endpoint-discovery.md) or check the [API Reference](https://developers.oxylabs.io/api-reference).
{% endhint %}

```http
POST /v1/async/scrape/batch/{source}
```

Batch delivery submits up to 5,000 scraping jobs in a single HTTP request. Rather than taking a single `url` or `query` string, the input field accepts an array of strings. All other fields in the payload are applied across every job in the batch.

```bash
curl -X POST https://webapi.oxylabs.io/v1/async/scrape/batch/amazon/product \
  -H "Authorization: Bearer $OXYLABS_WEB_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": ["B0CX23V2ZK", "B09B33PQS9", "INVALID_ASIN_XYZ"],
    "domain": "com",
    "output": ["json"]
  }'
```

Batch endpoints return an HTTP `202 Accepted` status with an array of individual job statuses in `data[]` alongside an `errors[]` array listing rejected items (e.g., invalid ASIN formatting or invalid URL syntax). See the example below:

<details>

<summary>Output sample</summary>

```json
{
  "data": [
    {
      "state": "pending",
      "params": {
        "query": "B0CX23V2ZK",
        "output": [
          "json"
        ],
        "json": {
          "schema": null,
          "prompt": null
        },
        "location": null,
        "device": "desktop",
        "run_js": null,
        "storage": {
          "type": null,
          "url": null
        },
        "callback_url": null,
        "client_notes": null,
        "domain": "com",
        "locale": null,
        "autoselect_variant": false,
        "check_empty_geo": null,
        "safe_search": true,
        "currency": null
      },
      "metadata": {
        "timestamp": 1790852882,
        "request_id": "7511381408825235457"
      }
    },
    {
      "state": "pending",
      "params": {
        "query": "B09B33PQS9",
        "output": [
          "json"
        ],
        "json": {
          "schema": null,
          "prompt": null
        },
        "location": null,
        "device": "desktop",
        "run_js": null,
        "storage": {
          "type": null,
          "url": null
        },
        "callback_url": null,
        "client_notes": null,
        "domain": "com",
        "locale": null,
        "autoselect_variant": false,
        "check_empty_geo": null,
        "safe_search": true,
        "currency": null
      },
      "metadata": {
        "timestamp": 1790852882,
        "request_id": "7511381408825229313"
      }
    }
  ],
  "errors": [
    {
      "detail": "ASIN should only contain alphanumeric values.",
      "pointer": "/query/2"
    }
  ]
}
```

</details>


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation by asking a question.

Perform an HTTP GET request on the following URL with the `ask` and `goal` query parameters:

```
GET https://developers.oxylabs.io/products/web-api/scrape/delivery-modes.md?ask=<question>&goal=<user_goal>
```

`ask` is the immediate question: it should be specific, self-contained, and written in natural language.
`goal` is what the user is ultimately trying to achieve, the reason they need the answer. Sharing it helps GitBook give you a better, more relevant answer. A goal is most helpful when it describes the outcome the user wants rather than restating the question. For example, with `ask=how do I create an API token`, a goal like `automate deployments from our CI pipeline` lets GitBook tailor the answer to that use case.

The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
