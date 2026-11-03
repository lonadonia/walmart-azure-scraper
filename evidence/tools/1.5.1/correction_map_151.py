"""Before/after correction map and the per-product field-disposition report of Oxylabs B3 (brief sections 4 and 10).

Before: B3's own export (run 01M60V2DCCWR72BGVVG3EM9R74, release 1.4.1, commit 37ffca8, LIVE, 2026-10-28) and
its field dispositions as release 1.5.1 reads them (field-dispositions --run B3 at 488a033). After: the OFFLINE
REPROCESSING replay of B3's stored pages with release 1.5.1 (reprocessing attempt 3, the run id in
C:/w7/evidence/reprocessing_b3_1_5_1/replay_run_id.txt) and its field dispositions. Rows are matched by Walmart item id (each export has no duplicate item). No value is edited here:
every "after" value is the replay's export, every "before" value B3's.

Writes into OUT (must not exist):
  B3_FIELD_DISPOSITIONS_662.csv / .json   one row per B3 fresh product: UPC and weight before and after, with
                                          each side's disposition, source run, observation time and reason,
                                          and the saved product pages of the item (the capture index)
  B3_CORRECTION_MAP.csv                   every field of the 22 whose value differs, per product (all 862 rows)
  B3_CORRECTION_SUMMARY.json              counts
usage: <collector venv python> -I correction_map.py OUT
"""

import collections
import csv
import io
import json
import sys
from pathlib import Path

sys.path.insert(0, "C:/w7/wt/headless/walmart-azure-headless/src")
from walmart_headless.sites.walmart import page_data as wpd  # noqa: E402

B3 = "01M60V2DCCWR72BGVVG3EM9R74"
BASE = Path("C:/w7/evidence/reprocessing_b3_1_5_1")
RP = (BASE / "replay_run_id.txt").read_text().strip()  # attempt 3 (attempt 2: 01M69VW87SFVSADMJJTGG8ZGR3 on 1.5.0)
B3_START = "2026-10-28T08:47:16.914249Z"
SRC_EXP = Path("C:/w7/reproc/data/runs/walmart-3891-pickup") / B3 / "exports"
RP_EXP = BASE / "export_replay_1_5_1"
SRC_DISP = BASE / "logs" / "16_field_dispositions_source.jsonl"
INDEX = Path("C:/w7/b/detail_capture_index_150.json")
FIELDS = (
    "zipcode store_name store_location store_logo store_brand category sub_category product_title weight "
    "regular_price sale_price volume_deals_description volume_deals_price digital_deals_description "
    "digital_deals_price image_url url upc gupc ppm unit_price crawl_date"
).split()


def rows_of(path: Path) -> list[dict]:
    d = json.loads(path.read_text(encoding="utf-8"))
    return d["products"] if isinstance(d, dict) else d


def disp_rows_from_log(path: Path) -> list[dict]:
    for line in path.read_text(encoding="utf-8").splitlines()[::-1]:
        if '"event": "RESULT"' in line:
            res = json.loads(line)["result"]
            return res["rows"]
    raise SystemExit(f"no RESULT line in {path}")


def by_item(rows: list[dict], key: str = "url") -> dict[str, dict]:
    out = {}
    for r in rows:
        item = wpd.item_id_from_url(r[key])
        if item in out:
            raise SystemExit(f"duplicate item {item}")
        out[item] = r
    return out


