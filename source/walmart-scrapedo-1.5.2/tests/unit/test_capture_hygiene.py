"""Every saved page under ``tests/captures`` is a sanitized copy (release 1.3.1): its page data holds no
value under a key the collector's sanitizer redacts (sessions, tokens, cookies, visitor, device and trace
IDs; :data:`walmart_headless.sites.walmart.sanitize.REDACT_KEY`), no IP address and no third-party API
key. The capture READMEs state this; this test keeps it true."""

from __future__ import annotations

import gzip
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

from walmart_headless.sites.walmart import page_data as wpd
from walmart_headless.sites.walmart.sanitize import API_KEY_VALUE, REDACT_KEY, REDACTED, _is_ip

CAPTURES = Path(__file__).resolve().parents[1] / "captures"
PAGES = sorted(CAPTURES.rglob("*.html.gz"))


def leaks(obj: Any, path: str = "") -> Iterator[str]:
    if isinstance(obj, dict):
        for key, value in obj.items():
            here = f"{path}.{key}"
            if REDACT_KEY.match(str(key)) and value not in (None, "", [], {}, REDACTED):
                yield here
            else:
                yield from leaks(value, here)
    elif isinstance(obj, list):
        for i, value in enumerate(obj):
            yield from leaks(value, f"{path}[{i}]")
    elif isinstance(obj, str) and (_is_ip(obj.strip()) or API_KEY_VALUE.search(obj)):
        yield path


def test_there_are_saved_pages() -> None:
    assert len(PAGES) >= 10


@pytest.mark.parametrize("page", PAGES, ids=[str(p.relative_to(CAPTURES)) for p in PAGES])
def test_a_saved_page_keeps_no_identifier_the_sanitizer_redacts(page: Path) -> None:
    html = gzip.decompress(page.read_bytes()).decode("utf-8")
    try:
        data = wpd.next_data(html)
    except wpd.PageDataMissing:
        data = None  # a challenge page without page data: its markup is checked below
    if data is not None:
        assert list(leaks(data)) == []
    assert API_KEY_VALUE.search(html) is None
