> For the complete documentation index, see [llms.txt](https://developers.oxylabs.io/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://developers.oxylabs.io/get-started/quick-start-web-api.md).

# Quick Start: Web API

Get from an API key to your first Oxylabs Web API search and scrape in just five minutes.

{% hint style="success" %}
Already familiar with the basics? Check out [Web API documentation](/products/web-api.md).
{% endhint %}

[**Oxylabs Web API**](https://oxylabs.io/products/web-api) gives your application or your AI agent two things the open web makes surprisingly hard: **finding the right, fresh pages, and extracting their data reliably**. One endpoint searches the live web and the other scrapes any page (rendering JavaScript and handling access challenges) and hands back clean data ready for use.

<table><thead><tr><th width="159">Endpoint</th><th>Gives you</th><th>Use it when</th></tr></thead><tbody><tr><td><a href="https://developers.oxylabs.io/products/web-api/search"><code>POST /v1/search</code></a></td><td>Ranked results: title, description, URL</td><td>You don't know which page holds the answer</td></tr><tr><td><a href="https://developers.oxylabs.io/products/web-api/scrape"><code>POST /v1/scrape</code></a></td><td>One page as Markdown, HTML, JSON or a screenshot</td><td>You know the URL and need what's on it</td></tr></tbody></table>

They are designed to be used together: **search to find, scrape to extract.** This quick start guide covers:

* **Manual integration** – your own code calling the API directly.
* **Easy AI integration** – using the Web API through a proprietary or your custom AI agent.

{% hint style="success" %}
Want to test Web API in a simple UI-based environment before full implementation? Check out [Web API Playground](https://developers.oxylabs.io/products/web-api/playground).
{% endhint %}

## Setup & API key <a href="#docs-internal-guid-4566d081-7fff-6c77-5105-4c81aa345516" id="docs-internal-guid-4566d081-7fff-6c77-5105-4c81aa345516"></a>

1. **Create an account:** Sign up at the [Oxylabs Dashboard](https://dashboard.oxylabs.io/).
2. **Add a product instance:** Click **+ Add product instance** and select Web API in the Web access category.
3. **Set up:** Choose the instance name, product usage limits (optional), and create the instance.
4. **Get credentials:** Click on the Web API instance in the dashboard home instance table and get your API key.
5. **Export your API key** into your project environment (e.g. your OS terminal or the CLI terminal in the project workspace):

```bash
export OXYLABS_WEB_API_KEY=your_api_key_here
```

{% hint style="info" %}
**Note:** Always keep your key server-side. Never commit it to source control or expose it in client-side code.
{% endhint %}

## Web API integration

#### Plugging this into an AI agent?

Skip to [AI agent integrations](#ai-agent-integration) to start using it with one command.

#### Building your own custom integration?

Start the manual integration below.

### Manual integration

Depending on your data needs, you can use the Web API endpoints separately for web search, scraping, or as full data collection and delivery pipeline.

{% stepper %}
{% step %}

#### Search for pages (`/search`)

Find which pages hold the answer to your defined `query`:

```bash
curl https://webapi.oxylabs.io/v1/search \
  -H "Authorization: Bearer $OXYLABS_WEB_API_KEY" \
  -H 'Content-Type: application/json' \
  -d '{"query": "eu ai act compliance deadlines", "max_results": 3}'
```

<details>

<summary>Output sample</summary>

```json
{
  "state": "done",
  "results": [
    {
      "title": "Implementation Timeline | EU Artificial Intelligence Act",
      "outline": [
        "Date 2 August 2025 Providers: need to be compliant with the AI Act by 2 August 2027..."
      ],
      "url": "https://artificialintelligenceact.eu/implementation-timeline/",
      "metadata": { "position": 1 }
    }
  ],
  "params": { "query": "eu ai act compliance deadlines", "location": null, "max_results": 3 },
  "metadata": { "timestamp": 1787431568, "request_id": "1788875675880097469" }
}
```

</details>
{% endstep %}

{% step %}

#### Scrape a page (`/scrape`)

Scrape full page content from any public website by passing the target `url` and the desired output format (`markdown`, `html`, `json`, `screenshot`). Here's a request for page content in Markdown:

```bash
curl https://webapi.oxylabs.io/v1/scrape \
  -H "Authorization: Bearer $OXYLABS_WEB_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://artificialintelligenceact.eu/implementation-timeline/",
       "output": ["markdown"]}'
```

{% endstep %}

{% step %}

#### Full pipeline (search-to-scrape)

`outline` found in `/search` is a list of truncated snippets and often not useful for advanced use cases or AI workflows.

To get structured data from a single query, search the web with `/search` for relevant data according to your `query` and pass the result URL to `/scrape` for data retrieval. Here's a full working Python example:

{% code expandable="true" %}

```python
import os, requests

API = "https://webapi.oxylabs.io"
HEADERS = {"Authorization": f"Bearer {os.environ['OXYLABS_WEB_API_KEY']}"}

def research(question: str, read_top: int = 2) -> list[dict]:
    # 1. Discover target URLs
    hits = requests.post(
        f"{API}/v1/search",
        headers=HEADERS,
        json={"query": question, "max_results": 10},
    )
    hits.raise_for_status()
    # 2. Extract full page content as Markdown
    pages = []
    for hit in hits.json()["results"][:read_top]:
        page = requests.post(
            f"{API}/v1/scrape",
            headers=HEADERS,
            json={"url": hit["url"], "output": ["markdown"]},
            timeout=120,
        )
        if not page.ok:
            print(f"skipped {hit['url']}: {page.status_code}")
            continue
        pages.append(
            {
                "url": hit["url"],
                "title": hit["title"],
                "content": page.json()["results"][0]["markdown"],
            }
        )
    return pages

for page in research("eu ai act compliance deadlines"):
    print(f"--- {page['title']} ({page['url']})")
    print(page["content"][:500])
```

{% endcode %}
{% endstep %}
{% endstepper %}

{% hint style="info" %}
**Everything above is realtime – the result comes back in the response.** For high volume data collection we recommend running scrapers as jobs under `/v1/async/scrape` and deliver by polling, callback or straight to your bucket. See [Delivery modes](https://developers.oxylabs.io/products/web-api/scrape/delivery-modes).
{% endhint %}

### AI agent integration

Oxylabs Web API is designed for easy AI agent workflows using **Agent Skills**, **MCP** (Model Context Protocol) or simple **one-prompt integrations**. Once you have your API key, choose the integration method.

{% tabs %}
{% tab title="One-Prompt Integration" icon="rectangle-terminal" %}
**One-page integration prompt – paste a prompt into a coding agent and have it build a custom integration for you.**

If you want an AI coding assistant (like Claude Code, Cursor, or Copilot) to build an integration for you, paste the following prompt:

{% code overflow="wrap" expandable="true" %}

```
Integrate the Oxylabs Web API into this project for live web search and page reading.

Read https://developers.oxylabs.io/products/web-api/for-agents.md and follow
it. It has the base URL, auth, both endpoint schemas, reference code, the error and retry
rules, and the checklist to satisfy. If the page does not load, stop and tell me; do not
reconstruct the API from memory.

Decide the path and tell me before writing anything:
- Will this project's own code call the API at runtime? -> write the client the page
  specifies, matching how this codebase already makes outbound HTTP calls.
- Is the web access for you during this session rather than for the project's code?
  -> install the MCP server and the skills, the way the page describes.

The key is in OXYLABS_WEB_API_KEY or a .env here. If it is in neither, ask me. Never
print the key: not in code, logs, tests, or your replies to me.

Prove it works before writing tests: make one real search, scrape one URL from the
results, and show me both request ids. If a call returns 401, stop and tell me.

When a scrape comes back empty or skeletal, retry it once with run_js: true. If it is still
empty and the site is on a country TLD (.lt, .es, .co.uk), retry once more with run_js and
location set to that country, then report the page as unreadable.

Then add a test for the retry and error mapping against a mocked transport and run it.
If you cannot run commands in this environment, say so once and give me the exact
commands to run instead.

Report back: the path you took, each checklist item on the page marked done or not,
what I still need to do myself, and anything you could not finish. Do not ask me
whether to proceed; do the work.
```

{% endcode %}

See a full example and learn more about Web API integration in the [documentation](https://developers.oxylabs.io/products/web-api).
{% endtab %}

{% tab title="Agent Skills" icon="head-side-gear" %}
**Agent skills – installs the knowledge on how to use the API, no running server required.**

Add official agent skills that teach your AI agent how to search, scrape, cite sources, and handle web research through Oxylabs Web API using the following terminal command:

```bash
npx skills add oxylabs/web-api-skills
```

Now your agent knows all there is to know about Oxylabs Web API and how to use it. To learn more about Web API agent skills, see our [documentation](https://developers.oxylabs.io/ai-workflows/agent-skills).
{% endtab %}

{% tab title="MCP Server" icon="server" %}
**MCP server – typed tools for search, scrape, and dedicated scrapers for any MCP client.**

Connect to or self-host our official MCP server to expose Web API search, scrape, and extract tools directly to Claude Code, Cursor, or your custom AI agent.

For easiest implementation, add the server to your client by pointing your agent to the Oxylabs-hosted server – `https://mcp.oxylabs.io/web-api-mcp`:

<details>

<summary><i class="fa-claude">:claude:</i>  <strong>Claude Code</strong></summary>

```bash
claude mcp add --transport http --scope user oxylabs-web-api \
  https://mcp.oxylabs.io/web-api-mcp \
  --header "Authorization: Bearer ${OXYLABS_WEB_API_KEY}"
```

</details>

<details>

<summary><i class="fa-openai">:openai:</i>  <strong>ChatGPT/Codex</strong></summary>

```bash
codex mcp add oxylabs-web-api \
  --url https://mcp.oxylabs.io/web-api-mcp \
  --bearer-token-env-var OXYLABS_WEB_API_KEY
```

</details>

<details>

<summary><i class="fa-cursor">:cursor:</i>  <strong>Cursor</strong> (or other clients supporting custom headers)</summary>

For any client that supports remote MCP servers with custom headers, add the server URL and an `Authorization` header to the client's MCP configuration. For example, in Cursor's `mcp.json`:

```json
{
  "mcpServers": {
    "oxylabs-web-api": {
      "url": "https://mcp.oxylabs.io/web-api-mcp",
      "headers": {
        "Authorization": "Bearer ${env:OXYLABS_WEB_API_KEY}"
      }
    }
  }
}
```

Field names can differ between clients – check your client's documentation for how to add a remote MCP server with headers.

</details>

To learn more about Web API MCP integration or how to self-host the official Oxylabs server server, see [MCP servers](https://developers.oxylabs.io/ai-workflows/mcp).
{% endtab %}
{% endtabs %}

### Essential parameters

#### /search <a href="#docs-internal-guid-5786cd1b-7fff-0a37-d2dd-abcf76c7e3ef" id="docs-internal-guid-5786cd1b-7fff-0a37-d2dd-abcf76c7e3ef"></a>

<table><thead><tr><th width="121">Parameter</th><th width="86">Type</th><th>Description</th></tr></thead><tbody><tr><td><code>query</code></td><td>string</td><td>Search keyword or phrase</td></tr><tr><td><code>max_results</code></td><td>integer</td><td>Number of organic search results to return (<code>1-20</code>)</td></tr><tr><td><code>location</code></td><td>string</td><td>2-letter country code (e.g., <code>"DE"</code>, <code>"US"</code>) for localized search</td></tr></tbody></table>

#### /scrape

<table><thead><tr><th width="111">Parameter</th><th width="99">Type</th><th>Description</th></tr></thead><tbody><tr><td><code>url</code></td><td>string</td><td>URL to scrape</td></tr><tr><td><code>output</code></td><td>array</td><td>Formats to return: <code>"html"</code> (default), <code>"markdown"</code>, <code>"json"</code>, <code>"screenshot"</code></td></tr><tr><td><code>json</code></td><td>object</td><td>Used for custom AI parsing through prompt or schema</td></tr><tr><td><code>location</code></td><td>string</td><td>2-letter country code (e.g., <code>"DE"</code>, <code>"US"</code>). Some dedicated scrapers use a different format. See <a href="/products/web-api/scrape/dedicated-scrapers.md">Dedicated Scrapers</a>.</td></tr><tr><td><code>run_js</code></td><td>boolean</td><td>Renders the page in a real browser before capturing content. Slower, use a client timeout of <code>150</code>s or more.</td></tr><tr><td><code>device</code></td><td>string</td><td>Device emulation: <code>"desktop"</code> (default) or <code>"mobile"</code>.</td></tr></tbody></table>

### Common response codes

<table><thead><tr><th width="112">Status</th><th width="322">Meaning</th><th>Retry?</th></tr></thead><tbody><tr><td><code>200</code> / <code>202</code></td><td>Success. Realtime / async job accepted</td><td>–</td></tr><tr><td><code>400</code></td><td>Malformed request</td><td>No, fix the field named in <code>errors[].pointer</code>.</td></tr><tr><td><code>401</code></td><td>Authentication error (bad or missing API key).</td><td>No, check the key on your Web API instance</td></tr><tr><td><code>429</code></td><td>Rate limit or spent quota</td><td>Rate limit: yes, with backoff. Quota: no.</td></tr><tr><td><code>5xx</code></td><td>Upstream failure or failed to scrape</td><td>Yes, up to ~3 attempts with backoff.</td></tr></tbody></table>

See all [response codes](https://developers.oxylabs.io/products/web-api/troubleshooting) to learn about all status codes and find troubleshooting tips.

## Next steps

* **Want the full picture of the product?** See the [Web API documentation](https://developers.oxylabs.io/products/web-api).
* **Building your first custom requests?** Prototype faster with [Web API Playground](https://developers.oxylabs.io/products/web-api/playground).
* **Need data from a specific site?** Check out all Web API [Dedicated Scrapers](https://developers.oxylabs.io/products/web-api/scrape/dedicated-scrapers).
* **Want structured JSON from any page?** Try Web API's built-in [AI Parsing](https://developers.oxylabs.io/products/web-api/scrape/ai-parsing).
* **Scraping at volume or delivering to cloud storage?** Learn more about available [Delivery Modes](https://developers.oxylabs.io/products/web-api/scrape/delivery-modes).
* **Want an AI agent to use the Web API without you writing code?** Try official Oxylabs [MCP server](https://developers.oxylabs.io/ai-workflows/mcp) or [Agent Skills](https://developers.oxylabs.io/ai-workflows/agent-skills).


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation by asking a question.

Perform an HTTP GET request on the following URL with the `ask` and `goal` query parameters:

```
GET https://developers.oxylabs.io/get-started/quick-start-web-api.md?ask=<question>&goal=<user_goal>
```

`ask` is the immediate question: it should be specific, self-contained, and written in natural language.
`goal` is what the user is ultimately trying to achieve, the reason they need the answer. Sharing it helps GitBook give you a better, more relevant answer. A goal is most helpful when it describes the outcome the user wants rather than restating the question. For example, with `ask=how do I create an API token`, a goal like `automate deployments from our CI pipeline` lets GitBook tailor the answer to that use case.

The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
