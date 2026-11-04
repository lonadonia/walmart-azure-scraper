# Collector 1.6.1: offline tests

SYNTHETIC: fixture pages and a temporary local PostgreSQL; no request reached a provider or Walmart.

| File | What it holds |
|---|---|
| `COLLECTOR_1.6.0_TO_1.6.1.diff`, `DIFFSTAT.txt` | the whole change from release 1.6.0 (`56f078e`) to 1.6.1 (`1780349`), collector folder only |
| `INTEGRATION_1.6.1.log` | the integration suite on 1.6.1, in the development tree: 189 passed in 21 min 0 s (2026-11-03 17:57:09Z to 18:18:16Z) |
| `UNIT_AND_STATIC_1.6.1.log` | the unit suite (499 passed) and ruff, ruff format and mypy (strict), all clean, on 1.6.1 (18:19:08Z to 18:19:27Z) |

Release 1.6.1 makes a run that ends before its detail pass still use what earlier reads of a product's own page
established (the 30-day reuse window), with that read's own time, run, revision and page. The test
`tests/integration/test_detail_path.py::test_a_run_that_ends_before_its_detail_pass_still_uses_what_earlier_reads_established`
fails on 1.6.0 and passes on 1.6.1 (the source's `docs/VERIFICATION.md`, "Release 1.6.1"). The correction was found
by this delivery's field-by-field reconciliation (W2): the live S7 of 2026-10-31 (release 1.5.1) had left 32 products
blank that S6's saved reads answered.
