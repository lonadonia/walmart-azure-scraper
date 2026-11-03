"""Assemble the evidence tree of Walmart release 1.5.2 (offline) into a NEW folder.

The evidence of 1.5.1 is carried byte for byte, from the delivered ZIP itself: every file keeps its path and hash, and its
row of EVIDENCE_MANIFEST.csv stays as it was. This release adds one folder, 7_release_1_5_2/, through the same rules
as 1.5.1 (assemble_evidence_151.py's Tree: stored pages through the sanitizer, text through the abbreviation rules, each
file listed with its source and both hashes). README.md, SANITIZATION.md, EVIDENCE_MANIFEST.csv, SANITIZATION_LOG.csv and
ASSEMBLY_CHECK.txt are the only files of the tree that are new versions.

usage: <worktree venv python> -I -X utf8 assemble_evidence_152.py OUT_DIR
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import sys
import zipfile
from collections import Counter
from pathlib import Path

sys.path.insert(0, r"C:\w7\tools\delivery151")
import assemble_evidence_151 as a  # noqa: E402

W7 = Path(r"C:\w7")
EV = W7 / "ev152"
TOOLS = W7 / "tools"
DOCS = W7 / "stage152" / "evidence_docs"
OLD_ZIP = a.REPO / "deliverables" / "20261101_walmart_1.5.1" / "WALMART_EVIDENCE_1.5.1.zip"
OLD_TOP = "walmart-evidence-1.5.1/"
NEW_VERSIONS = {"README.md", "SANITIZATION.md", "EVIDENCE_MANIFEST.csv", "SANITIZATION_LOG.csv", "ASSEMBLY_CHECK.txt"}
BASE = "7_release_1_5_2"
FIELDS = ["path", "class", "source", "source_sha256", "package_sha256", "change"]
LOG_FIELDS = ["path", "source", "source_sha256", "package_sha256", "change", "content_sha256_source", "content_sha256_package"]


def rows(data: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(data.decode("utf-8"))))


def carry(out: Path) -> tuple[list[dict[str, str]], list[dict[str, str]], int]:
    """The 1.5.1 tree, byte for byte, with its manifest and log rows."""
    with zipfile.ZipFile(OLD_ZIP) as z:
        names = [n for n in z.namelist() if not n.endswith("/")]
        assert all(n.startswith(OLD_TOP) for n in names)
        n = 0
        for name in names:
            rel = name[len(OLD_TOP) :]
            if rel in NEW_VERSIONS:
                continue
            path = out / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(z.read(name))
            n += 1
        manifest = [r for r in rows(z.read(OLD_TOP + "EVIDENCE_MANIFEST.csv")) if r["path"] not in NEW_VERSIONS]
        log = [r for r in rows(z.read(OLD_TOP + "SANITIZATION_LOG.csv")) if r["path"] not in NEW_VERSIONS]
    return manifest, log, n


def plan(t: a.Tree) -> None:
    replay, repro, off = "OFFLINE REPLAY", "OFFLINE REPROCESSING", "OFFLINE VERIFIED"
    t.tree(EV / "final_a1", f"{BASE}/replay_campaign", replay)
    t.tree(EV / "final_a2", f"{BASE}/repeat_replay/a2", replay)
    t.add(EV / "repeat" / "A1_A2_COMPARISON.json", f"{BASE}/repeat_replay/A1_A2_COMPARISON.json", replay)
    t.tree(EV / "final_b3", f"{BASE}/replay_b3", repro)
    t.tree(EV / "correction_maps_final", f"{BASE}/correction_maps", replay)
    t.tree(EV / "agreement_final", f"{BASE}/agreement", replay)
    for name in ("replay_resume_before_fix.txt", "carried_replay_before_fix.txt"):
        t.add(EV / "logs" / name, f"{BASE}/defects_before_the_fix/{name}", off)
    t.tree(EV / "private_label", f"{BASE}/private_label", repro)
    t.tree(EV / "classic_docs_recheck", f"{BASE}/classic_documentation_recheck/pages", "HISTORICAL")
    t.add(EV / "classic_docs_recheck.json", f"{BASE}/classic_documentation_recheck/classic_docs_recheck.json", "HISTORICAL")
    t.tree(EV / "load_pc", f"{BASE}/load/workstation", "SYNTHETIC TEST")
    t.tree(EV / "reconciliation", f"{BASE}/sponsored_and_variant_reconciliation", "RECONCILIATION")
    t.tree(EV / "accounts", f"{BASE}/accounts", "ACCOUNT READING")
    t.tree(EV / "vm", f"{BASE}/owner_vm", "OWNER AZURE TEST")
    t.tree(EV / "walkthrough", f"{BASE}/walkthrough", "OWNER AZURE TEST")
    for name in (
        "agreement_152.py", "agreement_all_152.sh", "agreement_final_152.sh", "compare_a1_a2_152.py", "correction_map_152.py",
        "correction_map_b3_152.py", "correction_maps_final_152.py", "dup_pages_152.py", "final_chain_152.sh", "fresh_copy_152.py",
        "key_status_152.py", "reproc152_run.py", "s6_checks_152.py", "sv_reconcile_152.py", "classic_docs_recheck_152.py",
        "brand_evidence_152.py", "dump_copy_152.py",
    ):  # fmt: skip
        t.add(TOOLS / name, f"{BASE}/tools/{name}", "TOOL")
    t.tree(TOOLS / "vm152", f"{BASE}/tools/vm152", "TOOL", skip=("__pycache__",))
    t.tree(TOOLS / "delivery152", f"{BASE}/tools/delivery152", "TOOL", skip=("__pycache__",))
    t.tree(TOOLS / "docs152", f"{BASE}/tools/docs152", "TOOL", skip=("__pycache__",))
    for name in ("README.md", "SANITIZATION.md"):
        t.add(DOCS / name, name, "DOCUMENT")


def main() -> int:
    out = Path(sys.argv[1])
    if out.exists():
        raise SystemExit(f"{out} exists")
    out.mkdir(parents=True)
    manifest, log, carried = carry(out)
    t = a.Tree(out)
    plan(t)
    for row in t.manifest:
        row["source"] = a.abbreviate(row["source"].encode("utf-8"))[0].decode("utf-8")
    for row in t.log:
        row["source"] = a.abbreviate(row["source"].encode("utf-8"))[0].decode("utf-8")
    all_rows = [*manifest, *t.manifest]
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=FIELDS, lineterminator="\n")
    w.writeheader()
    w.writerows(all_rows)
    (out / "EVIDENCE_MANIFEST.csv").write_bytes(buf.getvalue().encode("utf-8"))
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=LOG_FIELDS, lineterminator="\n", restval="")
    w.writeheader()
    w.writerows([*log, *t.log])
    (out / "SANITIZATION_LOG.csv").write_bytes(buf.getvalue().encode("utf-8"))
    problems = []
    listed = {r["path"] for r in all_rows}
    present = {p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()} - {
        "EVIDENCE_MANIFEST.csv", "SANITIZATION_LOG.csv", "ASSEMBLY_CHECK.txt",
    }  # fmt: skip
    if listed != present:
        problems.append(f"manifest and tree differ: {sorted(listed ^ present)[:5]}")
    if len(listed) != len(all_rows):
        problems.append("a path is listed twice")
    for r in all_rows:
        if a.sha((out / r["path"]).read_bytes()) != r["package_sha256"]:
            problems.append(f"hash differs: {r['path']}")
    raw_named = [p for p in present if "/live/raw/" in p or p.endswith(".body.gz")]
    if raw_named:
        problems.append(f"raw originals in the package: {raw_named[:3]}")
    old_sha = hashlib.sha256(OLD_ZIP.read_bytes()).hexdigest()
    counts = Counter(r["class"] for r in all_rows)
    lines = [
        "ASSEMBLY CHECK of the Walmart 1.5.2 evidence tree (offline; no request)",
        f"carried byte for byte from WALMART_EVIDENCE_1.5.1.zip (SHA-256 {old_sha}): {carried} files",
        f"added in {BASE}/ and as new versions of the two documents: {len(t.manifest)} files",
        f"files listed: {len(listed)}",
        f"by class: {json.dumps(dict(sorted(counts.items())))}",
        f"files changed when packaged in this release: {len(t.log)}",
        f"raw originals in the package: {len(raw_named)}",
        f"RESULT: {'PASS' if not problems else 'FAIL ' + '; '.join(problems)}",
    ]
    (out / "ASSEMBLY_CHECK.txt").write_bytes(("\n".join(lines) + "\n").encode("utf-8"))
    print("\n".join(lines))
    for r in t.log[:40]:
        print(r["path"][:90], r["change"][:100])
    return 0 if not problems else 1


if __name__ == "__main__":
    raise SystemExit(main())
