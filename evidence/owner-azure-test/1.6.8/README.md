# Owner Azure test of release 1.6.8 (commit `85c29e7`) and probe 1.7.2

**Class: OWNER AZURE TEST.** Everything here ran on Hamza's own Azure test VM on 2026-11-05 (UTC), but for the probe
package built again before publication, run there on 2026-11-06: Ubuntu 24.04.5
LTS, kernel 7.0.0-1017-azure, x86_64, 2 vCPU, 3.9 GB of memory, PostgreSQL 16.15. It is **not the client's
environment**: the client's VM was not contacted, and no client observed or accepted these runs. **No provider,
retailer or Classic request was made**: the containers and processes had no provider key, and their HTTP(S) went to a
closed local port. The live pages replayed here were collected on 2026-11-04 by earlier releases (L10 on 1.6.4, L12 on
1.6.6); a replay is never counted as new collection.

Isolation: this work's own folders, its own PostgreSQL role and databases (`walmart_q168d_*`), its own Docker daemon
(Ubuntu's packages unpacked, not installed; its own socket and data root, no bridge, no firewall change) and its own
container and volume names. The VM's other databases and folders were not touched (`HOST_STATE.md`).

| Folder | What ran | When (UTC) | Result |
|---|---|---|---|
| [`linux-suite/`](linux-suite/) | the whole suite of commit `85c29e7` (a `git archive` of it): lock, ruff, format, mypy, unit, then each integration file in its own process; and the fail-before runs of 1.6.8's new tests on 1.6.7 and `9c14425` | 20:55:56Z to 21:20:02Z; 21:20:03Z to 21:24:30Z | unit 554, integration 222 in 23 files, all passed; the new tests fail on the earlier code with the messages in the logs |
| [`container/`](container/) | the Docker gate: both images built from the edition ZIPs (`IMAGES.md`: ids, layer digests, `docker save` SHA-256, base images by digest), smoke tests, fresh databases and migrations, replays of L12 and L10 from stored pages, `validate-export`, a replay killed with SIGKILL and resumed, rollback to the published 1.6.6 image and forward, data across a daemon restart, the coverage reports of the fifteen live runs | 21:24:30Z to 22:09:14Z | 89 steps; one not as expected by its exit code, `after` (exit 1: the gate's four databases were still present; they were dropped afterwards). Its walkthrough recording exited 0 but failed by its output (`command not found`) and is kept as `WALKTHROUGH_1.6.8_GATE_FAILED.cast` |
| [`qualification/`](qualification/) | both edition ZIPs, extracted and installed offline: lock, ruff, format, mypy, `--version`, `validate-config`, migrations on an empty database (refused before, current after, idempotent), unit and the whole integration suite, the operator drill (`test_operator_drill_owner.py`), the published 1.6.6 on the same database and 1.6.8 again | 22:09:14Z to 22:55:27Z | 44 rows, 0 not as expected (`QUAL_VERDICT_1.6.8.txt`): each edition 554 unit and 222 integration tests passed |
| [`probe-1.7.2/`](probe-1.7.2/) | `OXYLABS_CLASSIC_OFFLINE_PROBE_1.7.2.zip` extracted and run as its README says: the package as delivered, built again before publication with the workstation's user name replaced in one of its offline results ([`PACKAGE_REBUILD.txt`](../../offline-tests/1.7.2-classic-probe/PACKAGE_REBUILD.txt)); its first build's run, with the same results, in `earlier_build_79f32db3/` (2026-11-05, 22:55:27Z to 22:57:57Z) | 2026-11-06, 01:02:36Z to 01:05:06Z | 204 tests, 201 passed and 3 skipped (`junit_standalone_linux.xml`; the skips' reasons are in `01_pytest_standalone.txt`); every offline command as expected; live refused (exit 3) |
| [`walkthrough/`](walkthrough/) | the walkthrough recorded again in a session of its own (images built again from the ZIPs) | 22:58:05Z to 23:14:15Z (the recording 23:00:16Z to 23:14:13Z) | 10 steps, all as expected (`steps.jsonl`), the last finding the host as before the session; the recording has no error and says, in order, every narration line its script always says; the video ([`walkthrough/WALKTHROUGH_1.6.8.mp4`](../../../walkthrough/WALKTHROUGH_1.6.8.mp4)) is 163.2 s, 1096x736, 8 frames per second, with no sound |
| [`memory/`](memory/) | a replay of L10 from its stored pages by the Oxylabs edition ZIP, on the host rather than in Docker, timed, with the memory of its process tree sampled every 0.25 s (`measure_tree.py`); then the replay's check findings read from its database (`validation_findings_01M6PZXJ1X4QDHJDQNHJW3GPMT.txt`) | 23:14:49Z to 23:23:51Z (the replay 23:15:17Z to 23:23:49Z); the findings read at 23:30:55Z | 424 pages and 6,880 valid records, as the container's replay of L10; 511.5 s of wall time; one worker in one process; resident memory at most 1.38 GiB (the kernel's count; 1.31 GiB sampled), at least 1.75 GiB left available. Exit 6, as the container's replays of L10: besides G3, the yield check G4 fails (Household Essentials has no fresh product, Health & Wellness is 71% carried). A replay, not a live measurement |
| [`HOST_STATE.md`](HOST_STATE.md) | the host before and after this work, the databases dropped, what was kept | 23:31:51Z to 23:31:58Z | this work's 25 test databases dropped (4.4 GiB); the host as before the 1.6.7 gate but for those databases and the bridge `docker0` (gone between 10:49Z and 17:03Z, what removed it not established, not recreated); the VM left running |

The operator drill (both editions, `qualification/logs/<edition>.drill.jsonl`): `validate-config --check-db`,
`sync-config`, `run`, `status`, `export` and the storage location, a pause (exit 75) and `resume`, a publication refused
because the run's pages did not come from the network and the store is not a test target (`PUBLICATION_REFUSED` at
ERROR, exit 6), a manual `publish` of that run refused again (exit 6) with the last-good pointer unchanged, a run
stopped when its credits ran out (exit 4) that did not replace the published dataset, and store isolation (a second
store configured and enabled beside the first has no run and no folder; the stub saw only store id `3891`).

The paths in these logs name the VM's folders as `<vm-home>` and its user as `<vm-user>` (`manifests/REDACTIONS.csv`).
