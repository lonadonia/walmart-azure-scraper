> For the complete documentation index, see [llms.txt](https://developers.oxylabs.io/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://developers.oxylabs.io/dashboard/dashboard-api.md).

# Dashboard API

Programmatic access to Oxylabs product users for tracking usage statistics with the Dashboard API.

The **Dashboard API** allows you to **access your product usage statistics** programmatically and integrate the metrics into your internal systems. This allows automated reporting and real-time usage monitoring without using the Oxylabs dashboard on the web.

{% hint style="info" %}
**Note:** Dashboard API currently supports **Datacenter Proxies (DC**) and **Agent Browser (HB)**. You can also track [**Residential Proxies**](/products/proxies/residential-proxies/public-api.md), [**Mobile Proxies**](/products/proxies/mobile-proxies/public-api.md), [**Web Unblocker**](/products/web-unblocker/usage-statistics.md), and [**Web Scraper API**](/products/web-scraper-api/usage-and-billing/usage-statistics.md) usage statistics with simple API requests.
{% endhint %}

All API requests flow through this base path:

```
https://api.oxylabs.io/
```

## Authentication

{% hint style="warning" %}
**Important:** To get your Dashboard API key, please contact our [**Customer Support**](mailto:support@oxylabs.io) team. Once requested, the key will be generated and given to you directly within one business day.
{% endhint %}

You must include the key in the `Authorization` header of every request using the `Bearer` scheme.

```
Authorization: Bearer {YOUR_API_KEY}
```

## Endpoints

Dashboard API includes endpoints for product Instance Discovery and Usage Statistics. All responses are delivered in JSON format.

<table><thead><tr><th width="236.8125">Endpoint</th><th>Description</th></tr></thead><tbody><tr><td><a href="#instance-discovery">Instance discovery</a></td><td>The request returns a paginated list of product instances your account is authorized to access. You can use the returned IDs to filter results when calling other endpoints.</td></tr><tr><td><a href="#usage-statistics">Usage statistics</a></td><td>The request returns aggregated usage statistics per product for the authenticated client's product instances.</td></tr></tbody></table>

### Instance Discovery

```
GET /stats/v1/filters/instances
```

#### Query parameters

<table><thead><tr><th width="166">Parameter</th><th width="268.0481770833333">Description</th><th>Type</th></tr></thead><tbody><tr><td><code>products[]</code></td><td>Filter by product. Accepted values: <code>HB</code> (Agent Browser), <code>DC</code> (Datacenter Proxies), <code>null</code> (all products).</td><td>Array of strings</td></tr><tr><td><code>page</code></td><td>Page number. Default: <code>1</code>.</td><td>Integer</td></tr><tr><td><code>per_page</code></td><td>Results per page. Default: <code>100</code>. Maximum: <code>100</code>.</td><td>Integer</td></tr></tbody></table>

#### Example request

To start filtering data, you first need to identify your specific resources. The following example shows how to list your available Datacenter Proxies (DC) and Agent Browser (HB) instances.

**Input sample**

```
GET /stats/v1/filters/instances?products[]=HB&products[]=DC&page=1&per_page=50
Authorization: Bearer {YOUR_API_KEY}
```

**Output sample**

```json
{
  "data": [
    {
      "uuid": "my-hb-instance-uuid",
      "name": "my-hb-instance",
      "status": "enabled",
      "product": "HB"
    },
    {
      "uuid": "my-dc-instance-uuid",
      "name": "my-dc-instance",
      "status": "disabled",
      "product": "DC"
    }
  ],
  "meta": {
    "pagination": {
      "page": 1,
      "per_page": 50,
      "total_items": 2,
      "total_pages": 1
    }
  }
}
```

#### Response fields

<table><thead><tr><th width="166">Field</th><th width="268.0481770833333">Description</th><th>Type</th></tr></thead><tbody><tr><td><code>uuid</code></td><td>Unique identifier for the instance.</td><td>String (UUID)</td></tr><tr><td><code>name</code></td><td>Instance name as configured in the dashboard.</td><td>String</td></tr><tr><td><code>status</code></td><td>Product instance status (e.g., <code>enabled</code> or <code>disabled</code>).</td><td>String</td></tr><tr><td><code>product</code></td><td>Product identifier (e.g., <code>HB</code> (Agent Browser), <code>DC</code> (Datacenter Proxies), etc.).</td><td>String</td></tr><tr><td><code>page</code></td><td>Current page number.</td><td>Integer</td></tr><tr><td><code>per_page</code></td><td>Number of results on this page.</td><td>Integer</td></tr><tr><td><code>total_items</code></td><td>Total matching records across all pages.</td><td>Integer</td></tr><tr><td><code>total_pages</code></td><td>Total number of pages. Always at least <code>1</code>, even when there are no results.</td><td>Integer</td></tr></tbody></table>

### Usage Statistics

```
GET /stats/v1/usage
```

{% hint style="warning" %}
**Important:** The maximum date range for a single request (the difference between `date_to` and `date_from`) is **31 days**. To retrieve usage data for a longer period, please perform your queries in 31-day batches.
{% endhint %}

#### Query parameters

<table><thead><tr><th width="166">Parameter</th><th width="268.0481770833333">Description</th><th>Type</th></tr></thead><tbody><tr><td><mark style="background-color:green;"><code>product</code></mark></td><td>Product identifier (e.g., <code>HB</code> (Agent Browser), <code>DC</code> (Datacenter Proxies), etc.)</td><td>String</td></tr><tr><td><mark style="background-color:green;"><code>date_to</code></mark></td><td>Start date, inclusive (e.g., UTC <code>YYYY-MM-DDTHH:mm:ssZ</code> or offset-aware <code>YYYY-MM-DDTHH:mm:ss+02:00</code>).</td><td>Date (ISO 8601)</td></tr><tr><td><mark style="background-color:green;"><code>date_from</code></mark></td><td>End date, inclusive. Same format as <code>date_to</code>.</td><td>Date (ISO 8601)</td></tr><tr><td><mark style="background-color:green;"><code>group_by</code></mark></td><td>Result grouping options. Accepted values: <code>DAY</code>, <code>TARGET</code>, <code>INSTANCE</code>. Multiple values can be combined. The order of values determines the order of data grouping.</td><td>Array of strings</td></tr><tr><td><code>instances[]</code></td><td>Filter results to specific instances. Accepts multiple UUIDs obtained from <code>GET /stats/v1/filters/instances</code>. Invalid or unrecognized UUIDs are ignored.</td><td>UUID (Array of strings)</td></tr><tr><td><code>page</code></td><td>Page number. Default: <code>1</code>.</td><td>Integer</td></tr><tr><td><code>per_page</code></td><td>Results per page. Default: <code>100</code>. Maximum: <code>100</code>.</td><td>Integer</td></tr></tbody></table>

\- mandatory parameter

#### Example requests

**1. Group by TARGET**

The following example shows how to retrieve usage metrics for Agent Browser (`HB`) by grouping results by target, to see the total request count and traffic volume for each target within the selected date range.

**Input sample**

```
GET /stats/v1/usage?product=HB&date_from=2025-11-01T00:00:00Z&date_to=2025-11-30T23:59:59Z&group_by[]=TARGET
Authorization: Bearer {YOUR_API_KEY}
```

**Output sample**

```json
{
  "data": [
    {"grouped_by": ["some.target.A"], "requests": 10, "traffic_bytes": 100},
    {"grouped_by": ["some.target.B"], "requests": 10, "traffic_bytes": 100}
  ],
  "totals": {
    "requests": 20,
    "traffic_bytes": 200
  },
  "meta": {
    "pagination": {
      "page": 1,
      "per_page": 50,
      "total_items": 100,
      "total_pages": 2
    },
    "grouping": ["TARGET"]
  }
```

**2. Group by DAY + TARGET**

This example shows how to break down Agent Browser (`HB`) usage by both `Day` and `Target` to see exactly how much traffic each target consumed on a day-by-day basis.

**Input sample**

```
GET /stats/v1/usage?product=HB&date_from=2025-11-01T00:00:00Z&date_to=2025-11-30T23:59:59Z&group_by[]=DAY&group_by[]=TARGET
Authorization: Bearer {YOUR_API_KEY}
```

**Output sample**

```json

  "data": [
    {"grouped_by": ["2025-11-01", "some.target.A"], "requests": 10, "traffic_bytes": 100},
    {"grouped_by": ["2025-11-01", "some.target.B"], "requests": 10, "traffic_bytes": 100},
    {"grouped_by": ["2025-11-02", "some.target.A"], "requests": 10, "traffic_bytes": 100},
    {"grouped_by": ["2025-11-02", "some.target.B"], "requests": 10, "traffic_bytes": 100}
  ],
  "totals": {
    "requests": 40,
    "traffic_bytes": 400
  },
  "meta": {
    "pagination": {
      "page": 1,
      "per_page": 50,
      "total_items": 200,
      "total_pages": 4
    },
    "grouping": ["DAY", "TARGET"]
  }
}
```

#### Response fields

<table><thead><tr><th width="190">Field</th><th width="344.0481770833333">Description</th><th>Type</th></tr></thead><tbody><tr><td><code>grouped_by</code></td><td>Grouping options in the same order as the requested <code>group_by</code> parameters.</td><td>Array of strings</td></tr><tr><td><code>data.requests</code></td><td>Total request count for the grouped period/dimension combination.</td><td>Integer</td></tr><tr><td><code>data.traffic_bytes</code></td><td>Total traffic in bytes for the grouped period/dimension combination.</td><td>Integer</td></tr><tr><td><code>totals</code></td><td>Total aggregated values for the selected period.</td><td>Object</td></tr><tr><td><code>totals.requests</code></td><td>Total request count across the entire selected period.</td><td>Integer</td></tr><tr><td><code>totals.traffic_bytes</code></td><td>Total traffic in bytes across the entire selected period.</td><td>Integer</td></tr><tr><td><code>page</code></td><td>Current page number.</td><td>Integer</td></tr><tr><td><code>per_page</code></td><td>Number of results on this page.</td><td>Integer</td></tr><tr><td><code>total_items</code></td><td>Total matching records across all pages.</td><td>Integer</td></tr><tr><td><code>total_pages</code></td><td>Total number of pages. Always at least <code>1</code>, even when there are no results.</td><td>Integer</td></tr><tr><td><code>meta.grouping</code></td><td>The active grouping options in the order they appear in <code>grouped_by</code>. Mirrors the <code>group_by</code> request parameter.</td><td>Array of strings</td></tr></tbody></table>

## Rate Limits

To ensure stability, Dashboard API rate limits are applied per API key and per client account for all requests.

* `10` requests per API key
* `100` requests across all API keys of an individual client

## Error Handling

Here are some common error types that you can get while using the Dashboard API:

<table><thead><tr><th width="166">Error code</th><th width="268.0481770833333">Error message</th><th>Description</th></tr></thead><tbody><tr><td><code>400</code></td><td>Bad request</td><td>The request could not be understood. Please check if the request is formatted correctly.</td></tr><tr><td><code>401</code></td><td>Invalid request</td><td>User has entered an invalid API key.</td></tr><tr><td><code>403</code></td><td>Forbidden</td><td>Access denied: missing API key. Please contact support or your account manager.</td></tr><tr><td><code>429</code></td><td>Too many requests</td><td>User has reached the thread/concurrent session limit.</td></tr><tr><td><code>500</code></td><td>Internal server error</td><td>We had an unexpected problem with the server. Try again later.</td></tr></tbody></table>

For questions, access issues, or integration support, please contact [**support@oxylabs.io**](mailto:support@oxylabs.io) or your account manager. When reporting a problem, please include:

* The endpoint and query parameters used
* The HTTP status code returned
* The full response body (redact your API key before sharing)
* Timestamps of the failing requests (UTC preferred)


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation by asking a question.

Perform an HTTP GET request on the following URL with the `ask` and `goal` query parameters:

```
GET https://developers.oxylabs.io/dashboard/dashboard-api.md?ask=<question>&goal=<user_goal>
```

`ask` is the immediate question: it should be specific, self-contained, and written in natural language.
`goal` is what the user is ultimately trying to achieve, the reason they need the answer. Sharing it helps GitBook give you a better, more relevant answer. A goal is most helpful when it describes the outcome the user wants rather than restating the question. For example, with `ask=how do I create an API token`, a goal like `automate deployments from our CI pipeline` lets GitBook tailor the answer to that use case.

The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
