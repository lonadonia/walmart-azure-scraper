# Page Not Found

The URL `api-targets/sitemap` does not exist. This page may have been moved, renamed, or deleted.

## Suggested Pages

You may be looking for one of the following:
- [Quick Start: Web API](https://developers.oxylabs.io/get-started/quick-start-web-api.md)
- [Dashboard API](https://developers.oxylabs.io/dashboard/dashboard-api.md)
- [Quick Start: Proxies](https://developers.oxylabs.io/get-started/quick-start-proxies.md)
- [Quick Start: Web Unblocker](https://developers.oxylabs.io/get-started/quick-start-web-unblocker.md)
- [Quick Start: Agent Browser](https://developers.oxylabs.io/get-started/quick-start-agent-browser.md)

## How to find the correct page

If the exact page cannot be found, you can still retrieve the information using the documentation query interface.

### Option 1 — Ask a question (recommended)

Perform an HTTP GET request on the following URL with the `ask` and `goal` query parameters:

```
GET https://developers.oxylabs.io/get-started/quick-start-web-api.md?ask=<question>&goal=<user_goal>
```

`ask` is the immediate question: it should be specific, self-contained, and written in natural language.
`goal` is what the user is ultimately trying to achieve, the reason they need the answer. Sharing it helps GitBook give you a better, more relevant answer. A goal is most helpful when it describes the outcome the user wants rather than restating the question. For example, with `ask=how do I create an API token`, a goal like `automate deployments from our CI pipeline` lets GitBook tailor the answer to that use case.

The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

### Option 2 — Browse the documentation index

Full index: https://developers.oxylabs.io/sitemap.md

Use this to discover valid page paths or navigate the documentation structure.

### Option 3 — Retrieve the full documentation corpus

Full export: https://developers.oxylabs.io/llms-full.txt

Use this to access all content at once and perform your own parsing or retrieval. It will be more expensive.

## Tips for requesting documentation

Prefer `.md` URLs for structured content, append `.md` to URLs (e.g., `/get-started/quick-start-web-api.md`).

You may also use `Accept: text/markdown` header for content negotiation.
