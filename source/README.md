# Walmart store-price collector, release 1.6.8: source

Two provider editions of one frozen revision:

| Folder | Provider | Live runs on this release |
| --- | --- | --- |
| `walmart-oxylabs-1.6.8/` | Oxylabs Web API (Bearer key; not the Classic product) | none: release 1.6.8 reads the subcategories a row's navigation links as category pages of their own, so a run makes more requests than 1.6.7 (one per such page and the result pages of the listings it names). The live runs L1 to L12 ran releases 1.6.0 to 1.6.6 (L12 on 1.6.6); their stored data were checked again offline with the 1.6.8 rules (see the review documents) |
| `walmart-scrapedo-1.6.8/` | Scrape.do | none: built and tested offline; a live Scrape.do run needs access supplied separately |

Revision: `85c29e7b2404500299056973f50c84b84e187a5a`, committed 2026-11-05T20:51:52+00:00.

The two folders are built from that revision by `deploy/build_edition.py`. They differ only in the files listed
in `BUILD_MANIFEST.json`: `config/collector.yaml` (the edition and the store's provider), `.env.example`,
`BUILD_INFO.json` and `EDITION.json`. Each runs alone: install and run only the one whose provider you use.

## Install

Python 3.12 and [uv](https://docs.astral.sh/uv/) are the only prerequisites; everything else comes from `uv.lock`.

```
cd walmart-oxylabs-1.6.8
uv sync --frozen
uv run --frozen walmart-collector --version
uv run --frozen walmart-collector validate-config
```

## Documents in each edition

| File | What |
| --- | --- |
| `README.md` | what the collector is, its commands and its output |
| `docs/OPERATIONS.md` | installation, operation (manual and scheduled), adding stores and categories, monitoring, exports, backups, recovery, replacing keys |
| `docs/CLI.md` | every command and its exit codes |
| `docs/AZURE.md`, `docs/AZURE_VM.md`, `azure/` | Azure deployment |
| `Dockerfile` | the container image's recipe (the review documents record where the image of this release was built and run) |
| `docs/EDITIONS.md` | how the editions are built and what differs |
| `docs/VERIFICATION.md` | what was verified at each release |
| `config/` | stores, categories and limits; schedules ship off |

No key, database URL or data file is in this package. Keys and the database come from the environment
(`.env.example` names them).
