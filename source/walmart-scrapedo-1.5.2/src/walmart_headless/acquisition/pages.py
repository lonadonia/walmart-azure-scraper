"""A fetched page and the ways a fetch can fail, independent of how the page was fetched.

Scrape.do returns Walmart's own response for each request; :class:`PageFetch` records it (URL, status,
timing, the challenge verdict, the stored copy) the same way for every page of a run.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from typing import Any
from urllib.parse import urlsplit

from walmart_headless.acquisition.capture import CapturedResponse
from walmart_headless.acquisition.challenge import ChallengeVerdict, is_rate_limit_only, parse_retry_after
from walmart_headless.core.timeutil import utcnow

# (url, resource type) -> may the page make this request?
ResourcePolicy = Callable[[str, str], bool]


def trace_url(url: str) -> str:
    """A traced request's address without its query or fragment (they can carry visitor IDs)."""
    parts = urlsplit(url)
    return f"{parts.scheme}://{parts.netloc}{parts.path}"[:300]


@dataclass
class PageFetch:
    fetch_id: str
    purpose: str
    url: str
    final_url: str = ""
    status: int | None = None
    started_at: str = ""
    duration_ms: int | None = None
    challenge: ChallengeVerdict = field(default_factory=lambda: ChallengeVerdict(False))
    dom_key: str | None = None
    screenshot_key: str | None = None
    captured: list[CapturedResponse] = field(default_factory=list)
    notes: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["challenge"] = asdict(self.challenge)
        return d


class ChallengeDetected(RuntimeError):
    def __init__(self, fetch: PageFetch):
        super().__init__(f"challenge on {fetch.url}: {', '.join(fetch.challenge.reasons)}")
        self.fetch = fetch


class RateLimited(ChallengeDetected):
    """A plain HTTP 429 from the site: stopped like a challenge; the worker may pause the category for
    ``retry_after_s`` before a single retry."""

    def __init__(self, fetch: PageFetch, retry_after_s: float | None):
        super().__init__(fetch)
        self.retry_after_s = retry_after_s


def refusal(fetch: PageFetch, retry_after_header: str | None) -> ChallengeDetected:
    if retry_after_header is not None:
        fetch.notes["retry_after"] = retry_after_header[:100]
    if is_rate_limit_only(fetch.challenge):
        return RateLimited(fetch, parse_retry_after(retry_after_header, utcnow()))
    return ChallengeDetected(fetch)


class NavigationFailed(RuntimeError):
    """The request itself failed (connection reset, timeout): no document; ``fetch`` holds the evidence."""

    def __init__(self, fetch: PageFetch, message: str):
        super().__init__(message)
        self.fetch = fetch


class RobotsDisallowed(RuntimeError):
    pass


class RobotsUnreachable(RobotsDisallowed):
    """robots.txt could not be fetched at all."""


class NoDocumentResponse(RobotsUnreachable):
    """The request ended without any document response: a tooling fault, not an answer from the site."""


class NotInSource(LookupError):
    """A replay asked for a page the run it reads again never fetched (nothing is requested instead)."""
