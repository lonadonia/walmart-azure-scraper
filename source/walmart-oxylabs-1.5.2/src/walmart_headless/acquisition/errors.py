"""Failures on the provider's side (authentication, quota, concurrency, rejected parameters, our own credit
cap, network), kept apart from the retailer's own answers (challenge pages, HTTP 403/429), which stay
:class:`walmart_headless.acquisition.pages.ChallengeDetected`."""

from __future__ import annotations

from enum import StrEnum


class ProviderErrorKind(StrEnum):
    AUTH = "auth"  # key missing, invalid, revoked or account suspended
    QUOTA = "quota"  # credits or plan limit exhausted
    CONCURRENCY = "concurrency"  # too many requests at once
    CONFIG = "config"  # parameters rejected
    BUDGET = "budget"  # this run's own credit cap
    CEILING = "ceiling"  # the operator's provider ceiling or the task's money budget (every process)
    NETWORK = "network"  # provider unreachable
    SESSION = "session"  # the provider session went away mid-run
    PROVIDER = "provider"  # any other provider-side failure


class ProviderError(RuntimeError):
    """``units`` and ``usd``: what the failed request's submissions may have cost (charged, or sent without
    an answer), so the run's own accounting counts them; the ledger holds each submission."""

    def __init__(self, kind: ProviderErrorKind, message: str, *, units: float = 0.0, usd: float = 0.0):
        super().__init__(f"{kind.value}: {message}")
        self.kind = kind
        self.units = units
        self.usd = usd
