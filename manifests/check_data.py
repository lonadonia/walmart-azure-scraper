"""Check the live product files of this repository (offline, standard library).

Run from anywhere:  python3 manifests/check_data.py

1. For each file data/RUN_SUMMARY.json delivers in data/ (the 1.5.x stages S4, S6 and S7; the 1.6.x runs L8 and L10):
   - its SHA-256 and row count are the ones RUN_SUMMARY.json records;
   - it is byte for byte the run's own export (the stage's "exports" folder);
   - every row has the 22 fields in order, all strings; gupc and unit_price are empty; store_logo is filled;
     zipcode 60085 and one store;
   - no item id or URL appears twice; the CSV holds the same rows as the JSON;
   - every row is in the run's record_map.json: a fresh row was observed by this run, by the run's own commit; a
     carried row names an earlier run; each row's crawl_date is its record's. An evidence file over 50 MB is
     published gzip-compressed (record_map.json.gz, listed in the run folder's COMPRESSED.csv); it is read
     decompressed, after its SHA-256 is checked against the one COMPRESSED.csv records for the original.
2. For every 1.6.x run in RUN_SUMMARY.json, delivered or not: every row of each of its four exports
   (products_fresh.json/.csv, products.json/.csv) has the 22 fields in order, all strings, and the four deal fields
   (volume_deals_description, volume_deals_price, digital_deals_description, digital_deals_price) are "", as the
   client's clarification requires from release 1.6.0. The 1.5.x files were made under the earlier rule and are not
   edited; they are not held to it.
Prints one line per file or run and ends with PASS or FAIL (exit status 0 or 1). Nothing here makes a request.
"""
from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIELDS = ["zipcode", "store_name", "store_location", "store_logo", "store_brand", "category", "sub_category",
          "product_title", "weight", "regular_price", "sale_price", "volume_deals_description", "volume_deals_price",
          "digital_deals_description", "digital_deals_price", "image_url", "url", "upc", "gupc", "ppm", "unit_price",
          "crawl_date"]
DEALS = ["volume_deals_description", "volume_deals_price", "digital_deals_description", "digital_deals_price"]
EXPORTS = ["products_fresh.json", "products_fresh.csv", "products.json", "products.csv"]
ITEM = re.compile(r"/ip/(?:[^/?]*/)?(\d+)")
problems: list[str] = []


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def rows_of(path: Path, mine: list[str]) -> list[dict[str, str]]:
    if path.suffix == ".json":
        return json.loads(path.read_text("utf-8"))
    text = path.read_bytes().decode("utf-8-sig")
    if next(csv.reader(io.StringIO(text, newline=""))) != FIELDS:
        mine.append("CSV header is not the 22 fields in order")
    return [dict(r) for r in csv.DictReader(io.StringIO(text, newline=""))]


def export_bytes(exports: Path, name: str) -> bytes:
    """An export file as the run wrote it: the file itself or, when it was over 50 MB, its gzip copy, whose
    decompressed SHA-256 must be the one the run folder's COMPRESSED.csv records."""
    plain = exports / name
    if plain.is_file():
        return plain.read_bytes()
    gz = exports / (name + ".gz")
    data = gzip.decompress(gz.read_bytes())
    listed = {r["file"]: r for r in csv.DictReader((exports.parent / "COMPRESSED.csv").open(encoding="utf-8"))}
    entry = listed.get(f"{exports.name}/{name}")
    if entry is None or entry["sha256"] != sha(data) or int(entry["bytes"]) != len(data):
        problems.append(f"{gz.relative_to(ROOT).as_posix()}: not the original COMPRESSED.csv records")
    return data


def contract(rows: list[dict[str, str]], mine: list[str], deals: bool) -> None:
    if any(list(r) != FIELDS for r in rows):
        mine.append("a row without the 22 fields in order")
    if any(not isinstance(v, str) for r in rows for v in r.values()):
        mine.append("a value that is not a string")
    if any(r.get("gupc") or r.get("unit_price") for r in rows):
        mine.append("gupc or unit_price not empty")
    if deals:
        bad = sum(1 for r in rows if any(r.get(f) for f in DEALS))
        if bad:
            mine.append(f"{bad} rows with a deal field that is not empty")


