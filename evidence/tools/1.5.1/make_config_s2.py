"""Stage S2's configuration: a copy of the frozen edition's config folder (C:/w7/live/ed/walmart-oxylabs-1.5.0/config)
in C:/w7/live/config_s2, with one change: collector.yaml's `seeds: []` replaced by the 41 cases of the 1.4.1
reconciliation (11 sponsored-only placements, 30 tile-only variant siblings), the open ones first. Each seed takes
only the item id, the product link and the listing it was named on from the 1.4.1 case file
(walmart-shared-evidence-1.4.1/4_offline_reprocessing/final_1_4_1/sv_cases/SPONSORED_AND_VARIANT_CASES_1_4_1.csv);
everything else is observed again. Every other file is copied byte for byte (SHA-256 compared).
usage: python -I make_config_s2.py
"""

import csv
import hashlib
import shutil
from pathlib import Path

SRC = Path(r"C:\w7\live\ed\walmart-oxylabs-1.5.0\config")
DST = Path(r"C:\w7\live\config_s2")
CASES = Path(
    r"C:\w7\b\sh\walmart-shared-evidence-1.4.1\4_offline_reprocessing\final_1_4_1\sv_cases"
    r"\SPONSORED_AND_VARIANT_CASES_1_4_1.csv"
)
# Open on 2026-10-31 (1.4.1 reconciliation and the VM queues read at 21:11Z): read first.
OPEN_SPONSORED = ["S01", "S03", "S05", "S06", "S08"]
CLOSED_SPONSORED = ["S02", "S04", "S07", "S09", "S10", "S11"]
# V21 was decided by a product page in 1.4.1 and is pending again in both queues; then a spread of identities.
VARIANT_ORDER = ["V21", "V01", "V05", "V13", "V20", "V04", "V09", "V12", "V14", "V19", "V24", "V25"]


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> None:
    if DST.exists():
        raise SystemExit(f"{DST} exists")
    shutil.copytree(SRC, DST)
    for f in SRC.iterdir():
        assert sha(f) == sha(DST / f.name), f
    rows = {r["case"]: r for r in csv.DictReader(open(CASES, encoding="utf-8-sig", newline=""))}
    variants = VARIANT_ORDER + sorted(c for c in rows if c.startswith("V") and c not in VARIANT_ORDER)
    order = OPEN_SPONSORED + CLOSED_SPONSORED + variants
    assert sorted(order) == sorted(rows), "every case once"
    lines = ["      seeds:                       # stage S2: the 41 cases of the 1.4.1 reconciliation, open first"]
    for case in order:
        r = rows[case]
        kind = "sponsored" if r["kind"] == "sponsored_only" else "variant"
        url = r["source_url"].strip()
        assert url.startswith("https://www.walmart.com/ip/"), (case, url)
        lines += [
            f"        - kind: {kind}",
            f"          item_id: \"{r['item_id']}\"",
            f"          url: \"{url}\"",
            f"          listing_id: \"{r['original_listing_id']}\"",
            f"          source: \"{case} of the 1.4.1 reconciliation (SPONSORED_AND_VARIANT_RECONCILIATION.csv), first "
            f"named by run {r['original_run']}\"",
        ]
    y = DST / "collector.yaml"
    text = y.read_bytes().decode("utf-8")
    old = "      seeds: []                    # items an earlier report named, read first: {kind, item_id, url, listing_id}"
    assert text.count(old) == 1, "the seeds line"
    y.write_bytes(text.replace(old, "\n".join(lines)).encode("utf-8"))
    print("written", y, sha(y), "seeds", len(order))


if __name__ == "__main__":
    main()
