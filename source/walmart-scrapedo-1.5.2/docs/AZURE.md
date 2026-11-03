# Azure deployment

Two options are documented separately: **A. Container Apps jobs** (this file, `azure/main.bicep`) and
**B. one small Linux VM** for the smallest test (AZURE_VM.md). Neither has been run in Azure.

> Status: the template (`azure/main.bicep`) compiles and lints without warnings (Bicep CLI 0.48.1). It
> has **not been deployed** and the image has **not been built**: no Azure subscription and no Docker were
> available where this package was prepared. A local run of the same commands (VERIFICATION.md) is not
> proof of an Azure deployment.

## Resources

| Resource | Created by the template | Purpose |
|---|---|---|
| User-assigned managed identity `walmart-collector-identity` | yes | the jobs' only identity |
| Role assignments | yes | AcrPull on the registry; Key Vault Secrets User on the vault; Storage Blob Data Contributor on this collector's container |
| Blob container `walmart-collector` | yes (in the existing account) | stored pages, exports, `published/` |
| Scheduled job per store (`walmart-3891-pickup`; the name is a parameter) | yes | `run --store <key> --scheduled` on the store's UTC cron |
| Manual job `walmart-collector-ops` | yes | operations: `db-upgrade`, `status`, `resume`, `stop`, `finalize`, `export`, `release-hold`, ... |
| Container Apps environment + Log Analytics workspace | only with `createEnvironment=true` | runs the jobs; collects their output |
| Container registry, Key Vault, storage account, PostgreSQL server | no (existing, named by parameters) | |

Nothing in the template or the image holds a secret value.

## Prerequisites

1. A resource group with a container registry, a Key Vault using Azure RBAC authorization, a storage
   account, and an Azure Database for PostgreSQL flexible server with a database for this collector
   (e.g. `walmart_collector`; never shared with another collector).
2. Two Key Vault secrets (create them from files so no value lands in shell history, then delete the files):

   ```bash
   az keyvault secret set --vault-name <kv> --name walmart-collector-scrapedo-api-key --file scrapedo.key
   az keyvault secret set --vault-name <kv> --name walmart-collector-database-url --file database-url.txt
   ```

   The database URL is `postgresql://<user>:<password>@<server>.postgres.database.azure.com:5432/walmart_collector?sslmode=require`.
   With `databaseAuth=entra` it has no password: the job's managed identity signs in with an Entra token.
   In that case, after the first deployment, make the identity a database role, e.g. as the server's Entra
   administrator: `SELECT * FROM pgaadauth_create_principal('walmart-collector-identity', false, false);`
   and grant it rights on the `walmart_collector` database.
3. `cp azure/main.parameters.example.json azure/main.parameters.json` and fill it in (the file is
   git-ignored: it names your resources, not secrets).

## Deploy

```bash
az login
azure/deploy.sh <resource-group> <registry-name> azure/main.parameters.json
```

The script builds the image in the registry (`az acr build`, with the source commit recorded in the
image's `BUILD_INFO.json`), deploys the template, and runs `db-upgrade` through the operations job. It
starts no collection.

Then, through the operations job: `validate-config --check-db --require-credentials` and
`provider-balance`.

## Operations job

The command is written in the job's `WALMART_COLLECTOR_COMMAND` variable, then the job is started (the
Azure CLI cannot pass arguments that begin with `--` to `job start` reliably):

```bash
OPS=walmart-collector-ops; RG=<resource-group>
az containerapp job update -n $OPS -g $RG --set-env-vars "WALMART_COLLECTOR_COMMAND=status --store walmart-3891-pickup"
az containerapp job start  -n $OPS -g $RG
az containerapp job execution list -n $OPS -g $RG -o table      # then read the execution's logs
```

Examples: `resume --store walmart-3891-pickup`, `stop --store walmart-3891-pickup --reason "..."`,
`finalize --store walmart-3891-pickup`, `release-hold --store walmart-3891-pickup --reason "..."`,
`export --store walmart-3891-pickup --out /tmp/x` (exports are also in the blob container),
`run --store walmart-3891-pickup --categories 4 --max-pages-per-listing 1 --max-products 10` (a pilot).

## Schedule, continuation and daylight-saving time

