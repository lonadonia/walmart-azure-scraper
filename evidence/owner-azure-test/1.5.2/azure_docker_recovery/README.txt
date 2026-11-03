OWNER AZURE TEST: release 1.5.2 in Docker on Hamza's Azure test VM, 2026-11-01

What this is
  Release 1.5.2 (commit 627c804) built in Docker from the delivered source ZIP and run offline on Hamza's own Azure test
  VM. It is not the client's Azure environment, and nothing here is a live run: no Oxylabs, Scrape.do, Classic or Walmart
  request was made. Deploying in the client's Azure remains to be done (ACCEPTANCE_RUNBOOK.md).

The machine
  Ubuntu 24.04.5 LTS, 2 vCPUs, 3.9 GB of memory, reachable by SSH only from the owner's VPN. Installed for this work at
  19:07Z to 19:08Z: Docker (docker.io 29.1.3), ffmpeg and asciinema with their dependencies, 166 packages in all.
  Cleaned at 21:25:27Z to 21:26:17Z: the containers, volumes, network, images and build cache removed, then the 166
  packages purged (none left), with Docker's state folders and the docker group. Left on the VM: the folder of this work
  (68 MB: the logs, the ZIPs, the backups, the first pass's archive and a dump of the test database after the container
  replays). Nothing in it runs, and no timer or cron entry names the collector. The six databases' row counts after the
  cleanup are those of 19:25:58Z. The VM was left running, as it was found.

What ran, and the result (UTC, 2026-11-01; one log per step)
  19:25:58Z  The machine's environment, the row counts of its own six databases and a backup of them, before any Docker
             or collector step (the packages above were already installed).
  19:55:15Z  The Oxylabs Classic offline probe 1.5.2 from its ZIP alone: installed from its lock, 71 tests passed and 1
             skipped, its plan, an offline campaign, and the live command, which is refused (exit 3); nothing was sent.
             The ZIP tested here, whose hash the walkthrough shows, has SHA-256
             20de284c329cf3c582bc8d8b871937a4dfc9787cfbca2e8daf1498e67a1d357b. The delivered ZIP,
             d4785ccbb8b23a4d2bb6cfb6b16ba1242cab5cab0b292e3222581f7844282193, was rebuilt on 2026-11-02 from the same
             revision to replace the workstation's name in one recorded file (offline_results/junit_standalone.xml, its
             "hostname" attribute). The other 131 of its 132 files are identical (PROBE_ZIP_TESTED_VS_DELIVERED.json), and
             the delivered ZIP is verified from a clean extraction on the workstation (PACKAGE_VERIFICATION.txt).
  19:55:31Z  Both editions built from WALMART_SOURCE_1.5.2.zip
             (SHA-256 1100aa16ce7d459afd020c057eff3fb42cd54bcc172a4c22f04ba3f1859af941): exit 0 in 27 s (Oxylabs) and
             22 s (Scrape.do). Each image is 74 MB compressed and 323 MB unpacked.
  19:56:21Z  In both images, --version gives "walmart-azure-headless 1.5.2" and validate-config exits 0. Without a key,
             validate-config --require-credentials is refused with exit 3 (CREDENTIALS). The collector runs as the
             unprivileged user "collector" (uid 10001).
  19:56:34Z  The containers' Docker network is internal: it reaches the test database container and nothing else. A
             connection to an outside address fails (Network is unreachable).
  19:56:46Z  db-upgrade on a copy of the campaign database (already at schema revision 0006), then validate-config.
  19:56:50Z  The nine runs of 2026-10-31 replayed in the container from their stored pages, then exported (to 19:59:22Z).
             S1, S2, S3: exit 0, only the coverage check G3 failing, the one check a pilot run is expected to fail.
             S5a, S5b serial, S5b parallel, S7: exit 6, checks G3 and G4, as in their live runs.
             S4 stopped with SIGTERM (exit 75) and resumed (exit 0); S6 killed with SIGKILL (exit 137) and resumed
             (exit 0); both then failed G3 only. After each resume, the only pages read twice were robots.txt and the
             store page: the resumed session's own setup.
             Compared with the same replays on the workstation: for all nine, the product, offer and membership files
             are byte-identical, and the field-outcome files are identical once each replay's own run and fetch ids are
             numbered. The differences that remain are listed in CONTAINER_COMPARISON.txt.
  19:59:25Z  From the source ZIP, the Oxylabs edition's checks: ruff, the format check, mypy, the unit tests and 18
             integration test files, each exit 0.
  20:14:23Z  SYNTHETIC TEST: publication faults against a fixture standing in for Walmart: 10 passed.
  20:16:10Z  SYNTHETIC TEST: the load tests against a local fixture, with 1, 2 and 4 workers: 6 passed.
             With the two steps above: 666 tests in 21 JUnit files, none failed, errored or skipped.
  20:20:08Z  The six databases' row counts again: unchanged since 19:25:58Z.
  21:06:33Z  Both images checked again: the same image ids, --version and validate-config exit 0.
  21:19:22Z  The recorded walkthrough, WALKTHROUGH_1.5.2.mp4: the commands above shown again, and a new kill and resume
             on a fresh copy of the campaign database, dropped afterwards.
  21:25:27Z  The cleanup above (owner_vm/logs/cleanup.log; the row counts in owner_vm/logs/counts_after_cleanup.log).

Not evidence
  A first pass from 19:28Z ran commit 2ed64b7, the first 1.5.2 commit, before the final fix (627c804). Its logs are kept
  on the VM, outside the evidence; its list of steps is in owner_vm/v152x/ for reference. Only its records made before
  any Docker or collector step are used: the environment, the row counts and the backup, 19:25:58Z to 19:26:00Z.

Where to look
  DOCKER_VM_RESULT.json in this folder: the build results by edition.
  WALMART_EVIDENCE_1.5.2.zip: 7_release_1_5_2/owner_vm/ holds the record of every step: commands.csv (each step's start,
  end and exit code), logs/ (one log per step), junit/, load/, publication/, the container's exports
  (replay/exports_container.tar.gz), CONTAINER_COMPARISON.txt, PROBE_ZIP_TESTED_VS_DELIVERED.json, pkgs_added.txt, the
  cleanup script and its log, and
  backup/SHA256SUMS.txt (the backups themselves stay on the VM).
  WALMART_EVIDENCE_1.5.2.zip: 7_release_1_5_2/walkthrough/ holds the walkthrough's script, its recording (.cast) and the
  renderer that made the MP4.
