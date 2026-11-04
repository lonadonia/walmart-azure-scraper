"""Adds the installed 1.6.2 edition to C:/w9/live/live160_run.py's EDITIONS (a step names it with
``"edition": "1.6.2"``). Applied once, after the last 1.6.1 step ended; nothing else in the harness changes. The
harness before this patch is kept as C:/w9/logs/live160_run.before_162.py."""

import shutil
from pathlib import Path

P = Path("C:/w9/live/live160_run.py")
s = P.read_text(encoding="utf-8")
if '"1.6.2"' in s:
    raise SystemExit("already patched")
shutil.copy2(P, "C:/w9/logs/live160_run.before_162.py")
a = '    "1.6.1": Path(r"C:\\w9\\live\\ed\\walmart-oxylabs-1.6.1"),\n}\n'
b = (
    '    "1.6.1": Path(r"C:\\w9\\live\\ed\\walmart-oxylabs-1.6.1"),\n'
    '    "1.6.2": Path(r"C:\\w9\\live\\ed\\walmart-oxylabs-1.6.2"),\n'
    "}\n"
)
assert s.count(a) == 1
P.write_bytes(s.replace(a, b).encode("utf-8"))
print("patched")
