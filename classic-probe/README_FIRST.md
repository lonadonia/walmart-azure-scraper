# Oxylabs Classic offline probe 1.5.2: start here

An offline, reviewable probe for the Oxylabs **Classic** Web Scraper API. **It has never sent a request**: its live
mode is disabled in the code, and no credential is in this package.

**It implements the Walmart stage only** (Walmart #3891, Waukegan, Pickup). Its ledger reserves Mariano's share of the
campaign, which does not implement or qualify a Mariano's adapter.

| What | Value |
| --- | --- |
| Probe version | 1.5.2 |
| Frozen revision | `627c804d66aa33fc423fd2296c8896c5d5c2c3d4` (the revision of Walmart release 1.5.2) |
| The probe's own code last changed in | `2ed64b70809a67c49c68ebda5e3c3420f079073b` |
| Live mode | disabled: `gates.LIVE_ENABLED = False` in `oxylabs-classic-probe/src/classic_probe/gates.py` |
| Requests sent to Oxylabs or to a retailer | none |

## What is here

| Path | What |
| --- | --- |
| `oxylabs-classic-probe/` | the probe's tree, unchanged from that revision, with its `uv.lock`. Read its `README.md` |
| `oxylabs-classic-probe/CLASSIC_TEST_PLAN.md` | the staged plan for a future approved campaign |
| `oxylabs-classic-probe/docs/PAYLOAD_MATRIX.md` | every request the plan can send, its upper bound and its stops |
| `oxylabs-classic-probe/docs/DOCUMENTED_CONTRACT.md` | what the documentation says, page by page, with each saved page's SHA-256 |
| `offline_results/` | the outputs of the probe's offline run: tests, lint, types, plan, replay. `offline_results/README.txt` says what each file is |
| `saved_documentation/` | the public Oxylabs pages the contract names, as read on 2026-10-31. The 12 used pages were downloaded again on 2026-11-01 and are byte-identical |
| `FILE_SHA256.txt` | the SHA-256 of every file of the probe's tree at that revision |
| `PACKAGE_MANIFEST.json` | this package's identity |

## Run it (offline)

Python 3.12 and [uv](https://docs.astral.sh/uv/) are the only prerequisites.

```
cd oxylabs-classic-probe
uv sync --frozen
uv run --frozen pytest
uv run --frozen ruff check src tests
uv run --frozen mypy
uv run --frozen classic-probe plan --targets config/targets.json
uv run --frozen classic-probe validate --targets config/targets.json --rates config/rates.example.json
```

The tests close the network: an attempt to open a socket or resolve a name fails the test that made it. Run from
this package alone, one test is skipped (`test_the_vendored_files_are_still_the_collectors_files`): it compares the
three vendored readers with the collector's files, which are not beside the probe here. To run it, put a copy of
`walmart-oxylabs-1.5.2/` from `WALMART_SOURCE_1.5.2.zip` beside `oxylabs-classic-probe/`, named
`walmart-azure-headless`.

## What is not established

The tests use SYNTHETIC Classic responses. **They show nothing about what Classic returns**: no account, target
entitlement, rate, store context, fulfillment or pagination has been confirmed. The limits in the plan (10 requests
per retailer, 20 in total, 30 minutes, USD 5) are a proposal to the client, not an approval. Running a campaign
needs the account owner's credentials, entitlements, confirmed rates and written approval, and a later version of
this probe with live mode enabled.
