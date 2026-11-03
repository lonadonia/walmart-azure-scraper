# Acceptance runbook: Walmart release 1.5.2 and the Oxylabs Classic offline probe 1.5.2

This runbook lets anyone with a clone of this repository repeat its checks:

- the files and their checksums;
- each edition's source, on its own;
- the product files and where each row came from;
- the record of the verifier that wrote [`evidence/verification/PACKAGE_VERIFICATION.txt`](../evidence/verification/PACKAGE_VERIFICATION.txt);
- the Classic probe.

Sections 1 to 6 are **offline**. No step needs a provider key, none sends a request to Oxylabs, Scrape.do or
Walmart, and none costs anything.

Section 7 is the **proposed** live sequence for the client to observe on this same release. It is paid, and it needs
the client's written approval of the account and the amount. It has not been run in this form, and release 1.5.2 has
not run live at all: [`TEST_PLAN.md`](TEST_PLAN.md) says what comes first.

Hamza ran the offline steps on the preparation workstation (Windows 11) and in containers on Hamza's own Azure test VM on 2026-11-01 and 2026-11-02 (UTC). [`evidence/verification/PACKAGE_VERIFICATION.txt`](../evidence/verification/PACKAGE_VERIFICATION.txt)
gives each step's command, exit code, duration and output. Nobody else has run them yet, so nothing here is a test
that the client observed or executed.

Paths are relative to the root of this repository unless they start with an edition folder. The delivery's paths,
into its folder and into its ZIPs, are rewritten to repository paths ([`manifests/FILE_MAP.csv`](../manifests/FILE_MAP.csv) maps
every file).

## 0. What you need