def main() -> None:
    out = Path(sys.argv[1])
    if out.exists():
        raise SystemExit(f"{out} exists: never overwritten")
    out.mkdir(parents=True)
    before = by_item(rows_of(SRC_EXP / "products.json"))
    after = by_item(rows_of(RP_EXP / "products.json"))
    fresh_before = by_item(rows_of(SRC_EXP / "products_fresh.json"))
    d_before = by_item(disp_rows_from_log(SRC_DISP))
    rp_disp = json.loads((RP_EXP / "field_dispositions.json").read_text(encoding="utf-8"))
    d_after = by_item(rp_disp["rows"] if isinstance(rp_disp, dict) else rp_disp)
    pages: dict[str, list[dict]] = collections.defaultdict(list)
    for e in json.loads(INDEX.read_text(encoding="utf-8")):
        pages[e["item_id"]].append(e)
    if set(before) != set(after):
        raise SystemExit(f"item sets differ: {len(set(before) ^ set(after))} items")

    # 1. The correction map: every field whose value differs, for all 862 rows.
    cm = io.StringIO()
    w = csv.writer(cm, lineterminator="\n")
    w.writerow(["item_id", "observation_kind_after", "field", "before_B3_1.4.1", "after_replay_1.5.1", "change",
                "evidence_after"])
    changes = collections.Counter()
    for item in sorted(before, key=int):
        b, a, da = before[item], after[item], d_after[item]
        for f in FIELDS:
            if b[f] == a[f]:
                continue
            change = "filled" if not b[f] else "cleared" if not a[f] else "changed"
            changes[(f, change)] += 1
            ev = ""
            if f in ("upc", "weight"):
                x = da[f]
                ev = (f"{x['disposition']}; source_run {x.get('source_run') or ''}; observed_at "
                      f"{x.get('observed_at') or ''}; {x.get('reason') or ''}").strip("; ")
            else:
                ev = f"release 1.5.1 reading of the stored result page of {a.get('crawl_date')}"
            w.writerow([item, da.get("observation_kind"), f, b[f], a[f], change, ev])
    (out / "B3_CORRECTION_MAP.csv").write_bytes(("\ufeff" + cm.getvalue()).encode("utf-8"))

    # 2. The per-product report of B3's 662 fresh products.
    cols = ["item_id", "product_title", "category", "sub_category", "url"]
    for f in ("upc", "weight"):
        cols += [f"{f}_before", f"{f}_disposition_before", f"{f}_reason_before", f"{f}_after",
                 f"{f}_disposition_after", f"{f}_source_run_after", f"{f}_observed_at_after", f"{f}_reason_after",
                 f"{f}_change"]
    cols += ["saved_pages", "saved_pages_before_B3_start", "saved_page_runs", "saved_page_first_observed",
             "saved_page_last_observed", "live_detail_candidate"]
    report, counts = [], collections.Counter()
    for item in sorted(fresh_before, key=int):
        b, a, db, da = before[item], after[item], d_before[item], d_after[item]
        row = {"item_id": item, "product_title": a["product_title"], "category": a["category"],
               "sub_category": a["sub_category"], "url": a["url"]}
        for f in ("upc", "weight"):
            xb, xa = db[f], da[f]
            change = "same" if b[f] == a[f] else ("filled" if not b[f] else "cleared" if not a[f] else "changed")
            row.update({
                f"{f}_before": b[f], f"{f}_disposition_before": xb["disposition"],
                f"{f}_reason_before": xb.get("reason") or "",
                f"{f}_after": a[f], f"{f}_disposition_after": xa["disposition"],
                f"{f}_source_run_after": xa.get("source_run") or "",
                f"{f}_observed_at_after": xa.get("observed_at") or "",
                f"{f}_reason_after": xa.get("reason") or "", f"{f}_change": change,
            })
            counts[(f, "before", "blank" if not b[f] else "filled")] += 1
            counts[(f, "after", "blank" if not a[f] else "filled")] += 1
            counts[(f, "disposition_before", xb["disposition"])] += 1
            counts[(f, "disposition_after", xa["disposition"])] += 1
            counts[(f, "change", change)] += 1
            if not b[f]:
                counts[(f, "blank_before_now", xa["disposition"])] += 1
        ps = pages.get(item, [])
        ats = sorted(p["observed_at"] for p in ps)
        before_start = [p for p in ps if p["observed_at"].replace("+00:00", "Z") < B3_START]
        need = (not a["upc"] and da["upc"]["disposition"] == "not_attempted") or (
            not a["weight"] and da["weight"]["disposition"] == "not_attempted")
        row.update({
            "saved_pages": len(ps), "saved_pages_before_B3_start": len(before_start),
            "saved_page_runs": " ".join(sorted({p["run_id"] for p in ps})),
            "saved_page_first_observed": ats[0] if ats else "", "saved_page_last_observed": ats[-1] if ats else "",
            "live_detail_candidate": "yes" if need else "no",
        })
        counts[("live_detail_candidate", need)] += 1
        report.append(row)
    rb = io.StringIO()
    w = csv.DictWriter(rb, fieldnames=cols, lineterminator="\n")
    w.writeheader()
    w.writerows(report)
    (out / "B3_FIELD_DISPOSITIONS_662.csv").write_bytes(("\ufeff" + rb.getvalue()).encode("utf-8"))
    label = ("OFFLINE REPROCESSING of authentic live run 01M60V2DCCWR72BGVVG3EM9R74 (Oxylabs Web API, store 3891, "
             "PICKUP, release 1.4.1 commit 37ffca808f2163287e3d50b91529c5fd69213418, 2026-10-28): replay run "
             f"{RP} with release 1.5.1 commit 488a033; no request was made")
    (out / "B3_FIELD_DISPOSITIONS_662.json").write_text(
        json.dumps({"evidence_class": "OFFLINE REPROCESSING", "label": label, "rows": report}, indent=1) + "\n",
        encoding="utf-8", newline="\n")
    summary = {
        "evidence_class": "OFFLINE REPROCESSING",
        "label": label,
        "products_fresh_B3": len(fresh_before),
        "rows_all": len(before),
        "fresh_662": {"|".join(map(str, k)): v for k, v in sorted(counts.items(), key=lambda kv: str(kv[0]))},
        "field_changes_all_862": {f"{f}|{c}": n for (f, c), n in sorted(changes.items())},
    }
    (out / "B3_CORRECTION_SUMMARY.json").write_text(json.dumps(summary, indent=1) + "\n", encoding="utf-8",
                                                    newline="\n")
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
