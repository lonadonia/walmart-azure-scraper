"""Writes scripts/build_walmart_165_delivery.py from build_walmart_164_delivery.py: release 1.6.5 and the source
README's live-run line for this release. Release 1.6.5 changes only the independent source check: no live stage ran
on it, and the line says so. The probe part is unchanged: the shared probe 1.7.0 is not rebuilt. Run once.

usage: python -I make_build_165.py
"""

from pathlib import Path

SRC = Path(r"C:\w9\wt\scripts\build_walmart_164_delivery.py")
DST = Path(r"C:\w9\wt\scripts\build_walmart_165_delivery.py")
if DST.exists():
    raise SystemExit("already written")
s = SRC.read_text(encoding="utf-8")
old_row = (
    "| `walmart-oxylabs-{release}/` | Oxylabs Web API (Bearer key; not the Classic product) | the live census L10 of "
    "2026-11-04 (page 1 of each listing, detail reading off); L1 to L9 ran releases 1.6.0 to 1.6.3 (see the review "
    "documents) |\n"
)
new_row = (
    "| `walmart-oxylabs-{release}/` | Oxylabs Web API (Bearer key; not the Classic product) | none: release "
    "{release} changes only the independent source check, and what a run collects and exports is that of 1.6.4. "
    "The live runs L1 to L10 ran releases 1.6.0 to 1.6.4 (the census L10 on 1.6.4), and the export of L10 was "
    "verified offline with this release (see the review documents) |\n"
)
reps = [
    ('"""Build the Walmart release 1.6.4 delivery', '"""Build the Walmart release 1.6.5 delivery'),
    ('RELEASE = "1.6.4"\nFIXED_TIME = (2026, 11, 4, 0, 0, 0)\n', 'RELEASE = "1.6.5"\nFIXED_TIME = (2026, 11, 4, 0, 0, 0)\n'),
    (old_row, new_row),
]
for a, b in reps:
    assert s.count(a) == 1, a[:90]
    s = s.replace(a, b)
for a, b in (
    ("scripts/build_walmart_164_delivery.py", "scripts/build_walmart_165_delivery.py"),
    ("WALMART_SOURCE_1.6.4.zip", "WALMART_SOURCE_1.6.5.zip"),
    ("walmart-source-1.6.4/", "walmart-source-1.6.5/"),
    ("walmart-oxylabs-1.6.4/ and walmart-scrapedo-1.6.4/", "walmart-oxylabs-1.6.5/ and walmart-scrapedo-1.6.5/"),
    ("WALMART_EVIDENCE_1.6.4.zip", "WALMART_EVIDENCE_1.6.5.zip"),
    ("walmart-evidence-1.6.4/", "walmart-evidence-1.6.5/"),
):
    s = s.replace(a, b)
left = [ln for ln in s.splitlines() if "1.6.4" in ln or "164" in ln]
print("lines still naming 1.6.4:", left)
DST.write_bytes(s.encode("utf-8"))
print("written", DST)
