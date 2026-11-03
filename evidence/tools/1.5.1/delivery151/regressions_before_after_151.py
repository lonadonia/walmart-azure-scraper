"""The 1.5.1 regressions run against the frozen 1.5.0 source and against 1.5.1 (offline; no provider request, no network).

For each revision: the collector folder is exported with `git archive` into a new folder, the four changed test files of 1.5.1 are laid over
the 1.5.0 export (nothing else of 1.5.0 is changed), `uv sync --frozen --offline` installs it from the lock, and pytest runs those four files
with the local PostgreSQL of pgserver. A per-test table says which tests are new in 1.5.1 and how each ended on 1.5.0 and on 1.5.1.

usage: python -I -X utf8 regressions_before_after_151.py WORK OUT
  WORK  a new, short folder for the two exports (MAX_PATH)
  OUT   a new folder for the results
"""

from __future__ import annotations

import csv
import io
import json
import os
import re
import subprocess
import sys
import tarfile
import time
import xml.etree.ElementTree as ET
from pathlib import Path

REPO = Path(r"C:\w7\wt")
SUB = "headless/walmart-azure-headless"
BEFORE, AFTER = "7b6f3258e0f4ab755732605eb88717c592d07073", "488a033fc22d09db9f6270feae274d8c77963d6f"
FILES = ["tests/unit/test_pack_size.py", "tests/unit/test_private_label.py", "tests/unit/test_walmart.py", "tests/integration/test_detail_path.py"]
UV = r"<home>\.local\bin\uv.exe"
UV_PYTHON = r"C:\w6\py312\pkg\tools\python.exe"
DEF = re.compile(r"^\s*(?:async\s+)?def\s+(test_\w+)", re.M)


def git(*args: str) -> bytes:
    return subprocess.run(["git", "-C", str(REPO), *args], check=True, capture_output=True).stdout


def export(rev: str, dest: Path) -> Path:
    with tarfile.open(fileobj=io.BytesIO(git("archive", "--format=tar", rev, SUB))) as tf:
        tf.extractall(dest, filter="data")
    return dest / SUB


def utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def main() -> int:
    work, out = Path(sys.argv[1]), Path(sys.argv[2])
    for p in (work, out):
        if p.exists():
            raise SystemExit(f"{p} exists")
        p.mkdir(parents=True)
    commands: list[dict[str, str]] = []
    results: dict[str, dict[str, str]] = {}
    for label, rev in (("before_1_5_0", BEFORE), ("after_1_5_1", AFTER)):
        tree = export(rev, work / label)
        laid = []
        if rev == BEFORE:
            for f in FILES:
                (tree / f).write_bytes(git("show", f"{AFTER}:{SUB}/{f}"))
                laid.append(f)
        env = {k: v for k, v in os.environ.items() if not k.upper().startswith(("OXYLABS", "SCRAPEDO", "SCRAPE_DO", "WALMART_"))}
        env.update({"UV_PYTHON": UV_PYTHON, "PSYCOPG_IMPL": "python", "HTTP_PROXY": "http://127.0.0.1:9", "HTTPS_PROXY": "http://127.0.0.1:9",
                    "NO_PROXY": "127.0.0.1,localhost", "PYTHONDONTWRITEBYTECODE": "1"})
        dest = out / label
        dest.mkdir()
        steps = [
            ("uv_sync", [UV, "sync", "--frozen", "--offline"]),
            ("version", [str(tree / ".venv" / "Scripts" / "python.exe"), "-c", "import walmart_headless as w; print(w.__version__, w.__file__)"]),
            ("pytest", [str(tree / ".venv" / "Scripts" / "python.exe"), "-m", "pytest", *FILES, "-p", "no:cacheprovider", "-q", "-rfE",
                        f"--junitxml={dest / 'junit.xml'}"]),
        ]
        for name, cmd in steps:
            if name == "pytest":
                pg = tree / ".venv" / "Lib" / "site-packages" / "pgserver" / "pginstall" / "bin"
                env["PATH"] = f"{pg};{env.get('PATH', '')}"
            started = utc()
            t0 = time.monotonic()
            r = subprocess.run(cmd, cwd=tree, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
            text = (r.stdout + ("\n--- stderr ---\n" + r.stderr if r.stderr.strip() else "")).replace(str(work), "<work>")
            (dest / f"{name}.txt").write_bytes(text.encode("utf-8"))
            commands.append({"revision": label, "commit": rev, "step": name, "command": " ".join(Path(c).name if i == 0 else c for i, c in enumerate(cmd)).replace(str(dest), f"<out>/{label}"),
                             "exit_code": str(r.returncode), "started_utc": started, "seconds": f"{time.monotonic() - t0:.1f}",
                             "test_files_of_1_5_1_laid_over": ", ".join(laid)})
            if name == "uv_sync" and r.returncode != 0:
                raise SystemExit(f"uv sync failed for {label}")
        junit = dest / "junit.xml"
        raw = junit.read_bytes()
        junit.write_bytes(re.sub(rb'hostname="[^"]*"', b'hostname="(workstation)"', raw))
        for case in ET.parse(junit).getroot().iter("testcase"):
            key = f"{case.get('classname')}::{case.get('name')}"
            outcome = "passed"
            for child in case:
                if child.tag in ("failure", "error"):
                    outcome = "failed" if child.tag == "failure" else "error"
                elif child.tag == "skipped":
                    outcome = "skipped"
            results.setdefault(key, {})[label] = outcome
    old_names: set[str] = set()
    for f in FILES:
        old_names |= set(DEF.findall(git("show", f"{BEFORE}:{SUB}/{f}").decode("utf-8")))
    rows = []
    for key in sorted(results):
        base = key.split("::", 1)[1].split("[", 1)[0]
        rows.append({"test": key, "new_in_1_5_1": "yes" if base not in old_names else "no",
                     "result_on_1_5_0": results[key].get("before_1_5_0", "not run"), "result_on_1_5_1": results[key].get("after_1_5_1", "not run")})
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(rows[0]), lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    (out / "REGRESSIONS_BEFORE_AND_AFTER.csv").write_bytes(buf.getvalue().encode("utf-8"))
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(commands[0]), lineterminator="\n")
    w.writeheader()
    w.writerows(commands)
    (out / "commands.csv").write_bytes(buf.getvalue().encode("utf-8"))
    new = [r for r in rows if r["new_in_1_5_1"] == "yes"]
    summary = {
        "class": "OFFLINE (unit and PostgreSQL integration tests; no provider request, proxies pointed at a closed port)",
        "before": BEFORE, "after": AFTER, "test_files": FILES,
        "tests": len(rows), "new_in_1_5_1": len(new),
        "new_failing_on_1_5_0": sum(r["result_on_1_5_0"] in ("failed", "error") for r in new),
        "new_passing_on_1_5_0": [r["test"] for r in new if r["result_on_1_5_0"] == "passed"],
        "existing_changed_outcome": [r["test"] for r in rows if r["new_in_1_5_1"] == "no" and r["result_on_1_5_0"] != r["result_on_1_5_1"]],
        "all_passing_on_1_5_1": all(r["result_on_1_5_1"] == "passed" for r in rows),
        "not_passing_on_1_5_1": [r["test"] for r in rows if r["result_on_1_5_1"] != "passed"],
    }
    (out / "SUMMARY.json").write_bytes((json.dumps(summary, indent=1) + "\n").encode("utf-8"))
    print(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
