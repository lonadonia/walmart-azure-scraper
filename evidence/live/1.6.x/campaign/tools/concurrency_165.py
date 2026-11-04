"""Serial and parallel measurements of this delivery's live runs (offline; reads the published evidence CSVs): per run,
its workers, active execution time, provider submissions by purpose with their elapsed time (median, p90), and
the throughput (successful page fetches per active minute). Writes CONCURRENCY_MEASURED_1_6_5.csv and prints a JSON
summary. Each run's release is the one its own database row records (`db/runs.csv`, `parser_version`).
concurrency_164.py took it from a table of labels instead, and gave L11 and L11b (release 1.6.5) its default, 1.6.1.

usage: python -I concurrency_165.py RUNS_DIR OUT_CSV
"""

from __future__ import annotations

import csv
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

def rows(p: Path) -> list[dict[str, str]]:
    with p.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def pct(xs: list[float], q: float) -> float:
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(round(q * (len(xs) - 1))))]


def main(argv: list[str]) -> int:
    runs_dir, out = Path(argv[0]), Path(argv[1])
    table = []
    for d in sorted(p for p in runs_dir.iterdir() if p.is_dir()):
        label, run_id = d.name.split("_", 1)
        [run_row] = rows(d / "db" / "runs.csv")
        if run_row["id"] != run_id or not run_row["parser_version"]:
            raise SystemExit(f"{d.name}: its runs.csv names {run_row['id']}")
        segs = rows(d / "db" / "collection_segments.csv")
        usage = rows(d / "db" / "provider_usage.csv")
        fetches = rows(d / "db" / "page_fetches.csv")
        active = sum(float(s["active_s"] or 0) for s in segs)
        workers = sorted({int(s["workers"]) for s in segs if s["workers"]})
        by_purpose: dict[str, list[dict[str, str]]] = defaultdict(list)
        for u in usage:
            by_purpose[u["purpose"]].append(u)
        ok_fetches = [f for f in fetches if f["http_status"] == "200"]
        for purpose, us in sorted(by_purpose.items()):
            el = [float(u["elapsed_ms"]) / 1000 for u in us if u["elapsed_ms"]]
            table.append(
                {
                    "run_label": label,
                    "run_id": run_id,
                    "release": run_row["parser_version"],
                    "workers": ";".join(map(str, workers)),
                    "executions": len(segs),
                    "active_s": round(active, 1),
                    "purpose": purpose,
                    "submissions": len(us),
                    "outcomes": ";".join(f"{k}={v}" for k, v in sorted(
                        {o: sum(1 for u in us if u["outcome"] == o) for o in {u["outcome"] for u in us}}.items())),
                    "elapsed_median_s": round(statistics.median(el), 1) if el else "",
                    "elapsed_p90_s": round(pct(el, 0.9), 1) if el else "",
                    "run_pages_ok": len(ok_fetches),
                    "run_pages_ok_per_active_minute": round(len(ok_fetches) / (active / 60), 2) if active else "",
                }
            )
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(table[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(table)
    summary: dict[str, dict] = {}
    for r in table:
        s = summary.setdefault(r["run_label"], {"workers": r["workers"], "executions": r["executions"],
                                                "active_min": round(r["active_s"] / 60, 1),
                                                "pages_ok": r["run_pages_ok"],
                                                "pages_ok_per_active_min": r["run_pages_ok_per_active_minute"],
                                                "purposes": {}})
        s["purposes"][r["purpose"]] = {"n": r["submissions"], "median_s": r["elapsed_median_s"],
                                       "p90_s": r["elapsed_p90_s"]}
    print(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
