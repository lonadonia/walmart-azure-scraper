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
