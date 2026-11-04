"""Lets each step of C:/w9/live/live160_run.py name the installed edition it runs (``"edition": "1.6.1"``; default
1.6.0, the edition of every earlier step), and records it in the step's log (``HARNESS_EDITION``). Applied once,
after the last 1.6.0 step ended; nothing else in the harness changes."""

from pathlib import Path

P = Path("C:/w9/live/live160_run.py")
s = P.read_text(encoding="utf-8")
if "EDITIONS = {" in s:
    raise SystemExit("already patched")
reps = [
    (
        'PROJECT = Path(r"C:\\w9\\live\\ed\\walmart-oxylabs-1.6.0")\nPYTHON = PROJECT / ".venv" / "Scripts" / "python.exe"\n',
        'EDITIONS = {  # a step names its edition ("edition"); 1.6.0 when it names none (every step before 1.6.1)\n'
        '    "1.6.0": Path(r"C:\\w9\\live\\ed\\walmart-oxylabs-1.6.0"),\n'
        '    "1.6.1": Path(r"C:\\w9\\live\\ed\\walmart-oxylabs-1.6.1"),\n'
        "}\n"
        'PROJECT = EDITIONS["1.6.0"]\n'
        'PYTHON = PROJECT / ".venv" / "Scripts" / "python.exe"\n',
    ),
    (
        "    otl = trial()\n    lease = None\n    stop = threading.Event()\n",
        '    print(json.dumps({"event": "HARNESS_EDITION", "edition": spec.get("edition", "1.6.0"),\n'
        '                      "python": sys.executable}), flush=True)\n'
        "    otl = trial()\n    lease = None\n    stop = threading.Event()\n",
    ),
    (
        '                config = spec.get("config") or CONFIG\n',
        '                ed = EDITIONS[spec.get("edition", "1.6.0")]\n'
        '                config = spec.get("config") or str(ed / "config" / "collector.yaml")\n',
    ),
    (
        '                        [str(PYTHON), "-I", str(Path(__file__).resolve()), "--child", label],\n'
        "                        cwd=PROJECT,\n",
        '                        [str(ed / ".venv" / "Scripts" / "python.exe"), "-I", str(Path(__file__).resolve()),\n'
        '                         "--child", label],\n'
        "                        cwd=ed,\n",
    ),
]
for a, b in reps:
    assert s.count(a) == 1, a[:80]
    s = s.replace(a, b)
P.write_bytes(s.encode("utf-8"))
print("patched")
