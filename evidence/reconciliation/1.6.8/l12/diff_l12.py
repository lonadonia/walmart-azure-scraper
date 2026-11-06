"""The L12 export as release 1.6.6 published it, against the 1.6.8 replay's export of the same run: every record
matched by its product URL, every field that differs written as one row. No request; files only.

usage: python -I -X utf8 diff_l12.py OLD_PRODUCTS_CSV NEW_PRODUCTS_CSV OUT_CSV OUT_JSON
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import sys
from collections import Counter
from pathlib import Path

CONTRACT = ("zipcode store_name store_location store_logo store_brand category sub_category product_title weight "
            "regular_price sale_price volume_deals_description volume_deals_price digital_deals_description "
            "digital_deals_price image_url url upc gupc ppm unit_price crawl_date").split()
ALWAYS_EMPTY = ("volume_deals_description", "volume_deals_price", "digital_deals_description", "digital_deals_price",
                "gupc", "unit_price")


def load(p: Path) -> tuple[list[str], list[dict[str, str]], str]:
    raw = p.read_bytes()
    rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"), newline="")))
    return list(rows[0].keys()), rows, hashlib.sha256(raw).hexdigest()


def main(old_p: Path, new_p: Path, out_csv: Path, out_json: Path) -> int:
    old_h, old, old_sha = load(old_p)
    new_h, new, new_sha = load(new_p)
    assert old_h == CONTRACT and new_h == CONTRACT, (old_h, new_h)
    ok = {k: [r[k] for r in old] for k in ()}
    del ok
    o = {r["url"]: r for r in old}
    n = {r["url"]: r for r in new}
    assert len(o) == len(old) and len(n) == len(new), "a product URL appears twice"
    diffs, by_field, kinds = [], Counter(), Counter()
    for url in sorted(set(o) | set(n)):
        a, b = o.get(url), n.get(url)
        if a is None or b is None:
            kinds["only_in_" + ("new" if a is None else "old")] += 1
            diffs.append({"url": url, "field": "(record)", "old": "" if a is None else "present",
                          "new": "" if b is None else "present"})
            continue
        for f in CONTRACT:
            if a[f] != b[f]:
                by_field[f] += 1
                diffs.append({"url": url, "field": f, "old": a[f], "new": b[f]})
    buf = io.StringIO(newline="")
    w = csv.DictWriter(buf, fieldnames=["url", "field", "old", "new"], lineterminator="\n")
    w.writeheader()
    w.writerows(diffs)
    out_csv.write_bytes(buf.getvalue().encode("utf-8"))
    renames = Counter((d["old"], d["new"]) for d in diffs if d["field"] == "sub_category")
    summary = {
        "old": {"file": old_p.name, "sha256": old_sha, "records": len(old)},
        "new": {"file": new_p.name, "sha256": new_sha, "records": len(new)},
        "records_matched_by_url": len(set(o) & set(n)),
        "records_only_in_one": dict(kinds),
        "changed_fields": dict(sorted(by_field.items())),
        "sub_category_renames": [{"old": a, "new": b, "records": c} for (a, b), c in renames.most_common()],
        "upc_changes": [d for d in diffs if d["field"] == "upc"],
        "always_empty_fields_non_empty": {f: sum(1 for r in new if r[f]) for f in ALWAYS_EMPTY},
        "contract_header_equal": True,
    }
    out_json.write_bytes((json.dumps(summary, indent=1, ensure_ascii=False) + "\n").encode("utf-8"))
    print(json.dumps({k: summary[k] for k in ("records_matched_by_url", "records_only_in_one", "changed_fields",
                                              "always_empty_fields_non_empty")}))
    print(json.dumps(summary["sub_category_renames"][:12], ensure_ascii=False))
    print(json.dumps(summary["upc_changes"], ensure_ascii=False)[:1200])
    return 0


if __name__ == "__main__":
    raise SystemExit(main(*(Path(a) for a in sys.argv[1:5])))
