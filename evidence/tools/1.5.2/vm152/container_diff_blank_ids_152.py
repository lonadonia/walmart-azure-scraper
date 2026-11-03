"""Second pass of the container comparison: every id blanked (not numbered), so a shifted numbering can neither hide nor
make a difference. The two normalized files are compared by GNU diff, and the differing lines are classed by JSON key:
"<" lines are the workstation's, ">" lines the container's. Offline; reads only.

usage: python -I -X utf8 container_diff_blank_ids_152.py WORKSTATION_RUNS CONTAINER_RUNS TMP_DIR OUT.json
"""

import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

ULID = re.compile(r"\b01[0-9A-HJKMNP-TV-Z]{24}\b")
STAMP = re.compile(r"\b20\d\d-\d\d-\d\dT\d\d:\d\d:\d\d(\.\d+)?(Z|\+00:00)?\b")
KEY = re.compile(r'^[<>] \s*"([^"]+)":')
DIFF = r"C:\Program Files\Git\usr\bin\diff.exe"


def norm(src: Path, dst: Path) -> None:
    dst.write_text(STAMP.sub("T", ULID.sub("ID", src.read_text("utf-8"))), encoding="utf-8", newline="\n")


a, b, tmp, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4])
tmp.mkdir(parents=True, exist_ok=True)
report = {}
for sd in sorted(a.iterdir()):
    for name in ("record_map.json", "provenance.json", "manifest.json"):
        x, y = tmp / f"{sd.name}_ws_{name}", tmp / f"{sd.name}_ct_{name}"
        norm(sd / "exports" / name, x)
        norm(b / sd.name / "exports" / name, y)
        d = subprocess.run([DIFF, str(x), str(y)], capture_output=True, text=True, encoding="utf-8").stdout.splitlines()
        ws, ct = Counter(), Counter()
        for line in d:
            if line[:1] in "<>":
                m = KEY.match(line)
                (ws if line[0] == "<" else ct)[m.group(1) if m else line[2:].strip()[:40]] += 1
        report[f"{sd.name}/{name}"] = {"workstation_lines": dict(ws.most_common()), "container_lines": dict(ct.most_common())}
        x.unlink()
        y.unlink()
out.write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
for k, v in report.items():
    print(k, json.dumps(v)[:600])
