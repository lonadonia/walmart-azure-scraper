"""Brief section 4: B3's blanks that offline reprocessing could not fill (243 UPCs and 20 weights, from the 662 products), against what
the campaign's product-page reads then established, from each stage's field_dispositions.json. Read only; no request.
A blank that no page read answered stays what it is: not attempted, never "absent from the source".
usage: python -I -X utf8 b3_blanks_after_campaign.py OUT_DIR
"""

from __future__ import annotations

import collections
import csv
import json
import sys
from pathlib import Path

EV = Path(r"C:\w7\evidence\live150")
MAP = Path(r"C:\w7\evidence\reprocessing_b3_1_5_1\reconciliation\B3_FIELD_DISPOSITIONS_662.csv")
FILLED = {"present_in_listing", "recovered_from_saved_detail", "fetched_this_run"}


def item(url: str) -> str:
    return url.split("?", 1)[0].rstrip("/").rsplit("/", 1)[-1]


def main() -> int:
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=False)
    runs = json.loads((EV / "runs.json").read_text("utf-8"))
    seen: dict[str, list[tuple[str, dict]]] = collections.defaultdict(list)
    names: collections.Counter[str] = collections.Counter()
    for stage in runs:
        for row in json.loads((EV / "runs" / stage / "exports" / "field_dispositions.json").read_text("utf-8")):
            if row.get("observation_kind") == "fresh":
                seen[item(row["url"])].append((stage, row))
                names[row["upc"]["disposition"]] += 1
                names[row["weight"]["disposition"]] += 1
    rows = list(csv.DictReader(MAP.open(encoding="utf-8-sig", newline="")))
    result = []
    tally: collections.Counter[str] = collections.Counter()
    for r in rows:
        blank_upc, blank_weight = not r["upc_after"], not r["weight_after"]
        if not blank_upc and not blank_weight:
            continue
        i = r["item_id"]
        entry = {"item_id": i, "product_title": r["product_title"], "category": r["category"], "sub_category": r["sub_category"],
                 "upc_after_reprocessing": r["upc_disposition_after"] if blank_upc else "(filled)",
                 "weight_after_reprocessing": r["weight_disposition_after"] if blank_weight else "(filled)"}
        for field, blank in (("upc", blank_upc), ("weight", blank_weight)):
            if not blank:
                entry.update({f"{field}_campaign_outcome": "", f"{field}_campaign_value": "", f"{field}_campaign_stage": "", f"{field}_campaign_run": "", f"{field}_campaign_page": "", f"{field}_observed_at": "", f"{field}_status_now": "not blank after reprocessing"})
                continue
            hits = seen.get(i, [])
            with_value = [(s, x[field]) for s, x in hits if x[field].get("value")]
            decided = [(s, x[field]) for s, x in hits if x[field]["disposition"] in ("absent_in_source", "unresolved_conflict", "identity_mismatch", "parse_failure", "inaccessible_challenged")]
            if with_value:
                # The read closest to the source: a fetched page or a saved page of the campaign, not a listing's own text.
                s, d = with_value[-1]
                status = "filled by the campaign" if field == "upc" or d["disposition"] != "present_in_listing" else "filled by the listing's own title in a campaign run"
            elif decided:
                s, d = decided[-1]
                status = f"read, no value: {d['disposition']}"
            elif hits:
                s, d = hits[-1]
                status = "seen by the campaign, its page not read within the budget"
            else:
                s, d = "", {}
                status = "not in any listing page the campaign read"
            tally[f"{field}: {status}"] += 1
            entry.update({f"{field}_campaign_outcome": d.get("disposition", ""), f"{field}_campaign_value": d.get("value", ""), f"{field}_campaign_stage": s,
                          f"{field}_campaign_run": d.get("source_run") or (runs[s] if s else ""), f"{field}_campaign_page": d.get("page_fetch_id") or "",
                          f"{field}_observed_at": d.get("observed_at") or "", f"{field}_status_now": status})
        result.append(entry)
    with (out / "B3_BLANKS_AFTER_CAMPAIGN.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(result[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(result)
    summary = {"evidence_class": "LIVE VERIFIED where a campaign page read answered; PENDING otherwise; no request made here",
               "rows": len(result), "tally": dict(sorted(tally.items())), "dispositions_seen_in_campaign_exports": dict(names)}
    (out / "B3_BLANKS_AFTER_CAMPAIGN_SUMMARY.json").write_bytes((json.dumps(summary, indent=1) + "\n").encode("utf-8"))
    print(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
