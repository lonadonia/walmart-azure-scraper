"""The Classic probe's offline run for the delivery: from a clean export of the frozen revision, installed from its lockfile. No request, no credential.

usage: C:/w6/py312/pkg/tools/python.exe -I -X utf8 probe_results_151.py REV WORK OUT
- WORK (new): the clean export of headless/oxylabs-classic-probe at REV, with its .venv.
- OUT (new): offline_results/ of the probe ZIP: outputs named by what they are, commands.csv with each command, exit code and time.
Every step but the install has HTTP(S) sent to a closed local port and no OXYLABS variable.
"""

from __future__ import annotations

import csv
import io
import json
import os
import shutil
import subprocess
import sys
import tarfile
from datetime import UTC, datetime
from pathlib import Path

REPO = Path(r"C:\w7\wt")
UV = r"<home>\.local\bin\uv.exe"
PROBE = "headless/oxylabs-classic-probe"
DEAD = "http://127.0.0.1:9"
FIXTURE_WRITER = r"""
import json, sys
from pathlib import Path
sys.path.insert(0, ".")
from tests import fixture_builder as fb
from tests.test_offline import SYNTHETIC_RATES
out = Path(sys.argv[1])
fixtures = out / "fixtures"
fixtures.mkdir(parents=True)
spec = {"steps": {}}
for step, answers in fb.complete().items():
    spec["steps"][step] = []
    for i, (status, body) in enumerate(answers):
        (fixtures / f"{step}-{i}.json").write_bytes(body)
        spec["steps"][step].append({"http_status": status, "body_file": f"{step}-{i}.json"})
(fixtures / "replay.json").write_text(json.dumps(spec, indent=1), "utf-8")
(out / "synthetic_rates.json").write_text(json.dumps(SYNTHETIC_RATES, indent=1), "utf-8")
print(len(spec["steps"]), "steps")
"""


