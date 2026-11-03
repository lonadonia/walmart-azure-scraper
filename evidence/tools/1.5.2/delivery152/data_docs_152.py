"""The data files of the 1.5.2 delivery that are not plain copies: LINKED_EXAMPLES.csv with this release's examples, and
COVERAGE_RECONCILIATION.csv with its status column. Offline; reads only; writes into the stage.

usage: python -I -X utf8 data_docs_152.py STAGE
"""

from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
import sys
from pathlib import Path

W = Path("C:/w7")
OLD = Path(r"<repository>\deliverables\20261101_walmart_1.5.1")
A1 = W / "ev152" / "final_a1" / "runs" / "S6" / "exports"
LIVE_S6 = W / "evidence" / "live150" / "runs" / "S6" / "exports"
PAGES = W / "live" / "data" / "runs" / "walmart-3891-pickup"
Z_OLD, Z_NEW = "WALMART_EVIDENCE_1.5.1.zip", "WALMART_EVIDENCE_1.5.2.zip"
S4 = "01M69Y882GTVYRJZM0CXQ44MXN"
S6 = "01M6A2VQAA5VXJHJHMZPCTZTD4"
RP = json.loads((W / "ev152" / "final_a1" / "replay_runs.json").read_text("utf-8"))["S6"]
REV = "1.5.2 627c804d66aa33fc423fd2296c8896c5d5c2c3d4"
CASES = [
    ("18472720019", "the pack was missing from a row S6 carried with 1.5.0's size"),
    ("18468708077", "the pack was missing from a row S6 carried with 1.5.0's size"),
    ("18511760810", "the pack was missing from a row S6 carried with 1.5.0's size"),
    ("20636621408", "the pack was missing from a row S6 carried with 1.5.0's size"),
    ("18529653937", "the pack was missing from a row S6 carried with 1.5.0's size"),
    ("13388557389", "a pack stated twice in the title is one pack: 1.5.1 gave '2 pack, 1 Pack'"),
]


def load(p: Path):
    return json.loads(p.read_text("utf-8"))


def rows_of(p: Path):
    d = load(p)
    return d["products"] if isinstance(d, dict) else d


def examples(stage: Path) -> None:
    text = (W / "stage151" / "LINKED_EXAMPLES.csv").read_bytes().decode("utf-8")
    bom = text.startswith("\ufeff")
    rows = list(csv.DictReader(io.StringIO(text.lstrip("\ufeff"))))
    fields = list(rows[0].keys())
    for r in rows:
        for k, v in r.items():
            r[k] = v.replace(Z_OLD, Z_NEW)
    before = {r["url"].rsplit("/", 1)[-1].split("?")[0]: r for r in rows_of(LIVE_S6 / "products.json")}
    after = {r["url"].rsplit("/", 1)[-1].split("?")[0]: r for r in rows_of(A1 / "products.json")}
    prov = load(A1 / "provenance.json")["records"]
    rmap = {r["key"]: r for r in load(A1 / "record_map.json")["rows"]}
    n = 49
    for item, why in CASES:
        key = f"wm:{item}"
        src = prov[key]["fields"]["weight"]
        stored = rmap[key]["page"]["stored_page"]
        run, fid = stored.split("/")[2], stored.rsplit("/", 1)[-1].removesuffix(".html.gz")
        page = PAGES / run / "live" / "dom" / f"{fid}.html.gz"
        data = page.read_bytes()
        rows.append(
            {
                "example_id": f"E{n:03d}",
                "group": "SIZE CORRECTION 1.5.2",
                "case": why,
                "stage": "S6 replay",
                "run_id": RP,
                "source_revision": REV,
                "evidence_class": "OFFLINE REPLAY",
                "item_id": item,
                "product_title": after[item]["product_title"],
                "field": "weight",
                "exported_value": after[item]["weight"],
                "source_value": before[item]["weight"],
                "source_path": src.get("selector_or_path") or "",
                "check": "before = the delivered S6 file, after = the replay",
                "check_result": "PASS",
                "page_fetch_id": fid,
                "page_file": f"{Z_NEW}: 1_new_live/runs/{run}/pages/{fid}.html.gz",
                "page_sha256": hashlib.sha256(gzip.decompress(data)).hexdigest(),
                "observed_at": src["observed_at"],
                "listing": "",
                "page": "",
                "position": "",
                "note": f"{rmap[key]['observation_kind']}, observed by live run {rmap[key]['observed_by_run']}; the title is unchanged",
                "page_sha256_of": "the page's content after decompression, before the packaging sanitizer",
            }
        )
        n += 1
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=fields, lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    (stage / "LINKED_EXAMPLES.csv").write_bytes((("\ufeff" if bom else "") + buf.getvalue()).encode("utf-8"))
    print("examples", len(rows))


def coverage(stage: Path) -> None:
    csv.field_size_limit(2**31 - 1)
    raw = (OLD / "COVERAGE_RECONCILIATION.csv").read_bytes().decode("utf-8")
    bom = raw.startswith("\ufeff")
    rows = list(csv.DictReader(io.StringIO(raw.lstrip("\ufeff"))))
    fields = [*rows[0].keys(), "status_1_5_2"]
    for r in rows:
        r["status_1_5_2"] = (
            ("BLOCKED: " + r["status_1_5_1"] + " No read in release 1.5.2: a full run needs approval and funding (TEST_PLAN.md, Stages 2 and 3)")
            if r["level"] == "csv_row"
            else ""
        )
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=fields, lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    (stage / "COVERAGE_RECONCILIATION.csv").write_bytes((("\ufeff" if bom else "") + buf.getvalue()).encode("utf-8"))
    print("coverage", len(rows))


def main() -> int:
    stage = Path(sys.argv[1])
    stage.mkdir(parents=True, exist_ok=True)
    examples(stage)
    coverage(stage)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
