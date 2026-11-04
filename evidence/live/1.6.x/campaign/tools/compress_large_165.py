"""Replaces each file larger than 50,000,000 bytes in the given evidence folders by its gzip copy (`<name>.gz`,
deterministic: level 9, no name, mtime 0), so that every published file stays under GitHub's 50 MB warning size and its
100 MB limit. Each folder that has one gets COMPRESSED.csv: the file's path, its size and SHA-256 before compression
(the bytes the run wrote), and the compressed file's path, size and SHA-256. `gzip -dc <name>.gz | sha256sum` gives the
original SHA-256 again. Nothing else changes.

usage: python -I compress_large_165.py FOLDER...
"""

from __future__ import annotations

import csv
import gzip
import hashlib
import json
import sys
from pathlib import Path

LIMIT = 50_000_000


def main() -> int:
    for folder in map(Path, sys.argv[1:]):
        rows = []
        for p in sorted(x for x in folder.rglob("*") if x.is_file()):
            if p.stat().st_size <= LIMIT or p.name.endswith(".gz"):
                continue
            data = p.read_bytes()
            gz = gzip.compress(data, compresslevel=9, mtime=0)
            assert gzip.decompress(gz) == data
            target = p.with_name(p.name + ".gz")
            if target.exists():
                raise SystemExit(f"{target} exists")
            target.write_bytes(gz)
            p.unlink()
            rows.append([p.relative_to(folder).as_posix(), len(data), hashlib.sha256(data).hexdigest(),
                         target.relative_to(folder).as_posix(), len(gz), hashlib.sha256(gz).hexdigest()])
        if rows:
            out = folder / "COMPRESSED.csv"
            if out.exists():
                raise SystemExit(f"{out} exists")
            with out.open("w", newline="", encoding="utf-8") as f:
                w = csv.writer(f, lineterminator="\n")
                w.writerow(["file", "bytes", "sha256", "published_as", "published_bytes", "published_sha256"])
                w.writerows(rows)
        print(json.dumps({"folder": folder.name, "compressed": [r[0] for r in rows],
                          "bytes_before": sum(r[1] for r in rows), "bytes_after": sum(r[4] for r in rows)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