def now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def main() -> int:
    rev, work, out = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])
    if work.exists() or out.exists():
        raise SystemExit("WORK and OUT must be new folders")
    work.mkdir(parents=True)
    out.mkdir(parents=True)
    tar = subprocess.run(["git", "-C", str(REPO), "archive", "--format=tar", rev, "--", PROBE], check=True, capture_output=True).stdout
    with tarfile.open(fileobj=io.BytesIO(tar)) as t:
        t.extractall(work, filter="data")
    root = work / PROBE
    env = {k: v for k, v in os.environ.items() if not k.upper().startswith(("OXYLABS", "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "NO_PROXY", "VIRTUAL_ENV"))}
    env.update(UV_PYTHON=r"C:\w6\py312\pkg\tools\python.exe", PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    closed = dict(env, HTTP_PROXY=DEAD, HTTPS_PROXY=DEAD, ALL_PROXY=DEAD, NO_PROXY="localhost,127.0.0.1,::1")
    log: list[dict[str, object]] = []

    def run(name: str, cmd: list[str], ok: tuple[int, ...] = (0,), the_env: dict[str, str] | None = None) -> int:
        started = now()
        p = subprocess.run(cmd, cwd=root, env=the_env or closed, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=1800)
        text = (p.stdout or "") + (p.stderr or "")
        (out / f"{name}.txt").write_bytes(text.encode("utf-8"))
        shown = " ".join(c if not c.startswith(str(root)) else c.replace(str(root) + os.sep, "") for c in cmd).replace(UV, "uv").replace(str(root), ".").replace("\\", "/")
        log.append({"output_file": f"{name}.txt", "command": shown, "exit_code": p.returncode, "expected_exit_codes": "/".join(map(str, ok)), "as_expected": p.returncode in ok, "started_at": started, "ended_at": now()})
        print(name, "exit", p.returncode, "ok" if p.returncode in ok else "UNEXPECTED")
        return p.returncode

    run("00_uv_sync_frozen", [UV, "sync", "--frozen"], the_env=env)
    py = str(root / ".venv" / "Scripts" / "python.exe")
    cli = [py, "-m", "classic_probe"]
    run("01_pytest_standalone", [py, "-m", "pytest", "-q", "-p", "no:cacheprovider", "-rs", f"--junitxml={root / 'junit_standalone.xml'}"])
    run("02_ruff_check", [py, "-m", "ruff", "check", "src", "tests"])
    run("03_ruff_format_check", [py, "-m", "ruff", "format", "--check", "src", "tests"])
    run("04_mypy", [py, "-m", "mypy"])
    run("05_version", [*cli, "--version"])
    run("06_help", [*cli, "--help"])
    run("07_plan", [*cli, "plan", "--targets", "config/targets.json"])
    run("08_plan_with_placeholder_rates", [*cli, "plan", "--targets", "config/targets.json", "--rates", "config/rates.example.json"])
    run("09_validate", [*cli, "validate", "--targets", "config/targets.json", "--rates", "config/rates.example.json"])
    scratch = root / "offline_out"
    scratch.mkdir()
    (root / "write_fixtures.py").write_text(FIXTURE_WRITER, encoding="utf-8")
    run("10_write_synthetic_fixtures", [py, "write_fixtures.py", "offline_out/synthetic"])
    run("11_replay_synthetic_responses", [*cli, "replay", "--targets", "config/targets.json", "--fixtures", "offline_out/synthetic/fixtures", "--rates", "offline_out/synthetic/synthetic_rates.json", "--out", "offline_out/replay"])
    run("12_campaign_init_offline", [*cli, "campaign-init", "--manifest", "offline_out/manifest.json", "--ledger", "offline_out/ledger.sqlite3", "--campaign-id", "offline-check", "--offline"])
    run("13_status", [*cli, "status", "--manifest", "offline_out/manifest.json"])
    run("14_export", [*cli, "export", "--manifest", "offline_out/manifest.json", "--out", "offline_out/export"])
    run("15_live_is_refused", [*cli, "live", "--manifest", "offline_out/manifest.json"], ok=(3,))
    shutil.copyfile(root / "junit_standalone.xml", out / "junit_standalone.xml")
    for name in ("replay", "export"):
        shutil.copytree(scratch / name, out / name, ignore=shutil.ignore_patterns("*.sqlite3", "*.sqlite3-*"))
    shutil.copytree(scratch / "synthetic", out / "synthetic_inputs_of_the_replay")
    shutil.copyfile(scratch / "manifest.json", out / "offline_campaign_manifest.json")
    (out / "synthetic_inputs_of_the_replay" / "README.txt").write_bytes(b"SYNTHETIC: invented Classic responses and an invented rate card, written by tests/fixture_builder.py. They say nothing about what Classic returns or charges.\n")
    with (out / "commands.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(log[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(log)
    readme = [
        "OFFLINE RESULTS of the Oxylabs Classic probe. No request was sent and no credential was read.",
        f"Revision: {subprocess.run(['git', '-C', str(REPO), 'rev-parse', rev], check=True, capture_output=True, text=True).stdout.strip()}. Clean export, installed with uv sync --frozen.",
        f"Run (UTC): {log[0]['started_at']} to {log[-1]['ended_at']}.",
        "Every command but the install ran with HTTP(S) sent to a closed local port and no OXYLABS variable; commands.csv lists each with its exit code.",
        "",
        "01_pytest_standalone, junit_standalone.xml  the probe's tests, from the probe alone: SYNTHETIC responses, and real saved Walmart pages inside invented Classic envelopes. One test is skipped: it needs the collector beside the probe (README_FIRST.md).",
        "07 to 09                                    the plan and validation. The rate card is the shipped placeholder: no rate is known.",
        "10, 11, replay/, synthetic_inputs_of_the_replay/   the Walmart steps replayed against SYNTHETIC responses and an invented rate card (OFFLINE REPLAY). It shows the ledger and the stops work; it shows nothing about Classic.",
        "12 to 14, export/, offline_campaign_manifest.json  an offline ledger: created, read and exported. Marked offline: it cannot back a live campaign.",
        "15_live_is_refused                          live mode refused, exit 3, with what a campaign still lacks.",
    ]
    (out / "README.txt").write_bytes(("\n".join(readme) + "\n").encode("utf-8"))
    bad = [r for r in log if not r["as_expected"]]
    print(json.dumps({"commands": len(log), "unexpected": [r["output_file"] for r in bad]}))
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
