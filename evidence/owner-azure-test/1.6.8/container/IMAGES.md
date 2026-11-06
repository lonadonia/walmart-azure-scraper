# Release 1.6.8 as Docker images, on the owner's Azure test VM

**Evidence class.** OWNER AZURE TEST VM. The tests ran on SYNTHETIC data and REPLAYED stored live pages. No request
reached a provider or Walmart: every container ran without a provider key, with HTTP(S) sent to a closed local port
(`127.0.0.1:9`). The build itself fetched the base images and the locked Python packages. This is an owner test, not
the client's environment. The client's VM was not touched.

| Item | Value |
|---|---|
| Host | the owner's Azure test VM: Ubuntu 24.04.5 LTS, kernel 7.0.0-1017-azure, x86_64, 2 vCPU, 3.9 GB of memory, PostgreSQL 16 |
| Date | 2026-11-05, 21:24:30Z to 22:09:14Z (`steps.jsonl`: 89 steps) |
| Source | the two edition ZIPs of `WALMART_SOURCE_1.6.8.zip`, built at commit `85c29e7b2404500299056973f50c84b84e187a5a`, their SHA-256 checked first (`logs/prep.log`) |
| Docker | Ubuntu's packages `docker.io` 29.1.3-0ubuntu3~24.04.2, `containerd` 2.2.1-0ubuntu1~24.04.4 and `runc` 1.3.4-0ubuntu1~24.04.1. They were downloaded and unpacked into the project folder, not installed; their SHA-256 are in `logs/prep.log`. The daemon ran only for this gate. It had its own data root, run folder and socket, no bridge, and no iptables or forwarding rules (`daemon.json`) |

The VM has no system Docker.

## The images

Each image was built by `docker build --pull --network host` from its edition's extracted folder. The legacy builder
was used (`DOCKER_BUILDKIT=0`), with `SOURCE_COMMIT` and `BUILT_AT` as build arguments (`logs/build_<edition>.log`).

| Image | Image ID | Size (bytes) | `docker save` SHA-256 | `BUILD_INFO.json` |
|---|---|---|---|---|
| `walmart-collector-q168d:1.6.8-oxylabs` | `sha256:330d11c531928fa57b1c9048e5b87e5fb332f096f8e3c0a1abc9203e97b538e7` | 222,457,222 | `f454fe26418d54a99b43977c0cbcf9a4ba7a1f9b6fb805536f5b73f80118a761` | commit `85c29e7…`, built 2026-11-05T21:24:43Z |
| `walmart-collector-q168d:1.6.8-scrapedo` | `sha256:be4e7e408bfe57f04ad2af2512581f0d201c0d73088fc8a5fa39a6ec774f7e5e` | 222,457,224 | `b801b7342480399f0054def1f7e1ae9a68d2fe88d9c56c5148e4b5082824f9d2` | commit `85c29e7…`, built 2026-11-05T21:25:45Z |
| `walmart-collector-q168d:1.6.6-oxylabs` (rollback) | `sha256:2ac45cd5a1bf113dd6fb0f204c246b5d8535a768de3edcf423d3c18e2036c609` | 222 MB | not saved | the published 1.6.6 Oxylabs ZIP (SHA-256 `0859a2f6…`), commit `cbea802…` |

The two base images were pulled by digest:
- `python:3.12-slim-bookworm`: `python@sha256:935c3c5b12357a7e10caa9c1e6ca5692344d97cf229832ef584be2cec9fc03df`;
- `uv` 0.13.1: `ghcr.io/astral-sh/uv@sha256:4a1f3666816dafadd20ceb71eac9a7d56d7ef30279f7d64048519ab901ada336`.

The images were not pushed to any registry.

Inside each 1.6.8 image (`logs/image_report.log`):
- **Version and identity.** `BUILD_INFO.json` names commit `85c29e7`, and `--version` prints `walmart-azure-headless 1.6.8`.
- **User and defaults.** The user is `collector` (uid 10001, not root). The entrypoint is `walmart-collector`, and
  the default command is `validate-config`.
- **Layers and history.** Each image's layer digests (`RootFS.Layers`), environment and build history are in the same log.
- **Files match the ZIP.** `/app/src` and `/app/config` equal the edition ZIP's files, SHA-256 for SHA-256: 101 files.
- **No secrets.** No env file or private key is present. A search for `*.env`, `.env*`, `*.pem` and `*.key` finds
  only public CA certificates. These are the base image's certificate store under `/etc/ssl/certs` and pip's
  certifi bundle.

## What ran, and the results

Each step's command, exit code and expected exit code are in `steps.jsonl`, and its output is in `logs/<step>.log`.

