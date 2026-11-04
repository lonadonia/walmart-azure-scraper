# Azure option B: one small Linux VM

This collector runs on one Ubuntu 24.04 VM with a local PostgreSQL server, a service user and no schedule.
The scripts are in `deploy/vm/`. The delivery's Azure execution report says what was installed and run
this way on the operator's own Azure test VM: the resource, the host, the commands, the exit codes and the
measured memory. The Container Apps option (AZURE.md, `azure/main.bicep`) is separate
and was not deployed.

Only this collector is installed. Mariano's collector is not part of this procedure, and nothing here
depends on the earlier dashboard server.

## Size

| Resource | Used for the 2026-10-26 test | Notes |
|---|---|---|
| VM | `Standard_D2nls_v6`: 2 vCPU, 3.9 GiB RAM, Ubuntu 24.04 LTS, East US | 4 GiB is enough when the measured peak of PostgreSQL, the OS and one collection stays well below it (the execution report has the samples); 8 GiB only if a measured peak goes above 3 GiB |
| OS disk | 30 GB Standard SSD | about 0.3 MB of stored pages for each result page (compressed provider answer plus the page copy). Enough for tests and pilots, not for months of full-scope runs: production needs a data disk or a retention rule for old run folders |
| Network | public IP; SSH only | the collector makes outbound HTTPS calls only (Scrape.do or Oxylabs); no inbound web port. SSH is limited on the host to the operator's address (`restrict-ssh.sh`); restrict the network security group's SSH rule to the same address in the portal too |

## Permissions (no subscription-wide Owner)

**A. The VM exists (this test).** The operator needs **no Azure role**: an SSH login with `sudo` on that VM
is enough to install, run and stop the collector. Starting and deallocating the VM needs a custom role on
that VM only:

```json
{
  "Name": "Collector VM operator",
  "IsCustom": true,
  "Description": "Read, start, restart and deallocate one VM; nothing else.",
  "Actions": [
    "Microsoft.Compute/virtualMachines/read",
    "Microsoft.Compute/virtualMachines/instanceView/read",
    "Microsoft.Compute/virtualMachines/start/action",
    "Microsoft.Compute/virtualMachines/restart/action",
    "Microsoft.Compute/virtualMachines/deallocate/action"
  ],
  "NotActions": [],
  "AssignableScopes": ["/subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.Compute/virtualMachines/<vm>"]
}
```

Optionally, **Cost Management Reader** on the resource group lets the operator read the test's cost.

**B. A new VM.** The owner creates a dedicated resource group and assigns, at that resource group only and
for the test period, the built-in **Contributor** role (it cannot assign roles), or a custom role limited to
`Microsoft.Compute/virtualMachines/*`, `disks/*`, `Microsoft.Network/{virtualNetworks,networkSecurityGroups,
publicIPAddresses,networkInterfaces}/*` and `Microsoft.Resources/deployments/*` in that group. Remove the
assignment when the test ends.

## Install (from the operator's workstation)

```bash
# 1. The source of one commit, and the scripts. core.autocrlf=false keeps every file byte for byte (the
#    repository's .gitattributes is not inside the archived folder, so a Windows checkout would add CRLF)
git -c core.autocrlf=false archive --format=tar.gz --prefix=walmart-azure-headless/ -o walmart-src.tar.gz   <commit>:headless/walmart-azure-headless
sha256sum walmart-src.tar.gz
scp walmart-src.tar.gz deploy/vm/* azureuser@<vm>:/tmp/walmart-install/
# 2. Install or upgrade (idempotent): PostgreSQL 16, uv, the service user, the release, the database backup,
#    the migration, then the switch of /opt/walmart-collector/current
ssh azureuser@<vm> 'sudo bash /tmp/walmart-install/install.sh /tmp/walmart-install/walmart-src.tar.gz <full commit id>'
# 3. The keys: sent on standard input to files only the service user can read (never on a command line)
ssh azureuser@<vm> 'sudo install -m 0600 -o walmart -g walmart /dev/stdin /etc/walmart-collector/secrets/scrapedo.env' < scrapedo.env
ssh azureuser@<vm> 'sudo install -m 0600 -o walmart -g walmart /dev/stdin /etc/walmart-collector/secrets/oxylabs.env' < oxylabs.env
# 4. SSH only from the operator's address, with a 10-minute dead-man timer until confirmed from a new session
ssh azureuser@<vm> 'sudo bash /tmp/walmart-install/restrict-ssh.sh <operator address>'
ssh azureuser@<vm> 'sudo bash /tmp/walmart-install/restrict-ssh.sh confirm'
```

An edition (release 1.4.0, [EDITIONS.md](EDITIONS.md)) is installed from its source ZIP beside the core,
without changing the core's `current` release, environment, database or data:
`sudo bash install.sh WALMART_<EDITION>_SOURCE_<version>.zip <full commit id> <edition>`. It gets the release
folder `releases/<version>-<commit>-<edition>` (linked as `/opt/walmart-collector/edition-<edition>`), the
database `walmart_<edition>`, the data folder `/var/lib/walmart-collector/editions/<edition>/data` and
`/etc/walmart-collector/env.<edition>`, which names its provider's key file only; its commands run with
`WC_ENV` and `WC_RELEASE` (`walmart-cmd`, `walmart-run`). `install.sh` refuses a ZIP of another edition or one
built from another commit than the one given. `WC_CONFIG` names another configuration file for a command,
such as a test campaign's copy of the release's configuration folder with follow-up seeds of its own. A run
records the store's collection settings it ran with (`config_snapshot.collection`, seeds included), not the
file: keep the copy's hashes with the campaign's records.

