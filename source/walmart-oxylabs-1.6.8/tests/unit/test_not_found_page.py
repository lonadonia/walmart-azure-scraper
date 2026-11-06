"""Release 1.6.3: Walmart's own not-found page is neither a challenge nor an empty listing.

On 2026-11-04 (live L6, release 1.6.2) the Shampoo child listing "nexxus-shampoo", a link its parent's
Departments facet named, answered with Walmart's not-found page, HTTP 200. That page is minified: its page
data is written ``<script id=__NEXT_DATA__ type="application/json">``, the id unquoted, and its route is
``/404``. Release 1.6.2 looked only for ``id="__NEXT_DATA__"``: it read "missing_initial_state", called the
page a challenge, stopped the run (``SITE_REFUSAL``) and held the store, and its sanitizer dropped that page
data from the stored copy. The page here is SYNTHETIC, with the live page's markers
(``tests/synthetic_walmart.py``).

The names this release adds are read from their modules inside the tests, so that the tests of what did not
change also run on release 1.6.2.
"""

from __future__ import annotations

import pytest

from tests import synthetic_walmart as syn
from walmart_headless.acquisition import challenge
from walmart_headless.acquisition.challenge import (
    WALMART_STATE_MARKER,
    ChallengeVerdict,
    detect_document_challenge,
    signals,
)
from walmart_headless.sites.walmart import page_data as wpd
from walmart_headless.sites.walmart.sanitize import sanitize_html

STORE = "3891"


def judge(html: str, *, expect: bool = True) -> ChallengeVerdict:
    return detect_document_challenge(
        200, html, expect_initial_state=expect, state_marker=WALMART_STATE_MARKER
    )


def test_the_site_not_found_page_is_no_challenge() -> None:
    page = syn.not_found_page()
    assert WALMART_STATE_MARKER not in page  # the quoted form release 1.6.2 looked for
    v = judge(page)
    assert not v.is_challenge and v.reasons == ()
    assert challenge.has_state(page, WALMART_STATE_MARKER)


def test_its_page_data_is_read_and_says_it_is_the_not_found_page() -> None:
    nd = wpd.next_data(syn.not_found_page())
    assert wpd.search_result(nd) is None and wpd.category_page(nd) == ""
    assert wpd.not_found_page(nd) == "/404"


def test_the_stored_copy_keeps_that_page_data_redacted_and_readable() -> None:
    out, report = sanitize_html(syn.not_found_page())
    assert report.page_data_kept
    assert not judge(out).is_challenge
    assert wpd.next_data(out)["page"] == "/404"


@pytest.mark.parametrize("quote", ['"', "'", ""], ids=["double-quoted", "single-quoted", "unquoted"])
def test_the_page_data_script_is_found_however_its_id_is_quoted(quote: str) -> None:
    data = {"page": "/browse/[...slug]", "props": {"pageProps": {}}}
    page = syn.next_data_script(data).replace('id="__NEXT_DATA__"', f"id={quote}__NEXT_DATA__{quote}")
    assert not judge(page).is_challenge
    assert wpd.next_data(page)["page"] == "/browse/[...slug]"
    assert sanitize_html(page)[1].page_data_kept


def test_a_listing_page_and_a_category_page_are_not_the_not_found_page() -> None:
    listing = wpd.next_data(syn.listing_page([syn.Item("7101", "Whole Milk", "$3.12")], store=STORE))
    assert wpd.not_found_page(listing) == ""
    hub = wpd.next_data(syn.next_data_script({"page": "/cp/[...categoryParams]", "props": {"pageProps": {}}}))
    assert wpd.not_found_page(hub) == ""


def test_a_challenge_is_still_a_challenge_with_unquoted_page_data() -> None:
    page = syn.not_found_page().replace("</body>", f"{syn.CHALLENGE_DIALOG}</body>")
    v = judge(page)
    assert v.is_challenge
    assert {"perimeterx_captcha", "perimeterx_robot_or_human"} <= set(signals(v))


@pytest.mark.parametrize(
    "page",
    [
        "<!doctype html><html><body><p>Uh-oh... This page could not be found.</p></body></html>",
        # The name in text or in another script's code is not the page data's script.
        "<html><body><p>id=__NEXT_DATA__</p><script>var x='__NEXT_DATA__'</script></body></html>",
        '<html><body><script id=__NEXT_DATA__X type="application/json">{}</script></body></html>',
    ],
    ids=["no-page-data", "the-name-elsewhere", "another-id"],
)
def test_a_page_without_the_page_data_script_is_still_refused_as_before(page: str) -> None:
    v = judge(page)
    assert v.is_challenge and signals(v) == ("missing_initial_state",)
    assert not judge(page, expect=False).is_challenge
