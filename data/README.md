# Data: the live product files

These are the product files the live runs of 2026-10-31 exported for Walmart #3891, 3900 Fountain Square Pl,
Waukegan, IL 60085, with Pickup fulfilment, through the Oxylabs Web API. They are byte for byte the files of the
1.5.1 delivery, as the 1.5.2 delivery carried them. **No row here was collected by release 1.5.2**, because 1.5.2
has not run live.

| Folder | Run | Release that collected it | Fresh | Retained |
|---|---|---|---:|---:|
| [`S6-1.5.1/`](S6-1.5.1/) | S6, `01M6A2VQAA5VXJHJHMZPCTZTD4`, 2026-10-31T22:56Z | **1.5.1** (`488a033`) | **580** | 706 |
| [`S7-1.5.1/`](S7-1.5.1/) | S7, `01M6A52HA6XYCEDS6DBE5N5RQ7`, 2026-10-31T23:35Z: S6's first page, read again | 1.5.1 (`488a033`) | 32 | 706 |
| [`S4-1.5.0/`](S4-1.5.0/) | S4, `01M69Y882GTVYRJZM0CXQ44MXN`, 2026-10-31T21:36Z | 1.5.0 (`7b6f325`) | 677 | 689 |

- **Fresh** (`products_fresh.*`): products the run observed itself. S6's 580 are distinct and valid, from 15 Pickup
  result pages of five listings.
- **Retained** (`products_retained.*`): the run's export with the products it carried from earlier runs. Each
  carried row keeps its own run and date and is never counted as fresh.
- Each run is a capped pilot, rejected by the coverage gate G3 at least, so nothing was published. The files do not
  cover the full catalogue.
- **The format.** Each file has the 22 fields in order, all strings, with `""` for a missing value. `gupc` and
  `unit_price` are always empty, PPM is copied as displayed, and `crawl_date` is the store-local date of the row's
  own observation. JSON and CSV hold the same rows.

**Blank UPCs and sizes in S6's 580 fresh rows.** `data/RUN_SUMMARY.json` gives the outcomes recorded live by 1.5.1:

| Field | Live outcome (S6, release 1.5.1) |
|---|---|
| UPC | fetched from its own page 1, recovered from a saved page 352, absent from its page 1, page not read 226 (`budget_deadline_interruption`) |
| Size | in the listing 555, recovered from a saved page 12, absent 3, conflict 1, page not read 9 |

A recovered value keeps the time, run and revision of the page it came from. Release 1.5.2 read S6's stored pages
again **offline**: 353 UPCs recovered, 1 absent and 226 `not_attempted`, because a replay fetches nothing. Those
outputs are evidence, not live data: [`../evidence/offline-replay/1.5.2/offline_reprocessing/`](../evidence/offline-replay/1.5.2/offline_reprocessing/).

**Also here:** [`RUN_SUMMARY.json`](RUN_SUMMARY.json) records the nine runs (revision, store checks, pages, ledger,
counts, and each file's SHA-256 and row count). [`COVERAGE_RECONCILIATION.csv`](COVERAGE_RECONCILIATION.csv) gives
coverage by CSV row, listing, child listing and page, and no row is complete. Both keep the delivery's own paths:
`live/S6_1.5.1/` is now `data/S6-1.5.1/`, `WALMART_EVIDENCE_1.5.x.zip: 1_new_live/` is `evidence/live/`, and
`TEST_PLAN.md` is [`../review/TEST_PLAN.md`](../review/TEST_PLAN.md).

**Check:** `python3 manifests/check_data.py`, from the root of a clone. It checks each file against
`RUN_SUMMARY.json`, its run's own export and `record_map.json`, and the 22-field contract. It ends with `PASS`.
