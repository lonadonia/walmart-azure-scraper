# Oxylabs Classic offline probe 1.7.1: start here

An offline, reviewable probe for the Oxylabs **Classic** Web Scraper API. **It has never sent a request**: its live
mode is disabled in the code, and no credential is in this package.

This is the shared probe (Walmart and Mariano's on one ledger). Version 1.7.0 corrected the five findings of the
client's second review (C1 to C5) in the shared layer, C2 and C4 only in part; version 1.7.1 completes them: the
session's deadline also bounds the ledger writes after an answer, the export and a supervisor's recovery (C2), and an
answer that reached the disk survives a crash without a paid refetch (C4). Each gap was first reproduced by a test
that fails on 1.7.0 (`offline_results/` has both runs). The steps, the response checks, the limits and the Mariano's
adapter are those of 1.6.0. The Walmart probe 1.5.2 that the client reviewed is published unchanged beside it.

| What | Value |
| --- | --- |
| Probe version | 1.7.1 |
| Frozen revision | `cbea802891d4e66b74a0abc33e0af0af74c89708` (the revision of Walmart release 1.6.6) |
| The probe's own code last changed in | `68ff3d8518b38a3792792ed6ffb8e73c2756245f` (1.7.1: C2 and C4 completed); its tree last changed in `68ff3d8518b38a3792792ed6ffb8e73c2756245f` |
| Live mode | disabled: `gates.LIVE_ENABLED = False` in `oxylabs-classic-probe/src/classic_probe/gates.py` |
| Requests sent to Oxylabs or to a retailer | none |

## What is here

| Path | What |
| --- | --- |
| `oxylabs-classic-probe/` | the probe's tree, unchanged from that revision, with its `uv.lock`. Read its `README.md` |
| `oxylabs-classic-probe/CLASSIC_TEST_PLAN.md` | the staged plan for a future approved campaign |
| `oxylabs-classic-probe/docs/PAYLOAD_MATRIX.md` | every request the plan can send, its upper bound and its stops |
| `oxylabs-classic-probe/docs/DOCUMENTED_CONTRACT.md` | what the documentation says, page by page, with each saved page's SHA-256 |
| `offline_results/` | the outputs of the probe's offline run of this tree: tests, lint, types, plan, both replays, the refused live command. `offline_results/README.txt` says what each file is |
| `saved_documentation/` | the public Oxylabs pages the contract names: those read on 2026-10-31 (`INDEX.json`), as published with probe 1.5.2, and those read for Mariano's on 2026-11-02 (`classic_docs_20261102/`, with its `index.json`), as published with the Mariano's delivery |
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
this package alone, two tests are skipped: `test_the_vendored_files_are_still_the_collectors_files`, once for each
collector, compares the vendored page readers with the collector's own files, which are not beside the probe here.
Every vendored copy is still checked against its recorded Git object (`test_each_vendored_file_is_the_recorded_copy`).
The three Walmart readers are the same Git objects in collector 1.5.2, from which they were copied, and in 1.6.6.

## What is not established

The Walmart tests use SYNTHETIC Classic responses; the Mariano's tests use real saved Mariano's pages inside invented
Classic envelopes (OFFLINE REPLAY). **They show nothing about what Classic returns**: no account, target entitlement,
rate, store context, fulfillment or pagination has been confirmed. The limits in the plan (10 requests per retailer,
20 in total, 30 minutes, USD 5 with USD 0.50 of headroom) are a proposal to the client, not an approval. Running a
campaign needs the account owner's Classic credentials, entitlements, confirmed rates and written approval, and a
later version of this probe with live mode enabled. The credential used for this delivery's live stages is an
Oxylabs Web API key, not a Classic username and password.
