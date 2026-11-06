OWNER AZURE TEST: the delivered Classic probe package OXYLABS_CLASSIC_OFFLINE_PROBE_1.7.2.zip on the owner's
Azure test VM (Linux), extracted and run as its README_FIRST.md says, with no request (vm_probe_172e.sh).

This folder: the package as delivered, SHA-256 fe25579154b9cac70628fa8b7e3a61a85858b01f6900ff0aded04b3d6da76e1e,
run 2026-11-06T01:02:36Z to 2026-11-06T01:05:06Z: its 67 file hashes checked; the whole suite, 204 tests,
201 passed and 3 skipped (junit_standalone_linux.xml; the skips' reasons in 01_pytest_standalone.txt);
every offline command as expected, live mode refused with exit 3 (commands.csv); the review tests, 23 passed.

earlier_build_79f32db3/: the same run, 2026-11-05T22:55:27Z to 2026-11-05T22:57:57Z, of the package's first build
(SHA-256 79f32db3457ff0694a28f7a1787527b369edbdbc015fa626ff0da16a694aeb8a), with the same results. That build was
never delivered: before publication, the names scan found the workstation's user name in one of its offline
results (16b_review_tests_on_1.7.1_source.txt, a JSON-escaped path the packing had not replaced). The
package was built again by the same builder from the same revision, results and documentation, with that
name replaced: the two builds differ only in that log and in offline_results/README.txt, which says so; the
probe's tree is the same (FILE_SHA256.txt and PACKAGE_MANIFEST.json byte for byte). See
../../../offline-tests/1.7.2-classic-probe/PACKAGE_REBUILD.txt.
