# Acceptance runbook: Walmart release 1.6.5 and the shared Classic probe 1.7.0

This runbook lets anyone with a clone of this repository repeat its checks, and shows how the collector is installed
and operated:

1. the files and their checksums;
2. each edition's source on its own, from a clean copy (install, lock, lint, types, tests, migrations, container);
3. the product files;
4. one row, from the product file to the page it was read from;
5. the record of the clean-extraction verification of this delivery;
6. the Classic probe 1.7.0;
7. operating the collector: install, migrate, run, status, pause and resume, finalize, export, publication,
   rollback, and where the data is kept.

Sections 1 to 6 are **offline**: no step needs a provider key, none sends a request to Oxylabs, Scrape.do or
Walmart, and none costs anything. Section 7 describes commands. The live ones are paid and need an approved budget
on the account that pays for them. [`TEST_PLAN.md`](TEST_PLAN.md) has the proposed live work, including a sequence
the client can observe.

Hamza ran the offline steps on the preparation workstation (Windows 11) on 2026-11-04 (UTC). Nobody else has run
them yet. Nothing here is a test the client observed or executed, and nothing ran in the client's environment.

## 0. What you need

| Tool | Used here | Needed for |
|---|---|---|
| Python 3.12 (the project requires >=3.12,<3.13) | CPython 3.12.10 (python.org, signed) | every section |
| [uv](https://docs.astral.sh/uv/) | 0.13.1 | sections 2, 6 and 7 (it installs the locked environments) |
| Docker | not available on the workstation | the container build (section 2, optional) |
| Bicep CLI | 0.48.1 | the Azure template check (optional; the result is in section 5) |

You do not need to install PostgreSQL. The test suites start a temporary PostgreSQL of their own (pgserver,
installed by uv from the lock). Each edition's environment takes about 200 MB.

## 1. The files of this repository

`manifests/SHA256SUMS.txt` lists every file of the repository except itself: the SHA-256, two spaces, then the
path with `/`.

On Linux or macOS (or Git Bash), at the root of a clone:

```bash
sha256sum -c manifests/SHA256SUMS.txt          # every line ends "OK"
git ls-files | grep -vc '^manifests/SHA256SUMS.txt$' ; wc -l < manifests/SHA256SUMS.txt   # the two numbers are equal
python3 manifests/check_frozen_trees.py        # source/, classic-probe/ and classic-probe-1.7.0/ against their manifests
python3 manifests/check_data.py                # the product files of data/ and every 1.6.x export: contract and lineage
```

In Windows PowerShell, at the root of a clone:

```powershell
$bad = 0
Get-Content manifests/SHA256SUMS.txt | ForEach-Object {
  $hash, $path = $_ -split '  ', 2
  if ((Get-FileHash -Algorithm SHA256 -LiteralPath $path).Hash.ToLower() -ne $hash) { "DIFFERENT $path"; $bad++ }
}
"different: $bad"                                                     # different: 0
python manifests/check_frozen_trees.py; python manifests/check_data.py   # each ends with PASS
```

Both scripts use Python's standard library only and send no request. The earlier publication is unchanged at its
tag `review-1.5.2-20261103`. This one is a new commit after it, under its own tag.

## 2. Each edition alone, from a clean copy

[`source/`](../source/) is the top folder of the source ZIP `WALMART_SOURCE_1.6.5.zip`, file for file. It holds
`walmart-oxylabs-1.6.5/` and `walmart-scrapedo-1.6.5/`. The Oxylabs edition ZIP of each release that ran live, as
built, is in [`evidence/live/1.6.x/builds/`](../evidence/live/1.6.x/builds/). Copy `source/` out of the clone into a new, short folder, so that uv's environments are not created
inside the clone (Windows limits most paths to 260 characters):

```powershell
mkdir C:\v165
Copy-Item -Recurse source C:\v165\walmart-source-1.6.5
```

On Linux: `cp -r source <folder>/walmart-source-1.6.5`. Each edition's `EDITION.json` lists its files with their
SHA-256. `BUILD_MANIFEST.json` gives each edition's file count and tree hash. The two editions differ in four files
only: `.env.example`, `BUILD_INFO.json`, `EDITION.json` and `config/collector.yaml`. Right after copying, before uv
adds an environment to each:

```bash
cd <folder>/walmart-source-1.6.5
diff -rq walmart-oxylabs-1.6.5 walmart-scrapedo-1.6.5        # four lines
```

Then, in each edition folder, run these with no provider key and no database URL in the environment:

```bash
uv lock --check                                   # the lock matches pyproject.toml
uv sync --frozen                                  # the locked environment (.venv)
uv run --frozen walmart-collector --version       # walmart-azure-headless 1.6.5
uv run --frozen walmart-collector --help
uv run --frozen walmart-collector validate-config
uv run --frozen ruff check src tests
uv run --frozen ruff format --check src tests
uv run --frozen mypy                              # strict, as pyproject.toml configures it
uv run --frozen python -m pytest -q tests/unit
uv run --frozen python -m pytest -q tests/integration
```

**What `validate-config` prints.** One JSON line with `"event": "RESULT"`:
- its `edition` is `{"name": "oxylabs", "providers": ["oxylabs"]}` in the Oxylabs edition, and the same with
  `scrapedo` in the other;
- every store's `provider` is the edition's own, and every store's schedule is off;
- no key and no database URL is configured;
- `code` is version `1.6.5`, commit `67d216eb8ee2ec839a437b0b5bf2d594324b6982`.

**Notes.**
- **On Windows:** set `PSYCOPG_IMPL=python`, and put the environment's pgserver PostgreSQL bin folder
  (`.venv\Lib\site-packages\pgserver\pginstall\bin`) first on `PATH`; it holds the PostgreSQL client library.
- **To show that no test reaches a provider:** after `uv sync`, set `HTTP_PROXY`, `HTTPS_PROXY` and `ALL_PROXY` to
  `http://127.0.0.1:9`, and `NO_PROXY` to `localhost,127.0.0.1`. The verification of section 5 ran every step but
  the installs this way.
- **On this workstation only:** Windows Smart App Control blocks the `_socket` module of the uv-managed Python, so
  `UV_PYTHON` named the signed python.org CPython 3.12.10.

**Migrations.** No migration changed in releases 1.6.0 to 1.6.5: `git diff 627c804 67d216e` touches nothing under
the package's migrations, and the schema head is still `0006`. The integration suite checks them on its temporary
PostgreSQL. `test_the_schema_is_checked_and_upgraded_and_the_configuration_validated`
(`tests/integration/test_operations.py`) starts from an empty schema. `validate-config --check-db` and `status`
refuse it (exit 2). `db-upgrade` takes it from no revision to `0006`, and `validate-config --check-db
--require-credentials` then passes. To do it on a database of your own, see section 7.

**The container.** It was **not built for 1.6.5**: the workstation has no container runtime, and the client's VM is
deallocated. The `Dockerfile` changed since 1.5.2 only in two comment lines (the version in its build examples). The
1.5.2 image was built and run on the owner's Azure test VM
([`evidence/owner-azure-test/1.5.2/`](../evidence/owner-azure-test/1.5.2/)). Where Docker is installed, in an
edition folder of the copied source:

```bash
docker build -t walmart-oxylabs:1.6.5 .
docker run --rm walmart-oxylabs:1.6.5 --version          # walmart-azure-headless 1.6.5
docker run --rm walmart-oxylabs:1.6.5                    # validate-config: the RESULT line, no key or database set
```

The image's entry point is the collector, and its default command is `validate-config`. With a PostgreSQL of your
own and the data folder as a volume, the same image runs `db-upgrade`, `run`, `resume` and the other commands of
section 7: `docker run --rm --env-file .env -v <data folder>:/data walmart-oxylabs:1.6.5 <command>`. This is in the
client-environment milestone ([`MILESTONES.md`](MILESTONES.md)).

Each edition's `docs/EDITIONS.md` explains the editions, `docs/VERIFICATION.md` describes every release's changes
and checks, and `docs/OPERATIONS.md` and `docs/AZURE.md` describe operation.

## 3. The product files

| Folder | What it is |
|---|---|
| [`data/L10-1.6.4/`](../data/L10-1.6.4/) | release 1.6.4: run L10 (`01M6KA3CKYJSD6WDY4TDAAV73Y`), the census, detail reading off. `products_fresh` holds the 7,057 rows L10 observed itself: 7,055 valid, and 2 products their page showed with no price, exported with empty prices and marked `exported_not_valid` in the run's `record_map.json`. `products_retained` is its full export of 10,301 rows: those plus 3,244 carried from earlier runs, each with its own run and date. The final release 1.6.5 changed only the source check, and the export passes its `validate-export --run` |
| [`data/L8-1.6.3/`](../data/L8-1.6.3/) | release 1.6.3: run L8 (`01M6K6P21BW509BMRTN1FSB9H7`), the last demonstration with detail reading on: 675 fresh, and a retained export of 2,515 rows (1,840 carried) |
| [`data/S6-1.5.1/`](../data/S6-1.5.1/), [`data/S7-1.5.1/`](../data/S7-1.5.1/), [`data/S4-1.5.0/`](../data/S4-1.5.0/) | the live files of 2026-10-31, unchanged, as published in 1.5.2. They were made under the earlier deal-field rule and are not edited |

Every other 1.6.x run's exports are in its folder of [`evidence/live/1.6.x/runs/`](../evidence/live/1.6.x/runs/).
[`data/RUN_SUMMARY.json`](../data/RUN_SUMMARY.json) gives each run's release, commit, edition ZIP, store, times,
status, gates, request counts and spending. For each delivered file it gives the SHA-256 and the row count. There
is no merged file, and the providers' rows are never mixed.

Each row has the 22 fields in order, all strings:
- `gupc` and `unit_price` are always empty;
- from release 1.6.0, the four deal fields are always empty;
- `zipcode` is 60085;
- `crawl_date` is the store-local date (America/Chicago) of the row's own observation. A carried row keeps its
  original date.

To check a file from a copied edition: `uv run --frozen walmart-collector validate-export --file
<clone>/data/L10-1.6.4/products_fresh.json`. Without an environment, `python3 manifests/check_data.py` checks every
delivered file the same way, against its run's own export and `record_map.json`.

## 4. One row, from the product file to the page it was read from

1. Take a row of a `products_fresh` file and note its `url`. The item id is the last number of its path.
2. Open the run's `exports/record_map.json` (in its folder of `evidence/live/1.6.x/runs/`) and find the row with
   that `url`. It gives `observation_kind`, `observed_by_run`, `observed_at`, the code's `commit`, and the stored
   page the row was read from (`page.stored_page`, with its SHA-256).
3. The page is in the run folder's `pages/`, under that name. Its fetch is the row of `db/page_fetches.csv` with that
   id, which gives the URL, purpose, time and HTTP status. `PAGE_LINEAGE.csv` ties the stored, sanitized page to the
   SHA-256 of the provider's raw answer. The raw answer is kept private and is never published, and
   `RAW_ORIGINALS_MANIFEST.csv` lists it.
4. A carried row names its own earlier run in `observed_by_run`; open that run's folder instead. A row carried from a
   1.5.x run points to `evidence/live/runs/<run>/`.
5. A blank UPC or size: the run's `exports/field_dispositions.json` says why it is blank. A value recovered from a
   saved product page names that page, and that read's run, time and revision. A page never read is
   `not_attempted`. A page asked for and not answered is `blocked` or `request_failed`.

## 5. The verification of this delivery from clean extractions

[`evidence/verification/1.6.5/package/`](../evidence/verification/1.6.5/package/) is the record. Each step ran as
its own process, in a new extraction of `WALMART_SOURCE_1.6.5.zip`, with HTTP(S) sent to a closed local port and with
no provider key, database URL or collector setting of the workstation:
- for each edition: the tree against its manifest, `uv lock --check`, `uv sync --frozen`, ruff, ruff format, mypy,
  `--version`, `--help`, `validate-config`, and the unit and integration suites;
- `steps.jsonl` gives each step's command, exit code and duration, `logs/` each step's output, and `junit/` the
  JUnit XML;
- `REPORT.txt` gives the result: 23 steps, 0 not ok; in each edition, 533 unit and 200 integration tests passed;
- `BICEP_CHECKS.txt` gives the Bicep build and lint of each edition's `azure/main.bicep` (no deployment): exit 0, and
  the lint reported nothing.

Beside it in `evidence/verification/1.6.5/`:
- `last_good_publication/` is the synthetic publication-fault check of section 3 of
  [`RECOVERY_AND_OPERATIONS.md`](RECOVERY_AND_OPERATIONS.md);
- `source_check_l10/` is the check of the live L10 and L8 exports with 1.6.5's source check, and the record of the
  1.6.4 check's defect.

The test logs of the development tree, per release, are in `evidence/offline-tests/<release>-collector/`.

## 6. The Classic probe 1.7.0

[`classic-probe-1.7.0/`](../classic-probe-1.7.0/) is the probe archive `OXYLABS_CLASSIC_OFFLINE_PROBE_1.7.0.zip`,
file for file. Its `README_FIRST.md` gives the commands: `uv sync --frozen`, `pytest`, ruff, mypy, `plan` and
`validate`. All of them are offline. The probe has never sent a request. Its live mode is disabled in the code
(`gates.LIVE_ENABLED = False`), and it holds no credential. Run from the probe alone, two tests are skipped, because
they compare the vendored page readers with the collectors' own files, which are not beside it.
[`CLASSIC_PROBE_CORRECTIONS.md`](CLASSIC_PROBE_CORRECTIONS.md) maps C1 to C5 to their corrections and tests. The
Walmart probe 1.5.2 that the client reviewed is unchanged in [`classic-probe/`](../classic-probe/).

## 7. Operating the collector

Commands are `uv run --frozen walmart-collector ...` in an edition folder, or the same arguments to the container.
Each edition's `docs/CLI.md` documents every command and exit code.

**Install and migrate.**
1. Python 3.12 and uv, then `uv sync --frozen`.
2. A PostgreSQL database for this collector alone.
3. Copy `.env.example` to `.env` and fill in `WALMART_COLLECTOR_DATABASE_URL`, `WALMART_COLLECTOR_DATA_DIR` and the
   edition's key (`OXYLABS_WEB_API_KEY` or `OXYLABS_WEB_API_KEY_FILE`; `SCRAPEDO_API_KEY` or `SCRAPEDO_API_KEY_FILE`).
   `.env` is never committed or packaged.
4. `db-upgrade`, then `validate-config --check-db --require-credentials`. Every command but `db-upgrade` refuses a
   database whose schema is not current. An upgrade is: install the new release, `db-upgrade`, then
   `validate-config`.
5. Spending: an Oxylabs run sends nothing until `set-ceiling --provider oxylabs --submissions N --usd X --basis ...`
   is set. `set-budget --usd X --basis ...` caps the money across both providers.

**Run, status, pause, resume, finalize, export.**

| Command | What it does |
|---|---|
| `run --store walmart-3891-pickup` | a run of the configured scope (limits make it a bounded pilot, which is never published) |
| `status [--run ID]` | holds, the last runs, the published dataset, the ledger |
| a termination signal: Ctrl+Break on Windows, SIGTERM on Linux, or the job's time limit | a pause: the execution stops at its next checkpoint, and the run is `interrupted` (exit 75), resumable |
| `resume --run ID [--workers N]` | continues from the checkpoints; no collected page is requested again |
| `stop --run ID` | not a pause: it stops collecting for good. The execution stops at its next checkpoint, and the run is finalized with what it collected |
| `finalize --run ID` | closes an unfinished run without any request, and checks and exports what it collected (a partial or pilot dataset, never published). It cannot be resumed afterwards |
| `export --run ID --out DIR`, `validate-export --run ID` | the run's files, and their contract check |
| `coverage-report --run ID`, `field-dispositions --run ID` | coverage per row, listing and page; why each field is filled or blank |
| `release-hold --store KEY --reason TEXT` | after a stop that held the store (exit 5 or 7), once the cause is understood |

**Where the data is.**
- **The database** holds the runs, records, ledgers and the publication pointer. Back it up with point-in-time
  restore on Azure (7 to 35 days), or with `pg_dump -Fc` elsewhere.
- **The storage** is a local folder (`WALMART_COLLECTOR_DATA_DIR`) or the Blob container. It holds each run's stored
  pages and exports, under `runs/<store>/<run>/`, and the published dataset under `published/<store>/`. Turn on soft
  delete and versioning on the Blob account.
- **`published/<store>/latest.json` is the last-good pointer.** It names the published run and its manifest; it is
  not a product file. The database's pointer is authoritative: a missing or stale `latest.json` is rewritten by the
  next publication.

**Publication and rollback.**
- Only a complete, validated, non-pilot run is published, and the pointer moves only after every export file is
  verified again.
- A run that fails a gate leaves the published dataset as it was. So does a run that is interrupted, blocked, for
  the wrong store, thin, empty or corrupt (section 3 of [`RECOVERY_AND_OPERATIONS.md`](RECOVERY_AND_OPERATIONS.md)).
- A rollback of the code is: install the previous release, from its source ZIP or its image tag. The schema has
  not changed since 1.5.2, so 1.5.2 and 1.6.5 share head `0006`.
- A rollback of the data: the earlier runs' exports stay under `runs/`. With Blob versioning on, an earlier
  `latest.json` and its manifest can be restored. With the database restored to a point in time, the pointer goes
  back with it.

**Schedule.** It ships disabled (`schedule.enabled: false`), and `run --scheduled` exits 0 with `SCHEDULE_OFF`. The
cadence, the daylight-saving policy and the backlog rules are in section 5 of
[`RECOVERY_AND_OPERATIONS.md`](RECOVERY_AND_OPERATIONS.md). Enabling it is the client's decision.
