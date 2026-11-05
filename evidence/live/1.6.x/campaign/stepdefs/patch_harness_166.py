"""Adds the installed 1.6.6 edition to C:/w9/live/live160_run.py's EDITIONS (a step names it with
``"edition": "1.6.6"``). Applied once, after the last 1.6.5 step ended (L11b closed and the Oxylabs ceiling set to 0,
steps 194 to 196); nothing else in the harness changes. The harness before this patch is kept as
C:/w9/logs/live160_run.before_166.py; an existing backup is never overwritten."""

import hashlib
import shutil
from pathlib import Path

P = Path("C:/w9/live/live160_run.py")
BACKUP = Path("C:/w9/logs/live160_run.before_166.py")
s = P.read_text(encoding="utf-8")
if '"1.6.6"' in s:
    raise SystemExit("already patched")
if BACKUP.exists():
    raise SystemExit(f"{BACKUP} exists: not overwritten")
shutil.copy2(P, BACKUP)
assert BACKUP.read_bytes() == P.read_bytes()
a = '    "1.6.5": Path(r"C:\\w9\\live\\ed\\walmart-oxylabs-1.6.5"),\n}\n'
b = (
    '    "1.6.5": Path(r"C:\\w9\\live\\ed\\walmart-oxylabs-1.6.5"),\n'
    '    "1.6.6": Path(r"C:\\w9\\live\\ed\\walmart-oxylabs-1.6.6"),\n'
    "}\n"
)
assert s.count(a) == 1
P.write_bytes(s.replace(a, b).encode("utf-8"))
print("patched; backup", BACKUP, hashlib.sha256(BACKUP.read_bytes()).hexdigest(),
      "now", hashlib.sha256(P.read_bytes()).hexdigest())
