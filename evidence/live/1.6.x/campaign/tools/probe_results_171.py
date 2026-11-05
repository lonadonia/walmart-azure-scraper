"""The Classic probe's offline run for the delivery (probe 1.7.1; adapted from probe_results_170.py): from a clean export of the frozen revision, installed from its lockfile. No request, no credential.

usage: C:/w6/py312/pkg/tools/python.exe -I -X utf8 probe_results_171.py REV OLD_REV WORK OUT
- OLD_REV: the revision of probe 1.7.0, whose src/ the reproduction tests of REV are run against (they must fail).
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

REPO = Path(r"C:\w9\wt")
UV = str(Path.home() / ".local" / "bin" / "uv.exe")
PROBE = "headless/oxylabs-classic-probe"
DEAD = "http://127.0.0.1:9"
FIXTURE_WRITER = r"""
import json, sys
from pathlib import Path
sys.path.insert(0, ".")
from tests import fixture_builder as fb
from tests.conftest import SYNTHETIC_RATES
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
MARIANOS_WRITER = r"""
import json, sys
from pathlib import Path
sys.path.insert(0, ".")
from tests import test_marianos as tm
out = Path(sys.argv[1])
fixtures = out / "fixtures"
fixtures.mkdir(parents=True)
spec = {"steps": {}}
for step, answers in tm.complete().items():
    spec["steps"][step] = []
    for i, (status, body) in enumerate(answers):
        (fixtures / f"{step}-{i}.json").write_bytes(body)
        spec["steps"][step].append({"http_status": status, "body_file": f"{step}-{i}.json"})
(fixtures / "replay.json").write_text(json.dumps(spec, indent=1), "utf-8")
(out / "synthetic_rates.json").write_text(json.dumps(tm.RATES, indent=1), "utf-8")  # tests/test_marianos.py: invented, with Mariano's rates
print(len(spec["steps"]), "steps")
"""


