"""HISTORICAL_REFERENCES.csv for the 1.5.1 evidence: earlier deliveries and sources this release relies on, by path and SHA-256 (offline; reads them, changes nothing).
Not copied: their files are named so they can be opened and checked. "listed_in" says whether the file is on that delivery's own SHA256SUMS.txt with the same hash.
usage: python -I -X utf8 historical_refs_151.py OUT.csv
"""

from __future__ import annotations

import csv
import hashlib
import sys
from pathlib import Path

DEL = Path(r"<repository>\deliverables")
D141 = "20261028_walmart_1.4.1_dual_provider"
REFS = [
    # path below deliverables/, the delivery whose SHA256SUMS lists it, its name there, what this release used it for
    (f"{D141}/SHA256SUMS.txt", "", "", "the client-reviewed baseline: release 1.4.1, source revision 37ffca808f2163287e3d50b91529c5fd69213418"),
    (f"{D141}/ACCEPTANCE_MATRIX.csv", D141, "ACCEPTANCE_MATRIX.csv", "the 109 requirement rows carried into this delivery's matrix"),
    ("walmart_oxylabs/WALMART_OXYLABS_EVIDENCE_1.4.1.zip", D141, "oxylabs/WALMART_OXYLABS_EVIDENCE_1.4.1.zip", "saved pages of runs B1, B3 and others: the captures reprocessed offline and imported for reuse"),
    ("walmart_oxylabs/WALMART_OXYLABS_SOURCE_1.4.1.zip", D141, "oxylabs/WALMART_OXYLABS_SOURCE_1.4.1.zip", "the source the client reviewed"),
    ("walmart_oxylabs/products_fresh.json", D141, "oxylabs/products_fresh.json", "the B3 product file, the 'before' side of the correction map"),
    ("walmart_oxylabs/products_retained.json", D141, "oxylabs/products_retained.json", "the retained file of B3"),
    ("walmart_scrapedo/WALMART_SCRAPEDO_EVIDENCE_1.4.1.zip", D141, "scrapedo/WALMART_SCRAPEDO_EVIDENCE_1.4.1.zip", "saved pages of the Scrape.do runs, imported for reuse; the Scrape.do demonstration on 1.4.1"),
    ("walmart_scrapedo/WALMART_SCRAPEDO_SOURCE_1.4.1.zip", D141, "scrapedo/WALMART_SCRAPEDO_SOURCE_1.4.1.zip", "the source of the Scrape.do edition on 1.4.1"),
    (f"{D141}/shared/WALMART_SHARED_EVIDENCE_1.4.1.zip", D141, "shared/WALMART_SHARED_EVIDENCE_1.4.1.zip", "historical live pages imported for reuse; the 1.4.1 Azure test"),
    ("20261027_walmart_1.3.1/SHA256SUMS.txt", "", "", "release 1.3.1, the Azure VM run of 2026-10-26 on release 1.3.0"),
    ("20261024_walmart_1.2.1/SHA256SUMS.txt", "", "", "release 1.2.1: the source of the 41 reopened sponsored and variant cases"),
]


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    rows = []
    for rel, delivery, name, why in REFS:
        p = DEL / rel
        digest = sha(p)
        listed = ""
        if delivery:
            sums = {ln.split("  ", 1)[1]: ln.split("  ", 1)[0] for ln in (DEL / delivery / "SHA256SUMS.txt").read_text("utf-8").splitlines() if "  " in ln}
            listed = "same hash" if sums.get(name) == digest else "DIFFERS"
            if listed == "DIFFERS":
                raise SystemExit(f"{rel} differs from {delivery}/SHA256SUMS.txt")
            listed = f"{delivery}/SHA256SUMS.txt lists {name}: {listed}"
        rows.append({"path_below_deliverables": rel, "sha256": digest, "bytes": p.stat().st_size, "checked_against": listed, "used_for": why})
    rows.append({"path_below_deliverables": "(not delivered) database dump of the Azure VM, walmart_oxylabs-20261031T202648Z.dump", "sha256": "61c6e346e7ed9fbf53f99ad259af1340b2729043934701441cb1c1e7d0013c64", "bytes": "", "checked_against": "restored for the offline reprocessing; row counts equal to the VM's (2_offline_reprocessing/b3_on_1_5_1/00_restore.txt)", "used_for": "the state B3 was reprocessed from; the VM's follow-up queues"})
    with open(sys.argv[1], "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    print(len(rows), "references")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
