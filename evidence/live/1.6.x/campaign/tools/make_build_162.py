"""Writes scripts/build_walmart_162_delivery.py from build_walmart_161_delivery.py: release 1.6.2, its fixed time, and
the source README's live-run line for this release (the live stages that ran on it, given as an argument so that it
names only what ran). The probe part is unchanged: the shared probe 1.7.0 is not rebuilt (its tree did not change
after 1780349; its archive of 2026-11-03 is published as built). Run once.

usage: python -I make_build_162.py "LIVE RUNS TEXT"
"""

import sys
from pathlib import Path

SRC = Path(r"C:\w9\wt\scripts\build_walmart_161_delivery.py")
DST = Path(r"C:\w9\wt\scripts\build_walmart_162_delivery.py")
if DST.exists():
    raise SystemExit("already written")
if len(sys.argv) != 2 or not sys.argv[1].strip():
    raise SystemExit(__doc__)
live_text = sys.argv[1].strip()
s = SRC.read_text(encoding="utf-8")
old_row = (
    "| `walmart-oxylabs-{release}/` | Oxylabs Web API (Bearer key; not the Classic product) | the staged live runs of "
    "2026-11-03 from L3 on (L1 and L2 ran 1.6.0, the release before; see the review documents) |\n"
)
new_row = f"| `walmart-oxylabs-{{release}}/` | Oxylabs Web API (Bearer key; not the Classic product) | {live_text} |\n"
reps = [
    ('"""Build the Walmart release 1.6.1 delivery', '"""Build the Walmart release 1.6.2 delivery'),
    ('RELEASE = "1.6.1"\nFIXED_TIME = (2026, 11, 3, 0, 0, 0)\n', 'RELEASE = "1.6.2"\nFIXED_TIME = (2026, 11, 4, 0, 0, 0)\n'),
    (old_row, new_row),
]
for a, b in reps:
    assert s.count(a) == 1, a[:90]
    s = s.replace(a, b)
# the docstring's own file names
for a, b in (
    ("scripts/build_walmart_161_delivery.py", "scripts/build_walmart_162_delivery.py"),
    ("WALMART_SOURCE_1.6.1.zip", "WALMART_SOURCE_1.6.2.zip"),
    ("walmart-source-1.6.1/", "walmart-source-1.6.2/"),
    ("walmart-oxylabs-1.6.1/ and walmart-scrapedo-1.6.1/", "walmart-oxylabs-1.6.2/ and walmart-scrapedo-1.6.2/"),
    ("WALMART_EVIDENCE_1.6.1.zip", "WALMART_EVIDENCE_1.6.2.zip"),
    ("walmart-evidence-1.6.1/", "walmart-evidence-1.6.2/"),
):
    s = s.replace(a, b)
left = [ln for ln in s.splitlines() if "1.6.1" in ln or "161" in ln]
print("lines still naming 1.6.1:", left)
DST.write_bytes(s.encode("utf-8"))
print("written", DST)
