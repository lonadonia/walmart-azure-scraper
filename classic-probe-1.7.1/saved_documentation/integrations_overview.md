> For the complete documentation index, see [llms.txt](https://developers.oxylabs.io/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://developers.oxylabs.io/integrations/overview.md).

# Oxylabs Integrations

Find detailed third-party integration guides for Oxylabs proxies, Web Unblocker, and Web Scraper API (Classic).

{% hint style="success" %}
If you're integrating Oxylabs solutions to AI tools and agents, check out our [**AI Workflows**](/ai-workflows/overview.md) hub.
{% endhint %}

Oxylabs solutions are easy to integrate with the most popular third-party software. Choose your product and learn how to implement it into your workflows:

<table data-view="cards"><thead><tr><th align="center"></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td align="center"><h4><strong>Proxy integrations</strong></h4></td><td>Manage your proxies easily with the most popular apps, browsers or extensions.</td><td><a href="/integrations/proxy-integrations.md">Proxy Integrations</a></td></tr><tr><td align="center"><h4><strong>Web Unblocker integration</strong></h4></td><td>Integrate Web Unblocker to access the most difficult websites.</td><td><a href="/integrations/web-unblocker-integrations.md">Web Unblocker Integrations</a></td></tr><tr><td align="center"><h4><strong>Web Scraper API (Classic) integrations</strong></h4></td><td>Use Web Scraper API with SDKs, REST APIs, and AI frameworks.</td><td><a href="/integrations/web-scraper-api-integrations.md">Web Scraper API (Classic) Integrations</a></td></tr></tbody></table>


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation by asking a question.

Perform an HTTP GET request on the following URL with the `ask` and `goal` query parameters:

```
GET https://developers.oxylabs.io/integrations/overview.md?ask=<question>&goal=<user_goal>
```

`ask` is the immediate question: it should be specific, self-contained, and written in natural language.
`goal` is what the user is ultimately trying to achieve, the reason they need the answer. Sharing it helps GitBook give you a better, more relevant answer. A goal is most helpful when it describes the outcome the user wants rather than restating the question. For example, with `ask=how do I create an API token`, a goal like `automate deployments from our CI pipeline` lets GitBook tailor the answer to that use case.

The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
