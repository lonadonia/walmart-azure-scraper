"""Scrape.do for the command line (``provider-balance``, ``status``, ``set-ceiling``): the key's measured
balance, the ceiling and the shared ledger's totals. The key comes from the environment
(:func:`walmart_headless.acquisition.scrapedo.load_keys`) and is never returned: only its role and a
short fingerprint.

Balances are *measured* values: ``GET /info`` (free; read on request and before and after each run) or
the ``Scrape.do-Remaining-Credits`` header of the latest answer, each with its time and source. Ledger
totals are the credits the provider charged (its cost header), kept apart from reservations still in
flight; nothing here is an estimate.
"""

from __future__ import annotations

import time
from typing import Any

import httpx
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from walmart_headless.acquisition.scrapedo import (
    API_BASE,
    INFO_MIN_INTERVAL_S,
    PROVIDER,
    Key,
    ceiling,
    key_rows,
    load_keys,
    record_reading,
    redact,
    set_ceiling,
    sync_keys,
    used_since,
)
from walmart_headless.db.models import AuditLog, ProviderUsage

DOCUMENTED_COSTS = {
    "walmart_store_endpoint": "10 credits per successful page (/plugin/walmart/store)",
    "general_api_datacenter": "1 credit per successful page (robots.txt and the store's own page)",
    "failures": "plugin failures (HTTP 502) and input errors (400) are not charged; Walmart's own 404 is",
}


def masked(fingerprint: str) -> str:
    return f"…{fingerprint[-6:]}" if fingerprint else ""


def status(s: Session, keys: list[Key] | None = None) -> dict[str, Any]:
    keys = load_keys() if keys is None else keys
    sync_keys(s, keys)
    rows = key_rows(s)
    active = next(
        (k.role for k in keys if rows.get(k.role) is None or rows[k.role].exhausted_at is None), None
    )
    key_list = []
    for k in keys:
        r = rows.get(k.role)
        key_list.append(
            {
                "role": k.role,
                "fingerprint": masked(k.fingerprint),
                "active": k.role == active,
                "remaining": r.remaining if r else None,
                "monthly": r.monthly if r else None,
                "read_at": r.read_at.isoformat() if r and r.read_at else None,
                "read_source": r.read_source if r else None,
                "exhausted_at": r.exhausted_at.isoformat() if r and r.exhausted_at else None,
            }
        )
    cap = ceiling(s)
    used = used_since(s, cap.get("since"))
    reserved = float(
        s.scalar(
            select(func.coalesce(func.sum(ProviderUsage.credits), 0.0)).where(
                ProviderUsage.provider == PROVIDER, ProviderUsage.outcome == "reserved"
            )
        )
        or 0.0
    )
    # Sent without an answer (interrupted, connection lost, a process that died): kept as possibly charged.
    uncertain = float(
        s.scalar(
            select(func.coalesce(func.sum(ProviderUsage.credits), 0.0)).where(
                ProviderUsage.provider == PROVIDER, ProviderUsage.cost_source == "unknown"
            )
        )
        or 0.0
    )
    by_key = {
        masked(str(f or "")) or "unknown": {"credits": float(c or 0), "requests": int(n or 0)}
        for f, c, n in s.execute(
            select(ProviderUsage.key_fingerprint, func.sum(ProviderUsage.credits), func.count())
            .where(ProviderUsage.provider == PROVIDER, ProviderUsage.outcome != "reserved")
            .group_by(ProviderUsage.key_fingerprint)
        )
    }
    charged = float(
        s.scalar(
            select(func.coalesce(func.sum(ProviderUsage.credits), 0.0)).where(
                ProviderUsage.provider == PROVIDER, ProviderUsage.outcome != "reserved"
            )
        )
        or 0.0
    )
    return {
        "provider": "scrape.do",
        "key_configured": bool(keys),
        "keys": key_list,
        "ceiling": {**cap, "used": used, "left": (float(cap["ceiling_credits"]) - used) if cap else None},
        "charged_total": charged,
        "reserved_in_flight": reserved,
        "charged_uncertain": uncertain,
        "by_key": by_key,
        "documented_costs": DOCUMENTED_COSTS,
    }


def refresh(
    s: Session, actor: str, keys: list[Key] | None = None, client: httpx.Client | None = None
) -> dict[str, Any]:
    """Read the key's balance (``GET /info``, free; at most 10 calls a minute)."""
    keys = load_keys() if keys is None else keys
    sync_keys(s, keys)
    http = client or httpx.Client(timeout=30)
    errors: dict[str, str] = {}
    try:
        for i, k in enumerate(keys):
            if i:
                time.sleep(INFO_MIN_INTERVAL_S)
            try:
                r = http.get(f"{API_BASE}/info", params={"token": k.token.get_secret_value()})
            except httpx.HTTPError as exc:
                errors[k.role] = redact(f"{type(exc).__name__}", keys)
                continue
            if r.status_code != 200:
                errors[k.role] = f"HTTP {r.status_code}: {redact(r.text[:160], keys)}"
                continue
            record_reading(s, k, r.json(), "info")
    finally:
        if client is None:
            http.close()
    s.add(AuditLog(actor=actor, action="scrapedo_refresh", target="scrapedo", data={"errors": errors}))
    out = status(s, keys)
    out["errors"] = errors
    return out


def save_ceiling(
    s: Session, credits: float, basis: str, actor: str, *, usd_per_credit: float | None = None
) -> dict[str, Any]:
    value = set_ceiling(s, credits, basis, actor, usd_per_credit)
    s.add(AuditLog(actor=actor, action="scrapedo_ceiling", target="scrapedo", data=value))
    return value
