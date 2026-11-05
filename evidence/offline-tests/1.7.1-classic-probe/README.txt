OFFLINE TESTS of the shared Classic probe 1.7.1 (findings C2 and C4 completed), in the development tree, on the
preparation workstation, 2026-11-04 (UTC). No request was sent to Oxylabs or to a retailer: every connection is a
request worker's (a child process) to a scripted stub on 127.0.0.1. The clean-export results of the delivered
revision are in classic-probe-1.7.1/offline_results/ (they repeat these runs from the commit itself).

  REPRODUCTION_ON_1.7.0_FIRST_RUN.log  21:37:46Z. The first run of the reproduction tests, against release 1.7.0's
                                       code (its src/ tree da055ccd..., unchanged): 7 failed. The test file was
                                       edited afterwards (in the failure reports, the lines moved by 2 to 6 and one
                                       assertion was rewrapped); the run of the committed versions follows.
  REPRODUCTION_ON_1.7.0.log            22:22:46Z. The final reproduction tests (tests/test_c2_c4_reproduction.py,
                                       SHA-256 8ec6cca9..., and tests/session_drill.py, SHA-256 47d4504b..., both
                                       as committed in 68ff3d8) against release 1.7.0's code (src/ tree da055ccd...
                                       from commit 6b9be92): 7 failed. Each failure shows the gap: a recovery that
                                       waited 30 s for the lock after the session's end and raised; writes after an
                                       answer that waited 30 s for the lock; a kill that could not be reaped and
                                       raised; an answer lost by a crash before its kept copy; a manifest renamed
                                       without a sync; no write-through rename on Windows; a body cut at its
                                       deadline with no record.
  REPRODUCTION_ON_1.7.1.log            22:22:12Z. The same 7 tests on 1.7.1: 7 passed.
  DEV_TREE_TESTS_1.7.1.log             about 22:20Z to 22:21:37Z. The whole suite on 1.7.1: 171 passed, 2 skipped. The
                                       two skips are the vendored-file checks: the collectors beside the probe
                                       there were other releases (Walmart 1.6.5, Mariano's 1.2.1) than those the
                                       copies were taken from (1.5.2 and 1.8.0rc3); each copy is still checked
                                       against its recorded Git object.
  CLASSIC_PROBE_1.7.0_TO_1.7.1.diff    git diff 6b9be92 68ff3d8 -- headless/oxylabs-classic-probe (1.7.0, tree
                                       8305ffe2..., to 1.7.1, tree 7adfea8f...).
  DIFFSTAT.txt                         its per-file summary: 16 files, 1,492 lines added and 167 removed.

The development tree's src/ files (24) were hashed at 22:22Z, before and after the 1.7.0 run, and equal the files
committed in 68ff3d8; no source file of the probe changed after 22:19:16Z.
