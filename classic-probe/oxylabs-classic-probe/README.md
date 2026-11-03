# oxylabs-classic-probe 1.5.2

An **offline** probe and request plan for the Oxylabs **Classic** Web Scraper API (Realtime method). It holds three things:

- the documented request contract;
- the checks a Classic response must pass before anything more is sent;
- one durable ledger that enforces the proposed campaign limits for both retailers together.

**Its live mode is disabled.** No command of this build sends a request to Oxylabs or to a retailer, and no command reads a credential.

**This artifact implements the Walmart stage only** (Walmart #3891, 3900 Fountain Square Pl, Waukegan, IL 60085, Pickup). The shared ledger reserves Mariano's share of the campaign, 10 requests and USD 2.25, so that Walmart cannot use it. Reserving that share does not implement or qualify a Mariano's adapter: this build has none and plans nothing for Mariano's.

Version 1.5.2 changes no behaviour of version 1.5.0. It adds this statement, the documentation recheck of 2026-11-01 and one open question in [docs/DOCUMENTED_CONTRACT.md](docs/DOCUMENTED_CONTRACT.md).

This package is separate from the Walmart collector (`../walmart-azure-headless`). It does not use the collector's Oxylabs Web API or Scrape.do accounts, and nothing here is evidence of what Classic returns.

| What | Status in this build |
| --- | --- |
| Request contract (payload forms, parameter names) | Built from the official documentation read on 2026-10-31 ([docs/DOCUMENTED_CONTRACT.md](docs/DOCUMENTED_CONTRACT.md)) |
| Response checks (store, fulfillment, identity, pagination, challenge, parser status) | **SYNTHETIC TEST**: tested against invented responses shaped like the documented envelope |
| Shared ledger (10 per retailer, 20 total, 30 minutes, USD 5, headroom, deadline) | **SYNTHETIC TEST**: tested offline, including concurrent processes and crashes |
| A Classic request | **NOT TESTED**: none was made. That needs the account owner's credentials, entitlement, rates and approval |
| Mariano's | **NOT TESTED**: no adapter in this probe. Its share of the limits stays reserved |

## What this build will not do

- Send a request. `HttpTransport` refuses to be built while `gates.LIVE_ENABLED` is `False`. Changing that takes a code change, a new version and the owner's approval.
- Read a credential. `live` lists what a campaign still lacks, and it refuses before any credential is looked at.
- Probe an account. There are no automatic balance, usage, entitlement, authentication or qualification calls. The documented usage endpoint is never called.
- Use another service's results to qualify Classic. Results from the Walmart collector's providers say nothing about Classic.
- Assume pagination, store targeting or broader access works. Every one of them is checked in the response itself.

## Install and check (offline)

```
uv sync --frozen
uv run pytest
uv run ruff check src tests
uv run mypy
```

The tests close the network: any attempt to open a socket or resolve a name fails the test that made it. They also remove the two credential variables from their environment.

## Commands

All commands are offline. `classic-probe --help` and `python -m classic_probe --help` show the same list.

| Command | Reads | Writes | Sends |
| --- | --- | --- | --- |
| `plan --targets config/targets.json [--rates FILE]` | the targets, an optional rate card | nothing | nothing |
| `validate --targets config/targets.json [--rates FILE]` | the same | nothing | nothing |
| `campaign-init --manifest M --ledger L --campaign-id ID [--offline]` | nothing | a new ledger and its manifest (refuses to replace either) | nothing |
| `status --manifest M` | the ledger | nothing | nothing |
| `confirm-charge --manifest M --seq N --value V --unit U --basis TEXT` | the ledger | one confirmed charge, with where it was read | nothing |
| `export --manifest M --out DIR` | the ledger | `ledger_export.json` | nothing |
| `replay --targets T --fixtures DIR --rates FILE --out DIR` | saved responses | a new offline ledger and the evidence | nothing (OFFLINE REPLAY) |
| `live --manifest M [--approval F] [--entitlement F] [--rates F]` | those files | nothing | nothing: always refused in this build |

Exit codes: `0` ok, `2` refused input, `3` live refused, `4` the campaign stopped, `5` evidence export failed.

## The campaign limits (proposed; ceilings, never raised)

| Limit | Value | Enforced by |
| --- | --- | --- |
| Requests per retailer | 10, including setup, authentication or qualification calls, every retry and every restart | `Ledger.reserve`: the 11th is never reserved |
| Requests for both retailers | 20 | the same check, across both retailers |
| Campaign time | 30 minutes for the combined campaign, from its first reservation | each reservation must end before the end less 3 minutes kept for evidence export and cleanup |
| Provider charges | USD 5.00 combined, less USD 0.50 of headroom for delayed or uncertain charges | each request reserves its worst-case charge. Each retailer's share is USD 2.25 and is not borrowed |

A request exists in the ledger before it is sent:

1. `BEGIN IMMEDIATE` serializes concurrent invocations.
2. Each request reserves its worst-case charge before it leaves.
3. The reservation stays until the owner records a confirmed charge with its basis.

So a crash after a reservation, a request with no answer and a response the documentation says is not billed all keep their reservation. A row is never deleted and a reservation never changes; database triggers refuse both. The first stop stays the campaign's reason.

What keeps a second execution from granting itself a fresh budget:

- `open` never creates a ledger.
- Every ledger has a random genesis id, and the owner's approval must name it.
- A ledger is bound to its host.
- A path on a network share is refused.

## The Walmart steps

[docs/PAYLOAD_MATRIX.md](docs/PAYLOAD_MATRIX.md) has each payload in full.

1. `walmart-search-p1`: `walmart_search` for the store's Pickup results, with `?type=raw,parsed`.
2. `walmart-search-p2`: the same with `start_page: 2`, sent only when page 1's `last_visible_page` shows a page 2.
3. `walmart-product`: `walmart_product` for page 1's first non-sponsored Walmart.com product with a Pickup line.
4. `walmart-category-url`: a required category page by its URL alone. The documentation states no store or fulfillment parameter for this form. It is last because a page for any other store stops the campaign.

Store, fulfillment and identity are read from Walmart's own page data in the raw result. The readers are the Walmart collector's validated readers, vendored unchanged in `src/classic_probe/vendor/` (`VENDORED.json` has their origin and SHA-256). The parsed result has to agree with them.

These stop the campaign, and nothing more is sent after them:

- **The retailer refuses:** a challenge or refusal page, or a retailer status that is not 2xx.
- **Wrong or missing context:** another store or fulfillment, a parsed location that disagrees, no raw page to read the store from.
- **Wrong product or page:** a product page for another item, a page 2 that repeats page 1, an empty page.
- **Unusable response:** a body outside the documented structure, a failed parser status.
- **Account problems:** HTTP 401, 403, 400 or 422.
- **Limits:** a limit is reached, or a request is still open at its deadline. Its charge is then unknown and its reservation stays.

A documented temporary error (429, 500, 524, 612, 613) is retried at most once, and only within every limit. The retry is a new dispatch with its own reservation.

## Files

| Path | What |
| --- | --- |
| `config/targets.json` | the two retailers. Walmart #3891 Waukegan, Pickup, store verified from Walmart's own data. Mariano's Vernon Hills, Pickup, store id not verified, no adapter |
| `config/*.example.json`, `.env.example` | placeholders only. No rate, approval, entitlement or credential ships with the probe |
| `docs/DOCUMENTED_CONTRACT.md` | what the documentation says, page by page, with the SHA-256 of each saved page |
| `docs/PAYLOAD_MATRIX.md` | every request the plan can send, with its reserved upper bound and its stop conditions |
| `CLASSIC_TEST_PLAN.md` | the staged plan for a future approved campaign |
| `tests/` | the offline tests. Their responses are SYNTHETIC |
