# Walmart store-price collector, release 1.5.2: source

Two provider editions of one frozen revision:

| Folder | Provider | Live runs on this release |
| --- | --- | --- |
| `walmart-oxylabs-1.5.2/` | Oxylabs Web API (Bearer key; not the Classic product) | none: the last live runs were on 1.5.1 (2026-10-31), and this release read their stored pages again offline |
| `walmart-scrapedo-1.5.2/` | Scrape.do | none: the account had 10 of 1,000 monthly requests left |

Revision: `627c804d66aa33fc423fd2296c8896c5d5c2c3d4`, committed 2026-11-01T19:52:28+00:00.

The two folders are built from that revision by `deploy/build_edition.py`. They differ only in the files listed
in `BUILD_MANIFEST.json`: `config/collector.yaml` (the edition and the store's provider), `.env.example`,
`BUILD_INFO.json` and `EDITION.json`. Each runs alone: install and run only the one whose provider you use.

## Install

Python 3.12 and [uv](https://docs.astral.sh/uv/) are the only prerequisites; everything else comes from `uv.lock`.

```
cd walmart-oxylabs-1.5.2
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
| `Dockerfile` | the container image, built and run on the owner's Azure test VM for this delivery |
| `docs/EDITIONS.md` | how the editions are built and what differs |
| `docs/VERIFICATION.md` | what was verified at each release |
| `config/` | stores, categories and limits; schedules ship off |

No key, database URL or data file is in this package. Keys and the database come from the environment
(`.env.example` names them).
