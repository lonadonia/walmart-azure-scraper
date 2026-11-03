"""The numbers the 1.5.2 documents quote, read from the final replays' exports and maps. Reads only.

usage: python -I -X utf8 facts_152.py OUT.json
"""

from __future__ import annotations

import collections
import csv
import json
import sys
from pathlib import Path

A1 = Path("C:/w7/ev152/final_a1")
B3 = Path("C:/w7/ev152/final_b3/export_replay_1_5_2")
CM = Path("C:/w7/ev152/correction_maps_final")
LIVE = Path("C:/w7/evidence/live150")
OLD_B3 = Path("C:/w7/evidence/reprocessing_b3_1_5_1/export_replay_1_5_1")


def load(p: Path):
    return json.loads(p.read_text("utf-8"))


def rows_of(p: Path):
    d = load(p)
    return d["products"] if isinstance(d, dict) else d


def disp(folder: Path, fresh_only: bool):
    rows = load(folder / "field_dispositions.json")
    fresh = {r["url"] for r in rows_of(folder / "products_fresh.json")}
    prods = {r["url"]: r for r in rows_of(folder / "products.json")}
    out: dict = {"upc": collections.Counter(), "weight": collections.Counter()}
    keymap = {}
    for u in prods:
        keymap[u] = u
    fresh_keys = {f"wm:{u.split('?')[0].rstrip('/').rsplit('/', 1)[-1]}" for u in fresh}
    n = 0
    for r in rows:
        if fresh_only and r["key"] not in fresh_keys:
            continue
        n += 1
        for f in ("upc", "weight"):
            out[f][r[f]["disposition"]] += 1
    return {"rows": n, "upc": dict(out["upc"].most_common()), "weight": dict(out["weight"].most_common())}


def summary(folder: Path):
    fresh, kept = rows_of(folder / "products_fresh.json"), rows_of(folder / "products.json")
    def side(rows):
        return {
            "rows": len(rows),
            "upc_filled": sum(1 for r in rows if r["upc"]),
            "upc_blank": sum(1 for r in rows if not r["upc"]),
            "weight_filled": sum(1 for r in rows if r["weight"]),
            "weight_blank": sum(1 for r in rows if not r["weight"]),
            "store_brand": dict(collections.Counter(r["store_brand"] for r in rows)),
            "ppm_filled": sum(1 for r in rows if r["ppm"]),
            "gupc_filled": sum(1 for r in rows if r["gupc"]),
            "unit_price_filled": sum(1 for r in rows if r["unit_price"]),
            "crawl_dates": dict(collections.Counter(r["crawl_date"] for r in rows)),
        }
    man = load(folder / "manifest.json")
    return {
        "fresh": side(fresh),
        "retained": side(kept),
        "dispositions_fresh": disp(folder, True),
        "dispositions_retained": disp(folder, False),
        "manifest": {k: man[k] for k in man if k in ("mode", "run_id", "record_count", "replayed_record_count")},
    }


def map_summary(name: str):
    return load(CM / f"{name}_CORRECTION_SUMMARY.json")


def main() -> int:
    out = {
        "S6_replay": summary(A1 / "runs" / "S6" / "exports"),
        "S7_replay": summary(A1 / "runs" / "S7" / "exports"),
        "S4_replay": summary(A1 / "runs" / "S4" / "exports"),
        "B3_replay": summary(B3),
        "S6_live_1_5_1": summary(LIVE / "runs" / "S6" / "exports"),
        "B3_replay_1_5_1": summary(OLD_B3),
        "maps": {
            n: {k: v for k, v in map_summary(n).items() if k in ("rows", "by_change_class", "exported_values_changed_by_field", "products_before", "products_after", "replay_run", "source_run")}
            for n in ("S1", "S2", "S3", "S4", "S5a", "S5b_serial", "S5b_parallel", "S6", "S7", "B3_1_5_1_TO_1_5_2")
        },
        "b3_1_4_1": load(CM / "b3_1_4_1_to_1_5_2" / "B3_CORRECTION_SUMMARY.json"),
        "replay_runs": load(A1 / "replay_runs.json"),
        "b3_replay_run": Path("C:/w7/ev152/final_b3/replay_run_id.txt").read_text("utf-8").strip(),
    }
    Path(sys.argv[1]).write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", "utf-8")
    for k in ("S6_replay", "S6_live_1_5_1", "B3_replay", "B3_replay_1_5_1"):
        v = out[k]
        print(k, json.dumps({"fresh": {x: v["fresh"][x] for x in ("rows", "upc_filled", "upc_blank", "weight_filled", "weight_blank", "store_brand")},
                             "retained": {x: v["retained"][x] for x in ("rows", "upc_filled", "upc_blank", "weight_filled", "weight_blank", "store_brand")},
                             "disp_fresh": v["dispositions_fresh"], "disp_retained": v["dispositions_retained"]}))
    print(out["replay_runs"], out["b3_replay_run"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
