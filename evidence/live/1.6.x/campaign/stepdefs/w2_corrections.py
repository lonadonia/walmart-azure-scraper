"""W2: the row/field correction table for UPC and size (weight), from the S6 baseline the client reviewed in the 1.5.2
delivery (data/S6-1.5.1/products_retained.csv: S6's export, 706 rows, of which 580 fresh) to the newest export
of this delivery (offline; no request). The columns and files are named for that export's release (1.6.0,
1.6.1, 1.6.2 or 1.6.3, from runs.json); each run of this delivery is named with the release it ran.

For each product row and each of the two fields: the value delivered in 1.5.2 and its live outcome (S6's own
field_dispositions), the value of the 1.6.0 export and its outcome, what changed, and the page the new value rests on:
its run, page fetch, time and source revision, the SHA-256 of the private original (the provider's unsanitized
answer body, as the collector recorded it) and, where the page is published, the public sanitized copy and its
SHA-256. A product of the 1.5.2 dataset absent from the 1.6.0 export keeps its 1.5.2 values ("not in the 1.6.0
export"). Every aggregate is computed from the table's rows.

usage: python -I w2_corrections.py OUT_DIR NEW_EXPORT_DIR PUBLIC_ROOT [PUBLIC_ROOT ...]
"""

import csv
import gzip
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

REPO = Path("C:/w8/repo")
OLD_CSV = REPO / "data/S6-1.5.1/products_retained.csv"
OLD_FRESH = REPO / "data/S6-1.5.1/products_fresh.csv"
OLD_RUN = "01M6A2VQAA5VXJHJHMZPCTZTD4"
# Every run of this delivery and the release it ran (runs.json; L1 and L2 ran 1.6.0, L5 and L6 1.6.2, L7 to L9 1.6.3).
RUNS_JSON = Path(r"C:\w9\evidence\live160\runs.json")
DELIVERY_RUNS = {
    run: (
        "1.6.0" if stage in ("L1", "L2") else "1.6.2" if stage in ("L5", "L6")
        else "1.6.3" if stage in ("L7", "L8", "L9") else "1.6.1"
    )
    for stage, run in json.loads(RUNS_JSON.read_text(encoding="utf-8")).items()
    if stage in ("L1", "L2", "L3", "L2b", "L4r", "L4", "L5", "L6", "L7", "L8", "L9")
}
LIMITS = {
    "budget_deadline_interruption": "the product's own page was not read (a run limit); a later run can read it",
    "not_attempted": "the product's own page was not requested (detail reading off)",
    "absent_in_source": "the product's own page states no value: a source limit, nothing to read again",
    "unresolved_conflict": "the source states two different measures: kept blank, the conflict is listed",
    "blocked": "the page read was refused (a challenge)",
    "request_failed": "the page read failed; it can be read again",
}
OLD_DISP = REPO / f"evidence/live/runs/{OLD_RUN}/exports/field_dispositions.json"
FIELDS = {"upc": "upc", "weight": "size (weight)"}


