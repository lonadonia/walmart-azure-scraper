OFFLINE TESTS of the shared Classic probe 1.7.2 (the client's review of 1.7.1: C4, incomplete bodies; C2, the
whole-session deadline and stale evidence; the drip test that failed on Linux), 2026-11-05 (UTC). Live mode stays
disabled. No request was sent to Oxylabs or to a retailer: every connection is a request worker's (a child
process) to a scripted stub on 127.0.0.1. The delivered archive's own results are in
classic-probe-1.7.2/offline_results/.

Probe 1.7.1 is commit 68ff3d8 (tree 7adfea8f); probe 1.7.2 is commit 7768514 (tree 3ada8871) of the development
monorepo. Collector releases 1.6.6 to 1.6.8 do not change the probe.

WINDOWS (the preparation workstation, Windows 11, Python 3.12.10)

  REPRODUCTION_ON_1.7.1_WINDOWS.log    The review tests against the frozen 1.7.1 code: git archive 68ff3d8 with
                                       the test files of 7768514 copied in (loopback_stub, processes,
                                       session_drill, test_isolated_transport, test_review_of_171). 13 failed, 11
                                       passed, 1 skipped (the FIFO test: Windows has no FIFO at a file's path).
                                       Among the failures: a server that declares Content-Length 100, sends the
                                       two bytes {} and closes gave an answer (DID NOT RAISE TransportFailed),
                                       with status 200 and with status 500.
  FULL_1.7.2_WINDOWS.log               The whole suite on 1.7.2 (git archive 7768514): 199 passed, 5 skipped;
                                       ruff, format, mypy and mypy --platform linux clean.

LINUX (the owner's Azure test VM, Ubuntu 24.04.5, kernel 7.0.0-1017-azure, Python 3.12.3), in linux-owner-vm/

  PUBLISHED_1.7.1_LINUX.log            The published probe 1.7.1, as extracted, on Linux: 1 failed, 169 passed,
                                       3 skipped. The failure is the one the client saw:
                                       test_a_body_dripped_past_the_deadline_is_cut_off expected a forced kill
                                       (workers_killed == 1) when the worker had ended by itself (0).
  REPRODUCTION_ON_1.7.1_LINUX.log      The same reproduction tree as on Windows: 14 failed, 11 passed. The 14 are
                                       Windows' 13 and the FIFO test: a FIFO at the evidence path held 1.7.1's
                                       supervisor past its hard end.
  REPRODUCTION_ON_1.7.2_LINUX.log      The same tests on 1.7.2: 25 passed.
  FULL_1.7.2_LINUX.log                 The whole suite on 1.7.2: 201 passed, 3 skipped.
  STATIC_1.7.2_LINUX.log               ruff, format and mypy on 1.7.2: clean.

  The delivered archive on Linux: OXYLABS_CLASSIC_OFFLINE_PROBE_1.7.2.zip (SHA-256 fe255791...) extracted on the
  owner's VM and run as its own README says, 2026-11-06 from 01:02:36Z to 01:05:06Z
  (../../owner-azure-test/1.6.8/probe-1.7.2/): its 67 file hashes checked; the whole suite, 204 tests, 201 passed
  and 3 skipped (the three Linux skips below; JUnit file junit_standalone_linux.xml); ruff, format and mypy clean;
  every command of its offline guide exited as expected, live mode refused with exit 3 (commands.csv); the review
  tests, 23 passed. Its pytest log is quiet (the probe's own settings): the counts are the JUnit file's.
  The archive was built again before publication, with the workstation's user name replaced in one of its
  offline results (PACKAGE_REBUILD.txt); its first build (79f32db3...), which differs from it only there and in
  offline_results/README.txt, gave the same results on 2026-11-05 from 22:55:27Z to 22:57:57Z
  (../../owner-azure-test/1.6.8/probe-1.7.2/earlier_build_79f32db3/).

THE SKIPS, AND WHY THEY DIFFER BY SYSTEM

  Both systems  test_vendored.py, twice: the Walmart and Mariano's collectors' sources are not beside a
                probe-only extraction, so the vendored copies cannot be compared with them there; each copy
                is still checked against its recorded Git object.
  Windows only  the FIFO tests (test_review_of_171.py, test_supervisor_evidence.py): Windows has no FIFO at a
                file's path, so nothing there can hold an open. The same bound is tested on Windows by the stale,
                left-behind and wall-clock tests. A symbolic-link test: making a link needs a privilege a normal
                Windows account lacks; Windows links are refused by the same lstat test.
  Linux only    the write-through rename (test_c2_c4_reproduction.py) is the Windows form of a synced rename.

THE CORRECTIONS IN 1.7.2 (CLASSIC_PROBE_1.7.1_TO_1.7.2.diff, DIFFSTAT.txt: 19 files, +1,917/-188)

  C4  A body shorter than its declared Content-Length, zero bytes included, or a chunked body cut short, is kept
      as partial with its declared and received lengths and SHA-256. It is never parsed, and its money stays
      held. The transport and the recovery check the declared length again. A worker killed after it renamed
      its file no longer loses a whole answer or a kept partial. Each worker status names its dispatch, and a
      recovery refuses a status of another dispatch or one without that identity. No recovery sends a request.
  C2  Evidence is read only from a regular file, bounded in size and time; a FIFO, a link or a folder is refused
      at once. A session's evidence must name its execution id, so a previous campaign's complete file is not
      taken. The session's process tree is ended whole when it ends. The recovery's bound is monotonic. The
      supervisor returns within its hard end plus 0.5 s.
  The drip test asserts the deadline, the outcome, the partial and the worker's end, whichever ended it; a
  separate test forces a hung worker and checks a real kill and reap.
  The protections of C1 (redirects and credentials), C3 (checks under the lock and before dispatch), C5 (a real,
  bounded backoff) and the shared accounting are kept: no test of theirs was removed or changed, and they pass
  on 1.7.2. The only lines the diff removes from tests are the drip test's single forced-kill assertion
  (replaced as above), a stub of Popen.communicate that 1.7.2's transport no longer calls, and a test helper's
  signature (test_durable_evidence.py), whose callers changed with it.
