# Collector 1.6.0: offline tests

SYNTHETIC: fixture pages and a temporary local PostgreSQL; no request reached a provider or Walmart.

| File | What it holds |
|---|---|
| `COLLECTOR_1.5.2_TO_1.6.0.diff`, `DIFFSTAT.txt` | the whole change from release 1.5.2 (`627c804`), the one the client reviewed, to 1.6.0 (`56f078e`), collector folder only |
| `UNIT_1.6.0.log` | the unit suite on 1.6.0, in the development tree: 499 passed (2026-11-03 16:55:52Z to 16:56:10Z) |
| `INTEGRATION_1.6.0.log` | the integration suite on 1.6.0, in the development tree: 188 passed in 21 min 47 s (16:56:28Z to 17:18:22Z) |

Release 1.6.0 makes the four deal fields (`volume_deals_description`, `volume_deals_price`,
`digital_deals_description`, `digital_deals_price`) always `""`, from every path, as the client's clarification
requires, and adds the optional Oxylabs account gate that reserves every submission in the shared trial ledger before
it is sent. Its tests start from nonempty deal data and check the final fields: `tests/unit/test_exports_policy.py`,
`tests/integration/test_deal_fields_policy.py` (fresh JSON and CSV, a carried legacy row, a replay and a re-export,
the publication, the contract check) and `tests/integration/test_account_gate.py`. These are new behaviours: release
1.5.2 filled the deal fields from the page by design, so no 1.6.0 test was run against it. The tests and what each
shows: the source's `docs/VERIFICATION.md`, "Release 1.6.0". The final release, 1.6.4, runs them again
(`../1.6.4-collector/`), in both editions from the delivered source ZIP (`../../verification/1.6.4/`).