def item(url: str) -> str:
    return url.split("?", 1)[0].rstrip("/").rsplit("/", 1)[-1]


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def main() -> int:
    out_dir, new_dir = Path(sys.argv[1]), Path(sys.argv[2])
    roots = [Path(p) for p in sys.argv[3:]]
    old_rows = {item(r["url"]): r for r in csv.DictReader(OLD_CSV.open(encoding="utf-8-sig"))}
    s6_fresh = {item(r["url"]) for r in csv.DictReader(OLD_FRESH.open(encoding="utf-8-sig"))}
    old_disp = {d.get("item_id") or d["key"].removeprefix("wm:"): d for d in json.loads(OLD_DISP.read_text("utf-8"))}
    new_rows = {item(r["url"]): r for r in json.loads((new_dir / "products.json").read_text("utf-8"))}
    new_disp = {d.get("item_id") or d["key"].removeprefix("wm:"): d for d in json.loads((new_dir / "field_dispositions.json").read_text("utf-8"))}
    manifest = json.loads((new_dir / "manifest.json").read_text("utf-8"))
    # release 1.6.3: a carried row's recovery from a saved read, when it was withheld (and why)
    withheld = {
        k.removeprefix("wm:"): w
        for k, v in (json.loads((new_dir / "provenance.json").read_text("utf-8")).get("records") or {}).items()
        if isinstance(v, dict) and (w := (v.get("historical") or {}).get("recovery_withheld"))
    }
    new_run = manifest["run_id"]
    rel = DELIVERY_RUNS[new_run]  # the release of the export compared with 1.5.2
    tag = rel.replace(".", "_")
    # The published pages, by page fetch, and the private originals' file hashes, from every RAW_ORIGINALS_MANIFEST.
    public: dict[str, tuple[str, str, str]] = {}
    raw_file: dict[str, str] = {}
    for root in roots:
        for p in root.rglob("*.html.gz"):
            b = p.read_bytes()
            public.setdefault(p.name.split(".", 1)[0], (p.relative_to(root).as_posix(), sha(b), sha(gzip.decompress(b))))
        for m in root.rglob("RAW_ORIGINALS_MANIFEST.csv"):
            for r in csv.DictReader(m.open(encoding="utf-8-sig")):
                name = r["raw_file_on_the_workstation"].rsplit("/", 1)[-1]
                raw_file.setdefault(name.split(".", 1)[0], r["sha256"])
    cols = [
        "item_id", "sub_category", "product_title", "s6_row", "field", "value_1_5_2", "outcome_1_5_2", "reason_1_5_2",
        f"value_{tag}", f"outcome_{tag}", f"reason_{tag}", f"observation_{tag}", "change", "source_path",
        "source_run", "source_revision", "observed_at", "page_fetch_id", "private_original_body_sha256",
        "private_original_file_sha256", "public_copy", "public_copy_file_sha256", "public_copy_body_sha256",
        "evidence_class", "remaining_limitation",
    ]
    rows = []
    for iid, old in sorted(old_rows.items(), key=lambda kv: (kv[1]["sub_category"], kv[0])):
        new = new_rows.get(iid)
        nd = new_disp.get(iid, {})
        od = old_disp.get(iid, {})
        for f in FIELDS:
            ov, nv = old[f], (new or {}).get(f, "")
            o_out = (od.get(f) or {}).get("disposition", "")
            nf = nd.get(f) or {}
            if new is None:
                change = f"not in the {rel} export"
            elif ov == nv:
                change = "unchanged" if ov else "still blank"
            elif not ov:
                change = "filled"
            elif not nv:
                change = "cleared"
            else:
                change = "changed"
            fid = str(nf.get("page_fetch_id") or "")
            pub = public.get(fid, ("", "", ""))
            n_out = nf.get("disposition", "")
            src_run = str(nf.get("source_run") or "")
            if new is None:
                cls = f"HISTORICAL (1.5.1 live, not in the {rel} export)"
            elif n_out == "fetched_detail" and src_run in DELIVERY_RUNS:
                cls = f"LIVE VERIFIED ({DELIVERY_RUNS[src_run]}): the product's own page, read by this delivery"
            elif n_out == "present_in_listing" and src_run in DELIVERY_RUNS:
                cls = f"LIVE VERIFIED ({DELIVERY_RUNS[src_run]}): the listing tile, read by this delivery"
            elif n_out in ("fetched_detail", "recovered_from_saved_detail", "absent_in_source", "unresolved_conflict")                     and fid:
                cls = f"LIVE (an earlier read of the product's own page, run {src_run}, reused)"
            elif nd.get("observation_kind") == "carried_forward":
                cls = "CARRIED (an earlier live run's value; not re-read)"
            else:
                cls = "NOT ESTABLISHED"
            limitation = "" if nv else LIMITS.get(n_out, n_out)
            if not nv and iid in withheld:
                w = withheld[iid]
                read = w.get("read") or {}
                limitation = (
                    f"a saved read of the product's own page (run {read.get('run_id')}, {read.get('requested_at')}) "
                    f"was not used for this carried row: {w.get('reason')} (historical.recovery_withheld); "
                    + limitation
                )
            rows.append(
                {
                    "item_id": iid,
                    "sub_category": old["sub_category"],
                    "product_title": (new or old)["product_title"],
                    "s6_row": "fresh" if iid in s6_fresh else "carried",
                    "field": FIELDS[f],
                    "value_1_5_2": ov,
                    "outcome_1_5_2": o_out,
                    "reason_1_5_2": (od.get(f) or {}).get("reason", ""),
                    f"value_{tag}": nv if new is not None else "",
                    f"outcome_{tag}": n_out,
                    f"reason_{tag}": nf.get("reason", "") or "; ".join(nf.get("conflicts", []) or []),
                    f"observation_{tag}": nd.get("observation_kind", ""),
                    "change": change,
                    "source_path": str(nf.get("path") or "") + (f" (rule {nf['rule']})" if nf.get("rule") else ""),
                    "source_run": nf.get("source_run", ""),
                    "source_revision": nf.get("source_revision", ""),
                    "observed_at": nf.get("observed_at", ""),
                    "page_fetch_id": fid,
                    "private_original_body_sha256": nf.get("body_sha256", ""),
                    "private_original_file_sha256": raw_file.get(fid, ""),
                    "public_copy": pub[0],
                    "public_copy_file_sha256": pub[1],
                    "public_copy_body_sha256": pub[2],
                    "evidence_class": cls,
                    "remaining_limitation": limitation,
                }
            )
    out_dir.mkdir(parents=True, exist_ok=True)
    with (out_dir / f"W2_FIELD_CORRECTIONS_{tag}.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    summary = {
        "from": f"data/S6-1.5.1/products_retained.csv ({len(old_rows)} rows, run {OLD_RUN}, release 1.5.1, as "
        "delivered in 1.5.2)",
        "to": f"the {rel} export of run {new_run} ({len(new_rows)} rows)",
        "s6_fresh_baseline_recomputed": {
            FIELDS[f]: dict(Counter(r["outcome_1_5_2"] for r in rows if r["field"] == FIELDS[f] and r["s6_row"] == "fresh"))
            for f in FIELDS
        },
        "s6_fresh_filled_1_5_2": {
            FIELDS[f]: sum(1 for r in rows if r["field"] == FIELDS[f] and r["s6_row"] == "fresh" and r["value_1_5_2"])
            for f in FIELDS
        },
        f"s6_fresh_filled_{tag}": {
            FIELDS[f]: sum(1 for r in rows if r["field"] == FIELDS[f] and r["s6_row"] == "fresh" and r[f"value_{tag}"])
            for f in FIELDS
        },
        "s6_fresh_changes_by_field": {
            FIELDS[f]: dict(Counter(r["change"] for r in rows if r["field"] == FIELDS[f] and r["s6_row"] == "fresh"))
            for f in FIELDS
        },
        "by_evidence_class": dict(Counter(r["evidence_class"] for r in rows)),
        "changes_by_field": {
            FIELDS[f]: dict(Counter(r["change"] for r in rows if r["field"] == FIELDS[f])) for f in FIELDS
        },
        f"outcome_{tag}_by_field": {
            FIELDS[f]: dict(Counter(r[f"outcome_{tag}"] for r in rows if r["field"] == FIELDS[f])) for f in FIELDS
        },
        "filled_by_outcome": dict(Counter(f"{r['field']} | {r[f"outcome_{tag}"]}" for r in rows if r["change"] == "filled")),
        "still_blank_by_outcome": dict(
            Counter(f"{r['field']} | {r[f"outcome_{tag}"]}" for r in rows if r["change"] == "still blank")
        ),
        "rows_with_a_page_of_the_compared_run": sum(1 for r in rows if r["source_run"] == new_run and r["page_fetch_id"]),
        "rows_with_a_page_of_this_delivery": sum(
            1 for r in rows if r["source_run"] in DELIVERY_RUNS and r["page_fetch_id"]
        ),
        "rows_with_a_public_copy": sum(1 for r in rows if r["public_copy"]),
        "rows_with_a_private_original_hash": sum(1 for r in rows if r["private_original_body_sha256"]),
        "note": f"Computed from W2_FIELD_CORRECTIONS_{tag}.csv. A blank stays blank unless a page states the value; "
        "nothing is inferred.",
    }
    (out_dir / f"W2_SUMMARY_{tag}.json").write_text(json.dumps(summary, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
