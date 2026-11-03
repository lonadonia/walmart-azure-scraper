"""Challenge detection on authentic saved pages and on ambiguous answers (release 1.3.1, defect A).

The pages in ``tests/captures/challenge_pages`` are sanitized copies of real answers (README there): a
legitimate product page whose page data quotes "reference #48395435" in a reply to a review (release 1.3.0
stopped on it), PerimeterX challenge pages of two live store changes, and their block answers. The
ambiguous answers are built from those pages."""

from __future__ import annotations

import asyncio
import gzip
import json
import re
from pathlib import Path

import pytest

from walmart_headless.acquisition.challenge import (
    WALMART_STATE_MARKER,
    ChallengeVerdict,
    blocked_response,
    detect_document_challenge,
    is_rate_limit_only,
    notes,
    signals,
)
from walmart_headless.acquisition.pages import ChallengeDetected
from walmart_headless.acquisition.robots import parse_robots
from walmart_headless.acquisition.scrapedo import Answer, Transport
from walmart_headless.acquisition.scrapedo_session import ScrapeDoWalmartSession
from walmart_headless.sites.walmart import page_data as wpd
from walmart_headless.sites.walmart.sanitize import sanitize_html
from walmart_headless.storage.local import LocalStorageAdapter

PAGES = Path(__file__).resolve().parents[1] / "captures" / "challenge_pages"
PRODUCT = "product_15353921746.html.gz"
CHALLENGES = ("store_5402_challenge.html.gz", "store_3891_challenge.html.gz")


def page(name: str) -> str:
    return gzip.decompress((PAGES / name).read_bytes()).decode("utf-8")


def judge(status: int | None, html: str, *, expect: bool = True) -> ChallengeVerdict:
    return detect_document_challenge(
        status, html, expect_initial_state=expect, state_marker=WALMART_STATE_MARKER
    )


def test_the_fixtures_match_their_manifest() -> None:
    import hashlib

    for entry in json.loads((PAGES / "MANIFEST.json").read_text("utf-8")):
        path = PAGES / entry["file"]
        data = gzip.decompress(path.read_bytes()) if path.suffix == ".gz" else path.read_bytes()
        assert hashlib.sha256(data).hexdigest() == entry["content_sha256"], entry["file"]


def test_a_legitimate_product_page_quoting_a_reference_number_in_a_review_is_content() -> None:
    html = page(PRODUCT)
    # The sentence that release 1.3.0 took for an Akamai reference id is in the page's own data only.
    data = re.search(r'<script[^>]*id="__NEXT_DATA__"[^>]*>.*?</script>', html, re.S)
    assert data is not None and "reference #48395435" in data.group(0)
    assert "reference #48395435" not in html.replace(data.group(0), "")
    v = judge(200, html)
    assert not v.is_challenge
    assert signals(v) == ()
    assert notes(v) == ("in_page_data:akamai_reference_id",)
    product = wpd.product_page(wpd.next_data(html))
    assert product is not None and product.page_item == "15353921746"  # read like any other product page


@pytest.mark.parametrize("name", CHALLENGES)
@pytest.mark.parametrize("status", [200, None])
@pytest.mark.parametrize("expect", [True, False])
def test_authentic_perimeterx_challenge_pages_are_refusals(
    name: str, status: int | None, expect: bool
) -> None:
    html = page(name)
    assert WALMART_STATE_MARKER in html  # the store page's data is there: only the dialog makes it a refusal
    v = judge(status, html, expect=expect)
    assert v.is_challenge
    assert {"perimeterx_captcha", "perimeterx_robot_or_human"} <= set(signals(v))


def test_the_dialog_added_after_400_kb_of_store_page_is_found() -> None:
    html = page("store_5402_challenge.html.gz")
    at = html.find('id="px-captcha"')
    assert at > 300_000  # the dialog is at the end of the page, where a 200 kB head scan never looked
    assert judge(200, html).is_challenge


def test_the_same_store_page_before_the_refused_store_change_is_content() -> None:
    v = judge(200, page("store_3891_page.html.gz"))
    assert not v.is_challenge and v.reasons == ()


@pytest.mark.parametrize("name", ["setpickup_412_block_5402.json", "setpickup_412_block_3891.json"])
def test_authentic_block_answers_to_the_store_change_are_refusals(name: str) -> None:
    assert blocked_response((PAGES / name).read_bytes())


def test_sanitizing_a_challenge_page_keeps_the_challenge_recognisable() -> None:
    for name in CHALLENGES:
        clean, _ = sanitize_html(page(name))
        assert judge(200, clean).is_challenge


# -- ambiguous answers -----------------------------------------------------------------------------------


def _with_text(html: str, fragment: str) -> str:
    return html.replace("</body>", fragment + "</body>", 1)


@pytest.mark.parametrize(
    ("fragment", "marker"),
    [
        ("<p>Access Denied to the archive: a novel</p>", "access_denied_text"),
        (
            "<div class='description'>Robot or human? A picture book for ages 4-8.</div>",
            "perimeterx_robot_or_human",
        ),
        ("<span>Customer service reference # A1234</span>", "akamai_reference_id"),
    ],
)
def test_denial_wording_on_a_content_page_without_a_challenge_element_is_noted_not_refused(
    fragment: str, marker: str
) -> None:
    html = _with_text(page(PRODUCT), fragment)
    v = judge(200, html)
    assert not v.is_challenge
    assert f"ambiguous_wording:{marker}" in notes(v)


