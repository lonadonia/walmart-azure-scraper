"""The kinds of difference between the container's replay exports and the workstation's (offline; reads only).

usage: python -I -X utf8 container_diff_kinds_152.py WORKSTATION_RUNS CONTAINER_RUNS OUT.json
For files with the same number of lines, each differing line pair is classed by its JSON key once the ids each replay gives
itself are numbered; files whose line counts differ are reported by count only.
"""
import json, re, sys
from collections import Counter
from pathlib import Path
ULID = re.compile(r"\b01[0-9A-HJKMNP-TV-Z]{24}\b")
STAMP = re.compile(r"\b20\d\d-\d\d-\d\dT\d\d:\d\d:\d\d(\.\d+)?(Z|\+00:00)?\b")
KEY = re.compile(r'^\s*"([^"]+)":')
def norm(text):
    ids = {}
    text = ULID.sub(lambda m: ids.setdefault(m.group(0), f"ID{len(ids)}"), text)
    return STAMP.sub("T", text).splitlines()
a, b, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
report = {}
for sd in sorted(a.iterdir()):
    for name in ("record_map.json", "provenance.json", "manifest.json"):
        la = norm((sd / "exports" / name).read_text("utf-8")); lb = norm((b / sd.name / "exports" / name).read_text("utf-8"))
        if len(la) != len(lb):
            report[f"{sd.name}/{name}"] = {"lines": [len(la), len(lb)]}
            continue
        kinds = Counter()
        for x, y in zip(la, lb):
            if x != y:
                m = KEY.match(x)
                kinds[m.group(1) if m else x.strip()[:40]] += 1
        report[f"{sd.name}/{name}"] = dict(kinds.most_common())
out.write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
for k, v in report.items():
    print(k, json.dumps(v)[:300])
