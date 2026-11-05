"""Check that source/, classic-probe/, classic-probe-1.7.0/ and classic-probe-1.7.1/ are the frozen trees they say they
are, file for file (offline, standard library).

Run from the root of a clone, before any environment is created inside it:  python3 manifests/check_frozen_trees.py

source/               collector release 1.6.6: each edition against its own EDITION.json (every file's SHA-256 and
                      the tree's) and against source/BUILD_MANIFEST.json (file count and tree SHA-256 of its commit);
classic-probe/        the Walmart probe 1.5.2 the client reviewed (frozen with collector 627c804), unchanged;
classic-probe-1.7.0/  the shared probe 1.7.0 of the 1.6.5 delivery (C1, C3 and C5 corrected, C2 and C4 in part;
                      frozen with collector 1.6.1, 1780349), unchanged and superseded;
classic-probe-1.7.1/  the shared probe 1.7.1 (C2 and C4 completed; frozen with collector 1.6.6's build, cbea802);
                      each probe tree against its FILE_SHA256.txt and PACKAGE_MANIFEST.json (count and file-list SHA-256);
all four              every file against manifests/FILE_MAP.csv: published unchanged, with the SHA-256 it had in the
                      delivered archive.
Prints each finding and ends with PASS or FAIL (exit status 0 or 1).
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE_RELEASE, SOURCE_COMMIT = "1.6.6", "cbea802891d4e66b74a0abc33e0af0af74c89708"
PROBES = {
    "classic-probe": ("1.5.2", "627c804d66aa33fc423fd2296c8896c5d5c2c3d4"),
    "classic-probe-1.7.0": ("1.7.0", "1780349e522d771a3642fe88bfb7b542044ec844"),
    "classic-probe-1.7.1": ("1.7.1", "cbea802891d4e66b74a0abc33e0af0af74c89708"),
}
problems: list[str] = []


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def files_under(folder: Path) -> dict[str, str]:
    return {p.relative_to(folder).as_posix(): sha(p.read_bytes()) for p in sorted(folder.rglob("*")) if p.is_file()}


def tree_digest(tree: dict[str, str]) -> str:
    # the collector's own definition (src/walmart_headless/editions.py: tree_digest)
    return sha("".join(f"{tree[p]}  {p}\n" for p in sorted(tree)).encode("utf-8"))


def check(ok: bool, what: str) -> None:
    print(("ok    " if ok else "FAIL  ") + what)
    if not ok:
        problems.append(what)


build = json.loads((ROOT / "source/BUILD_MANIFEST.json").read_text("utf-8"))
check(build.get("commit") == SOURCE_COMMIT and build.get("release") == SOURCE_RELEASE,
      f"source/BUILD_MANIFEST.json: release {build.get('release')}, commit {build.get('commit')}")
for name, ed in build["editions"].items():
    top = ROOT / "source" / ed["top_folder"]
    tree = files_under(top)
    record = json.loads((top / "EDITION.json").read_text("utf-8"))
    body = {p: h for p, h in tree.items() if p != "EDITION.json"}
    check(len(tree) == ed["files"], f"{ed['top_folder']}: {len(tree)} files (manifest: {ed['files']})")
    check(tree_digest(body) == ed["tree_sha256"] == record.get("tree_sha256"),
          f"{ed['top_folder']}: tree SHA-256 {tree_digest(body)} (manifest and EDITION.json: {ed['tree_sha256']})")
    recorded = record.get("file_sha256", {})
    differ = sorted(p for p in set(body) | set(recorded) if body.get(p) != recorded.get(p))
    check(not differ, f"{ed['top_folder']}: every file's SHA-256 as EDITION.json records it"
          + (f" (differs: {', '.join(differ[:5])})" if differ else ""))
ox, sd = (ROOT / "source" / e["top_folder"] for e in build["editions"].values())
a, b = files_under(ox), files_under(sd)
between = sorted(p for p in set(a) | set(b) if a.get(p) != b.get(p))
check(between == sorted(build["files_that_differ_between_the_editions"]),
      f"the editions differ in exactly: {', '.join(between)}")

for folder, (version, revision) in PROBES.items():
    probe = ROOT / folder
    pkg = json.loads((probe / "PACKAGE_MANIFEST.json").read_text("utf-8"))
    listing = (probe / "FILE_SHA256.txt").read_bytes()
    check(pkg.get("frozen_revision") == revision and pkg.get("probe_version") == version
          and pkg.get("live_enabled") is False and pkg.get("requests_sent") == 0,
          f"{folder}/PACKAGE_MANIFEST.json: probe {pkg.get('probe_version')}, revision {pkg.get('frozen_revision')}, "
          f"live_enabled {pkg.get('live_enabled')}, requests_sent {pkg.get('requests_sent')}")
    check(sha(listing) == pkg["file_list_sha256"], f"{folder}/FILE_SHA256.txt has the SHA-256 PACKAGE_MANIFEST.json records")
    listed = dict(reversed(line.split("  ", 1)) for line in listing.decode("utf-8").splitlines())
    tree = files_under(probe / "oxylabs-classic-probe")
    actual = {"oxylabs-classic-probe/" + p: h for p, h in tree.items()}
    check(actual == listed and len(actual) == pkg["files_of_the_probe_tree"],
          f"{folder}/oxylabs-classic-probe: {len(actual)} files, each as FILE_SHA256.txt lists it "
          f"(manifest: {pkg['files_of_the_probe_tree']})")

with (ROOT / "manifests/FILE_MAP.csv").open(encoding="utf-8", newline="") as f:
    fmap = {r["path"]: r for r in csv.DictReader(f)}
for folder in ("source", *PROBES):
    here = {f"{folder}/{p}": h for p, h in files_under(ROOT / folder).items()}
    mapped = {p: r for p, r in fmap.items() if p.startswith(folder + "/")}
    bad = sorted(p for p in set(here) | set(mapped)
                 if p not in here or p not in mapped or mapped[p]["state"] != "unchanged"
                 or not (here[p] == mapped[p]["original_sha256"] == mapped[p]["sha256"]))
    check(not bad, f"{folder}/: {len(here)} files, each unchanged from the delivered archive (manifests/FILE_MAP.csv)"
          + (f" (differs: {', '.join(bad[:5])})" if bad else ""))

print("FAIL" if problems else "PASS")
sys.exit(1 if problems else 0)
