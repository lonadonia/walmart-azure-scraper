> For the complete documentation index, see [llms.txt](https://developers.oxylabs.io/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://developers.oxylabs.io/api-reference/errors-and-status-codes.md).

# Errors & Status Codes

Technical specification for HTTP status codes, RFC 9457 problem documents, error classification, and production retry logic for the Oxylabs Web API.

### Status code & retry matrix

Retry logic must be gated strictly on response HTTP status codes. Retrying non-retryable client errors (`400`, `401`, `403`, `404`) causes identical failures and unnecessary API load.

<table><thead><tr><th width="207">Status + Code</th><th width="183">RFC 9457 title</th><th>Description</th><th width="117">Retryable?</th></tr></thead><tbody><tr><td><code>200 OK</code></td><td>—</td><td>Realtime call success. Execution complete; process response body.</td><td>No</td></tr><tr><td><code>202 Accepted</code></td><td>—</td><td>Async job accepted. Job queued; retrieve via <code>metadata.request_id</code>.</td><td>No</td></tr><tr><td><code>400 Bad Request</code></td><td><code>INVALID_BODY_PROPERTY</code>, <code>MALFORMED_JSON</code></td><td>Validation or malformed payload. Fix parameters in <code>errors[]</code> before resending.</td><td>No</td></tr><tr><td><code>401 Unauthorized</code></td><td>— <em>(Empty Body)</em></td><td>Invalid, missing, or revoked API key. Verify Bearer token format and dashboard instance key.</td><td>No</td></tr><tr><td><code>403 Forbidden</code></td><td>—</td><td>Entitlement restriction. Account lacks access to target route or source.</td><td>No</td></tr><tr><td><code>404 Not Found</code></td><td><code>NOT_FOUND</code></td><td>Route or job ID invalid/expired. Check endpoint path or async request handle.</td><td>No</td></tr><tr><td><code>405 Method Not Allowed</code></td><td><code>METHOD_NOT_ALLOWED</code></td><td>Method other than <code>POST</code> used. Change HTTP request method to <code>POST</code>.</td><td>No</td></tr><tr><td><code>408 Request Timeout</code></td><td>—</td><td>Realtime scraping timeout. Retry request using exponential backoff.</td><td>Yes</td></tr><tr><td><code>413 Payload Too Large</code></td><td>—</td><td>Payload or batch size exceeded. Reduce payload size or batch target count.</td><td>No</td></tr><tr><td><code>429 Too Many Requests</code></td><td>—</td><td>Concurrency limit or quota exhausted. Lower concurrency and apply jittered backoff. Alert operator if persistent.</td><td><p>Rate limit: Yes</p><p>Quota: No</p></td></tr><tr><td><code>500 Internal Error</code></td><td><code>REQUEST_FAILED_AFTER_TOO_MANY_RETRIES</code>, <code>INTERNAL_ERROR</code></td><td>Upstream failure or faulted scrape. Faulted scrapes are not charged. Retry with backoff.</td><td>Yes</td></tr><tr><td><code>503 Service Unavailable</code></td><td><code>SERVICE_UNAVAILABLE</code></td><td>Service temporarily down. Retry with backoff.</td><td>Yes</td></tr></tbody></table>

### RFC 9457 Problem documents

When an HTTP error occurs, the Web API returns an [RFC 9457](https://www.rfc-editor.org/rfc/rfc9457) problem document served as `application/problem+json`.

{% hint style="info" %}
`401 Unauthorized` Exception: HTTP `401` status responses carry an empty body. The HTTP status code itself represents the complete authentication failure state.
{% endhint %}

#### 1. Invalid body property (`400 Bad Request`)

An invalid `storage.url` returns `VALIDATION_ERROR` with `errors[].pointer` set to `#/storage/url`. The request is not created.

```json
{
  "status": 400,
  "title": "INVALID_BODY_PROPERTY",
  "detail": "A body property has an invalid value.",
  "instance": "6ad5c6df-4ef52bbe9bd1519f8dbfc4ae",
  "errors": [
    {
      "detail": "Must be one of: gcs, s3, s3_gzip, s3_compatible, tos.",
      "pointer": "#/storage/type"
    }
  ]
}
```

#### 2. Faulted scrape error (`500 Internal Error`)

If a scrape fails after all retries, `POST /v1/scrape` returns an HTTP `500` status with `state: "faulted"`. Faulted scrapes do not consume account quota.

```json
{
  "status": 500,
  "state": "faulted",
  "title": "REQUEST_FAILED_AFTER_TOO_MANY_RETRIES",
  "detail": "The request failed after the maximum number of retries. You can try again at no extra cost, as we don't charge you for faulted scrapes.",
  "instance": "6ad5c789-3cb04e139b34a1eaee352bae",
  "params": {
    "url": "https://oxyasdasdasdasdlabsghrehaerhaerh.io",
    "output": ["html"],
    "json": { "schema": null, "prompt": null },
    "location": null,
    "device": "desktop",
    "run_js": null
  },
  "metadata": {
    "timestamp": 1792395145,
    "request_id": "7517850129655711745"
  }
}
```

### Response schema breakdown

<table><thead><tr><th width="192">Field Path</th><th width="99.5">Type</th><th>Description</th></tr></thead><tbody><tr><td><code>status</code></td><td>integer</td><td>HTTP status code.</td></tr><tr><td><code>state</code></td><td>string</td><td>Present on faulted <code>500</code> scrape responses (<code>"faulted"</code>). Successful calls return <code>"done"</code>.</td></tr><tr><td><code>title</code></td><td>string</td><td>Machine-readable error code. Branch application error logic on this value.</td></tr><tr><td><code>detail</code></td><td>string</td><td>Human-readable error message. Do not parse prose for program branching.</td></tr><tr><td><code>instance</code></td><td>string</td><td>Unique trace handle for internal debugging and support escalation.</td></tr><tr><td><code>metadata.request_id</code></td><td>string</td><td>19-digit tracking handle for billing and support tickets.</td></tr><tr><td><code>metadata.timestamp</code></td><td>integer</td><td>Unix epoch timestamp in seconds.</td></tr><tr><td><code>errors[]</code></td><td>array</td><td>Present on request validation errors. Contains field-level failure objects.</td></tr><tr><td><code>errors[].pointer</code></td><td>string</td><td>JSON Pointer identifying the invalid request field (e.g., <code>#/storage/type</code>).</td></tr><tr><td><code>errors[].detail</code></td><td>string</td><td>Detailed failure reason for the specified field pointer.</td></tr></tbody></table>

### Error code reference (`title`)

Programmatic error routing should evaluate the `title` attribute:

<table><thead><tr><th>"title" Code</th><th width="122">HTTP Status</th><th>Description</th></tr></thead><tbody><tr><td><code>MALFORMED_JSON</code></td><td><code>400</code></td><td>Request body is not valid JSON.</td></tr><tr><td><code>INVALID_BODY_PROPERTY</code></td><td><code>400</code></td><td>A request body property has an invalid value.</td></tr><tr><td><code>NOT_FOUND</code></td><td><code>404</code></td><td>Invalid route path or unassigned endpoint sub-resource.</td></tr><tr><td><code>METHOD_NOT_ALLOWED</code></td><td><code>405</code></td><td>Incorrect HTTP method used (Web API endpoints require <code>POST</code>).</td></tr><tr><td><code>REQUEST_FAILED_AFTER_TOO_MANY_RETRIES</code></td><td><code>500</code></td><td>The scrape failed after the maximum number of retries. Uncharged.</td></tr><tr><td><code>INTERNAL_ERROR</code></td><td><code>500</code></td><td>Internal processing error.</td></tr><tr><td><code>SERVICE_UNAVAILABLE</code></td><td><code>503</code></td><td>Temporary backend service disruption.</td></tr></tbody></table>

### Media-specific errors

Returned by `POST /v1/async/scrape/media` and its sub-endpoints when the video can't be downloaded.

<table><thead><tr><th width="74.03125">Code</th><th width="216.372304199773">Status</th><th>Description</th></tr></thead><tbody><tr><td><code>11201</code></td><td><code>VIDEO_DELETED</code></td><td>Video is deleted.</td></tr><tr><td><code>11202</code></td><td><code>VIDEO_UNAVAILABLE</code></td><td>Video is unavailable.</td></tr><tr><td><code>11203</code></td><td><code>VIDEO_PRIVATE</code></td><td>Video is set to private by uploader and only they and explicitly invited people can see it.</td></tr><tr><td><code>11204</code></td><td><code>VIDEO_GEO_RESTRICTED</code></td><td>Video is geo-restricted.</td></tr><tr><td><code>11205</code></td><td><code>VIDEO_LIVE</code></td><td>Video is live now.</td></tr><tr><td><code>11206</code></td><td><code>VIDEO_AGE_RESTRICTED</code></td><td>Video is age restricted.</td></tr><tr><td><code>11207</code></td><td><code>VIDEO_MEMBER_ONLY</code></td><td>Video is for channel members only, and viewers have to pay the monthly subscription fee.</td></tr><tr><td><code>11208</code></td><td><code>VIDEO_PREMIUM_ONLY</code></td><td>Video requires the YouTube Premium subscription.</td></tr><tr><td><code>11209</code></td><td><code>VIDEO_LIVE_OR_TOO_LONG</code></td><td>Video is either live or too long to download.</td></tr><tr><td><code>11210</code></td><td><code>VIDEO_TOO_LONG</code></td><td>Video is too long to download.</td></tr><tr><td><code>11211</code></td><td><code>VIDEO_SIGN_IN_REQUIRED</code></td><td>Sign in is required.</td></tr><tr><td><code>11301</code></td><td><code>MEDIA_UNAVAILABLE</code></td><td>Video was deleted or no longer exists</td></tr><tr><td><code>11302</code></td><td><code>MEDIA_PRIVATE</code></td><td>Video or account is private</td></tr><tr><td><code>11303</code></td><td><code>MEDIA_GEO_RESTRICTED</code></td><td>Video is not available in the job's region</td></tr><tr><td><code>11304</code></td><td><code>MEDIA_UNSUPPORTED</code></td><td>Not a downloadable video: a photo, slideshow, livestream, or post with no video formats, or a video too long or too large to download</td></tr></tbody></table>


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation by asking a question.

Perform an HTTP GET request on the following URL with the `ask` and `goal` query parameters:

```
GET https://developers.oxylabs.io/api-reference/errors-and-status-codes.md?ask=<question>&goal=<user_goal>
```

`ask` is the immediate question: it should be specific, self-contained, and written in natural language.
`goal` is what the user is ultimately trying to achieve, the reason they need the answer. Sharing it helps GitBook give you a better, more relevant answer. A goal is most helpful when it describes the outcome the user wants rather than restating the question. For example, with `ask=how do I create an API token`, a goal like `automate deployments from our CI pipeline` lets GitBook tailor the answer to that use case.

The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
