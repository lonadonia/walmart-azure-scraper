"""The live not-found answer of L6 judged by an installed release's own code (offline: no request).

usage: <release's python> -I not_found_check.py RAW_BODY_GZ

Prints, as JSON: the release (walmart_headless.__version__), the SHA-256 of the stored raw answer (the .gz file and the
body it holds), the challenge verdict on the raw body and on the sanitized copy that release stores, whether the
sanitizer kept the page data, and the page data's route when that release finds it. No page content is printed.
"""

import gzip
import hashlib
import json
import sys
from pathlib import Path

import walmart_headless
from walmart_headless.acquisition.challenge import WALMART_STATE_MARKER, detect_document_challenge
from walmart_headless.sites.walmart import page_data as wpd
from walmart_headless.sites.walmart.sanitize import sanitize_html

path = Path(sys.argv[1])
gz = path.read_bytes()
body = gzip.decompress(gz)
html = body.decode("utf-8")
raw = detect_document_challenge(200, html, expect_initial_state=True, state_marker=WALMART_STATE_MARKER)
dom, report = sanitize_html(html)
stored = detect_document_challenge(200, dom, expect_initial_state=True, state_marker=WALMART_STATE_MARKER)
try:
    route = wpd.next_data(dom).get("page")
except wpd.PageDataMissing as exc:
    route = f"(no page data: {exc})"
print(
    json.dumps(
        {
            "release": walmart_headless.__version__,
            "file": path.name,
            "file_sha256": hashlib.sha256(gz).hexdigest(),
            "body_sha256": hashlib.sha256(body).hexdigest(),
            "body_bytes": len(body),
            "quoted_marker_present": WALMART_STATE_MARKER in html,
            "raw_verdict": {"is_challenge": raw.is_challenge, "reasons": list(raw.reasons)},
            "sanitizer_kept_page_data": report.page_data_kept,
            "stored_copy_verdict": {"is_challenge": stored.is_challenge, "reasons": list(stored.reasons)},
            "stored_copy_route": route,
        },
        indent=1,
    )
)
