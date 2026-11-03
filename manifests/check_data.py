"""Check the live product files in data/ (offline, standard library).

Run from anywhere:  python3 manifests/check_data.py

For each file named in data/RUN_SUMMARY.json (runs S6 and S7 of release 1.5.1, S4 of release 1.5.0):
- its SHA-256 and row count are the ones RUN_SUMMARY.json records;
- it is byte for byte the run's own export in evidence/live/runs/<run id>/exports/;
- every row has the 22 fields in order, all strings; gupc and unit_price are empty; zipcode 60085 and one store;
- no item id or URL appears twice; the CSV holds the same rows as the JSON;
- every row is in the run's record_map.json: a fresh row was observed by this run, by the run's own commit; a
  carried row names an earlier run; each row's crawl_date is its record's.
Prints one line per file and ends with PASS or FAIL (exit status 0 or 1). Nothing here makes a request.
"""
from __future__ import annotations

import csv
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
ITEM = re.compile(r"/ip/(?:[^/?]*/)?(\d+)")
FOLDER = {"live/S6_1.5.1/": "data/S6-1.5.1/", "live/S7_1.5.1/": "data/S7-1.5.1/", "live/S4_1.5.0/": "data/S4-1.5.0/"}
problems: list[str] = []


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def repo_path(delivered: str) -> str:
    for a, b in FOLDER.items():
        if delivered.startswith(a):
            return b + delivered[len(a):]
    raise SystemExit(f"no repository folder for {delivered}")


def rows_of(path: Path) -> list[dict[str, str]]:
    if path.suffix == ".json":
        return json.loads(path.read_text("utf-8"))
    text = path.read_bytes().decode("utf-8-sig")
    if next(csv.reader(io.StringIO(text, newline=""))) != FIELDS:
        problems.append(f"{path.name}: CSV header is not the 22 fields in order")
    return [dict(r) for r in csv.DictReader(io.StringIO(text, newline=""))]


summary = json.loads((ROOT / "data/RUN_SUMMARY.json").read_text("utf-8"))
checked = 0
for stage in summary["stages"]:
    delivered = stage.get("delivered_files") or {}
    if not delivered:
        continue
    run, commit = stage["run"], stage["commit"]
    exports = ROOT / "evidence/live/runs" / run / "exports"
    record = {e["url"]: e for e in json.loads((exports / "record_map.json").read_text("utf-8"))["rows"]}
    json_rows: dict[str, list[dict[str, str]]] = {}
    for name, info in sorted(delivered.items()):
        rel = repo_path(name)
        path = ROOT / rel
        data = path.read_bytes()
        rows = rows_of(path)
        mine: list[str] = []
        if sha(data) != info["sha256"]:
            mine.append("SHA-256 differs from RUN_SUMMARY.json")
        if data != (exports / info["copied_from_export"]).read_bytes():
            mine.append(f"not byte for byte the run's exports/{info['copied_from_export']}")
        if len(rows) != info["rows"]:
            mine.append(f"{len(rows)} rows, RUN_SUMMARY.json says {info['rows']}")
        if any(list(r) != FIELDS for r in rows):
            mine.append("a row without the 22 fields in order")
        if any(not isinstance(v, str) for r in rows for v in r.values()):
            mine.append("a value that is not a string")
        if any(r["gupc"] or r["unit_price"] for r in rows):
            mine.append("gupc or unit_price not empty")
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
        if "products_fresh" in name and set(kinds) != {"fresh"}:
            mine.append(f"the fresh file holds {dict(kinds)}")
        if path.suffix == ".json":
            json_rows[name] = rows
        else:
            twin = name[:-4] + ".json"
            if twin in delivered and rows_of(ROOT / repo_path(twin)) != rows:
                mine.append("the CSV does not hold the JSON's rows")
        checked += 1
        status = "ok    " if not mine else "FAIL  "
        print(f"{status}{rel}: {len(rows)} rows, {stage['stage']} run {run} release {stage['release']} "
              f"({commit[:7]}); {', '.join(f'{k} {v}' for k, v in sorted(kinds.items()))}"
              + (f"; {'; '.join(mine)}" if mine else ""))
        problems.extend(f"{rel}: {m}" for m in mine)

if checked != 12:
    problems.append(f"{checked} files checked, 12 expected")
print("FAIL" if problems else "PASS")
sys.exit(1 if problems else 0)
