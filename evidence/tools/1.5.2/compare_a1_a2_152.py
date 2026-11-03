"""Two replays of the same stored pages with the same revision: which export files are identical, and what differs in
the others once the ids and times each replay gives itself are set aside. Reads only.

usage: python -I -X utf8 compare_a1_a2_152.py A B OUT.json
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

a, b, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
ULID = re.compile(r"\b01[0-9A-HJKMNP-TV-Z]{24}\b")
STAMP = re.compile(r"\b20\d\d-\d\d-\d\dT\d\d:\d\d:\d\d(\.\d+)?(Z|\+00:00)?\b")
report: dict = {}
for stage_dir in sorted((a / "runs").iterdir()):
    stage = stage_dir.name
    report[stage] = {}
    for f in sorted((stage_dir / "exports").iterdir()):
        g = b / "runs" / stage / "exports" / f.name
        if not g.exists():
            report[stage][f.name] = "missing in B"
            continue
        x, y = f.read_bytes(), g.read_bytes()
        if x == y:
            report[stage][f.name] = "identical"
            continue
        # The ids of runs and fetches differ by construction; times of the replay itself too. Map each id to its order
        # of first appearance so a wrong link still shows as a difference.
        def norm(t: bytes) -> str:
            seen: dict[str, str] = {}

            def rep(m: re.Match) -> str:
                return seen.setdefault(m.group(0), f"ID{len(seen)}")

            s = ULID.sub(rep, t.decode("utf-8"))
            return s

        nx, ny = norm(x), norm(y)
        if nx == ny:
            report[stage][f.name] = "identical once run and fetch ids are numbered"
            continue
        # Times the replay stamps itself (generated_at, created_at, built on a clock), in JSON files only.
        tx, ty = STAMP.sub("T", nx), STAMP.sub("T", ny)
        if tx == ty:
            # Which stamps differ: only the replay's own clock may.
            lx, ly = nx.splitlines(), ny.splitlines()
            diff = [(p, q) for p, q in zip(lx, ly, strict=False) if p != q]
            report[stage][f.name] = {
                "same once ids are numbered and these lines' times set aside": len(diff),
                "lines": sorted({re.sub(r'":.*', '"', p.strip())[:60] for p, q in diff})[:12],
            }
            continue
        lx, ly = tx.splitlines(), ty.splitlines()
        diff = [(p, q) for p, q in zip(lx, ly, strict=False) if p != q]
        report[stage][f.name] = {"DIFFERS": len(diff), "lines_a": len(lx), "lines_b": len(ly), "first": [(p[:200], q[:200]) for p, q in diff[:3]]}
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(report, indent=1, ensure_ascii=False) + "\n", "utf-8")
summary: dict = {}
for stage, files in report.items():
    for name, v in files.items():
        key = v if isinstance(v, str) else next(iter(v))
        summary.setdefault(key, []).append(f"{stage}/{name}")
for k, v in summary.items():
    print(k, len(v), v[:6] if "identical" not in k else "")
for stage, files in report.items():
    for name, v in files.items():
        if isinstance(v, dict):
            print(stage, name, json.dumps(v, ensure_ascii=False)[:420])
print("sha256 of the S6 products.json:", hashlib.sha256((a / "runs/S6/exports/products.json").read_bytes()).hexdigest())
