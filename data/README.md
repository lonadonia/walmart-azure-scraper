# Data: the live product files

The product files that live runs exported for Walmart #3891, 3900 Fountain Square Pl, Waukegan, IL 60085, with
Pickup fulfilment, through the Oxylabs Web API. Each folder is named after the run and the release that collected
it. Every run is a capped pilot, rejected by the coverage gate G3 at least, so nothing was published, and no file
covers the full catalogue.

## The 1.6.x runs (2026-11-03 and 2026-11-04, the user's Oxylabs Web API trial)

| Folder | Run | Release that collected it | Fresh | Retained |
|---|---|---|---:|---:|
| [`L10-1.6.4/`](L10-1.6.4/) | L10, `01M6KA3CKYJSD6WDY4TDAAV73Y`, 2026-11-04T12:56Z to 13:42Z: the census, detail reading off | **1.6.4** (`28ac7d3`) | **7,057** (7,055 valid) | 10,301 |
| [`L8-1.6.3/`](L8-1.6.3/) | L8, `01M6K6P21BW509BMRTN1FSB9H7`, 2026-11-04T11:56Z to 12:04Z: a demonstration, detail reading on | 1.6.3 (`def55e5`) | 675 | 2,515 |

- **Fresh** (`products_fresh.*`): the products the run observed itself. L10's has 7,057 rows: 7,055 valid, and 2
  products that their page showed with no price at all (Sheba `17277162155`, Children's Zyrtec `610741365`). Those
  two are exported with empty prices and marked `exported_not_valid` in the run's `record_map.json`; they are not
  counted.
- **Retained** (`products_retained.*`): the run's export with the products it carried from earlier runs. Each
  carried row keeps its own run and date and is never counted as fresh.
- **The final release, 1.6.5,** changed only the independent source check. Both exports pass its `validate-export
  --run`: 10,301 of 10,301 and 2,515 of 2,515 records verified against their stored pages
  ([`../evidence/verification/1.6.5/source_check_l10/`](../evidence/verification/1.6.5/source_check_l10/)). They stay
  attributed to the releases that collected them.
- **The format.** Each file has the 22 fields in order, all strings, with `""` for a missing value. `gupc` and
  `unit_price` are always empty, and from release 1.6.0 the four deal fields are always empty. PPM is copied as
  displayed, and `crawl_date` is the store-local date of the row's own observation. JSON and CSV hold the same rows.
- **Blank UPCs** (each run's `field_dispositions.json` gives every blank its reason):
  - L10's 7,057 fresh rows: 367 UPCs from saved product-page reads, each naming its read; 6,688 `not_attempted`,
    because detail reading was off; 2 absent in the source.
  - L8's 675 fresh rows: 667 from saved reads, 5 from the 6 product pages it fetched, 2 absent in the source, 1
    identity mismatch.

Every other 1.6.x run's exports are in its folder of
[`../evidence/live/1.6.x/runs/`](../evidence/live/1.6.x/runs/). [`RUN_SUMMARY.json`](RUN_SUMMARY.json) records every
run of this store that the repository publishes, the 1.5.x runs and the fourteen 1.6.x runs: release, commit, edition
ZIP, store checks, times, gates, pages, ledgers, counts, and each delivered file's SHA-256 and row count. The current
coverage tables are in [`../evidence/reconciliation/1.6.5/w4/`](../evidence/reconciliation/1.6.5/w4/);
[`COVERAGE_RECONCILIATION.csv`](COVERAGE_RECONCILIATION.csv) is release 1.5.2's, kept as published.

**Check:** `python3 manifests/check_data.py`, from the root of a clone. It checks each file against
`RUN_SUMMARY.json`, its run's own export and `record_map.json`, and the 22-field contract. It ends with `PASS`.

## The 1.5.x runs (2026-10-31), as published with release 1.5.2

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

In the 1.5.2 publication, [`RUN_SUMMARY.json`](RUN_SUMMARY.json) recorded these nine runs. It now records the
1.6.x runs too. The 1.5.x entries keep the values that publication gave them, with two changes: their delivered files
are named by their paths in this repository (`data/S6-1.5.1/`, where the delivery wrote `live/S6_1.5.1/`), and each
entry adds its exports and run folder here (`exports`, `run_folder_in_repository`). Their other paths are the
delivery's own: `WALMART_EVIDENCE_1.5.x.zip: 1_new_live/` is `evidence/live/`.
[`COVERAGE_RECONCILIATION.csv`](COVERAGE_RECONCILIATION.csv) is release 1.5.2's coverage table, unchanged.