def test_the_same_wording_on_an_answer_without_the_page_data_is_a_refusal() -> None:
    v = judge(200, "<html><body><h1>Access Denied</h1><p>Reference #18.6f2d1</p></body></html>")
    assert v.is_challenge
    assert {"access_denied_text", "akamai_reference_id", "missing_initial_state"} <= set(signals(v))
    # robots.txt and other answers that need no page data: the wording alone decides
    v = judge(200, "Access Denied\nReference #18.6f2d1", expect=False)
    assert v.is_challenge and "access_denied_text" in signals(v)
    assert not judge(200, "User-agent: *\nDisallow: /cart", expect=False).is_challenge


def test_the_same_wording_beside_a_refusal_status_is_a_refusal() -> None:
    html = _with_text(page(PRODUCT), "<p>Access Denied</p>")
    v = judge(403, html)
    assert v.is_challenge and {"http_403", "access_denied_text"} <= set(signals(v))
    assert judge(403, page(PRODUCT)).is_challenge  # the status alone refuses, whatever the page says


def test_a_challenge_element_on_a_content_page_is_a_refusal_whatever_the_wording() -> None:
    html = _with_text(page(PRODUCT), '<div id="px-captcha"></div>')
    v = judge(200, html)
    assert v.is_challenge and "perimeterx_captcha" in signals(v)


def test_a_challenge_element_quoted_inside_the_page_data_is_content() -> None:
    nd = wpd.next_data(page(PRODUCT))
    nd["props"]["pageProps"]["note"] = '<div id="px-captcha"></div> Robot or human?'
    html = re.sub(
        r'(<script[^>]*id="__NEXT_DATA__"[^>]*>).*?(</script>)',
        lambda m: m.group(1) + json.dumps(nd).replace("<", "\\u003c").replace(">", "\\u003e") + m.group(2),
        page(PRODUCT),
        count=1,
        flags=re.S,
    )
    v = judge(200, html)
    assert not v.is_challenge
    assert "in_page_data:perimeterx_robot_or_human" in notes(v)


def test_a_blocked_route_in_the_page_data_is_a_refusal() -> None:
    html = page(PRODUCT).replace('"page":"/ip/[...itemParams]"', '"page":"/blocked"', 1)
    assert '"page":"/blocked"' in html
    v = judge(200, html)
    assert v.is_challenge and "blocked_page_data" in signals(v)


def test_a_rate_limit_stays_a_rate_limit_unless_the_answer_also_refuses() -> None:
    # The page's own data quotes "reference #…" (a note): the 429 stays a plain rate limit.
    noted = judge(429, page(PRODUCT))
    assert noted.is_challenge and is_rate_limit_only(noted)
    assert notes(noted) == ("in_page_data:akamai_reference_id",)
    # Denial wording in the markup beside a 429, or a challenge page with a 429: a block, never retried.
    worded = judge(429, _with_text(page(PRODUCT), "<p>Access Denied</p>"))
    assert worded.is_challenge and not is_rate_limit_only(worded)
    blocked = judge(429, page("store_3891_challenge.html.gz"))
    assert blocked.is_challenge and not is_rate_limit_only(blocked)


# -- through the provider session (no network: a fake transport answers with the saved page) -------------


class _Transport(Transport):
    """Answers every request with one page (no ledger, no client: nothing leaves the test)."""

    def __init__(self, body: str, status: int = 200):
        self.body, self.status = body.encode("utf-8"), status

    async def fetch(self, req: object) -> Answer:
        return Answer(
            url="https://www.walmart.com/ip/x/15353921746",
            endpoint="general",
            status=self.status,
            body=self.body,
            headers={},
            kind=None,
            credits=1.0,
            cost_source="test",
            remaining=None,
            request_id="test",
            key_role="TEST",
            key_fingerprint="0" * 12,
            elapsed_ms=1,
        )

    async def aclose(self) -> None:
        return None


def _session(tmp_path: Path, body: str) -> ScrapeDoWalmartSession:
    s = ScrapeDoWalmartSession(
        _Transport(body),
        LocalStorageAdapter(tmp_path),
        "runs/test",
        store_id="3891",
        zipcode="60085",
        store_page_url="https://www.walmart.com/store/3891-waukegan-il",
        sanitizer=sanitize_html,
    )
    s.robots = parse_robots("User-agent: *\nAllow: /\n")
    return s


def test_the_session_reads_the_legitimate_page_and_records_the_noted_wording(tmp_path: Path) -> None:
    s = _session(tmp_path, page(PRODUCT))
    fetch = asyncio.run(s.navigate("https://www.walmart.com/ip/x/15353921746", "product_detail"))
    assert not fetch.challenge.is_challenge
    [event] = [e for e in s.events if e.code == "PAGE_CAPTURED"]
    assert event.data["challenge"] == ["in_page_data:akamai_reference_id"]


def test_the_session_stops_on_an_authentic_challenge_page(tmp_path: Path) -> None:
    s = _session(tmp_path, page("store_3891_challenge.html.gz"))
    with pytest.raises(ChallengeDetected) as caught:
        asyncio.run(s.navigate("https://www.walmart.com/store/3891-waukegan-il", "store_page"))
    assert "perimeterx_captcha" in str(caught.value)
    [event] = [e for e in s.events if e.code == "CHALLENGE_DETECTED"]
    assert "perimeterx_captcha" in event.data["challenge"]
