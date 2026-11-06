# Walkthrough of release 1.6.8

[`WALKTHROUGH_1.6.8.mp4`](WALKTHROUGH_1.6.8.mp4) is a recorded terminal walkthrough of release 1.6.8 (commit
`85c29e7`). It lasts 163 s, has no audio, and is narrated in English by the lines that start with `#`. In the video
each pause is shortened to at most 2 s (`render_cast.py --idle 2.0`); the asciinema recording keeps the real times.
The source is the asciinema recording
[`WALKTHROUGH_1.6.8.cast`](../evidence/owner-azure-test/1.6.8/walkthrough/WALKTHROUGH_1.6.8.cast) (120 × 36). That
folder also holds the script it recorded (`walkthrough_168.sh`, with its helpers `walk_helpers.sh` and `walkview.py`),
the renderer (`render_cast.py`, with `render.json`), and the session's steps and logs: its images were built again
from the edition ZIPs (their ids differ from the gate's in
[`IMAGES.md`](../evidence/owner-azure-test/1.6.8/container/IMAGES.md), since each build writes its own time into
`/app/BUILD_INFO.json`), and its last step found the host as it was before it.

- **Where and when:** Hamza's Azure test VM, 2026-11-05, 23:00:16Z to 23:14:13Z. **Class: OWNER AZURE TEST.** This was
  not the client's environment.
- **Offline:** no provider, retailer or Classic request was made. The video holds **no live provider run** and no
  client observed it. L10 and L12 were collected on 2026-11-04 by earlier releases, and are only replayed.
- **What it shows, through the ordinary commands:**
  - both editions built in Docker from their ZIPs, and their versions and build information;
  - the store and Pickup configuration, with the schedule off and nothing on the VM that starts the collector;
  - without a provider key, the credentials check refuses (`validate-config --require-credentials`, exit 3); a
    `run` is refused the same way before any request (`test_operations.py`);
  - the schema checked and brought to its head;
  - **start:** L12 replayed from its stored pages;
  - **status** of that run, and **where its files are kept**;
  - **export**, and the 22 columns in the agreed order;
  - coverage under 1.6.8 of L10 as it was collected, with no CSV row complete;
  - **pause and resume:** a replay of L10 killed with SIGKILL after 62 pages (exit 137), then resumed by the ordinary
    command, which finished all 16 tasks: 426 pages, of which only robots.txt and the store page were read twice (a
    resumed execution checks the store first). The resume exits 6 (REJECTED) because the run's checks reject it.
    Besides G3 (categories incomplete), which a pilot is allowed to fail, and G14, which never blocks (a replay is
    not a fresh observation), the yield check G4 fails, as in the container's replays of L10 and the memory stage's
    (their logs' `CHECKS_COMPLETE`). In the memory stage's replay, Household Essentials has no fresh product (1,172
    carried) and Health & Wellness is 71% carried (293 carried, 121 fresh):
    [`validation_findings_01M6PZXJ1X4QDHJDQNHJW3GPMT.txt`](../evidence/owner-azure-test/1.6.8/memory/validation_findings_01M6PZXJ1X4QDHJDQNHJW3GPMT.txt).
    L12's replay fails only G3 and G14, so it exits 0. A replay is never published;
  - **rollback:** the published 1.6.6 on the same database, then 1.6.8 again;
  - the recording's own database copy and volume removed at the end.
- **Hashes:** MP4 `932aadadcb7af7acc159067ae5a3ca2a04af50c1e3cdb55407ce643e6b857354`, cast
  `2964c4bbccd5eee3178c5f457f77e335fbc5512f9d2cd8e5fd6d872997010cd8`.

# Walkthrough of release 1.5.2

[`WALKTHROUGH_1.5.2.mp4`](WALKTHROUGH_1.5.2.mp4) is a recorded terminal walkthrough of release 1.5.2 (commit
`627c804`). It lasts 170.1 s, has no audio, and is narrated by the lines that start with `#`. The source is the
asciinema recording
[`WALKTHROUGH_1.5.2.cast`](../evidence/owner-azure-test/1.5.2/walkthrough/WALKTHROUGH_1.5.2.cast) (120 × 36). That
folder also holds the script it recorded (`walkthrough.sh`), the renderer (`render_cast.py`) and the exit codes of the
recording and the render.

- **Where and when:** Hamza's Azure test VM, 2026-11-01T21:19:22Z to 21:22:52Z. **Class: OWNER AZURE TEST.** This was
  not the client's environment.
- **Offline:** no provider, retailer or Classic request was made. The video holds **no live provider run** and no
  client observed it.
- **What it shows:**
  - both editions built in Docker;
  - the store and Pickup configuration, with the schedule off;
  - a run refused without a key;
  - the container network reaching only the test database;
  - the nine runs of 2026-10-31 replayed from their stored pages, with a row traced to its page;
  - a corrected carried row and a recovered size;
  - an S6 replay killed with SIGKILL and resumed, on a fresh copy of the campaign database;
  - the publication-fault test, which is SYNTHETIC;
  - the Classic probe refusing its live command.
- **Hashes:** MP4 `92d6b2fd639170b72f297c51ac841e15f9daaf34138618b5b0d9e01d32d7b0d7`, cast
  `07bfb30c57c00b7f798428e4b7e6df9eab2643cf205c0e27b48687e0047d2fab`.

The narration names the delivery's own paths. `azure_docker_recovery/` is now
[`evidence/owner-azure-test/1.5.2/azure_docker_recovery/`](../evidence/owner-azure-test/1.5.2/azure_docker_recovery/),
and `7_release_1_5_2/owner_vm/` is [`evidence/owner-azure-test/1.5.2/owner_vm/`](../evidence/owner-azure-test/1.5.2/owner_vm/).
The Classic probe ZIP shown on screen was rebuilt on 2026-11-02 to replace the workstation's name in one recorded file.
Of its 132 files, 131 are unchanged: see
[`PROBE_ZIP_TESTED_VS_DELIVERED.json`](../evidence/owner-azure-test/1.5.2/owner_vm/PROBE_ZIP_TESTED_VS_DELIVERED.json).
