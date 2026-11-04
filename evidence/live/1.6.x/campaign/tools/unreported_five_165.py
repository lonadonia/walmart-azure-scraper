"""The 26 records L10 (release 1.6.4) read from its flat-layout page (fetch 01M6KB69AJA2N65MDQP4V1QWTE) are those of
the 1.6.5 capture's `l10_records.json`. Release 1.6.4's validate-export reported 21 of them. This reads, with the
running release's own source check (`compare`), every placement of the other 5 on every page stored by the runs up to
L10 (the pages L10's validation reads), and names the placements whose every field equals the record.

usage: <edition python> -I unreported_five_165.py OUT.json
"""

import gzip
import json
import sys
from pathlib import Path

import walmart_headless
from walmart_headless.checks import source_check as sc

ROOT = Path(r"C:\w9\live\data\runs\walmart-3891-pickup")
CAP = Path(r"C:\w9\wt\headless\walmart-azure-headless\tests\captures\listing_pages_20261104_flat")
LABELS = {v: k for k, v in json.loads(Path(r"C:\w9\evidence\live160\runs.json").read_text(encoding="utf-8")).items()}
L10, FLAT = "01M6KA3CKYJSD6WDY4TDAAV73Y", "01M6KB69AJA2N65MDQP4V1QWTE"
REPORTED = {sc.item_id_of(m["url"]) for m in json.loads(
    Path(r"C:\w9\evidence\verification165\l10_source_mismatches_1_6_4.json").read_text(encoding="utf-8"))["mismatches"]}
recs = {sc.item_id_of(r["url"]): r for r in json.loads((CAP / "l10_records.json").read_text(encoding="utf-8"))}
five = sorted(set(recs) - REPORTED)
assert len(recs) == 26 and len(REPORTED & set(recs)) == 21 and len(five) == 5
out = {i: {"placements": 0, "all_fields_equal_on": []} for i in five}
for run_dir in sorted(p for p in ROOT.iterdir() if (p / "live" / "dom").is_dir() and p.name <= L10):
    for p in sorted((run_dir / "live" / "dom").glob("*.html.gz")):
        raw = gzip.decompress(p.read_bytes()).decode("utf-8", "replace")
        hits = [i for i in five if i in raw]
        nd = sc.page_json(p) if hits else None
        if nd is None:
            continue
        for path, it in sc.items_of(nd):
            i = str(it.get("usItemId"))
            if i not in hits:
                continue
            out[i]["placements"] += 1
            if all(sc.compare(recs[i], it)[0].values()):
                out[i]["all_fields_equal_on"].append({"run": LABELS.get(run_dir.name, run_dir.name), "run_id": run_dir.name,
                                                     "fetch": p.name.removesuffix(".html.gz"), "json_path": path,
                                                     "flat_layout_page": p.name.startswith(FLAT)})
result = {"release": walmart_headless.__version__, "records_read_from_the_flat_page": 26, "reported_by_1_6_4": 21,
          "not_reported": out}
Path(sys.argv[1]).write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8")
print(json.dumps({i: [(e["run"], e["fetch"][-8:], e["flat_layout_page"]) for e in v["all_fields_equal_on"]] for i, v in out.items()}))