summary = json.loads((ROOT / "data/RUN_SUMMARY.json").read_text("utf-8"))
checked = 0
expected = 0
runs_checked = 0
for stage in summary["stages"]:
    run, commit, release = stage["run"], stage["commit"], stage["release"]
    exports = ROOT / stage["exports"]
    new_rule = release.startswith("1.6")
    delivered = stage.get("delivered_files") or {}
    expected += len(delivered)
    if delivered:
        record = {e["url"]: e for e in json.loads(export_bytes(exports, "record_map.json").decode("utf-8"))["rows"]}
    for rel, info in sorted(delivered.items()):
        path = ROOT / rel
        data = path.read_bytes()
        mine: list[str] = []
        rows = rows_of(path, mine)
        if sha(data) != info["sha256"]:
            mine.append("SHA-256 differs from RUN_SUMMARY.json")
        if data != (exports / info["copied_from_export"]).read_bytes():
            mine.append(f"not byte for byte the run's exports/{info['copied_from_export']}")
        if len(rows) != info["rows"]:
            mine.append(f"{len(rows)} rows, RUN_SUMMARY.json says {info['rows']}")
        contract(rows, mine, new_rule)
        if any(not r.get("store_logo") for r in rows):
            mine.append("a row without store_logo")
        if {r["zipcode"] for r in rows} != {"60085"} or len({r["store_location"] for r in rows}) != 1:
            mine.append("zipcode or store not the single store's")
        ids = [m.group(1) if (m := ITEM.search(r["url"])) else "" for r in rows]
        if "" in ids or len(set(ids)) != len(ids) or len({r["url"] for r in rows}) != len(rows):
            mine.append("an item id or URL missing or repeated")
        kinds: Counter[str] = Counter()
        for r in rows:
            e = record.get(r["url"])
            if e is None:
                mine.append(f"row not in record_map.json: {r['url']}")
                break
            kinds[e["observation_kind"]] += 1
            if e["crawl_date"] != r["crawl_date"]:
                mine.append(f"crawl_date differs from its record: {r['url']}")
                break
            fresh = e["observation_kind"] == "fresh"
            if fresh and (e["observed_by_run"] != run or e["code"]["commit"] != commit):
                mine.append(f"a fresh row not observed by this run and commit: {r['url']}")
                break
            if not fresh and e["observed_by_run"] == run:
                mine.append(f"a carried row names this run: {r['url']}")
                break
        if "products_fresh" in rel and set(kinds) != {"fresh"}:
            mine.append(f"the fresh file holds {dict(kinds)}")
        if path.suffix == ".csv":
            twin = rel[:-4] + ".json"
            if twin in delivered and rows_of(ROOT / twin, []) != rows:
                mine.append("the CSV does not hold the JSON's rows")
        checked += 1
        status = "ok    " if not mine else "FAIL  "
        print(f"{status}{rel}: {len(rows)} rows, {stage['stage']} run {run} release {release} "
              f"({commit[:7]}); {', '.join(f'{k} {v}' for k, v in sorted(kinds.items()))}"
              + (f"; {'; '.join(mine)}" if mine else ""))
        problems.extend(f"{rel}: {m}" for m in mine)
    if new_rule:
        mine = []
        counts = []
        for name in EXPORTS:
            p = exports / name
            if not p.is_file():
                mine.append(f"no exports/{name}")
                continue
            rows = rows_of(p, mine)
            contract(rows, mine, True)
            counts.append(f"{name} {len(rows)}")
        runs_checked += 1
        status = "ok    " if not mine else "FAIL  "
        print(f"{status}{stage['exports']}: {stage['stage']} release {release}: {', '.join(counts)}; 22 fields, "
              f"strings, deal fields \"\"" + (f"; {'; '.join(mine)}" if mine else ""))
        problems.extend(f"{stage['exports']}: {m}" for m in mine)

if checked != expected or checked != summary.get("files_delivered"):
    problems.append(f"{checked} delivered files checked, RUN_SUMMARY.json lists {summary.get('files_delivered')}")
print(f"{checked} delivered files and the exports of {runs_checked} 1.6.x runs checked")
print("FAIL" if problems else "PASS")
sys.exit(1 if problems else 0)