def now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def main() -> int:
    rev, old_rev, work, out = sys.argv[1], sys.argv[2], Path(sys.argv[3]), Path(sys.argv[4])
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

    def run(name: str, cmd: list[str], ok: tuple[int, ...] = (0,), the_env: dict[str, str] | None = None, where: Path | None = None, says: tuple[str, ...] = (), never: tuple[str, ...] = ()) -> int:
        started = now()
        p = subprocess.run(cmd, cwd=where or root, env=the_env or closed, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=1800)
        text = (p.stdout or "") + (p.stderr or "")
        (out / f"{name}.txt").write_bytes(text.encode("utf-8"))
        base = where or root
        shown = " ".join(c if not c.startswith(str(base)) else c.replace(str(base) + os.sep, "") for c in cmd).replace(UV, "uv").replace(str(base), ".").replace("\\", "/")
        if where is not None:
            shown = "(in the 1.7.0-source tree) " + shown
        good = p.returncode in ok and all(x in text for x in says) and not any(x in text for x in never)
        log.append({"output_file": f"{name}.txt", "command": shown, "exit_code": p.returncode, "expected_exit_codes": "/".join(map(str, ok)), "output_must_say": " & ".join(says), "output_must_not_say": " & ".join(never), "as_expected": good, "started_at": started, "ended_at": now()})
        print(name, "exit", p.returncode, "ok" if good else "UNEXPECTED")
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
    run("11_replay_synthetic_responses", [*cli, "replay", "--retailer", "walmart", "--targets", "config/targets.json", "--fixtures", "offline_out/synthetic/fixtures", "--rates", "offline_out/synthetic/synthetic_rates.json", "--out", "offline_out/replay"])
    (root / "write_marianos_fixtures.py").write_text(MARIANOS_WRITER, encoding="utf-8")
    run("11b_write_marianos_fixtures", [py, "write_marianos_fixtures.py", "offline_out/marianos_inputs"])
    run("11c_replay_marianos_saved_pages", [*cli, "replay", "--retailer", "marianos", "--targets", "config/targets.json", "--fixtures", "offline_out/marianos_inputs/fixtures", "--rates", "offline_out/marianos_inputs/synthetic_rates.json", "--out", "offline_out/replay_marianos"])
    run("12_campaign_init_offline", [*cli, "campaign-init", "--manifest", "offline_out/manifest.json", "--ledger", "offline_out/ledger.sqlite3", "--campaign-id", "offline-check", "--offline"])
    run("13_status", [*cli, "status", "--manifest", "offline_out/manifest.json"])
    run("14_export", [*cli, "export", "--manifest", "offline_out/manifest.json", "--out", "offline_out/export"])
    run("15_live_is_refused", [*cli, "live", "--manifest", "offline_out/manifest.json"], ok=(3,))
    # 16: the reproduction tests of 1.7.1 against the source of 1.7.0: they must fail (exit 1), 7 of 7.
    old = work / "repro_on_1.7.0"
    old.mkdir()
    # the whole probe folder of this revision (README.md, pyproject.toml, uv.lock, tests/, ...), then its src/
    # replaced by the src/ of 1.7.0: only the code under test differs
    new_tar = subprocess.run(["git", "-C", str(REPO), "archive", "--format=tar", rev, "--", PROBE], check=True, capture_output=True).stdout
    with tarfile.open(fileobj=io.BytesIO(new_tar)) as t:
        t.extractall(old, filter="data")
    old_root = old / PROBE
    shutil.rmtree(old_root / "src")
    old_tar = subprocess.run(["git", "-C", str(REPO), "archive", "--format=tar", old_rev, "--", PROBE + "/src"], check=True, capture_output=True).stdout
    with tarfile.open(fileobj=io.BytesIO(old_tar)) as t:
        t.extractall(old, filter="data")
    assert (old_root / "README.md").is_file() and (old_root / "src" / "classic_probe" / "campaign.py").is_file()
    assert not (old_root / "src" / "classic_probe" / "durable.py").exists(), "the src/ of 1.7.0 has no durable.py"
    run("16a_uv_sync_frozen_1.7.0_source", [UV, "sync", "--frozen"], the_env=env, where=old_root)
    old_py = str(old_root / ".venv" / "Scripts" / "python.exe")
    run("16b_reproductions_on_1.7.0_source", [old_py, "-m", "pytest", "-p", "no:cacheprovider", "-rA", "--tb=short", "tests/test_c2_c4_reproduction.py"], ok=(1,), where=old_root, says=("7 failed in ",), never=("No module named",))
    run("17_reproductions_on_1.7.1", [py, "-m", "pytest", "-p", "no:cacheprovider", "-rA", "--tb=short", "tests/test_c2_c4_reproduction.py"], says=("7 passed in ",))
    junit = (root / "junit_standalone.xml").read_text(encoding="utf-8")
    import re as _re
    junit, n = _re.subn(r'hostname="[^"]*"', 'hostname="(workstation)"', junit)
    assert n == 1, n
    (out / "junit_standalone.xml").write_bytes(junit.encode("utf-8"))
    for name in ("replay", "replay_marianos", "export"):
        shutil.copytree(scratch / name, out / name, ignore=shutil.ignore_patterns("*.sqlite3", "*.sqlite3-*"))
    shutil.copytree(scratch / "synthetic", out / "synthetic_inputs_of_the_replay")
    shutil.copytree(scratch / "marianos_inputs", out / "inputs_of_the_marianos_replay")
    (out / "inputs_of_the_marianos_replay" / "README.txt").write_bytes(b"OFFLINE REPLAY inputs: real Mariano's pages (Vernon Hills, Pickup) that the Mariano's collector saved through the Oxylabs Web API on 2026-11-02, each wrapped in an invented Classic envelope by tests/test_marianos.py, and an invented rate card. The pages are real; the Classic envelopes and the rates are not.\n")
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
        "Every command but the two installs (00, 16a) ran with HTTP(S) sent to a closed local port and no OXYLABS variable; commands.csv lists each with its exit code. A command is as_expected only when its exit code is the expected one and, where output_must_say is set, its output says that too (an exit code alone does not show that a test ran).",
        "",
        "01_pytest_standalone, junit_standalone.xml  the probe's tests, from the probe alone: SYNTHETIC responses, and real saved Walmart pages inside invented Classic envelopes. Skipped tests say why (-rs): see README_FIRST.md.",
        "07 to 09                                    the plan and validation. The rate card is the shipped placeholder: no rate is known.",
        "10, 11, replay/, synthetic_inputs_of_the_replay/   the Walmart steps replayed against SYNTHETIC responses and an invented rate card (OFFLINE REPLAY). It shows the ledger and the stops work; it shows nothing about Classic.",
        "11b, 11c, replay_marianos/, inputs_of_the_marianos_replay/   the Mariano's steps replayed against real saved Mariano's pages in invented Classic envelopes, with an invented rate card (OFFLINE REPLAY). It shows nothing about Classic.",
        "12 to 14, export/, offline_campaign_manifest.json  an offline ledger: created, read and exported. Marked offline: it cannot back a live campaign.",
        "15_live_is_refused                          live mode refused, exit 3, with what a campaign still lacks.",
        f"16a, 16b                                    the reproduction tests of 1.7.1 (tests/test_c2_c4_reproduction.py, with tests/session_drill.py) run against the src/ of probe 1.7.0 (revision {old_rev}): a second clean export of this revision whose src/ was replaced by that of 1.7.0, installed from the same lockfile. 16b must exit 1 and report 7 failed (C2 and C4 as 1.7.0 left them).",
        "17_reproductions_on_1.7.1                   the same 7 tests on this revision: they must report 7 passed.",
        "junit_standalone.xml: its hostname attribute reads (workstation); the workstation's name was replaced before packing, and nothing else in the file was changed.",
    ]
    (out / "README.txt").write_bytes(("\n".join(readme) + "\n").encode("utf-8"))
    bad = [r for r in log if not r["as_expected"]]
    print(json.dumps({"commands": len(log), "unexpected": [r["output_file"] for r in bad]}))
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