What `install.sh` sets up:

| Path | Owner, mode | Content |
|---|---|---|
| `/opt/walmart-collector/releases/<version>-<commit>/` | root, read-only to the service | the source, `.venv` (exact `uv.lock` versions on the system's Python 3.12), `BUILD_INFO.json` (commit, install time, source SHA-256). An edition's folder (`<version>-<commit>-<edition>`) keeps the `BUILD_INFO.json` it was built with, and gets `INSTALL_INFO.json` (commit, edition, install time, source SHA-256) |
| `/opt/walmart-collector/current` | root | the release in use; `previous` names the one before |
| `/etc/walmart-collector/env` | root:walmart 0640 | database URL (local socket, peer authentication: no password exists), data folder, key file paths; no secret |
| `/etc/walmart-collector/secrets/` | walmart 0700, files 0600 | the provider keys |
| `/var/lib/walmart-collector/data` | walmart 0750 | runs, stored pages (evidence) and their exports |
| `/var/lib/walmart-collector/{exports,evidence,logs}` | walmart 0750 | copied exports, evidence files, the JSON log and resource samples of each collection |
| `/var/backups/walmart-collector/` | root 0700 | `pg_dump` taken before each migration |
| PostgreSQL 16 | `listen_addresses = localhost` | database `walmart_collector` owned by role `walmart` |

Every collector command runs as the service user in a systemd sandbox (`ProtectSystem=strict`, writable
only under `/var/lib/walmart-collector`, `NoNewPrivileges`, private `/tmp`). No timer, cron entry or
enabled collector service is installed; `install.sh` refuses to finish if one exists.

## Run

```bash
sudo walmart-cmd validate-config --check-db --require-credentials
sudo walmart-cmd provider-balance                       # Scrape.do: free /info
sudo walmart-cmd set-ceiling --credits 950 --usd-per-credit 0 --basis "..."
sudo walmart-cmd set-ceiling --provider oxylabs --submissions 12 --usd 0.05 --minutes 15 --basis "..."
sudo walmart-run demo run --store walmart-3891-pickup --workers 2 ...    # a transient unit walmart-demo
tail -f /var/lib/walmart-collector/logs/demo.jsonl                       # or journalctl -u walmart-demo -f
sudo systemctl kill -s SIGTERM walmart-demo     # interrupts resumably: the run keeps its checkpoints, exit 75
sudo walmart-run demo-2 resume --store walmart-3891-pickup --workers 2
sudo walmart-cmd status --store walmart-3891-pickup
sudo walmart-cmd export --run <id> --out /var/lib/walmart-collector/exports/<id>
sudo walmart-cmd coverage-report --run <id> --out /var/lib/walmart-collector/exports/<id>
```

`walmart-run NAME ...` starts `walmart-NAME` and `walmart-sample-NAME` (CPU and memory every 5 s to
`logs/NAME.resources.csv`); the last line of `logs/NAME.jsonl` is the command's result with its exit code.
A second `run` or `resume` of the same store while one collects is refused by the database's store lock
(exit 9), whatever process starts it; a new `run` is also refused (exit 9) while the store has an unfinished
run, until that run is resumed or finalized. If the process dies without closing its run (a `SIGKILL`, a
power loss), the run stays `running` with no worker; the next `resume` marks it interrupted
(`RUN_RECOVERED`) and takes back the tasks the dead workers held (`TASK_LEASE_RECLAIMED`), from their
checkpoints.

## Schedules stay off

No timer is installed and the configuration ships with `schedule.enabled: false`. When the client approves
a schedule, a systemd timer firing every 30 minutes inside the window would run
`walmart-cmd run --store <key> --scheduled`, which acts only on the store-local occurrence and otherwise
continues an unfinished scheduled run (AZURE.md, Schedule, continuation and daylight-saving time; the same
logic, tested offline).

## Upgrade and rollback

* Upgrade: run `install.sh` again with the new source and commit. It installs the new release beside the
  old one, takes a `pg_dump`, migrates with the new release, and switches `current` only after the
  migration succeeded (a failed migration changes nothing: it runs in one transaction).
* Rollback: `sudo bash rollback.sh` refuses while a collection runs, restores the database from the dump
  taken before the current release's migration, and points `current` back at the previous release. Runs
  collected after that dump leave the database (export what must be kept first).

## Stop, deallocate, clean up

* `sudo systemctl kill -s SIGTERM walmart-NAME` stops a collection at once (exit 75); the run keeps its
  checkpoints and `resume` continues it. `systemctl list-units 'walmart-*'` must then list nothing active.
* A VM shut down from inside the OS is **still billed** for compute: deallocate it in the portal (or
  `az vm deallocate -g <rg> -n <vm>`). The disk and the public IP stay billed while it is deallocated.
* A budget alert is **not** a stop. The collector's own limits stop spending: the provider ceilings and the
  task's money budget are reserved before every request (CLI.md, `set-ceiling`, `set-budget`), and
  `max_run_minutes` / `max_segment_minutes` bound the time.
* Before deleting the VM, copy out what must be kept: the exports, `/var/lib/walmart-collector/` and a
  `pg_dump` of `walmart_collector`.

## Cost

Azure retail prices (pay as you go, Linux, East US, read from the Azure Retail Prices API on 2026-10-26):
`Standard_D2nls_v6` **$0.113 an hour** (about $82 for a month left running); a 30 GB Standard SSD about
$2.40 a month; a Standard static public IP $0.005 an hour. A 24-hour test costs about $2.71 of compute.
Prices vary by region and change; the Azure pricing calculator for the chosen region is authoritative.
