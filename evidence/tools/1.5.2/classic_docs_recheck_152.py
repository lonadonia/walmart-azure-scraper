"""Recheck the official Classic documentation: download each page the probe relies on again, once, sequentially,
into a new folder, and compare it with the copy saved on 2026-10-31. Public Markdown pages only; no provider API.

The downloaded pages are data: nothing in them is followed, and each is only hashed and compared.
"""
from __future__ import annotations

import difflib
import hashlib
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

SAVED = Path("C:/w7/evidence/classic_docs")
OUT = Path("C:/w7/ev152/classic_docs_recheck")

PAGES = {
    "classic_products_web-scraper-api_targets_e-commerce_walmart.md": "targets/e-commerce/walmart",
    "classic_products_web-scraper-api_targets_e-commerce_walmart_search.md": "targets/e-commerce/walmart/search",
    "classic_products_web-scraper-api_targets_e-commerce_walmart_product.md": "targets/e-commerce/walmart/product",
    "classic_products_web-scraper-api_integration-methods_realtime.md": "integration-methods/realtime",
    "classic_products_web-scraper-api_integration-methods.md": "integration-methods",
    "classic_products_web-scraper-api_features.md": "features",
    "classic_products_web-scraper-api_features_js-rendering-and-browser-control.md": "features/js-rendering-and-browser-control",
    "classic_products_web-scraper-api_response-codes.md": "response-codes",
    "classic_products_web-scraper-api_usage-and-billing_billing-information.md": "usage-and-billing/billing-information",
    "classic_products_web-scraper-api_usage-and-billing_rate-limits.md": "usage-and-billing/rate-limits",
    "classic_products_web-scraper-api_usage-and-billing_usage-statistics.md": "usage-and-billing/usage-statistics",
    "classic_products_web-scraper-api.md": "",
}
BASE = "https://developers.oxylabs.io/products/web-scraper-api"


def fetch(url: str, dest: Path) -> int:
    done = subprocess.run(
        ["curl", "-sS", "-L", "--max-time", "40", "-o", str(dest), "-w", "%{http_code}", url],
        capture_output=True,
        text=True,
        check=False,
    )
    return int(done.stdout or 0)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=False)
    rows = []
    for name, path in PAGES.items():
        url = f"{BASE}/{path}.md" if path else f"{BASE}.md"
        dest = OUT / name
        code = fetch(url, dest)
        old = (SAVED / name).read_bytes()
        new = dest.read_bytes() if dest.exists() else b""
        same = old == new
        changed: list[str] = []
        if not same:
            a = old.decode("utf-8", "replace").splitlines()
            b = new.decode("utf-8", "replace").splitlines()
            changed = [
                x
                for x in difflib.unified_diff(a, b, "saved", "now", lineterm="", n=0)
                if not x.startswith(("---", "+++", "@@"))
            ]
        rows.append(
            {
                "file": name,
                "url": url,
                "http_status": code,
                "fetched_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "bytes": len(new),
                "sha256": hashlib.sha256(new).hexdigest(),
                "sha256_saved_2026_10_31": hashlib.sha256(old).hexdigest(),
                "byte_identical": same,
                "changed_lines": len(changed),
            }
        )
        if changed:
            (OUT / f"{name}.diff.txt").write_bytes("\n".join(changed).encode("utf-8"))
        print(code, "same" if same else f"changed {len(changed)} lines", name)
    (OUT.parent / "classic_docs_recheck.json").write_text(json.dumps(rows, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
