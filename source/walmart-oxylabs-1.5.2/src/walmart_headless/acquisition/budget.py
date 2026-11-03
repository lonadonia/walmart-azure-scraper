"""The task's money budget across providers (``walmart-collector set-budget``).

Every provider ledger (``scrapedo.Ledger``, ``oxylabs.OxylabsLedger``) records each request in
``provider_usage`` with its largest possible cost in US dollars (``cost_usd``) before the request is sent.
Before reserving, a ledger takes this module's advisory lock and checks the total recorded since the
budget was set, over every provider, against the budget: so retries, restarts, other processes and a change
of provider all count against one figure, and concurrent workers cannot cross it together. A provider whose
price per unit is unknown records no dollar figure (``cost_usd`` empty) and is bounded by its own ceiling
only; the reports say so.

The lock is always taken before a provider's own lock (one order, so no deadlock).
"""

from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Any

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from walmart_headless.acquisition.errors import ProviderError, ProviderErrorKind
from walmart_headless.core.timeutil import iso, utcnow
from walmart_headless.db.models import ProviderUsage, SettingRow

SETTINGS_ROW = "budget:task"
_LOCK_ID = int.from_bytes(hashlib.sha256(b"walmart_headless:budget:task").digest()[:4], "big")


def lock(s: Session) -> None:
    """The budget's transaction-scoped advisory lock (released at commit or rollback)."""
    s.execute(text("SELECT pg_advisory_xact_lock(:id)"), {"id": _LOCK_ID})


def get(s: Session) -> dict[str, Any]:
    row = s.get(SettingRow, SETTINGS_ROW)
    return dict(row.value) if row else {}


def put(s: Session, max_usd: float, basis: str, actor: str) -> dict[str, Any]:
    if max_usd < 0:
        raise ValueError("the budget is a positive amount of US dollars")
    value = {"max_usd": max_usd, "since": iso(utcnow()), "basis": basis, "set_by": actor}
    row = s.get(SettingRow, SETTINGS_ROW)
    if row is None:
        s.add(SettingRow(key=SETTINGS_ROW, value=value, updated_by=actor))
    else:
        row.value, row.updated_by = value, actor
    return value


def _since(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value.replace("Z", "+00:00")) if value else None


def spent(s: Session, since: str | None = None, provider: str | None = None) -> dict[str, Any]:
    """US dollars recorded since ``since`` (reserved, charged and possibly charged requests), by provider."""
    q = select(
        ProviderUsage.provider,
        func.coalesce(func.sum(ProviderUsage.cost_usd), 0.0),
        func.count(),
        func.count(ProviderUsage.cost_usd),
    ).group_by(ProviderUsage.provider)
    start = _since(since)
    if start is not None:
        q = q.where(ProviderUsage.at >= start)
    if provider is not None:
        q = q.where(ProviderUsage.provider == provider)
    by: dict[str, Any] = {}
    for name, usd, n, priced in s.execute(q).all():
        by[str(name)] = {
            "usd": round(float(usd or 0.0), 6),
            "requests": int(n),
            "unpriced": int(n) - int(priced),
        }
    return {"usd": round(sum(v["usd"] for v in by.values()), 6), "by_provider": by}


def room(s: Session) -> float | None:
    """US dollars left in the task's budget now (None: no budget is set)."""
    cap = get(s)
    limit = cap.get("max_usd")
    if limit is None:
        return None
    used = float(spent(s, cap.get("since"))["usd"])
    return max(0.0, float(limit) - used)


def check(s: Session, usd: float | None, provider: str) -> None:
    """Raise CEILING when ``usd`` more would cross the task's budget (no budget set: nothing to check).
    The caller holds :func:`lock` and records the reservation in the same transaction."""
    cap = get(s)
    limit = cap.get("max_usd")
    if limit is None or usd is None:
        return
    used = spent(s, cap.get("since"))["usd"]
    if used + usd > float(limit) + 1e-9:
        raise ProviderError(
            ProviderErrorKind.CEILING,
            f"the task's money budget: ${used:.4f} of ${float(limit):.4f} recorded across providers, the "
            f"next {provider} request may cost ${usd:.4f}",
        )