Azure evaluates cron expressions in UTC; the store's schedule is in its own time (America/Chicago). A
full-scope run lasts longer than one execution (OPERATIONS.md, Capacity), so with
`schedule.continue_unfinished: true` (the shipped setting) the job fires **every 30 minutes**
(`*/30 * * * *`: each store's `cronUtc` in the `schedules` parameter of `azure/main.bicep`) and each firing decides once and exits.
`run --scheduled`:

1. exits 0 (`SCHEDULE_OFF`) while the schedule is off (the shipped state, until the client approves it);
2. once the store-local start time of a scheduled weekday has passed (Tue + Fri 06:00 by default; from 5
   minutes early; since release 1.5.0 a later firing still starts it, late, and the lateness is recorded in the
   occurrence ledger): exits 8 (`COLLECTION_HELD`) if the store is held;
   reports a finished occurrence (`OCCURRENCE_DONE`, with its outcome's exit code) or continues its
   unfinished run (`OCCURRENCE_CONTINUED`); otherwise, when the scheduled run of an earlier occurrence is
   unfinished, lets it go on and starts no run (`OCCURRENCE_DEFERRED`, recorded on that run;
   `schedule.on_overlap: continue`, release 1.3.1) or, with `on_overlap: supersede` (release 1.3.0), closes
   it as partial (`RUN_SUPERSEDED`: exported, never published); with no unfinished run, starts the new run;
3. at any other firing inside the daily window (the whole day in the shipped configuration; any weekday): continues the store's
   unfinished scheduled run (`OCCURRENCE_CONTINUED`, `"continuation": true`), unless another execution is
   collecting it (exit 9, `STORE_BUSY`) or the store is held (exit 8);
4. otherwise exits 0 in seconds (`NOT_DUE`, with the next local start).

Because the decision is made in store-local time, a daylight-saving change never moves or doubles a run.
One execution collects for at most `limits.max_segment_minutes` (300, below the job's 360-minute replica
timeout) and then pauses the run at its checkpoint (`SEGMENT_DURATION_LIMIT`, exit 75): the run is not
finalized or published there. A scheduled run that reaches the window's end pauses the same way
(`SCHEDULE_WINDOW_END`) and continues in a later day's window. The shipped configuration sets no time limit
for the whole run (`limits.max_run_minutes` empty: a number there is a budget, and a run that reaches it
ends incomplete and is never published); its credit budgets and the provider ceiling are counted across
executions and never reset by a continuation. A continued run keeps the
scope, limits and counters recorded at its start; its finished pages, pagination cursors, pending UPC
detail pages and observations are checkpointed, so a continuation neither repeats nor skips them.

With Tuesday and Friday starts, two starts are 72 hours (Tuesday to Friday) or 96 hours (Friday to
Tuesday) apart, all of it window time in the shipped configuration. A run longer than that is not cut short:
the next occurrence lets it go on (point 2), and the store's complete datasets come less often than twice a
week until runs fit the interval (OPERATIONS.md, Capacity). With `on_overlap: supersede` the next occurrence
closes it instead: a superseded run is a partial dataset, exported and never published, and the products it
verified remain part of the store's retained assortment for later runs. (Release 1.3.0 shipped
`supersede` with a 06:00 to 18:00 window: 36 hours of window time from a Tuesday start to the Friday start,
48 hours from Friday to Tuesday, and a 48-hour `max_run_minutes`.)

`walmart-collector schedule-status --store <key>` reports each occurrence (start, lateness, run, deadline), the
backlog and the capacity gap. A start that could not run keeps its identity and starts later, oldest first;
queuing it keeps it visible, and does not by itself satisfy the twice-weekly cadence.

`walmart-collector schedule-info --store <key>` prints the start-only expression (`cron_utc`, for both UTC
offsets) and, with continuation on, `cron_utc_with_continuation`. There is no scheduler inside the
collector: each execution decides once and exits.

## Overlap, timeouts and retries

* **Overlap.** Each execution runs one replica (`parallelism: 1`). Two executions for the same store (a
  manual one during a scheduled one, or a slow run reaching the next firing) cannot collect at once: the
  store lock (a PostgreSQL advisory lock plus a lock row) refuses the second one (exit 9, `STORE_BUSY`).
* **Timeouts.** `replicaTimeout` is 21,600 s (6 h); the collection's own `max_segment_minutes` (300)
  pauses the execution first, resumably, and a later firing continues the run (above). If Azure stops an
  execution (timeout or a manual stop), the collector receives SIGTERM:
  it closes the provider session, keeps the run's checkpoints, marks the run `interrupted` (`TERMINATED`),
  releases the store lock and exits 75.
* **Retries.** Inside an execution: each page up to `retries.max_attempts_per_task` times with backoff
  (a 429 waits for its Retry-After or `pause_on_429_s`); a run stopped by a transient provider failure is
  resumed up to `max_auto_resumes` times. Azure retries a failed execution once (`replicaRetryLimit: 1`);
  that retry continues or reports the same occurrence, never starts a second one. A refusal, a store
  mismatch or a failed canary is never retried: the store is held until `release-hold`.

## Identity and secrets

The jobs use one user-assigned identity, only for this collector:

* image pull from the registry (AcrPull);
* the two Key Vault secrets, referenced by the jobs as Container Apps secrets
  (`SCRAPEDO_API_KEY`, `WALMART_COLLECTOR_DATABASE_URL`);
* blob read/write on its own container (`WALMART_COLLECTOR_STORAGE=azure_blob`, `AZURE_CLIENT_ID` selects
  the identity for `DefaultAzureCredential`);
* optionally the database itself (`WALMART_COLLECTOR_DATABASE_AUTH=entra`).

The Mariano's collector is deployed from its own project with its own identity, secrets, database,
container and jobs; neither can read the other's secrets or state. Their logs are told apart by job name.

## What runs where

* **Azure (this deployment):** the collector's code, the schedule's firing, the database, the blob
  storage, the secrets, the logs.
* **Scrape.do:** fetching each Walmart page for the store's location (its Walmart store endpoint) and
  robots.txt and the store page (its general API); reporting the key's balance. Scrape.do sees the page URLs
  and the store id and ZIP code; it does not see the database, the exports or the configuration.
* **Walmart:** serves the pages to Scrape.do.

## Costs to expect

Container Apps jobs bill per execution (vCPU-seconds and GiB-seconds; a skipped firing runs for a few
seconds); Log Analytics bills ingestion; PostgreSQL and storage bill as usual. Scrape.do bills credits:
10 per Walmart page through the store endpoint, 1 for robots.txt and the store page; a full scope run of
every category and subcategory page costs far more than a pilot. Use `max_credits_per_run` and
`set-ceiling` to bound spending.
