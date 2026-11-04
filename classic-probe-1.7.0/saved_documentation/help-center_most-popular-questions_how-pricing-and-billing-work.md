> For the complete documentation index, see [llms.txt](https://developers.oxylabs.io/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://developers.oxylabs.io/help-center/most-popular-questions/how-pricing-and-billing-work.md).

# How pricing and billing work

Everything you pay for runs through a single credit balance. Here's how it works and how to adjust it as your needs change.

### How credit-based billing works

With credit-based billing, you purchase a plan, a recurring subscription for a set dollar amount. That amount is added to a single credit balance shared across all your self-service products. Instead of a separate subscription for each one, you draw from one balance for [Residential Proxies](https://developers.oxylabs.io/products/proxies/residential-proxies), [Datacenter Proxies](https://developers.oxylabs.io/products/proxies/datacenter-proxies), [Web API,](https://developers.oxylabs.io/products/web-api) [Web Unblocker](https://developers.oxylabs.io/products/web-unblocker), [Agent Browser](https://developers.oxylabs.io/products/headless-browser), and the rest.

* The amount set in your plan is charged in full and added to your balance every billing cycle.
* Credit is deducted according to each product's rates as you use it.
* Unused credit expires at the end of the cycle and doesn't carry over on its own, except when you upgrade (see below).
* An active plan is required to use self-service products, aside from your welcome credit while you're evaluating.

Track your balance, spending, and usage under **Billing & Spending** in the dashboard.

<img src="https://1295635003-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2FpGNgdeKVOM3XvAaPheYj%2Fuploads%2FB2oSmQagstKpLLq5ghfw%2Funknown.png?alt=media&amp;token=4dcfb703-6d02-4e8b-b4e6-bd8543d23940" alt="" height="413" width="624">

### Try it yourself with your welcome credit

Every new Oxylabs account receives a **one-time $5 welcome credit**, added to your shared credit balance the moment you register. No payment information required. Use it to test any self-service product from your dashboard before committing to a plan.

* Shared at the team level, not per user. A 5-person team gets $5 total, not $5 each.
* Stays valid indefinitely while you're on the free plan (no active plan).
* Once you activate a plan, any unused welcome credit carries into that first billing cycle only. If you upgrade again within that same cycle, it carries over again. Once the cycle renews normally, any unused welcome credit expires.

**Example:** You receive $5 welcome credit and activate a $100 plan. Balance: $105 for that first cycle. If the cycle renews without changes, only the new $100 is available next cycle. The welcome credit is gone.

### Topping up vs. changing your plan

If your account balance runs low mid-cycle, you have two options.

**Top up.** A one-time payment added to your balance immediately, without changing your plan. Go to **Billing & Spending → Top up balance**. Funds expire at the end of the current cycle unless you also upgrade before it ends.

<img src="https://1295635003-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2FpGNgdeKVOM3XvAaPheYj%2Fuploads%2Fk5rG6sf4IvR1NNnvVDNG%2Funknown.png?alt=media&amp;token=4faf2c4a-2019-4f84-b656-96f733774592" alt="" height="165" width="624">

**Upgrade or downgrade.** This changes your plan itself.

* *Upgrades* take effect immediately. Your current cycle ends today, you're charged the new plan amount right away, and any unused balance, including top-ups and first-cycle welcome credit, carries into the new cycle.
* *Downgrades* are scheduled for your next billing date. You keep your current plan and balance until then, and unused balance does not carry over.

<img src="https://1295635003-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2FpGNgdeKVOM3XvAaPheYj%2Fuploads%2FY9Q2v3C6K5KTl4FoPWw7%2Funknown.png?alt=media&amp;token=bc4ef7e4-1266-479d-802c-43dc1b1ec90c" alt="" height="171" width="624">

<img src="https://1295635003-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2FpGNgdeKVOM3XvAaPheYj%2Fuploads%2FpsBod9mKeZ1mSJ5VBjBE%2Funknown.png?alt=media&amp;token=0e65ab83-9f28-4d39-9b92-1ca455575520" alt="" height="239" width="624">

**Use a top-up** for a temporary increase in usage, like a month that runs higher than usual. **Consider upgrading if** you're topping up most months. That usually means your plan is undersized.

***

### Need something bigger?

If you need custom pricing, a larger trial allocation, or dedicated support to evaluate Oxylabs at scale:

* [Book a call](https://app.apollo.io/#/meet/mr7-v5e-vps/15-min) with an Oxylabs expert
* Contact us via email at <hello@oxylabs.io>
* Message our 24/7 Customer Support via[ live chat](https://oxylabs.drift.click/oxybot)

***

Related: [How do I choose the right product?](https://developers.oxylabs.io/help-center/most-popular-questions/how-do-i-choose-the-right-product)

***

<a href="https://dashboard.oxylabs.io/en/" class="button primary">Head back to the dashboard</a><br>


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation by asking a question.

Perform an HTTP GET request on the following URL with the `ask` and `goal` query parameters:

```
GET https://developers.oxylabs.io/help-center/most-popular-questions/how-pricing-and-billing-work.md?ask=<question>&goal=<user_goal>
```

`ask` is the immediate question: it should be specific, self-contained, and written in natural language.
`goal` is what the user is ultimately trying to achieve, the reason they need the answer. Sharing it helps GitBook give you a better, more relevant answer. A goal is most helpful when it describes the outcome the user wants rather than restating the question. For example, with `ask=how do I create an API token`, a goal like `automate deployments from our CI pipeline` lets GitBook tailor the answer to that use case.

The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
