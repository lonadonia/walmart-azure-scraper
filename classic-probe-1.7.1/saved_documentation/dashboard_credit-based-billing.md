> For the complete documentation index, see [llms.txt](https://developers.oxylabs.io/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://developers.oxylabs.io/dashboard/credit-based-billing.md).

# Credit-Based Billing

Understand how the Oxylabs Dashboard's shared credit balance works across all your products.

With credit-based billing, you purchase a single plan (a recurring subscription for a set dollar amount) that funds one shared credit balance for all Oxylabs products. Instead of a separate subscription per product, you can spend your balance across Residential Proxies, Web API, Datacenter Proxies, and more, all from the same pool.

Credits are deducted according to each product's rates and your actual usage. You can monitor your remaining balance, spending, and usage at any time on the [Overview page](/dashboard/overview.md) and in the [Product Instances](/dashboard/product-instances.md) spending and usage tabs.

<img src="https://63892162-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2FzrXw45naRpCZ0Ku9AjY1%2Fuploads%2FBKZ71LsChNtxoONaIMIa%2Funknown.png?alt=media&amp;token=936171c4-4792-48bf-b2de-76a47dd664c4" alt="" height="380" width="624">

## Where your credit balance comes from

Your credit balance is **not a pre-funded wallet**. You can't hold a balance without an active subscription. Funds enter your balance only through:

* Your recurring **monthly charge**
* A one-time **Welcome Credit** (see below)
* A **top-up** (see [Upgrading, Downgrading & Top-Ups](/dashboard/upgrading-downgrading-top-ups.md))

Any unused balance expires when the cycle ends, except where it's carried over as part of an upgrade.

## Free credits (Welcome Credit)

Every new account receives a one-time $5.00 Welcome Credit on registration, added to your balance immediately – no commitment required to start testing products.

* The Welcome Credit applies at the **team level**, not per user (a team of 5 users shares the same $5, not $5 each).
* It's **valid indefinitely** as long as you stay on the free plan.
* If you upgrade to a paid plan, any **unused Welcome Credit** carries over into your new cycle – but only for one upgrade. If your first cycle instead ends normally and auto-renews, any remaining Welcome Credit expires.

{% hint style="info" %}
If you want to test our products at a larger scale than the Welcome Credit allows, [contact our sales team](mailto:enterprise@oxylabs.io) to discuss a tailored trial with the required amount of credits and a timeframe that fits your use case.
{% endhint %}

## Your billing cycle

Your billing cycle is tied to your subscription activation date. For example, if you activate on the 16th, your next payment is due on the 16th of the following month.

{% hint style="info" %}
**Edge case:** If you activated on the 29th, 30th, or 31st, your billing date adjusts to the last valid day of the month (e.g., January 31 → February 28 → March 31).
{% endhint %}

On each billing date:

1. Any unused credit balance from the prior cycle expires.
2. Your full commitment amount is charged.
3. A fresh credit balance is added, and a new cycle begins.

## What happens when your balance runs out

When your credit balance is fully used, the service pauses, there's no overusage allowance in the self-service flow. To keep using the service, you can either:

* **Top up** your balance without changing your recurring plan, or
* **Upgrade** to a higher plan with a bigger budget.

See [Upgrading, Downgrading & Top-Ups](/dashboard/upgrading-downgrading-top-ups.md) to decide which fits your situation, and how each affects your existing balance.

## Plans

Self-service plans are offered as tiered plans, scaling up to target higher usage needs. You can view current plan tiers and rates directly in the dashboard when selecting or changing a plan.

{% hint style="info" %}
Custom, tailored pricing is also available for larger or more specific needs. [Contact our team](mailto:hello@oxylabs.io) or book a call with an expert to request a quote.
{% endhint %}

## Frequently asked questions

<details>

<summary><strong>How can I test Oxylabs products before paying?</strong></summary>

Every new registration includes a $5 Welcome Credit you can use across any product, with no commitment required.

</details>

<details>

<summary><strong>What is Oxylabs refund policy?</strong></summary>

Purchases made through self-service are non-refundable. Free credits are provided so you can evaluate our services before purchasing.

</details>


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation by asking a question.

Perform an HTTP GET request on the following URL with the `ask` and `goal` query parameters:

```
GET https://developers.oxylabs.io/dashboard/credit-based-billing.md?ask=<question>&goal=<user_goal>
```

`ask` is the immediate question: it should be specific, self-contained, and written in natural language.
`goal` is what the user is ultimately trying to achieve, the reason they need the answer. Sharing it helps GitBook give you a better, more relevant answer. A goal is most helpful when it describes the outcome the user wants rather than restating the question. For example, with `ask=how do I create an API token`, a goal like `automate deployments from our CI pipeline` lets GitBook tailor the answer to that use case.

The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