| Check | Result |
|---|---|
| Smoke: `--version`, `--help`, the default command | exit 0, both editions |
| No key in the container: `validate-config --require-credentials` | exit 3 (CREDENTIALS), both editions; the output says the edition's key is not configured |
| A new isolated database per edition (`walmart_q168d_c_oxylabs`, `…_scrapedo`) | the schema check fails first, as it must (exit 2; revision none, head `0006`). Then `db-upgrade` (to `0006`), the check again (0), `db-upgrade` again, which changes nothing (0), `sync-config` (0) and `status` (0) |
| The campaign database restored into `walmart_q168d_c_campaign`, the stored pages of L10 and L12 loaded into a volume | exit 0. Inputs: `campaign_live150.dump` (SHA-256 `29865961…`) and `stored_live_L10_L12.tar` (`02d66177…`) |
| Replay of L12 (`01M6MC7YE4PBXV88G3PJ5ENW4B`, release 1.6.6) as `01M6PSR0QX0H8X0HRE3YWNDA8Y` | exit 0, status rejected as a pilot: G3 failed, the coverage check a bounded run fails by design. 40 valid records and 10,261 carried, as in L12; 297 carried rows renamed by the agreed mapping ([L12 below](#l12-against-its-published-export)) |
| Replay of L10 (`01M6KA3CKYJSD6WDY4TDAAV73Y`, release 1.6.4) as `01M6PSW480FW90MCQ8FVS8RNMD` | exit 6, rejected by G3 and G4, as L10 itself was on 1.6.4 ("REJECTED AS A PILOT (G3, G4)"). G4: Household Essentials has no fresh valid record against 1,172 retained, and Health & Wellness 121 fresh valid against 293 retained (71%). 6,880 valid, 23 excluded, 3,289 carried, 2 exported not valid |
| `status`, `coverage-report` and `export` of both replays and of their source runs | exit 0 |
| `validate-export` of both replays, before the other runs' stored pages were in the volume | exit 2: the first page missing, a stored page of an earlier run that carried records cite. The step's expected exit was "any"; the message names only the missing file |
| The other 22 runs' stored pages loaded (`stored_live_other22.tar`, `0ff0b87c…`), then `validate-export` of each replay and of the killed run | exit 0, `passed`. Every exported record was checked against its own stored page: 10,301, 10,171 and 10,171 verified, 0 mismatched |
| Kill and resume of an L10 replay | the ordinary `resume` continued the run killed with SIGKILL. Its export equals the uninterrupted replay's, byte for byte (`kill_resume/KILL_RESUME_COMPARISON.txt`) |
| Rollback | the published 1.6.6 Oxylabs edition, built as an image, ran against the database 1.6.8 had migrated. It printed version 1.6.6, and the schema check passed (revision `0006` = head: 1.6.7 and 1.6.8 add no migration). `status` passed, as did `status` and `export` of the L12 replay. Its export equals 1.6.8's export of the same run, byte for byte (12 files) |
| Roll forward | 1.6.8 again on the same database: the schema check and `status`, exit 0 |
| Persistence across a restart | the gate's dockerd and containerd were stopped and started again. Images and volumes were listed. The campaign volume's 63 files have the same SHA-256 before and after. Each run's `status` is the same before and after. The exports made after the restart equal those made before, byte for byte (36 files) |
| Coverage reports of the 15 live runs, made by the 1.6.8 image from the stored data (`coverage_live/`) | exit 0. They are the inputs of the W4 tables (`../../../reconciliation/1.6.8/w4/`) |
| `after` | **exit 1, not passed.** The host-state comparison found the gate's four databases still present (`walmart_q168d_c_campaign`, `…_killresume`, `…_oxylabs`, `…_scrapedo`). They were kept for the checks made after the gate, then dropped (`../HOST_STATE.md`). No daemon or mount of the gate remained |
| `walk`, the recorded walkthrough | **failed, judged by its output.** The step exited 0, but the recording shows `command not found`. asciinema starts the recorded command through `sh` (dash), which does not pass on the gate's exported bash functions. The gate's script and recording are kept: `walkthrough_168.gate.sh`, `WALKTHROUGH_1.6.8_GATE_FAILED.cast`. The walkthrough was recorded again in a session of its own (`../walkthrough/`) |

### L12 against its published export

The 1.6.8 replay of L12 matches the export that release 1.6.6 published on all 10,301 records, matched by product
URL. It differs in two ways:
- **9 UPCs filled.** These come from saved product pages: `historical.upc_filled`, never a guess.
- **337 sub_category values.** All follow from the agreed mapping
  (`../../../reconciliation/1.6.8/l12/`).

The six always-empty fields stay empty.

| 1.6.6 name | 1.6.8 name | Rows | Why |
|---|---|---|---|
| Laundry | Shop All Laundry Supplies | 184 | the Household Essentials page names listing `1115193_1071967` so |
| Fabric Softener | Fabric Softeners | 52 (40 of them L12's own) | the same page names `1115193_1071967_1630538` so |
| Dry Dog Food | Dry dog food | 39 | the Pets page names `5440_202072_6432755_1636265` so |
| Laundry Detergents | Laundry Detergent | 38 | the Household Essentials page |
| Laundry Scent Boosters | Scent Boosters | 19 | the Household Essentials page |
| Great Value Pantry | Pantry | 5 | the Food page links `976759_976794_2002490` twice: "Pantry" (9th link), then "Great Value Pantry" (55th); the first name stands |
