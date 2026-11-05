> For the complete documentation index, see [llms.txt](https://developers.oxylabs.io/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://developers.oxylabs.io/products/web-api.md).

# Web API

Learn how to use and integrate Oxylabs Web API – an all-in-one REST API for web search and page data collection.

The Oxylabs Web API gives applications and AI agents live access to the open web through a unified REST interface. It handles JavaScript rendering, bot traffic challenges, proxy rotation, and geo-targeting through separate endpoint for different web data acquisition stages:

<table><thead><tr><th width="106">Endpoint</th><th width="504">Used for</th><th width="148">Input</th></tr></thead><tbody><tr><td><a href="/products/web-api/search.md">/search</a></td><td>Discovering and ranking organic web results.</td><td>Keyword / Query</td></tr><tr><td><a href="/products/web-api/scrape.md">/scrape</a></td><td>Rendering and extracting page data as Markdown, HTML, JSON, or Screenshot.</td><td>Page URL</td></tr></tbody></table>

{% hint style="success" %}
Web API endpoints are designed to be used together: **search to find, scrape to read.** `/search` descriptions are snippets, so anything you need to be accurate about comes from a `/scrape`.
{% endhint %}

## How to use it

### Get an API key

In the [Oxylabs dashboard](https://dashboard.oxylabs.io), create a **Web API** instance, get the API key from the product instance, and export it to your project environment (e.g. your OS terminal or the CLI terminal in the project workspace):

```bash
export OXYLABS_WEB_API_KEY=your_api_key_here
```

See [Authentication](/products/web-api/authentication.md) for key handling and rotation.

### Choose integration method

* **Plugging this into an AI agent (Claude Code, Cursor, or your own agent)?**\
  Check the [AI agent integrations](#ai-agent-integration) to start using it with one command.
* **Building your own integration?**\
  Follow the steps below to integrate directly using REST endpoints.

### Manual integration

{% stepper %}
{% step %}

#### Search

{% tabs %}
{% tab title="cURL" %}

```bash
curl https://webapi.oxylabs.io/v1/search \
  -H "Authorization: Bearer $OXYLABS_WEB_API_KEY" \
  -H 'Content-Type: application/json' \
  -d '{"query": "eu ai act compliance deadlines", "max_results": 3}'
```

{% endtab %}

{% tab title="Python" %}

```python
import os, requests

resp = requests.post(
    "https://webapi.oxylabs.io/v1/search",
    headers={"Authorization": f"Bearer {os.environ['OXYLABS_WEB_API_KEY']}"},
    json={"query": "eu ai act compliance deadlines", "max_results": 3},
    timeout=120,
)
resp.raise_for_status()

for r in resp.json()["results"]:
    print(r["metadata"]["position"], r["title"], r["url"], sep=" | ")
```

{% endtab %}

{% tab title="Node.js" %}

```javascript
const res = await fetch("https://webapi.oxylabs.io/v1/search", {
  method: "POST",
  headers: {
    Authorization: `Bearer ${process.env.OXYLABS_WEB_API_KEY}`,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({ query: "eu ai act compliance deadlines", max_results: 3 }),
});
if (!res.ok) throw new Error(`${res.status} ${await res.text()}`);

const { results } = await res.json();
results.forEach((r) => console.log(r.metadata.position, r.title, r.url));
```

{% endtab %}
{% endtabs %}

**Output sample**

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

See [/search](/products/web-api/search.md) for request parameters and output dictionary.
{% endstep %}

{% step %}

#### Scrape

Read the pages collected by `/search` or your URL list:

{% tabs %}
{% tab title="cURL" %}

```bash
curl https://webapi.oxylabs.io/v1/scrape \
  -H "Authorization: Bearer $OXYLABS_WEB_API_KEY" \
  -H 'Content-Type: application/json' \
  -d '{
      "url": "https://artificialintelligenceact.eu/implementation-timeline/",
      "output": ["markdown"]
  }'
```

{% endtab %}

{% tab title="Python" %}

```python
page = requests.post(
    "https://webapi.oxylabs.io/v1/scrape",
    headers={"Authorization": f"Bearer {os.environ['OXYLABS_WEB_API_KEY']}"},
    json={
        "url": "https://artificialintelligenceact.eu/implementation-timeline/",
        "output": ["markdown"],
    },
    timeout=120,
)
page.raise_for_status()
print(page.json()["results"][0]["markdown"][:2000])
```

{% endtab %}

{% tab title="Node.js" %}

```javascript
const page = await fetch("https://webapi.oxylabs.io/v1/scrape", {
  method: "POST",
  headers: {
    Authorization: `Bearer ${process.env.OXYLABS_WEB_API_KEY}`,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    url: "https://artificialintelligenceact.eu/implementation-timeline/",
    output: ["markdown"],
  }),
});
if (!page.ok) throw new Error(`${page.status} ${await page.text()}`);

const { results } = await page.json();
console.log(results[0].markdown.slice(0, 2000));
```

{% endtab %}
{% endtabs %}

See [/scrape](/products/web-api/scrape.md) for request parameters, output dictionary, delivery modes .
{% endstep %}

{% step %}

#### Combine: search-to-scrape

Search snippets (`outline`) are truncated and insufficient for deep analysis or LLM pipelines. The standard integration pattern queries `/v1/search` to discover authoritative links, then routes those URLs to `/v1/scrape` requesting Markdown output to strip unnecessary HTML artifacts.

Python example below shows both endpoints in a single workflow:

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
        timeout=120,
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

### AI agent integration

Connect the Web API directly to AI frameworks, coding assistants (Cursor, Claude Code), or custom agents.

#### Option 1: Integration Prompt

Paste the following complete prompt into an AI coding agent (Claude Code, Cursor, Copilot) to instruct it to build a custom integration following our technical specification:

{% code expandable="true" %}

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

The prompt points the agent at a single page with a full product source-of-truth: base URL, authorization, both endpoint schemas, reference code, error and retry rules, and an agent checklist.

You can find the complete agent specification reference in the [For Agents](/products/web-api/for-agents.md) page.

{% hint style="info" %}
**If the agent can't fetch URLs**, give it the full page instead. `for-agents.md` is plain Markdown and self-contained, so save it or paste it in above the prompt and drop the paragraph that names the URL. Keep the spec itself out of the prompt: the two retry rules are repeated there because an agent applies them mid-task, everything else belongs on the page so it can't drift.
{% endhint %}

#### Option 2: Agent skills

Install official agent skills to teach your AI agent research methodologies, source citation rules, and search-to-scrape execution:

```bash
npx skills add oxylabs/web-api-skills
```

For more installation options, see [Oxylabs Agent Skills](https://developers.oxylabs.io/ai-workflows/agent-skills).

#### Option 3: MCP server

Connect to or self-host our official MCP server to expose Web API search, scrape, and dedicated scraper tools directly to Claude Code, Cursor, or your custom AI agent by pointing your agent to the Oxylabs-hosted server – `https://mcp.oxylabs.io/web-api-mcp`:

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

To learn more about Web API MCP or how to self-host the official Oxylabs server server, see [MCP servers](https://developers.oxylabs.io/ai-workflows/mcp).

#### Skills or MCP?

<table data-header-hidden><thead><tr><th width="210"></th><th></th><th></th></tr></thead><tbody><tr><td></td><td><a href="https://developers.oxylabs.io/ai-workflows/agent-skills"><strong>Skills</strong></a></td><td><a href="https://developers.oxylabs.io/ai-workflows/mcp"><strong>MCP server</strong></a></td></tr><tr><td>Gives the agent</td><td>Judgment: when to search, which sources to trust, how to cite</td><td>Typed tools it can call directly</td></tr><tr><td>Needs a running process</td><td>No</td><td>Yes</td></tr><tr><td>Works in</td><td>Agents that load skill directories</td><td>Any MCP client</td></tr></tbody></table>

Installing both is an option. The server bundles `oxylabs-web-api` and serves it as the `oxylabs://skill/web-api` resource, so connecting it alone gives an agent both halves. Install the skills separately when you want them without a running server, or when you want migrate your codebase to Oxylabs.

## Learn more

<table data-header-hidden><thead><tr><th width="170"></th><th></th></tr></thead><tbody><tr><td><a href="/products/web-api/authentication.md"><strong>Authentication</strong></a></td><td>Key handling, header requirements, and authentication troubleshooting.</td></tr><tr><td><a href="/products/web-api/search.md"><strong>Search</strong></a></td><td>Full request parameters and response schemas for <code>/v1/search</code>.</td></tr><tr><td><a href="/products/web-api/scrape.md"><strong>Scrape</strong></a></td><td>Request parameters and output dictionary for <code>/v1/scrape</code>.</td></tr><tr><td><a href="/products/web-api/scrape/dedicated-scrapers.md"><strong>Dedicated Scrapers</strong></a></td><td>Target-specific parsed endpoints (Google, Amazon, YouTube, Walmart, etc.).</td></tr><tr><td><a href="/products/web-api/scrape/delivery-modes.md"><strong>Delivery Modes</strong></a></td><td>Realtime calls, async single-job polling/webhooks, and bulk batch queues.</td></tr><tr><td><a href="/products/web-api/scrape/ai-parsing.md"><strong>AI Parsing</strong></a></td><td>Extracting structured JSON using natural-language prompts or JSON Schemas.</td></tr><tr><td><a href="/products/web-api/troubleshooting.md"><strong>Troubleshooting</strong></a></td><td>HTTP status codes, retry logic, and troubleshooting tips.</td></tr></tbody></table>


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation by asking a question.

Perform an HTTP GET request on the following URL with the `ask` and `goal` query parameters:

```
GET https://developers.oxylabs.io/products/web-api.md?ask=<question>&goal=<user_goal>
```

`ask` is the immediate question: it should be specific, self-contained, and written in natural language.
`goal` is what the user is ultimately trying to achieve, the reason they need the answer. Sharing it helps GitBook give you a better, more relevant answer. A goal is most helpful when it describes the outcome the user wants rather than restating the question. For example, with `ask=how do I create an API token`, a goal like `automate deployments from our CI pipeline` lets GitBook tailor the answer to that use case.

The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
