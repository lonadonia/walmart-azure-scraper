> For the complete documentation index, see [llms.txt](https://developers.oxylabs.io/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://developers.oxylabs.io/products/web-api/troubleshooting.md).

# Troubleshooting

Web API status codes, error response formats, retry policy, and common troubleshooting solutions.

## Status codes

| Status + Code                               | Description                                                                                          | Retry?                                                                                |
| ------------------------------------------- | ---------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| `200 OK`                                    | Realtime result in the response body                                                                 | –                                                                                     |
| `202 ACCEPTED`                              | Async job accepted                                                                                   | –                                                                                     |
| `400 MALFORMED_REQUEST_BODY`                | Request body is not valid JSON                                                                       | No, fix payload formatting.                                                           |
| `400 VALIDATION_ERROR`                      | One or more fields failed validation.                                                                | No, fix all entries in `errors[]` before resending.                                   |
| `401 UNAUTHORIZED`                          | Authentication error (missing, invalid, malformed, or revoked key). No response body on this status. | No, fix credentials.                                                                  |
| `404 NOT_FOUND`                             | A path under `/search` doesn't exist or async `request_id` does not exist or is expired.             | No                                                                                    |
| `405 METHOD_NOT_ALLOWED`                    | Incorrect HTTP method used (endpoints require `POST`).                                               | No                                                                                    |
| `408 REQUEST_TIMEOUT`                       | `/scrape` only. The scraper didn't answer within the server's wait window                            | Yes, with backoff.                                                                    |
| `429 TOO_MANY_REQUESTS`                     | Rate limit or quota exceeded. See [Common errors](#id-1.-rate-limit-vs.-quota-exhaustion-429)        | <p><strong>Rate limit:</strong> yes, with backoff.<br><strong>Quota:</strong> no.</p> |
| `500 REQUEST_FAILED_AFTER_TOO_MANY_RETRIES` | All upstream engines failed. Not charged.                                                            | Yes, with backoff.                                                                    |
| `500 INTERNAL_SERVER_ERROR`                 | Unexpected system fault                                                                              | Yes, with backoff.                                                                    |
| `503 SERVICE_UNAVAILABLE`                   | Upstream service temporarily unavailable                                                             | Yes, with backoff.                                                                    |
| `5xx`                                       | Other transient upstream failure                                                                     | Yes, up to \~3 attempts with backoff.                                                 |

{% hint style="info" %}

* `Code` values are specific to `/search` structured error body (see below). Other endpoints return the status number only.
* New codes can appear as the API grows: treat an unrecognized one as "an error of this status class."
  {% endhint %}

## Error response

`/search` failures use an [RFC 9457](https://www.rfc-editor.org/rfc/rfc9457) problem document, served as `application/problem+json`:

```json
{
  "status": 400,
  "title": "VALIDATION_ERROR",
  "detail": "1 request field is invalid; fix every entry in `errors` and resend.",
  "instance": "6285041d-b00d8d69959c4b36f50fb53b",
  "metadata": {
    "timestamp": 1788762578,
    "request_id": "1788875675880097469"
  },
  "errors": [
    {
      "pointer": "#/max_results",
      "detail": "Input should be less than or equal to 20"
    }
  ]
}
```

<table><thead><tr><th width="195">Field</th><th>Description</th><th width="111">Type</th></tr></thead><tbody><tr><td><code>status</code></td><td>HTTP status code matching the response status line.</td><td>number</td></tr><tr><td><code>state</code></td><td>Present on faulted <code>500</code> responses (<code>"faulted"</code>). Successful calls return <code>"done"</code>.</td><td>string</td></tr><tr><td><code>title</code></td><td>Machine-readable error code. Branch application logic on this field.</td><td>string</td></tr><tr><td><code>detail</code></td><td>Human-readable explanation of the error. Do not match against this prose text.</td><td>string</td></tr><tr><td><code>instance</code></td><td>Trace identifier for the request. Include in support inquiries.</td><td>string</td></tr><tr><td><code>metadata.request_id</code></td><td>19-digit request handle used for tracking and support.</td><td>string</td></tr><tr><td><code>metadata.timestamp</code></td><td>Unix epoch timestamp in seconds.</td><td>number</td></tr><tr><td><code>params</code></td><td>All parameters used for the request with applied defaults. Present on validated requests (e.g., <code>500</code>), absent on <code>400</code>.</td><td>object</td></tr><tr><td><code>errors[]</code></td><td>List of parameter failures. Present on <code>VALIDATION_ERROR</code> only.</td><td>array</td></tr><tr><td><code>errors[].pointer</code></td><td>JSON Pointer identifying the rejected field (e.g., <code>#/max_results</code>).</td><td>string</td></tr><tr><td><code>errors[].detail</code></td><td>Explanation of why the specific field was rejected.</td><td>string</td></tr></tbody></table>

## Retries

Retry `408`, `429`, and `5xx` with exponential backoff and jitter, capped at \~3 attempts:

```python
import random, time, requests

RETRYABLE = {408, 429, 500, 502, 503, 504}

def call(url, payload, headers, attempts=3):
    for attempt in range(1, attempts + 1):
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=120)
        except requests.Timeout:
            if attempt == attempts:
                raise
            time.sleep(2**attempt + random.random())
            continue
        if resp.ok:
            return resp.json()
        if resp.status_code not in RETRYABLE or attempt == attempts:
            raise RuntimeError(f"{resp.status_code}: {resp.text[:200]}")
        time.sleep(2**attempt + random.random())  # jitter avoids lockstep retries
```

On sustained `429`, lower concurrency rather than shortening the backoff. Retrying faster against a rate limit will not solve it.

## Common errors & solutions

### **1. Rate limit vs. quota exhaustion (`429`)**

Both rate limit violations (exceeding requests-per-second concurrency) and account quota exhaustion return an HTTP `429 Too Many Requests` code.

**Solution:** If an HTTP `429` persists across multiple backoff attempts spanning more than 30 seconds, your account has exhausted its monthly request quota. Inspect your active usage limits in the [Oxylabs Dashboard](https://dashboard.oxylabs.io).

### **2. Timeouts on JavaScript-heavy pages (`run_js: true`)**

Headless browser rendering (`run_js: true`) or complex target sites require significantly more processing time than standard HTML fetches, often more than a typical default client timeout (5–10s).

**Solution:** Set client timeouts to \~150 seconds. For anything likely to run long regardless, use [Async Delivery](/products/web-api/scrape/delivery-modes.md#single-job-delivery-async) instead of holding the connection open.

## Media-specific errors (`/scrape/media`)

`/media` and its sub-endpoint jobs can finish with HTTP `200` and `state: "done"`, but return no data or file with media-specific error in `results[0].metadata.statuses.video_download`:

{% code expandable="true" %}

```json
"statuses": {
    "video_download": {
        "code": 11206,
        "tag": "DOWNLOAD_FAILED_VIDEO_AGE_RESTRICTED", //"DOWNLOAD_FAILED_" prefix + status
        "details": "The video is age-restricted."
    }
}
```

{% endcode %}

{% hint style="info" %}
`11201`-`11211` apply to `/media/youtube/metadata`, `/media/youtube/subtitles` and `/media/youtube/download` endpoints only.
{% endhint %}

<table><thead><tr><th width="219">Error</th><th width="271">Description</th><th>Solution</th></tr></thead><tbody><tr><td><code>11201</code><br><code>VIDEO_DELETED</code></td><td>The YouTube video was deleted.</td><td>Open the URL in a browser to confirm the video is still there. Retrying the same video won't help.</td></tr><tr><td><code>11202</code><br><code>VIDEO_UNAVAILABLE</code></td><td>YouTube reports the video as unavailable.</td><td>Open the video in a browser to check that it plays. If it does, contact support with the job's <code>request_id</code>.</td></tr><tr><td><code>11203</code><br><code>VIDEO_PRIVATE</code></td><td>The uploader set the video to private, so only they and invited viewers can see it.</td><td>Use a public video.</td></tr><tr><td><code>11204</code><br><code>VIDEO_GEO_RESTRICTED</code></td><td>The video isn't available in the region the job ran from.</td><td>If you need this video, contact support with the job's <code>request_id</code>.</td></tr><tr><td><code>11205</code><br><code>VIDEO_LIVE</code></td><td>The video is a livestream in progress.</td><td>Retry after the stream has ended.</td></tr><tr><td><code>11206</code><br><code>VIDEO_AGE_RESTRICTED</code></td><td>The video is age-restricted.</td><td>Age-restricted videos can't be retrieved. Use a different video.</td></tr><tr><td><code>11207</code><br><code>VIDEO_MEMBER_ONLY</code></td><td>The video is only available to paying channel members.</td><td>Members-only videos can't be retrieved. Use a different video.</td></tr><tr><td><code>11208</code><br><code>VIDEO_PREMIUM_ONLY</code></td><td>The video requires a YouTube Premium subscription.</td><td>Premium-only videos can't be retrieved. Use a different video.</td></tr><tr><td><code>11209</code><br><code>VIDEO_LIVE_OR_TOO_LONG</code></td><td>The video is either a livestream in progress or too long to download. <code>/media/youtube/download</code> only.</td><td>If the video is live, retry after the stream has ended. Videos up to 12 hours long can be downloaded.</td></tr><tr><td><code>11210</code><br><code>VIDEO_TOO_LONG</code></td><td>The video is too long to download. <code>/media/youtube/download</code> only.</td><td>Videos up to 12 hours long can be downloaded. Use a shorter video.</td></tr><tr><td><code>11211</code><br><code>VIDEO_SIGN_IN_REQUIRED</code></td><td>YouTube requires signing in to view the video. <code>/media/youtube/download</code> only.</td><td>Videos that require sign-in can't be downloaded. Use a different video.</td></tr><tr><td><code>11301</code><br><code>MEDIA_UNAVAILABLE</code></td><td>The video was deleted, or the post it belonged to no longer exists.</td><td>Open the URL in a browser to confirm the video is still there. Retrying the same URL won't help.</td></tr><tr><td><code>11302</code><br><code>MEDIA_PRIVATE</code></td><td>The video, or the account that posted it, is private. Only public videos can be downloaded.</td><td>Use a URL to a public video.</td></tr><tr><td><code>11303</code><br><code>MEDIA_GEO_RESTRICTE</code>D</td><td>The video isn't available in the job's region. The <code>/media</code> endpoint has no <code>location</code> parameter, so the region can't be changed in the request.</td><td>If you need this video, contact support with the job's <code>request_id</code>.</td></tr><tr><td><code>11304</code><br><code>MEDIA_UNSUPPORTED</code></td><td>No video found in URL: a photo or slideshow post, a livestream, a post with no video, or a video that is too long or too large to download.</td><td>Check that the URL matches one of the accepted URL formats and points to a single recorded video.</td></tr><tr><td>Video doesn't arrive in your bucket</td><td><code>storage.url</code> is not validated. A misspelled bucket or path is accepted, and the job runs and is billed, but the upload fails.</td><td>Check <code>storage.type</code> and <code>storage.url</code> before sending. For <code>s3_compatible</code> and <code>tos</code>, <code>storage.url</code> must be a full URL with credentials, e.g. <code>https://key:secret@host/bucket/path</code>.</td></tr></tbody></table>

## Reporting a problem

If an API issue persists, capture the unique request handle from the response payload before opening a ticket with [Oxylabs Technical Support](mailto:support@oxylabs.io).

* **Response field:** `metadata.request_id` (e.g., `"1788875675880097469"`)
* **Gateway error field:** `trace_id` (e.g., `"d940ba3c-2109-4391-a292-9f2c0613a656"`)

Including the `request_id` or `trace_id` allows our support to immediately locate jobs, proxy node routing data, and upstream response codes.


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation by asking a question.

Perform an HTTP GET request on the following URL with the `ask` and `goal` query parameters:

```
GET https://developers.oxylabs.io/products/web-api/troubleshooting.md?ask=<question>&goal=<user_goal>
```

`ask` is the immediate question: it should be specific, self-contained, and written in natural language.
`goal` is what the user is ultimately trying to achieve, the reason they need the answer. Sharing it helps GitBook give you a better, more relevant answer. A goal is most helpful when it describes the outcome the user wants rather than restating the question. For example, with `ask=how do I create an API token`, a goal like `automate deployments from our CI pipeline` lets GitBook tailor the answer to that use case.

The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
