"""How many exported rows have a size recovered from a saved product page while provenance.json's fields.weight still names
the listing tile's title, per stage and for the offline reprocessing. Read only; no request.
usage: python -I -X utf8 provenance_recovered_scan.py OUT.json
"""

from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

LIVE = Path(r"C:\w7\evidence\live150")
REPROC = Path(r"C:\w7\evidence\reprocessing_b3_1_5_1\export_replay_1_5_1")


def scan(base: Path) -> dict:
    prov = json.loads((base / "provenance.json").read_text("utf-8"))["records"]
    disp = json.loads((base / "field_dispositions.json").read_text("utf-8"))
    tally: collections.Counter[str] = collections.Counter()
    examples = []
    for row in disp:
        if row.get("observation_kind") not in ("fresh", "replayed"):
            continue
        weight = row["weight"]
        if weight["disposition"] != "recovered_from_saved_detail":
            continue
        tally["recovered_size_rows"] += 1
        rec = prov.get(row["key"]) or {}
        spec = (rec.get("fields") or {}).get("weight") or {}
        path = str(spec.get("selector_or_path") or "")
        detail = (rec.get("upc_detail") or {}).get("size") or {}
        if spec.get("source") == "walmart_title" and path.endswith("(none)"):
            tally["fields_weight_names_the_title_rule_none"] += 1
            if len(examples) < 3:
                examples.append({"key": row["key"], "exported": weight["value"], "fields_weight": spec,
                                 "field_dispositions_weight": weight, "upc_detail_size_path": detail.get("path")})
        if "weight" in (rec.get("missing") or {}):
            tally["missing_weight_text_still_present"] += 1
        if detail.get("value") == weight["value"]:
            tally["upc_detail_size_holds_the_same_value"] += 1
    return {"tally": dict(tally), "examples": examples}


def main() -> int:
    runs = json.loads((LIVE / "runs.json").read_text("utf-8"))
    result = {"evidence_class": "OFFLINE (read of the exports; no request)", "stages": {}}
    for stage in runs:
        result["stages"][stage] = scan(LIVE / "runs" / stage / "exports")
    result["stages"]["B3 OFFLINE REPROCESSING on 1.5.1"] = scan(REPROC)
    Path(sys.argv[1]).write_bytes((json.dumps(result, indent=1, ensure_ascii=False) + "\n").encode("utf-8"))
    for name, v in result["stages"].items():
        print(name, v["tally"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
