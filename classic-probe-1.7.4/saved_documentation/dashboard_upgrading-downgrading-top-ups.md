> For the complete documentation index, see [llms.txt](https://developers.oxylabs.io/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://developers.oxylabs.io/dashboard/upgrading-downgrading-top-ups.md).

# Upgrading, Downgrading, Top-Ups

Learn how to change your plan or add credits without changing your recurring commitment, and when to choose one over the other.

You can upgrade, downgrade, or top up your plan at any time directly from the [Oxylabs Dashboard](https://dashboard.oxylabs.io) – no need to contact support.

## Top-ups

A top-up lets you add credits to your balance without changing your plan. Use a top-up when you just need a bit more budget to get through the current cycle, without purchasing a higher plan going forward.

* You can top up **any amount**, at any point during an active billing cycle.
* The amount is charged immediately and added to your credit balance right away.
* Top-up funds **expire at the end of the current billing cycle** – unless you upgrade before the cycle ends (see below), in which case unused top-up funds carry over.

{% hint style="success" %}
**Example:** You're on a $100/month plan, have $20 left in your balance, and top up $50. Your new balance is $70 for the rest of this cycle. If you don't upgrade, that $70 expires when the cycle ends.
{% endhint %}

### **Top-up or upgrade?**&#x20;

Choose a top-up if you only need extra budget for this cycle. Choose an upgrade if you expect to need more budget on an ongoing basis.

## Upgrading your plan

Upgrades **take effect immediately** and you get additional budget to spend right away.

### **What happens when you upgrade**

1. Your current billing cycle ends immediately.
2. Your unused balance (remaining monthly plan’s balance, any top-up funds, and Welcome Credit if you're still in your first cycle) is calculated and preserved as carry-over credit.
3. You're charged the full new plan amount.
4. A new billing cycle starts today, where a `new balance` = `new plan's cost` + `your carry-over credit`.

{% hint style="success" %}
**Example:** You're on a $100 plan with $50 unused. You upgrade to a $450 plan. You pay $450 now, but your new balance is: $450 + $50 = $500, and a new cycle starts today.
{% endhint %}

{% hint style="info" %}
The $5 Welcome Credit only carries over if you upgrade within your **first billing cycle**. If your first cycle ends normally and renews instead, any remaining Welcome Credit expires.
{% endhint %}

## Downgrading your plan

Downgrades are **scheduled** and take effect at the **start of your next billing cycle** – you'll keep your current plan's limits and balance until then.

### **What happens when you downgrade**

1. Your current plan and balance remain fully active until the current cycle ends.
2. On your next billing date, the lower-tier plan amount is charged and applied.
3. Any unused balance from the prior cycle expires as normal. **No carry-over occurs on a downgrade**.

{% hint style="success" %}
**Example:** You're on a $450 plan and request a downgrade to $100 on the 20th. You continue on the $450 plan until your renewal date on the 16th of next month, when the $100 plan and its balance take effect.
{% endhint %}

## Canceling instead of downgrading

If you want to stop using the service altogether rather than move to a lower tier, see [Payment Methods, Invoices & Cancellation](/dashboard/payments-and-invoices.md).


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation by asking a question.

Perform an HTTP GET request on the following URL with the `ask` and `goal` query parameters:

```
GET https://developers.oxylabs.io/dashboard/upgrading-downgrading-top-ups.md?ask=<question>&goal=<user_goal>
```

`ask` is the immediate question: it should be specific, self-contained, and written in natural language.
`goal` is what the user is ultimately trying to achieve, the reason they need the answer. Sharing it helps GitBook give you a better, more relevant answer. A goal is most helpful when it describes the outcome the user wants rather than restating the question. For example, with `ask=how do I create an API token`, a goal like `automate deployments from our CI pipeline` lets GitBook tailor the answer to that use case.

The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
