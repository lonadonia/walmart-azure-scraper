# Editions: one collector, two providers (release 1.4.0)

The collector reads Walmart through one provider per run: Scrape.do's Walmart store endpoint or the Oxylabs
Web API. Release 1.4.0 ships it as two **editions**, each the same collector built for one of them:

| Edition | Provider | Source ZIP |
|---|---|---|
| `scrapedo` | Scrape.do, `https://api.scrape.do/plugin/walmart/store` (the store's `storeid` and `zipcode`; result pages with Walmart's own `fulfillment_method:Pickup` facet since release 1.4.1) | `WALMART_SCRAPEDO_SOURCE_<version>.zip` |
| `oxylabs` | Oxylabs Web API, `POST https://webapi.oxylabs.io/v1/scrape/walmart` (the store's `store_id` and `fulfillment_type`; Bearer key) and `/v1/scrape` for the other pages | `WALMART_OXYLABS_SOURCE_<version>.zip` |

Neither edition is the Oxylabs Classic product, and an Oxylabs Web API key is not Classic credentials.

Both editions ask Walmart for the same result grid, the store's Pickup grid (release 1.4.1): the Oxylabs Web
API applies Walmart's filter from its `fulfillment_type`, the Scrape.do edition adds Walmart's own facet
(`facet=fulfillment_method:Pickup`) to each result page it requests, since the store endpoint sets the store
only. In release 1.4.0 the Scrape.do edition read the store's unfiltered grid: its reported totals counted
out-of-stock, shipping-only and marketplace items (2026-10-28: Laundry 18,682 results against 624 in the
Pickup grid), which the record rules then excluded. Every result page records the filter its grid states,
and `coverage-report` gives it per page (`grid_fulfillment_filter`).

## What is the same, and what differs

Both editions of a release are built from **one revision** of this folder: the same code, settings, rules,
tests and documents. There is no copy of any logic per provider. An edition differs from that revision in
these files only (`src/walmart_headless/editions.py`):

| File | In the edition |
|---|---|
| `config/collector.yaml` | the `edition:` line names the edition and its one provider (`edition: { name: scrapedo, providers: [scrapedo] }`), and each store's `provider:` value is that provider; every other line is the revision's |
| `.env.example` | `editions/<edition>.env.example`: its provider's key variables only, a database and a data folder of its own |
| `BUILD_INFO.json` | added: the revision, its commit time and the edition (recorded with every run) |
| `EDITION.json` | added: the edition, its provider, the revision, each change with the SHA-256 of the file before and after (and the configuration lines replaced), and the SHA-256 of every file and of the whole tree |

The core (this folder in the repository) names both providers: `edition: { name: core, providers:
[scrapedo, oxylabs] }`.

## Isolation

* A run, a resumed run or `provider-balance` naming a provider the edition does not list is refused before
  any request (exit 2, `COMMAND_REFUSED`: "the scrapedo edition runs scrapedo only: provider oxylabs
  refused"), whatever keys the environment holds. A configuration whose store names another provider than
  its edition's is invalid (exit 2). No run falls back to another provider.
* Each edition has its own database, data folder (or blob container), environment and key. Retained
  products are carried forward from the edition's own earlier runs only, so one provider's observations
  never fill or inflate the other's results; spending ceilings and budgets live in the edition's database.
* Each run records its edition and provider (`config_snapshot.edition`, `config_snapshot.provider`) and the
  revision that collected (`config_snapshot.code`).

## Build

From a committed revision (never from the working tree):

```bash
python deploy/build_edition.py --rev <commit> --edition scrapedo --out dist/
python deploy/build_edition.py --rev <commit> --edition oxylabs --out dist/
```

The script exports the collector folder of that revision with `git archive` (committed files only: no
virtual environment, data or keys), builds the edition and writes its ZIP with one top folder,
`walmart-<edition>-<version>/`. The ZIP is reproducible (sorted entries, the commit time on every entry, the
committed permissions): the same revision gives the same bytes. It prints the ZIP's SHA-256 and the edition
record. `tests/unit/test_editions.py` checks, in the core and in each extracted edition alike, that a tree is
the core or exactly the edition its `EDITION.json` describes.

## Install and run

Locally, from an extracted edition:

```bash
uv sync --frozen
cp .env.example .env     # the edition's provider key, its own database and data folder
set -a; . ./.env; set +a
uv run walmart-collector db-upgrade
uv run walmart-collector validate-config --check-db --require-credentials
```

On the Azure VM ([AZURE_VM.md](AZURE_VM.md)), beside the core release and without changing it:

```bash
sudo bash install.sh WALMART_SCRAPEDO_SOURCE_<version>.zip <commit> scrapedo
sudo WC_ENV=/etc/walmart-collector/env.scrapedo WC_RELEASE=/opt/walmart-collector/edition-scrapedo \
  walmart-cmd validate-config --check-db --require-credentials
sudo WC_ENV=/etc/walmart-collector/env.scrapedo WC_RELEASE=/opt/walmart-collector/edition-scrapedo \
  walmart-run sd-pilot run --store walmart-3891-pickup ...
```

`install.sh` gives the edition the release folder `/opt/walmart-collector/releases/<version>-<commit>-<edition>`
(linked as `/opt/walmart-collector/edition-<edition>`), the database `walmart_<edition>`, the data folder
`/var/lib/walmart-collector/editions/<edition>/data` and the environment file
`/etc/walmart-collector/env.<edition>`, which names its provider's key file only. The core's `current`
release, environment, database and data are left as they were.
