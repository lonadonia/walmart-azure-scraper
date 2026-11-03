"""THIRD_PARTY_LICENSES.csv: every distribution the Walmart collector's lockfile (uv.lock) installs, with its licence as its own
installed metadata states it, read offline from a clean environment installed from that lock. Read only; no request.

`used_in` follows the lock's dependency graph, extras included ("psycopg[binary]" brings psycopg-binary): "runtime" is reachable from the
project's own dependencies, "tests and checks only" only from its development group.

usage: <python of an environment installed from the lock> -I -X utf8 licenses_151.py UV_LOCK OUT.csv
"""

from __future__ import annotations

import csv
import importlib.metadata as md
import sys
import tomllib
from collections import Counter
from pathlib import Path
from typing import Any

PROJECT = "walmart-azure-headless"


def closure(packages: dict[str, dict[str, Any]], deps: list[dict[str, Any]]) -> set[str]:
    """Every package reachable from these dependency entries, following each entry's extras."""
    seen: set[tuple[str, tuple[str, ...]]] = set()
    stack = list(deps)
    while stack:
        d = stack.pop()
        name = d["name"]
        p = packages.get(name)
        if p is None:
            continue
        key = (name, tuple(d.get("extra", [])))
        if key in seen:
            continue
        seen.add(key)
        stack += p.get("dependencies", [])
        for extra in d.get("extra", []):
            stack += p.get("optional-dependencies", {}).get(extra, [])
    return {k[0] for k in seen}


def licence_of(m: md.PackageMetadata) -> str:
    lic = (m.get("License-Expression") or "").strip()
    if not lic:
        lic = "; ".join(c.split("::")[-1].strip() for c in (m.get_all("Classifier") or []) if c.startswith("License ::"))
    if not lic:
        raw = (m.get("License") or "").strip().splitlines()
        lic = raw[0][:80] if raw else ""
    return lic or "not stated in the package metadata"


def main() -> int:
    lock = tomllib.loads(Path(sys.argv[1]).read_text("utf-8"))
    packages = {p["name"]: p for p in lock["package"]}
    root = packages[PROJECT]
    runtime = closure(packages, root.get("dependencies", []))
    dev = closure(packages, [d for g in root.get("dev-dependencies", {}).values() for d in g]) - runtime
    rows = []
    for name, p in sorted(packages.items()):
        if name == PROJECT:
            continue
        used = "runtime" if name in runtime else ("tests and checks only" if name in dev else "not reachable from the project (check the lock)")
        try:
            m = md.metadata(name)
        except md.PackageNotFoundError:
            rows.append({"package": name, "version": p.get("version", ""), "used_in": used,
                         "license": "not read: not installed on this platform (locked for another platform)", "home_page": ""})
            continue
        urls = {u.split(",")[0].strip().lower(): u.split(",", 1)[1].strip() for u in (m.get_all("Project-URL") or []) if "," in u}
        home = m.get("Home-page") or urls.get("homepage") or urls.get("repository") or urls.get("source") or next(iter(urls.values()), "")
        rows.append({"package": name, "version": m.get("Version") or p.get("version", ""), "used_in": used, "license": licence_of(m), "home_page": home})
    with open(sys.argv[2], "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    print(len(rows), dict(Counter(r["used_in"] for r in rows)))
    print(Counter(r["license"] for r in rows).most_common(30))
    print("not read or not stated:", [r["package"] for r in rows if r["license"].startswith("not")])
    print("not reachable:", [r["package"] for r in rows if r["used_in"].startswith("not")])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
