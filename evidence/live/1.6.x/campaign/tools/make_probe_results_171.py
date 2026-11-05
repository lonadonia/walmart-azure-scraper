"""Writes probe_results_171.py from probe_results_170.py: probe 1.7.1, plus the reproduction tests of 1.7.1 run
against the source of 1.7.0 (a second clean export: 1.7.1's tests, 1.7.0's src), and the workstation's name
replaced in the JUnit file (as done by hand for 1.7.0). Run once."""

from pathlib import Path

SRC = Path(r"C:\w9\live\tools\probe_results_170.py")
DST = Path(r"C:\w9\live\tools\probe_results_171.py")
s = SRC.read_text(encoding="utf-8")

reps = [
    (
        '"""The Classic probe\'s offline run for the delivery (probe 1.7.0; adapted from probe_results_151.py):',
        '"""The Classic probe\'s offline run for the delivery (probe 1.7.1; adapted from probe_results_170.py):',
    ),
    (
        "usage: C:/w6/py312/pkg/tools/python.exe -I -X utf8 probe_results_151.py REV WORK OUT",
        "usage: C:/w6/py312/pkg/tools/python.exe -I -X utf8 probe_results_171.py REV OLD_REV WORK OUT\n"
        "- OLD_REV: the revision of probe 1.7.0, whose src/ the reproduction tests of REV are run against (they must fail).",
    ),
    (
        "    rev, work, out = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])",
        "    rev, old_rev, work, out = sys.argv[1], sys.argv[2], Path(sys.argv[3]), Path(sys.argv[4])",
    ),
    (
        "    def run(name: str, cmd: list[str], ok: tuple[int, ...] = (0,), the_env: dict[str, str] | None = None) -> int:\n"
        "        started = now()\n"
        "        p = subprocess.run(cmd, cwd=root, env=the_env or closed,",
        "    def run(name: str, cmd: list[str], ok: tuple[int, ...] = (0,), the_env: dict[str, str] | None = None, where: Path | None = None) -> int:\n"
        "        started = now()\n"
        "        p = subprocess.run(cmd, cwd=where or root, env=the_env or closed,",
    ),
    (
        '        shown = " ".join(c if not c.startswith(str(root)) else c.replace(str(root) + os.sep, "") for c in cmd).replace(UV, "uv").replace(str(root), ".").replace("\\\\", "/")',
        '        base = where or root\n'
        '        shown = " ".join(c if not c.startswith(str(base)) else c.replace(str(base) + os.sep, "") for c in cmd).replace(UV, "uv").replace(str(base), ".").replace("\\\\", "/")\n'
        '        if where is not None:\n'
        '            shown = "(in the 1.7.0-source tree) " + shown',
    ),
    (
        '    run("15_live_is_refused", [*cli, "live", "--manifest", "offline_out/manifest.json"], ok=(3,))\n',
        '    run("15_live_is_refused", [*cli, "live", "--manifest", "offline_out/manifest.json"], ok=(3,))\n'
        "    # 16: the reproduction tests of 1.7.1 against the source of 1.7.0: they must fail (exit 1), 7 of 7.\n"
        '    old = work / "repro_on_1.7.0"\n'
        "    old.mkdir()\n"
        '    old_tar = subprocess.run(["git", "-C", str(REPO), "archive", "--format=tar", old_rev, "--", PROBE + "/src"], check=True, capture_output=True).stdout\n'
        "    with tarfile.open(fileobj=io.BytesIO(old_tar)) as t:\n"
        '        t.extractall(old, filter="data")\n'
        "    old_root = old / PROBE\n"
        '    for name in ("pyproject.toml", "uv.lock", "tests"):\n'
        "        src_path = root / name\n"
        "        if src_path.is_dir():\n"
        '            shutil.copytree(src_path, old_root / name, ignore=shutil.ignore_patterns("__pycache__"))\n'
        "        else:\n"
        "            shutil.copyfile(src_path, old_root / name)\n"
        '    run("16a_uv_sync_frozen_1.7.0_source", [UV, "sync", "--frozen"], the_env=env, where=old_root)\n'
        '    old_py = str(old_root / ".venv" / "Scripts" / "python.exe")\n'
        '    run("16b_reproductions_on_1.7.0_source", [old_py, "-m", "pytest", "-p", "no:cacheprovider", "-rA", "--tb=short", "tests/test_c2_c4_reproduction.py"], ok=(1,), where=old_root)\n'
        '    run("17_reproductions_on_1.7.1", [py, "-m", "pytest", "-p", "no:cacheprovider", "-rA", "--tb=short", "tests/test_c2_c4_reproduction.py"])\n',
    ),
    (
        '    shutil.copyfile(root / "junit_standalone.xml", out / "junit_standalone.xml")\n',
        '    junit = (root / "junit_standalone.xml").read_text(encoding="utf-8")\n'
        "    import re as _re\n"
        '    junit, n = _re.subn(r\'hostname="[^"]*"\', \'hostname="(workstation)"\', junit)\n'
        '    assert n == 1, n\n'
        '    (out / "junit_standalone.xml").write_bytes(junit.encode("utf-8"))\n',
    ),
    (
        '        "15_live_is_refused                          live mode refused, exit 3, with what a campaign still lacks.",\n',
        '        "15_live_is_refused                          live mode refused, exit 3, with what a campaign still lacks.",\n'
        '        f"16a, 16b                                    the reproduction tests of 1.7.1 (tests/test_c2_c4_reproduction.py, with tests/session_drill.py) run against the src/ of probe 1.7.0 (revision {old_rev}), in a second clean export installed from the same lockfile: exit 1 expected, the 7 tests failing (C2 and C4 as 1.7.0 left them).",\n'
        '        "17_reproductions_on_1.7.1                   the same 7 tests on this revision: they pass.",\n'
        "        \"junit_standalone.xml: its hostname attribute reads (workstation); the workstation's name was replaced before packing, and nothing else in the file was changed.\",\n",
    ),
]
for a, b in reps:
    assert s.count(a) == 1, a[:90]
    s = s.replace(a, b)
DST.write_bytes(s.encode("utf-8"))
print("written", DST)
