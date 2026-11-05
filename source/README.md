# Walmart store-price collector, release 1.6.6: source

Two provider editions of one frozen revision:

| Folder | Provider | Live runs on this release |
| --- | --- | --- |
| `walmart-oxylabs-1.6.6/` | Oxylabs Web API (Bearer key; not the Classic product) | none: release 1.6.6 changes only how a refused automatic publication is reported (an ERROR line and exit code 6, also on Azure's retry), and what a run collects, checks and exports is that of 1.6.5. The live runs L1 to L10 ran releases 1.6.0 to 1.6.4 (the census L10 on 1.6.4), and the export of L10 was verified offline with release 1.6.5 (see the review documents) |
| `walmart-scrapedo-1.6.6/` | Scrape.do | none: built and tested offline; a live Scrape.do run needs access supplied separately |

Revision: `cbea802891d4e66b74a0abc33e0af0af74c89708`, committed 2026-11-04T22:38:53+00:00.

The two folders are built from that revision by `deploy/build_edition.py`. They differ only in the files listed
in `BUILD_MANIFEST.json`: `config/collector.yaml` (the edition and the store's provider), `.env.example`,
`BUILD_INFO.json` and `EDITION.json`. Each runs alone: install and run only the one whose provider you use.

## Install

Python 3.12 and [uv](https://docs.astral.sh/uv/) are the only prerequisites; everything else comes from `uv.lock`.

```
cd walmart-oxylabs-1.6.6
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
| `Dockerfile` | the container image. Not built for 1.6.6: the workstation has no container runtime. Its recipe is 1.5.2's, which was built and run on the owner's Azure test VM, with two comment lines changed |
| `docs/EDITIONS.md` | how the editions are built and what differs |
| `docs/VERIFICATION.md` | what was verified at each release |
| `config/` | stores, categories and limits; schedules ship off |

No key, database URL or data file is in this package. Keys and the database come from the environment
(`.env.example` names them).
