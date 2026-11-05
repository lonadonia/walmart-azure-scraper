"""Install the frozen 1.6.6 Oxylabs edition for the live canary L12, from the delivered edition ZIP (no provider
request; the install fetches the locked packages only).

usage: python -I install_edition_166.py
- checks the ZIP's SHA-256 against the build's value, extracts it into C:/w9/live/ed (a new folder only), checks the
  edition's files against its EDITION.json (count and tree digest) and its BUILD_INFO.json commit, then runs
  `uv sync --frozen` in it.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import zipfile
from pathlib import Path

ZIP = Path(r"C:\w9\delivery166\source\editions\WALMART_OXYLABS_SOURCE_1.6.6.zip")
ZIP_SHA = "0859a2f693527bab073252edf941928bb4f118ea4a63d581078d96ddd2324e22"
COMMIT = "cbea802"  # the build revision: collector 1.6.6 (39cc61f) plus the builder commit
TOP = "walmart-oxylabs-1.6.6"
ED = Path(r"C:\w9\live\ed")
UV = str(Path.home() / ".local" / "bin" / "uv.exe")


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def main() -> int:
    data = ZIP.read_bytes()
    if sha(data) != ZIP_SHA:
        raise SystemExit("the edition ZIP is not the one built")
    dest = ED / TOP
    if dest.exists():
        raise SystemExit(f"{dest} exists")
    with zipfile.ZipFile(ZIP) as z:
        bad = [n for n in z.namelist() if not n.startswith(TOP + "/") or ".." in n.split("/") or n.startswith("/")]
        if bad:
            raise SystemExit(f"unsafe or foreign names: {bad[:3]}")
        z.extractall(ED)
    files = {p.relative_to(dest).as_posix(): sha(p.read_bytes()) for p in sorted(dest.rglob("*")) if p.is_file()}
    rec = json.loads((dest / "EDITION.json").read_text("utf-8"))
    body = {p: h for p, h in files.items() if p != "EDITION.json"}
    digest = sha("".join(f"{body[p]}  {p}\n" for p in sorted(body)).encode("utf-8"))
    info = json.loads((dest / "BUILD_INFO.json").read_text("utf-8"))
    problems = []
    if digest != rec.get("tree_sha256"):
        problems.append("tree digest differs from EDITION.json")
    if body != rec.get("file_sha256"):
        problems.append("files differ from EDITION.json")
    if not str(info.get("commit", "")).startswith(COMMIT):
        problems.append(f"BUILD_INFO commit {info.get('commit')}")
    if problems:
        raise SystemExit("; ".join(problems))
    env = {k: v for k, v in os.environ.items() if not k.upper().startswith(("OXYLABS", "SCRAPEDO", "VIRTUAL_ENV"))}
    env["UV_PYTHON"] = r"C:\w6\py312\pkg\tools\python.exe"
    rc = subprocess.run([UV, "sync", "--frozen"], cwd=dest, env=env).returncode
    print(json.dumps({"installed": str(dest), "files": len(files), "tree_sha256": digest, "commit": info.get("commit"),
                      "uv_sync_exit": rc}))
    return rc


if __name__ == "__main__":
    sys.exit(main())
