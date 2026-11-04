"""Verification of WALMART_SOURCE_1.6.1.zip from a clean extraction (offline but for the installs; no provider
request). Each step is its own process: output to WORK/logs/<step>.log, one JSON line to WORK/steps.jsonl. A step
run again keeps the earlier log in WORK/logs/attempts/. Every step but the installs runs with HTTP(S) sent to a
closed local port (127.0.0.1:9) and without any provider key, database URL or collector setting of this workstation.

usage: python -I verify161_clean.py ZIP WORK STEP...      STEP: extract | <edition>.<check> | report
       edition: oxylabs | scrapedo; check: tree, lock, install, ruff, format, mypy, version, help, validate-config,
       unit, integration
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import zipfile
from datetime import UTC, datetime
from pathlib import Path

UV = str(Path.home() / ".local" / "bin" / "uv.exe")
PY = r"C:\w6\py312\pkg\tools\python.exe"
TOP = "walmart-source-1.6.1"
EDITIONS = {"oxylabs": "walmart-oxylabs-1.6.1", "scrapedo": "walmart-scrapedo-1.6.1"}
DROP = ("OXYLABS", "SCRAPEDO", "SCRAPE_DO", "WALMART_COLLECTOR", "DATABASE_URL", "PG", "AZURE", "PUBLICATION_EVIDENCE")


def env(offline: bool) -> dict[str, str]:
    e = {k: v for k, v in os.environ.items() if not k.upper().startswith(DROP)}
    e["UV_PYTHON"] = PY
    e["PYTHONUTF8"] = "1"
    if offline:
        for k in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy", "ALL_PROXY", "all_proxy"):
            e[k] = "http://127.0.0.1:9"
        e["NO_PROXY"] = e["no_proxy"] = "localhost,127.0.0.1"
        e["UV_OFFLINE"] = "1"
    return e


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def tree_digest(tree: dict[str, str]) -> str:  # the collector's own definition (editions.py: tree_digest)
    return sha("".join(f"{tree[p]}  {p}\n" for p in sorted(tree)).encode("utf-8"))


def record(work: Path, step: str, rc: int, secs: float, note: str, cmd: str) -> None:
    line = {"step": step, "exit": rc, "seconds": round(secs, 1), "note": note, "command": cmd,
            "at": datetime.now(UTC).isoformat(timespec="seconds")}
    with (work / "steps.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(line) + "\n")
    print(json.dumps(line))


def run(work: Path, step: str, cwd: Path, args: list[str], offline: bool = True, expect: int = 0,
        timeout: int = 3600) -> int:
    logs = work / "logs"
    (logs / "attempts").mkdir(parents=True, exist_ok=True)
    log = logs / f"{step}.log"
    if log.exists():
        n = len(list((logs / "attempts").glob(f"{step}.*.log"))) + 1
        shutil.move(log, logs / "attempts" / f"{step}.{n}.log")
    t0 = time.monotonic()
    with log.open("wb") as f:
        f.write(f"$ {' '.join(args)}\n(cwd {cwd.name}; offline={offline})\n".encode())
        f.flush()
        try:
            rc = subprocess.run(args, cwd=cwd, env=env(offline), stdout=f, stderr=subprocess.STDOUT,
                                timeout=timeout).returncode
        except subprocess.TimeoutExpired:
            rc = -9
    note = "ok" if rc == expect else f"UNEXPECTED (expected {expect})"
    record(work, step, rc, time.monotonic() - t0, note, " ".join(args))
    return 0 if rc == expect else 1


def extract(zpath: Path, work: Path) -> int:
    out = work / "src"
    if out.exists():
        raise SystemExit(f"{out} exists: extract into a new folder only")
    t0 = time.monotonic()
    digest = sha(zpath.read_bytes())
    with zipfile.ZipFile(zpath) as z:
        names = z.namelist()
        bad = [n for n in names if not n.startswith(TOP + "/") or ".." in n.split("/") or n.startswith("/")]
        if bad:
            raise SystemExit(f"unsafe or foreign names: {bad[:3]}")
        z.extractall(out)
    record(work, "extract", 0, time.monotonic() - t0, f"ok: {len(names)} entries; zip sha256 {digest}", "extract")
    return 0


def tree(work: Path, edition: str) -> int:
    base = work / "src" / TOP
    build = json.loads((base / "BUILD_MANIFEST.json").read_text("utf-8"))
    top = base / EDITIONS[edition]
    files = {p.relative_to(top).as_posix(): sha(p.read_bytes()) for p in sorted(top.rglob("*")) if p.is_file()}
    rec = json.loads((top / "EDITION.json").read_text("utf-8"))
    body = {p: h for p, h in files.items() if p != "EDITION.json"}
    ed = build["editions"][edition]
    problems = []
    if len(files) != ed["files"]:
        problems.append(f"{len(files)} files, manifest {ed['files']}")
    if not (tree_digest(body) == ed["tree_sha256"] == rec.get("tree_sha256")):
        problems.append("tree digest differs")
    differ = sorted(p for p in set(body) | set(rec.get("file_sha256", {})) if body.get(p) != rec["file_sha256"].get(p))
    if differ:
        problems.append(f"files differ from EDITION.json: {differ[:5]}")
    info = json.loads((top / "BUILD_INFO.json").read_text("utf-8"))
    if info.get("commit") != build["commit"]:
        problems.append(f"BUILD_INFO commit {info.get('commit')}")
    for p in files:
        name = p.rsplit("/", 1)[-1]
        if (name == ".env" or name.startswith(".env.")) and name != ".env.example":
            problems.append(f"an env file: {p}")
    note = "ok: " + f"{len(files)} files, tree {tree_digest(body)[:16]}..., commit {build['commit'][:12]}" if not problems \
        else "PROBLEMS: " + "; ".join(problems)
    record(work, f"{edition}.tree", 0 if not problems else 1, 0.0, note, "tree check")
    return 0 if not problems else 1


def report(work: Path) -> int:
    steps: dict[str, dict] = {}
    for line in (work / "steps.jsonl").read_text("utf-8").splitlines():
        d = json.loads(line)
        steps[d["step"]] = d  # the last attempt counts
    bad = [s for s, d in steps.items() if d["note"].startswith(("UNEXPECTED", "PROBLEMS"))]
    lines = [f"{s}: exit {d['exit']} in {d['seconds']} s: {d['note']}" for s, d in steps.items()]
    text = "\n".join(lines) + f"\n\n{len(steps)} steps, {len(bad)} not ok: {', '.join(bad) or 'none'}\nRESULT: " + \
        ("PASS" if not bad else "FAIL") + "\n"
    (work / "REPORT.txt").write_text(text, encoding="utf-8")
    print(text)
    return 0 if not bad else 1


def main(argv: list[str]) -> int:
    zpath, work = Path(argv[0]), Path(argv[1])
    work.mkdir(parents=True, exist_ok=True)
    rc = 0
    for step in argv[2:]:
        if step == "extract":
            rc |= extract(zpath, work)
            continue
        if step == "report":
            rc |= report(work)
            continue
        edition, check = step.split(".", 1)
        cwd = work / "src" / TOP / EDITIONS[edition]
        cli = [UV, "run", "--frozen", "walmart-collector"]
        if check == "tree":
            rc |= tree(work, edition)
        elif check == "lock":
            rc |= run(work, step, cwd, [UV, "lock", "--check", "--offline"])
        elif check == "install":
            rc |= run(work, step, cwd, [UV, "sync", "--frozen"], offline=False)
        elif check == "ruff":
            rc |= run(work, step, cwd, [UV, "run", "--frozen", "ruff", "check", "src", "tests"])
        elif check == "format":
            rc |= run(work, step, cwd, [UV, "run", "--frozen", "ruff", "format", "--check", "src", "tests"])
        elif check == "mypy":
            rc |= run(work, step, cwd, [UV, "run", "--frozen", "mypy"])
        elif check == "version":
            rc |= run(work, step, cwd, [*cli, "--version"])
        elif check == "help":
            rc |= run(work, step, cwd, [*cli, "--help"])
        elif check == "validate-config":
            rc |= run(work, step, cwd, [*cli, "validate-config"])
        elif check == "unit":
            rc |= run(work, step, cwd, [UV, "run", "--frozen", "python", "-m", "pytest", "-q", "-p", "no:cacheprovider",
                                        "-rs", "tests/unit", f"--junitxml={work / 'junit' / (step + '.xml')}"])
        elif check == "integration":
            rc |= run(work, step, cwd, [UV, "run", "--frozen", "python", "-m", "pytest", "-q", "-p", "no:cacheprovider",
                                        "-rs", "tests/integration", f"--junitxml={work / 'junit' / (step + '.xml')}"],
                      timeout=4000)
        else:
            raise SystemExit(f"unknown step {step}")
    return rc


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