| Tool | Used here | Needed for |
|---|---|---|
| Python 3.12 (the project requires >=3.12,<3.13) | CPython 3.12.10 (python.org, signed) | every section |
| [uv](https://docs.astral.sh/uv/) | 0.13.1 | sections 2, 3, 5 and 6 (it installs the locked environments) |
| the Python package tzdata, on Windows only | installed by uv for the verifier | section 5 (the verifier converts times to the store's time zone, America/Chicago) |
| Bicep CLI (or az bicep) | 0.48.1 | the Azure template check (optional) |
| Windows PowerShell | 5.1 | the verifier's PDF page rendering (optional; Windows only) |
| Docker | 29.1.3 on the owner's Azure test VM (not on the workstation) | the container build (optional) |

You do not need to install PostgreSQL. The tests and the migration check start a temporary PostgreSQL of their own
(pgserver, installed by uv from the lock). Each edition's environment takes about 200 MB here. Allow about 1 GB for
both environments and the extracted evidence, plus uv's package cache.

## 1. The files of this repository

`manifests/SHA256SUMS.txt` lists every file of the repository except itself: the SHA-256, two spaces, then the
path with `/`. It replaces the delivery's own `SHA256SUMS.txt`, which named files not published here.

On Linux or macOS (or Git Bash), at the root of a clone:

```bash
sha256sum -c manifests/SHA256SUMS.txt          # every line ends "OK"
git ls-files | grep -vc '^manifests/SHA256SUMS.txt$' ; wc -l < manifests/SHA256SUMS.txt   # the two numbers are equal
python3 manifests/check_frozen_trees.py        # source/ and classic-probe/ against their own manifests
python3 manifests/check_data.py                # the product files of data/: contract and lineage
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

The two scripts use Python's standard library only and send no request.

The previous Walmart deliveries are unchanged. The list of 1.5.1, `deliverables/20261101_walmart_1.5.1/SHA256SUMS.txt`,
has the SHA-256 a72a7d623b3b7e80e51695e81eec28a77a32325e2b246ea056e9104f0c1c929e. That of 1.4.1,
`deliverables/20261028_walmart_1.4.1_dual_provider/SHA256SUMS.txt`, has the SHA-256
0e52a45442d9fb5529ce087074a733c86f33843ef02afe3565dafc1e3786897f. The oxylabs and scrapedo folders of 1.4.1 now sit beside it, in `deliverables/walmart_oxylabs/` and `deliverables/walmart_scrapedo/`. Each
file there keeps the hash that the list gives for its old path.

## 2. Each edition alone, from a clean copy

Copy `source/` out of the clone into a new, short folder, so that uv's environments are not created inside the
clone. Windows limits most paths to 260 characters.

```powershell
mkdir C:\v152
Copy-Item -Recurse source C:\v152\walmart-source-1.5.2
# C:\v152\walmart-source-1.5.2\walmart-oxylabs-1.5.2\  and  C:\v152\walmart-source-1.5.2\walmart-scrapedo-1.5.2\
```

On Linux, use `cp -r source <folder>/walmart-source-1.5.2`. `source/` is the source ZIP's top folder, file for file
(`manifests/check_frozen_trees.py` checks it). Each edition's `EDITION.json` lists its files with their SHA-256,
`BUILD_MANIFEST.json` gives each edition's file count and tree hash, and the two editions differ in four files only:

- `.env.example`
- `BUILD_INFO.json`
- `EDITION.json`
- `config/collector.yaml`

Every other file is byte for byte the same. Compare them right after extraction, before uv adds an environment to
each:

```bash
cd C:/v152/walmart-source-1.5.2
diff -rq walmart-oxylabs-1.5.2 walmart-scrapedo-1.5.2        # four lines
```

Then, in each edition folder, run these commands with no provider key and no database URL in the environment:

```bash
uv lock --check                                   # the lock matches pyproject.toml
uv sync --frozen                                  # the locked environment (.venv)
uv run --frozen walmart-collector --version       # walmart-azure-headless 1.5.2
uv run --frozen walmart-collector --help
uv run --frozen walmart-collector validate-config
uv run --frozen python -m ruff check src tests deploy
uv run --frozen python -m ruff format --check src tests deploy
uv run --frozen python -m mypy                    # strict, as pyproject.toml configures it
uv run --frozen python -m pytest -q tests/unit --junitxml=unit.xml
uv run --frozen python -m pytest -q tests/integration --junitxml=integration.xml
uv build --wheel                                  # the installable package
```

**What `validate-config` should print.** One JSON line with `"event": "RESULT"`:

- Its `edition` is `{"name": "oxylabs", "providers": ["oxylabs"]}` in the Oxylabs edition, and the same with
  `scrapedo` in the other.
- Every store's `provider` is the edition's own, and every store's schedule is off.
- `environment.database_url_set`, `scrapedo_key.configured` and `oxylabs_key.configured` are false.
- `code` is version `1.5.2`, commit 627c804d66aa33fc423fd2296c8896c5d5c2c3d4, source `build_info`.

**Every command exits 0.** The test suites need no network. Notes for running them:

- **On Windows:** set `PSYCOPG_IMPL=python`, and put the environment's pgserver PostgreSQL bin folder
  (.venv\Lib\site-packages\pgserver\pginstall\bin) first on `PATH`. It holds the PostgreSQL client library. The
  verifier does the same.
- **To show that no test can reach a provider:** after `uv sync`, set `HTTP_PROXY`, `HTTPS_PROXY` and `ALL_PROXY` to
  http://127.0.0.1:9, and `NO_PROXY` to localhost,127.0.0.1,::1. The collector's HTTP client honours them. The
  verifier ran every step except the installs this way, because `uv sync` needs the package index.
- **The lock check:** the verifier ran `uv lock --check --offline`, using the workstation's uv cache. On a machine
  with an empty cache, run it without `--offline`.

**Database migrations, on a temporary database.** The verifier's `db-migrate` step does these, against a temporary
PostgreSQL of its own:

- `db-upgrade` twice (the second run, on the migrated database, must succeed too);
- `validate-config --check-db`;
- `sync-config`;
- `status --store walmart-3891-pickup`.

To do it by hand with an empty database of your own: set `WALMART_COLLECTOR_DATABASE_URL` (`.env.example` shows its
form) and `WALMART_COLLECTOR_DATA_DIR`, then run `uv run --frozen walmart-collector db-upgrade`.

**The Azure template.** No deployment is made:

```bash
bicep build azure/main.bicep --stdout
bicep lint azure/main.bicep
```

**The container.** It was built and run on Hamza's Azure test VM, not on the workstation, which has no Docker
([`evidence/owner-azure-test/1.5.2/azure_docker_recovery/README.txt`](../evidence/owner-azure-test/1.5.2/azure_docker_recovery/README.txt) gives the result, and [`walkthrough/WALKTHROUGH_1.5.2.mp4`](../walkthrough/WALKTHROUGH_1.5.2.mp4) shows it). To repeat it where Docker is
installed, in an edition folder of the copied source:

```bash
docker build -t walmart-oxylabs:verify .
docker run --rm walmart-oxylabs:verify --version          # walmart-azure-headless 1.5.2
docker run --rm walmart-oxylabs:verify                    # validate-config: the RESULT line, no key or database set
```

The image's entry point is the collector and its default command is `validate-config`. With a PostgreSQL of your own
and the data folder as a volume, the image also runs `db-upgrade`, `replay` and `resume`:
[`evidence/owner-azure-test/1.5.2/azure_docker_recovery/README.txt`](../evidence/owner-azure-test/1.5.2/azure_docker_recovery/README.txt) gives the exact commands of the replay, the kill and the resume.

Each edition's `docs/EDITIONS.md` explains the editions, and `docs/VERIFICATION.md` the release's own checks.

## 3. The product files

| File | Rows | What it is |
|---|---:|---|
| [`data/S6-1.5.1/products_fresh.json`](../data/S6-1.5.1/products_fresh.json) / `.csv` | 580 | **the demonstration on release 1.5.1**: products observed by run S6 (01M6A2VQAA5VXJHJHMZPCTZTD4) |
| [`data/S6-1.5.1/products_retained.json`](../data/S6-1.5.1/products_retained.json) / `.csv` | 706 | S6's export with 126 rows carried from the campaign's earlier runs (not fresh) |
| [`data/S7-1.5.1/products_fresh.json`](../data/S7-1.5.1/products_fresh.json) / `.csv` | 32 | run S7 (release 1.5.1), S6's first page about 39 minutes later |
| [`data/S7-1.5.1/products_retained.json`](../data/S7-1.5.1/products_retained.json) / `.csv` | 706 | S7's export with 674 carried rows |
| [`data/S4-1.5.0/products_fresh.json`](../data/S4-1.5.0/products_fresh.json) / `.csv` | 677 | run S4 of release **1.5.0**, labelled as such |
| [`data/S4-1.5.0/products_retained.json`](../data/S4-1.5.0/products_retained.json) / `.csv` | 689 | S4's export with 12 carried rows |
| [`evidence/offline-replay/1.5.2/offline_reprocessing/S6_products_fresh_OFFLINE_REPLAY.json`](../evidence/offline-replay/1.5.2/offline_reprocessing/S6_products_fresh_OFFLINE_REPLAY.json) / `.csv` | 580 | **OFFLINE REPLAY**: S6's own stored pages read again by release 1.5.2; no new collection |
| [`evidence/offline-replay/1.5.2/offline_reprocessing/S6_products_retained_OFFLINE_REPLAY.json`](../evidence/offline-replay/1.5.2/offline_reprocessing/S6_products_retained_OFFLINE_REPLAY.json) / `.csv` | 706 | the same replay's export with its carried rows |
| [`evidence/offline-replay/1.5.2/offline_reprocessing/B3_products_fresh_OFFLINE_REPROCESSING.json`](../evidence/offline-replay/1.5.2/offline_reprocessing/B3_products_fresh_OFFLINE_REPROCESSING.json) / `.csv` | 662 | **OFFLINE REPROCESSING**: B3 of release 1.4.1 read again by 1.5.2 from its own stored pages; no new collection |
| [`evidence/offline-replay/1.5.2/offline_reprocessing/B3_products_retained_OFFLINE_REPROCESSING.json`](../evidence/offline-replay/1.5.2/offline_reprocessing/B3_products_retained_OFFLINE_REPROCESSING.json) / `.csv` | 862 | the same replay's export with B3's carried rows |

There is no merged file, and the two providers' rows are never mixed. [`data/RUN_SUMMARY.json`](../data/RUN_SUMMARY.json) gives each file's row
count, SHA-256 and run.

To check a file against the 22-field contract, from a copied edition:

```bash
uv run --frozen walmart-collector validate-export --file <clone>/data/S6-1.5.1/products_fresh.json
```

Without an environment, `python3 manifests/check_data.py` checks every file of `data/` the same way, and checks each
against its run's own export and `record_map.json`.

Each row has the 22 fields in order, all strings, and:

- `gupc` and `unit_price` are always empty;
- `zipcode` is 60085;
- `crawl_date` is the store-local date of the row's own observation (a carried row keeps its original date).

## 4. One row, from the product file to the page it was read from

1. Take a row of [`data/S6-1.5.1/products_fresh.json`](../data/S6-1.5.1/products_fresh.json) and note its `url`. The item id is the last number of its
   path.
2. Open [`evidence/live/runs/01M6A2VQAA5VXJHJHMZPCTZTD4/exports/record_map.json`](../evidence/live/runs/01M6A2VQAA5VXJHJHMZPCTZTD4/exports/record_map.json). Find the row
   with that `url`. It gives:
   - `observation_kind` (`fresh`);
   - `observed_by_run`, `observed_at` and the code `commit`;
   - `page.stored_page`, the page the row was read from, with its SHA-256 in `page.stored_page_sha256`.
3. The page is in the same run folder, under pages/ with that file name.
   - Its fetch is the row of `db/page_fetches.csv` with that id: URL, purpose, time and HTTP status.
   - Decompress the page and search it for the product title. `fields.<field>.selector_or_path` names where each
     value was read.
4. A carried row names its own earlier run in `observed_by_run`. Open that run's folder instead.
5. A blank UPC or size: the run's `exports/field_dispositions.json` says why it is blank.
   - A value recovered from a saved product page names that page, its run, time and revision.
   - A page that was not read is `not_attempted` or `budget_deadline_interruption`; one that was asked for and not
     answered is `blocked` or `request_failed` (exports of release 1.5.1 and earlier say `inaccessible_challenged`).

The verifier (section 5) made this check for every delivered row. The evidence ZIP's `README.md`
([`evidence/as-packaged/README.md`](../evidence/as-packaged/README.md)) explains each archive folder, and [`evidence/README.md`](../evidence/README.md)
gives its repository folder. [`EVIDENCE_MANIFEST.csv`](../evidence/as-packaged/EVIDENCE_MANIFEST.csv) lists every archive file with its SHA-256 as
packaged. [`SANITIZATION_LOG.csv`](../evidence/as-packaged/SANITIZATION_LOG.csv) lists every file changed when it was packaged, with both hashes: a
changed file is not a byte-for-byte original. The same holds for the files changed for this publication, listed in
[`manifests/REDACTIONS.csv`](../manifests/REDACTIONS.csv) with both hashes.

## 5. The verifier that wrote [`evidence/verification/PACKAGE_VERIFICATION.txt`](../evidence/verification/PACKAGE_VERIFICATION.txt)

**It is not published here.** The verifier, the modules it imports and the builder of the delivery were in the
delivery's `verification/delivery_scripts/`. They are bound to the delivery folder's layout, to the preparation
workstation's paths and to private inputs, so this repository does not publish them ([`manifests/EXCLUDED.csv`](../manifests/EXCLUDED.csv)
gives each one's SHA-256). Their record is published: [`evidence/verification/`](../evidence/verification/) holds the report, each
step's command, exit code and duration (`steps.jsonl`), each step's log, the JUnit XML and the data checks. What follows
says how the verifier worked, to read that record. For this repository, the checks of section 1 take its place.

**How it records.** The verifier runs each step as its own process and writes each step's output to the work
folder's `logs/` folder. It composes the report only from what was recorded, so a step that did not run is NOT RUN
and counts as a problem. A step name the verifier does not know makes it print the full list.

**The steps of each edition**, in order (use the prefix `oxylabs.`, then `scrapedo.`):

- `paths`, `lock`, `install`, `imports`, `edition`;
- `ruff`, `ruff-format`, `mypy`;
- `cli-version`, `cli-help`, `validate-config`, `db-migrate`;
- `validate-export.<file>` for each product file the edition checks, for example
  `oxylabs.validate-export.live__S6_1.5.1__products_fresh` (`__` stands for `/`);
- `wheel`, `bicep-build` and `bicep-lint` (with `--bicep=<bicep executable>`), `docker`;
- `unit`, then `int-<file>` for each of the 20 files of `tests/integration/` (for example `oxylabs.int-test_replay`).

**The probe's steps:** `probe.extract`, `probe.install`, `probe.imports`, `probe.ruff`, `probe.ruff-format`,
`probe.mypy`, `probe.pytest-standalone`, `probe.pytest-with-collector`, `probe.cli`.

**What the data step checks.** It checks the delivery itself, in 14 sections:

1. the inventory of the delivery folder;
2. archives;
3. the source ZIP;
4. the probe ZIP;
5. the evidence ZIP, extracted;
6. the product files;
7. every row of the nine runs' exports against its record and its stored page;
8. UPCs;
9. the offline reprocessing;
10. the acceptance matrix;
11. references;
12. PDFs;
13. secrets, personal data and wording;
14. earlier deliveries.

The top of the verifier describes each one.

**Inputs that stay on the preparation workstation.** Some checks used files that are not in this delivery:

- the provider keys (`--secrets`), to prove that no key value is anywhere in the delivery, with every archive member
  opened;
- the full values that the documents abbreviate (`--rules`);
- the operator's own names and addresses (`--personal`);
- the two secret scanners (`--scanner`, `--scanner2`);
- the git repository (`--repo`), to rebuild each edition from the commit.

Without them, those checks are reported NOT RUN and counted as problems, never as passed. Run a secret scanner of
your own over this repository instead.

**The earlier deliveries.** `--earlier` must name a folder that holds the earlier deliveries as they were on the
preparation workstation. Without it, section 14 is NOT RUN.

**PDF page rendering.** `--pdf-renderer` rendered every page of the delivery's one PDF, its client summary, with the
Windows PDF engine. That PDF, its Markdown source and the workstation utilities that rendered it are not published
here.

**A workstation setting.** On the preparation workstation, Windows Smart App Control blocks the `_socket` module of
the uv-managed Python. So the environments were built with `UV_PYTHON` naming the signed python.org CPython 3.12.10.
This setting is specific to that workstation; elsewhere, uv picks its own Python 3.12.

## 6. The Oxylabs Classic offline probe

The probe has never sent a request. Its live mode is disabled in the code, and it holds no credential.

```bash
mkdir C:/p152 && cp -r classic-probe/oxylabs-classic-probe C:/p152/
cd C:/p152/oxylabs-classic-probe
uv sync --frozen
uv run --frozen pytest                     # one skip, named in README_FIRST.md
uv run --frozen ruff check src tests
uv run --frozen ruff format --check src tests
uv run --frozen mypy
uv run --frozen classic-probe plan --targets config/targets.json
uv run --frozen classic-probe validate --targets config/targets.json --rates config/rates.example.json
uv run --frozen classic-probe campaign-init --manifest C:/p152/m.json --ledger C:/p152/l.sqlite3 --campaign-id review --offline
uv run --frozen classic-probe status --manifest C:/p152/m.json
uv run --frozen classic-probe live --manifest C:/p152/m.json     # refused, exit 3: it lists what is missing and sends nothing
```

The offline ledger of `campaign-init --offline` is a test ledger and never authorizes a request.

The skipped test compares the probe's three vendored page readers with the collector's own files. To run it, put a
copy of `source/walmart-oxylabs-1.5.2` beside oxylabs-classic-probe, under the name
walmart-azure-headless (`cp -r source/walmart-oxylabs-1.5.2 C:/p152/walmart-azure-headless`), as the probe's
[`README_FIRST.md`](../classic-probe/README_FIRST.md) says. The verifier's `probe.pytest-with-collector` step
does exactly that.

The tests use SYNTHETIC Classic responses, so they show nothing about what Classic returns for the client's account.
[`classic-probe/oxylabs-classic-probe/CLASSIC_TEST_PLAN.md`](../classic-probe/oxylabs-classic-probe/CLASSIC_TEST_PLAN.md) is the proposed campaign, and it is **unapproved**. It needs the account owner's credentials,
entitlement, rates and written approval, and a separately approved build with live mode enabled.

## 7. The proposed client-observed live sequence on release 1.5.2 (paid; needs approval; not yet run)

This is the next acceptance step. The runs of 2026-10-31 were Hamza's own, paid from Hamza's own balance. They ran releases 1.5.0 and 1.5.1 and are not
client-observed acceptance. This sequence runs release 1.5.2, with the same store and the same commands, while the
client watches (a screen share) or runs it. It is the first live run of 1.5.2 unless Stage 1 of [`TEST_PLAN.md`](TEST_PLAN.md) comes
first.

**Before it starts:**

1. **Written approval** from the client of:
   - the account (whose Oxylabs Web API key);
   - the limits below;
   - the time.

   The client's Oxylabs Classic proposal is a separate matter and stays unapproved.
2. **A database and a data folder of their own**, never the campaign's:
   - `WALMART_COLLECTOR_DATABASE_URL`;
   - `WALMART_COLLECTOR_DATA_DIR`;
   - the key in `OXYLABS_WEB_API_KEY`, set in the shell only and never in a file of the delivery.
3. **Schedules stay off.** Nothing here enables one.

**Proposed limits (Oxylabs Web API edition):**

- **Submissions:** at most 30 in all. That is the canary's 4, the demonstration's 22 (S6's count, with its kill and
  its resume), and 4 of headroom for a retry or a second resume.
- **Money:** USD 0.045 at the reserve rate of USD 0.0015 a submission.
- **Time:** 45 minutes from the first submission.

These limits are a proposal, not an approval. They come from what S1 and S6 used on 2026-10-31. Walmart's pages
change, so the counts can differ.

**The sequence.** Run it from a copy of the walmart-oxylabs-1.5.2 folder (section 2), with each command as
`uv run --frozen walmart-collector ...`.

```bash
validate-config --require-credentials --check-db      # the key shows as a fingerprint only
db-upgrade
set-ceiling --provider oxylabs --submissions 30 --usd 0.045 --minutes 45 --usd-per-result 0.0015 \
  --basis "client-observed acceptance of release 1.5.2, approved by <name> on <date>"

# 1. canary (as S1): store page, store checks, one listing page, one product page
run --store walmart-3891-pickup --provider oxylabs --categories 0 \
  --subcategory 0:/browse/food/fresh-fruits/976759_976793_9756351 \
  --max-pages-per-listing 1 --pilot-detail-pages 1 --follow-up-pages 0 --workers 1 --max-credits 6 --max-minutes 10

# 2. the demonstration (as S6): five category rows, up to 3 pages per listing
run --store walmart-3891-pickup --provider oxylabs --categories 0,1,3,6,7 \
  --subcategory 0:/browse/food/fresh-vegetables/976759_976793_8910423 \
  --subcategory 1:/browse/laundry/1115193_1071967 \
  --subcategory 3:/browse/hair-care/shampoo/1085666_3147628_5752434 \
  --subcategory 6:/browse/health-medicine/shop-all-cold-cough-flu-medicine/976760_4661388_6244277_7158394 \
  --subcategory 7:/browse/pets/dry-dog-food/5440_202072_6432755_1636265 \
  --max-pages-per-listing 3 --pilot-detail-pages 1 --follow-up-pages 0 --workers 1 --max-credits 23 --max-minutes 30

# 3. while step 2 collects, after a few pages: kill it hard, from another terminal
#    Windows: taskkill /F /T /PID <pid of walmart-collector>      Linux: kill -9 <pid>
status --run <run id>                  # the killed segment is "abandoned", with no end time invented
run --store walmart-3891-pickup ...    # the same command as step 2: refused, exit 9 (an unfinished run); no request
resume --run <run id> --workers 1      # continues from its checkpoints; pages already collected are not requested again

# 4. if it stops at its ceiling (exit 4, SPENDING_CEILING): close it without a request
finalize --run <run id>

# 5. the run's own checks and files (no request)
validate-export --run <run id>
export --run <run id> --out <folder>
field-dispositions --run <run id> --csv <folder>/field_dispositions.csv
coverage-report --run <run id> --out <folder>
schedule-status --store walmart-3891-pickup          # reads only; no schedule has run
```

**What it shows:**

- the same contract and checks as [`data/S6-1.5.1/products_fresh.json`](../data/S6-1.5.1/products_fresh.json);
- the store checks on every listing page;
- the kill, the refused overlap and the resume;
- the field outcomes, observed by the client on the delivered release.

Prices, assortment and stock will differ from 2026-10-31, because Walmart changes them.

**What it does not show:**

- full coverage of the required categories;
- the full store size;
- the runtime of a complete run;
- the twice-weekly cadence.

Each of those needs a complete run ([`COST_AND_RUNTIME_REPORT.md`](COST_AND_RUNTIME_REPORT.md), section 11).

**The Scrape.do edition.** The same sequence applies, from walmart-scrapedo-1.5.2, with `--provider scrapedo`, and
`set-ceiling --provider scrapedo --credits N --usd-per-credit X` instead of the Oxylabs ceiling. It needs Scrape.do
credits: the account had 10 of 1,000 monthly credits left at 2026-11-01T18:23:14Z. The
demonstration needs about 213 credits (the canary about 21, a 19-page run about 192). So the Scrape.do final-version
demonstration stays BLOCKED until credits are available and approved.
