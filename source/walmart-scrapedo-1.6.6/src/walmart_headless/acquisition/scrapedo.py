"""Scrape.do as the collection provider: the key, the spending ledger and the transport.

Documentation read 2026-10-21 and checked again for this collector: https://scrape.do/documentation/
(Request Costs, Status Codes, Timeout, Output & Response), the Walmart store endpoint
https://scrape.do/documentation/walmart-scraper-api/store/ (``token``, ``url``, ``zipcode`` and
``storeid`` given together for walmart.com; 10 credits per successful request; input errors and plugin
failures not charged; Walmart's own 404 charged; HTTP 502 "invalid combination of zipcode and storeid"),
and usage statistics https://scrape.do/documentation/api-response/usage-stats/ (``GET /info``, free, at
most 10 calls a minute).

Key. One Scrape.do key from the environment: ``SCRAPEDO_API_KEY`` (in Azure, a Container Apps secret
reference to Key Vault), or ``SCRAPEDO_API_KEY_FILE`` naming a mounted secret file that holds the key
alone or a ``SCRAPEDO_API_KEY=…`` line. It is used in the role ``primary``; only the role and a short
fingerprint are ever stored, shown or logged. Replacing the key means replacing the secret; a new key
starts with no reading and no exhaustion carried over.

Ledger. Every request reserves its largest possible cost in ``provider_usage`` under a PostgreSQL
advisory lock (one per provider), so concurrent workers can neither cross the task's credit ceiling nor
spend a key past its measured balance; the row is then settled to what the provider charged (its
``Scrape.do-Request-Cost`` header, which the documentation calls authoritative, else the documented rule:
credits only for 2xx/400/404/410; Walmart plugin pages 10). ``Scrape.do-Remaining-Credits`` updates the
key's measured balance after every answer; ``GET /info`` (free) reads it before and after a run.

Exhaustion. Only a confirmed exhaustion marks the key exhausted: an answer that names missing credits
(HTTP 401 "no credits", 402) is checked against the key's own ``/info`` reading, and the key is marked
exhausted only when that reading shows less than one request's cost left. A site refusal, a CAPTCHA,
HTTP 403/429 or a provider failure never marks it; an authentication failure is a configuration problem.
There is no other key and no other provider to fall back to: with the key exhausted the run stops
(``CREDITS_EXHAUSTED``), resumable from its checkpoint once credits are available again.
"""

from __future__ import annotations

import asyncio
import hashlib
import os
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from time import monotonic
from typing import Any, ClassVar

import httpx
from pydantic import SecretStr
from sqlalchemy import func, select, text, update
from sqlalchemy.orm import Session, sessionmaker

from walmart_headless.acquisition import budget
from walmart_headless.acquisition.challenge import parse_retry_after
from walmart_headless.acquisition.errors import ProviderError, ProviderErrorKind
from walmart_headless.core.timeutil import iso, utcnow
from walmart_headless.db.models import AuditLog, Event, ProviderKey, ProviderUsage, SettingRow

PROVIDER = "scrapedo"
API_BASE = "https://api.scrape.do"
WALMART_STORE_ENDPOINT = "/plugin/walmart/store"
GENERAL_ENDPOINT = "/"
ROLES = ("primary", "secondary")
ENV_KEY = "SCRAPEDO_API_KEY"
ENV_KEY_FILE = "SCRAPEDO_API_KEY_FILE"
SETTINGS_ROW = "provider:scrapedo"  # the credit ceiling and its basis (``walmart-collector set-ceiling``)
INFO_MIN_INTERVAL_S = 6.5  # /info: at most 10 calls a minute
MAX_RETRY_AFTER_S = 60.0
# A key marked exhausted is usable again when its own /info reading shows at least one Walmart page's
# credits (a new month, or credits the account's owner added): never from a cost header.
RENEWAL_MIN_CREDITS = 10.0
STALE_RESERVATION_S = 600  # longer than three attempts of a request can last
_LOCK_ID = int.from_bytes(hashlib.sha256(b"walmart_headless:provider:scrapedo").digest()[:4], "big")
REDACTED = "[REDACTED]"


class KeyBalanceLow(ProviderError):
    """The key's measured balance cannot pay the next request (to be confirmed by its own reading)."""


# -- keys ----------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Key:
    role: str
    token: SecretStr = field(repr=False)

    @property
    def fingerprint(self) -> str:
        return hashlib.sha256(self.token.get_secret_value().encode()).hexdigest()[:12]


def _file_token(path: Path) -> str:
    """A mounted secret file: the key alone, or a ``SCRAPEDO_API_KEY=…`` line."""
    text_ = path.read_text(encoding="utf-8-sig")
    for line in text_.splitlines():
        name, sep, value = line.strip().removeprefix("export ").partition("=")
        if sep and name.strip() in (ENV_KEY, "SCRAPEDO_TOKEN"):
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            return value
    lines = [x.strip() for x in text_.splitlines() if x.strip()]
    return lines[0] if len(lines) == 1 and "=" not in lines[0] else ""


def load_keys(environ: Mapping[str, str] | None = None) -> list[Key]:
    """The configured key (none when neither variable is set)."""
    env = os.environ if environ is None else environ
    token = (env.get(ENV_KEY) or "").strip()
    path = (env.get(ENV_KEY_FILE) or "").strip()
    if not token and path and Path(path).is_file():
        token = _file_token(Path(path))
    return [Key("primary", SecretStr(token))] if token else []


def redact(text_: str, keys: list[Key]) -> str:
    for k in keys:
        text_ = text_.replace(k.token.get_secret_value(), REDACTED)
    return re.sub(r"(?i)\btoken=[^&\s'\"<>]+", f"token={REDACTED}", text_)


# -- answers -------------------------------------------------------------------------------------------


def classify(status: int | None, body: bytes) -> str | None:
    """None for a usable answer; else the failure's kind (Status Codes page)."""
    if status is not None and 200 <= status < 300:
        return None
    t = body[:3000].decode("utf-8", "replace").lower()
    if status == 402 or (status == 401 and ("credit" in t or "subscription" in t)):
        return "balance"
    if status == 401:
        return "auth"
    if status == 404:
        return "not_found"  # the target's own 404: a store-specific answer, charged
    if status == 429:
        return "rate_limit"  # Scrape.do's concurrency limit (not charged), or the target's own 429
    if status == 400 and re.search(r"zipcode|storeid|store id|invalid parameters|valid walmart url", t):
        return "bad_parameters"
    if status == 400:
        return "target_400"  # Scrape.do documents this as charged when the target answered it
    if status == 502 and "invalid combination" in t:
        return "store_pair"
    if status in (502, 503, 504, 510):
        return "provider_failure"  # not charged
    return "provider_failure"


@dataclass
class Answer:
    url: str
    endpoint: str
    status: int | None
    body: bytes
    headers: dict[str, str]  # Scrape.do's own headers (no cookies)
    kind: str | None  # None: usable
    credits: float
    cost_source: str
    remaining: int | None
    request_id: str
    key_role: str
    key_fingerprint: str
    elapsed_ms: int
    attempts: list[dict[str, Any]] = field(default_factory=list)
    failovers: list[dict[str, Any]] = field(default_factory=list)
    cost_usd: float | None = None  # the request's dollar figure, when the provider's price is known

    @property
    def ok(self) -> bool:
        return self.kind is None


# -- the ledger -----------------------------------------------------------------------------------------


def ceiling(s: Session) -> dict[str, Any]:
    row = s.get(SettingRow, SETTINGS_ROW)
    return dict(row.value) if row else {}


def set_ceiling(
    s: Session, credits: float, basis: str, actor: str, usd_per_credit: float | None = None
) -> dict[str, Any]:
    """The credit ceiling from now on; ``usd_per_credit`` (the plan's price of one credit, 0 on the free
    plan) gives each request a dollar figure for the task's budget across providers (unknown: none)."""
    value = {
        "ceiling_credits": credits,
        "usd_per_credit": usd_per_credit,
        "since": iso(utcnow()),
        "basis": basis,
        "set_by": actor,
    }
    row = s.get(SettingRow, SETTINGS_ROW)
    if row is None:
        s.add(SettingRow(key=SETTINGS_ROW, value=value, updated_by=actor))
    else:
        row.value, row.updated_by = value, actor
    return value


def usd_rate(s: Session) -> float | None:
    """The price of one credit recorded with the ceiling (None: unknown)."""
    rate = ceiling(s).get("usd_per_credit")
    return None if rate is None else float(rate)


def api_product(endpoint: str) -> str:
    return "scrape.do walmart store endpoint" if endpoint == WALMART_STORE_ENDPOINT else "scrape.do api"


def used_since(s: Session, since: str | None) -> float:
    q = select(func.coalesce(func.sum(ProviderUsage.credits), 0.0)).where(ProviderUsage.provider == PROVIDER)
    if since:
        q = q.where(ProviderUsage.at >= datetime.fromisoformat(since.replace("Z", "+00:00")))
    return float(s.scalar(q) or 0.0)


def key_rows(s: Session) -> dict[str, ProviderKey]:
    return {r.role: r for r in s.scalars(select(ProviderKey).where(ProviderKey.provider == PROVIDER))}


def sync_roles(s: Session, roles: list[tuple[str, str]]) -> None:
    """One row per configured (role, fingerprint); a role whose key changed starts again (no reading and
    no exhaustion carried over)."""
    rows = key_rows(s)
    for role, fingerprint in roles:
        row = rows.get(role)
        if row is None:
            s.add(ProviderKey(provider=PROVIDER, role=role, fingerprint=fingerprint))
        elif row.fingerprint != fingerprint:
            row.fingerprint, row.remaining, row.read_at, row.read_source = fingerprint, None, None, None
            row.exhausted_at, row.exhausted_reason, row.updated_at = None, None, utcnow()


def sync_keys(s: Session, keys: list[Key]) -> None:
    sync_roles(s, [(k.role, k.fingerprint) for k in keys])


def record_reading(s: Session, key: Key, info: Mapping[str, Any], source: str = "info") -> None:
    row = s.get(ProviderKey, (PROVIDER, key.role))
    if row is None:
        row = ProviderKey(provider=PROVIDER, role=key.role, fingerprint=key.fingerprint)
        s.add(row)
    row.remaining = _int(info.get("RemainingMonthlyRequest"))
    row.monthly = _int(info.get("MaxMonthlyRequest"))
    row.concurrency = _int(info.get("ConcurrentRequest"))
    row.is_active_account = bool(info.get("IsActive")) if info.get("IsActive") is not None else None
    row.read_at, row.read_source, row.updated_at = utcnow(), source, utcnow()
    if (
        source == "info"
        and row.exhausted_at is not None
        and row.remaining is not None
        and row.remaining >= RENEWAL_MIN_CREDITS
    ):
        reason = (
            f"GET /info RemainingMonthlyRequest={row.remaining} after exhaustion at {iso(row.exhausted_at)}"
        )
        s.add(
            AuditLog(
                actor="system",
                action="provider_key_renewed",
                target=f"{PROVIDER}:{key.role}",
                reason=reason,
                data={"role": key.role, "fingerprint": key.fingerprint, "remaining": row.remaining},
            )
        )
        row.exhausted_at, row.exhausted_reason = None, None


def _int(v: Any) -> int | None:
    try:
        return None if v is None else int(v)
    except (TypeError, ValueError):
        return None


class Ledger:
    """The shared ledger and key state (database), used under the provider's advisory lock."""

    def __init__(self, factory: sessionmaker[Session], keys: list[Key]):
        self.factory, self.keys = factory, keys
        with factory() as s:
            sync_keys(s, keys)
            s.commit()

    def _lock(self, s: Session) -> None:
        budget.lock(s)  # always first: one lock order across providers
        s.execute(text("SELECT pg_advisory_xact_lock(:id)"), {"id": _LOCK_ID})

    def active(self) -> Key | None:
        with self.factory() as s:
            rows = key_rows(s)
        for k in self.keys:
            row = rows.get(k.role)
            if row is None or row.exhausted_at is None:
                return k
        return None

    def reserve(
        self,
        key: Key,
        cost: float,
        *,
        run_id: str | None,
        retailer: str | None,
        purpose: str,
        endpoint: str,
        target_url: str,
        attempt: int,
        segment_id: str | None = None,
        worker: str | None = None,
    ) -> str:
        """A reservation row, or :class:`ProviderError` (CEILING/QUOTA) when the cost does not fit."""
        with self.factory() as s:
            self._lock(s)
            # A reservation older than any request can last was left by a stopped process (a crash):
            # closed as "abandoned", its reserved cost kept as possibly charged.
            s.execute(
                update(ProviderUsage)
                .where(
                    ProviderUsage.provider == PROVIDER,
                    ProviderUsage.outcome == "reserved",
                    ProviderUsage.at < utcnow() - timedelta(seconds=STALE_RESERVATION_S),
                )
                .values(outcome="abandoned", cost_source="unknown")
            )
            cap = ceiling(s)
            limit = cap.get("ceiling_credits")
            used = used_since(s, cap.get("since"))
            if limit is not None and used + cost > float(limit):
                raise ProviderError(
                    ProviderErrorKind.CEILING,
                    f"the task's Scrape.do ceiling: {used:g} of {float(limit):g} credits used, "
                    f"the next request may cost {cost:g}",
                )
            rate = usd_rate(s)
            budget.check(s, None if rate is None else cost * rate, PROVIDER)
            row = s.get(ProviderKey, (PROVIDER, key.role))
            if row is not None and row.exhausted_at is not None:
                raise ProviderError(ProviderErrorKind.QUOTA, f"the {key.role} key is exhausted")
            if row is not None and row.remaining is not None:
                pending = float(
                    s.scalar(
                        select(func.coalesce(func.sum(ProviderUsage.credits), 0.0)).where(
                            ProviderUsage.provider == PROVIDER,
                            ProviderUsage.key_role == key.role,
                            ProviderUsage.outcome == "reserved",
                        )
                    )
                    or 0.0
                )
                if row.remaining - pending < cost:
                    raise KeyBalanceLow(
                        ProviderErrorKind.QUOTA,
                        f"the {key.role} key has {row.remaining} credits measured "
                        f"({pending:g} reserved), the next request may cost {cost:g}",
                    )
            usage = ProviderUsage(
                provider=PROVIDER,
                key_role=key.role,
                key_fingerprint=key.fingerprint,
                run_id=run_id,
                retailer=retailer,
                purpose=purpose[:32],
                endpoint=endpoint[:64],
                target_url=target_url,
                outcome="reserved",
                credits=cost,
                cost_source="reserved",
                elapsed_ms=0,
                attempt=attempt,
                api_product=api_product(endpoint)[:64],
                segment_id=segment_id,
                worker=(worker or "")[:64] or None,
                cost_usd=None if rate is None else cost * rate,
            )
            s.add(usage)
            s.flush()
            rid = usage.id
            s.commit()
            return rid

    def settle(self, row_id: str, answer: Answer) -> float | None:
        """Settle the row to what the provider charged; returns its dollar figure (None: price unknown)."""
        with self.factory() as s:
            self._lock(s)
            row = s.get(ProviderUsage, row_id)
            if row is None:
                return None
            rate = usd_rate(s)
            usd = None if rate is None else answer.credits * rate
            row.cost_usd = usd
            row.status, row.credits, row.cost_source = answer.status, answer.credits, answer.cost_source
            row.outcome = (answer.kind or "ok")[:32]
            row.remaining_after, row.request_id = answer.remaining, (answer.request_id or None)
            row.elapsed_ms = answer.elapsed_ms
            if answer.remaining is not None:
                key = s.get(ProviderKey, (PROVIDER, answer.key_role))
                if key is not None:
                    key.remaining, key.read_at, key.read_source = answer.remaining, utcnow(), "header"
                    key.updated_at = utcnow()
            s.commit()
            return usd

    def release(self, row_id: str, outcome: str, *, charged_unknown: bool = False) -> None:
        """A reservation without an answer: never sent (no cost), or sent and unanswered
        (``charged_unknown``: the reserved cost is kept as possibly charged, ``cost_source`` "unknown")."""
        with self.factory() as s:
            self._lock(s)
            row = s.get(ProviderUsage, row_id)
            if row is not None and row.outcome == "reserved":
                row.outcome = outcome[:32]
                if charged_unknown:
                    row.cost_source = "unknown"
                else:
                    row.credits, row.cost_source = 0.0, "rule"
                    row.cost_usd = None if row.cost_usd is None else 0.0
            s.commit()

    def exhaust(self, key: Key, reason: str, actor: str, run_id: str | None) -> Key | None:
        """Mark ``key`` exhausted (confirmed by the caller) and return the next usable key."""
        with self.factory() as s:
            self._lock(s)
            row = s.get(ProviderKey, (PROVIDER, key.role))
            if row is not None and row.exhausted_at is None:
                row.exhausted_at, row.exhausted_reason, row.updated_at = utcnow(), reason[:500], utcnow()
            nxt = None
            rows = key_rows(s)
            for k in self.keys:
                r = rows.get(k.role)
                if k.role != key.role and (r is None or r.exhausted_at is None):
                    nxt = k
                    break
            s.add(
                AuditLog(
                    actor=actor,
                    action="provider_failover" if nxt else "provider_exhausted",
                    target=f"{PROVIDER}:{key.role}",
                    reason=reason[:500],
                    data={
                        "from": key.role,
                        "from_fingerprint": key.fingerprint,
                        "to": nxt.role if nxt else None,
                        "reason": reason[:500],
                        "run_id": run_id,
                        "at": iso(utcnow()),
                    },
                )
            )
            if run_id is not None:  # also in the run's own activity
                s.add(
                    Event(
                        run_id=run_id,
                        level="WARN",
                        code="PROVIDER_FAILOVER" if nxt else "PROVIDER_EXHAUSTED",
                        message=f"Scrape.do {key.role} key exhausted (confirmed by its own balance reading)"
                        + (f"; the {nxt.role} key takes over" if nxt else "; no key left"),
                        data={"from": key.role, "to": nxt.role if nxt else None, "reason": reason[:500]},
                    )
                )
            s.commit()
            return nxt


# -- the transport ---------------------------------------------------------------------------------------


@dataclass
class Request:
    endpoint: str  # WALMART_STORE_ENDPOINT | GENERAL_ENDPOINT
    params: dict[str, str]  # without the token
    max_cost: float
    purpose: str


class Transport:
    """Requests through Scrape.do with the active key, the ledger and bounded retries."""

    # Tests point this at an in-memory mock of Scrape.do (never at the real API).
    client_factory: ClassVar[Callable[[], httpx.AsyncClient] | None] = None

    def __init__(
        self,
        ledger: Ledger,
        *,
        run_id: str | None,
        retailer: str | None,
        actor: str = "collector",
        timeout_s: float = 130.0,
        max_attempts: int = 3,
        pause_s: float = 3.0,
        client: httpx.AsyncClient | None = None,
        segment_id: str | None = None,
        worker: str | None = None,
    ):
        self.ledger, self.run_id, self.retailer, self.actor = ledger, run_id, retailer, actor
        self.max_attempts, self.pause_s = max_attempts, pause_s
        self.segment_id, self.worker = segment_id, worker
        factory = Transport.client_factory
        self.http = client or (
            factory() if factory else httpx.AsyncClient(timeout=timeout_s, follow_redirects=False)
        )
        self._last_info = 0.0
        self.events: list[dict[str, Any]] = []

    async def aclose(self) -> None:
        await self.http.aclose()

    async def info(self, key: Key) -> dict[str, Any]:
        """``GET /info`` (free, 10 a minute): the key's plan and remaining credits."""
        wait = INFO_MIN_INTERVAL_S - (monotonic() - self._last_info)
        if wait > 0:
            await asyncio.sleep(wait)
        self._last_info = monotonic()
        try:
            r = await self.http.get(f"{API_BASE}/info", params={"token": key.token.get_secret_value()})
        except httpx.HTTPError as exc:
            raise ProviderError(
                ProviderErrorKind.NETWORK, redact(f"{type(exc).__name__}: {exc}", [key])
            ) from None
        if r.status_code != 200:
            kind = ProviderErrorKind.AUTH if r.status_code in (401, 403) else ProviderErrorKind.PROVIDER
            raise ProviderError(kind, f"/info answered HTTP {r.status_code}: {redact(r.text[:200], [key])}")
        data: dict[str, Any] = r.json()
        return data

    async def read_balances(self) -> dict[str, dict[str, Any]]:
        out: dict[str, dict[str, Any]] = {}
        for k in self.ledger.keys:
            try:
                info = await self.info(k)
            except ProviderError as exc:
                out[k.role] = {"error": str(exc)[:200], "fingerprint": k.fingerprint}
                continue
            with self.ledger.factory() as s:
                record_reading(s, k, info, "info")
                s.commit()
            out[k.role] = {"fingerprint": k.fingerprint, "read_at": iso(utcnow()), **info}
        return out

    async def _confirmed_exhausted(self, key: Key, req: Request) -> tuple[bool, int | None]:
        """The key's own reading (``GET /info``): exhausted when it cannot pay this request."""
        try:
            info = await self.info(key)
        except ProviderError:
            return False, None
        remaining = _int(info.get("RemainingMonthlyRequest"))
        with self.ledger.factory() as s:
            record_reading(s, key, info, "info")
            s.commit()
        return remaining is not None and remaining < req.max_cost, remaining

    async def fetch(self, req: Request) -> Answer:
        """One request: each usable key at most once (re-read once when its measured balance looks too
        low); retries for provider failures and rate limits; a switch only on confirmed exhaustion."""
        tried: set[str] = set()
        rechecked: set[str] = set()
        failovers: list[dict[str, Any]] = []
        while True:
            key = self.ledger.active()
            if key is None or key.role in tried:
                raise ProviderError(
                    ProviderErrorKind.QUOTA,
                    "every Scrape.do key is exhausted (confirmed by the provider's own balance)",
                )
            try:
                answer = await self._with_key(key, req)
            except KeyBalanceLow as low:
                confirmed, remaining = await self._confirmed_exhausted(key, req)
                if not confirmed:
                    if key.role in rechecked:
                        raise
                    rechecked.add(key.role)  # the account shows more than measured: try it again once
                    continue
                reason = (
                    f"{low}; /info RemainingMonthlyRequest={remaining} (below the request's {req.max_cost:g})"
                )
            else:
                answer.failovers = failovers
                if answer.kind != "balance":
                    return answer
                confirmed, remaining = await self._confirmed_exhausted(key, req)
                if not confirmed:
                    return answer  # not confirmed: a provider answer the run stops on, never a switch
                reason = (
                    f"HTTP {answer.status} on {req.endpoint}; /info RemainingMonthlyRequest={remaining} "
                    f"(below the request's {req.max_cost:g})"
                )
            tried.add(key.role)
            nxt = self.ledger.exhaust(key, reason, self.actor, self.run_id)
            failovers.append(
                {"at": iso(utcnow()), "from": key.role, "to": nxt.role if nxt else None, "reason": reason}
            )
            self.events.append(
                {"code": "PROVIDER_FAILOVER", "from": key.role, "to": nxt.role if nxt else None}
            )
            if nxt is None:
                raise ProviderError(ProviderErrorKind.QUOTA, f"every Scrape.do key is exhausted: {reason}")

    async def _with_key(self, key: Key, req: Request) -> Answer:
        attempts: list[dict[str, Any]] = []
        t_all = monotonic()
        answer: Answer | None = None
        spent_usd: float | None = None
        for attempt in range(1, self.max_attempts + 1):
            row_id = self.ledger.reserve(
                key,
                req.max_cost,
                run_id=self.run_id,
                retailer=self.retailer,
                purpose=req.purpose,
                endpoint=req.endpoint,
                target_url=req.params.get("url", "")[:2000],
                attempt=attempt,
                segment_id=self.segment_id,
                worker=self.worker,
            )
            t0 = monotonic()
            try:
                r = await self.http.get(
                    f"{API_BASE}{req.endpoint}", params={**req.params, "token": key.token.get_secret_value()}
                )
            except httpx.HTTPError as exc:
                # Not connected: the provider never saw the request. Otherwise it may have answered (and
                # charged) after the connection failed: the reserved cost is kept, marked unknown.
                unsent = isinstance(exc, (httpx.ConnectError, httpx.ConnectTimeout))
                self.ledger.release(row_id, "network", charged_unknown=not unsent)
                attempts.append({"attempt": attempt, "error": redact(f"{type(exc).__name__}", [key])})
                if attempt == self.max_attempts:
                    raise ProviderError(
                        ProviderErrorKind.NETWORK, redact(f"{type(exc).__name__}: {exc}", [key])[:300]
                    ) from None
                await asyncio.sleep(self.pause_s * attempt)
                continue
            except BaseException:
                # Cancelled in flight (the collector service is stopping): the provider may still answer
                # and charge; the reserved cost is kept, marked unknown, and the run resumes from its
                # checkpoint (the page is requested again).
                self.ledger.release(row_id, "cancelled", charged_unknown=True)
                raise
            elapsed = int((monotonic() - t0) * 1000)
            headers = {k.lower(): v for k, v in r.headers.items() if k.lower().startswith("scrape.do")}
            headers.pop("scrape.do-cookies", None)
            kind = classify(r.status_code, r.content)
            cost_header = headers.get("scrape.do-request-cost", "")
            if re.fullmatch(r"\d+(?:\.\d+)?", cost_header):
                credits, source = float(cost_header), "header"
            else:
                charged_kind = kind is None or kind in ("not_found", "target_400")
                credits, source = (req.max_cost if charged_kind else 0.0), "rule"
            answer = Answer(
                url=req.params.get("url", ""),
                endpoint=req.endpoint,
                status=r.status_code,
                body=r.content,
                headers=headers,
                kind=kind,
                credits=credits,
                cost_source=source,
                remaining=_int(headers.get("scrape.do-remaining-credits")),
                request_id=headers.get("scrape.do-request-id") or headers.get("scrape.do-rid") or "",
                key_role=key.role,
                key_fingerprint=key.fingerprint,
                elapsed_ms=elapsed,
            )
            usd = self.ledger.settle(row_id, answer)
            answer.cost_usd = usd
            spent_usd = (spent_usd or 0.0) + usd if usd is not None else spent_usd
            attempts.append(
                {
                    "attempt": attempt,
                    "status": r.status_code,
                    "kind": kind,
                    "credits": credits,
                    "elapsed_ms": elapsed,
                    "request_id": answer.request_id,
                }
            )
            if kind in (None, "not_found", "auth", "balance", "bad_parameters", "store_pair", "target_400"):
                break
            if attempt < self.max_attempts:
                delay = self.pause_s * attempt
                if kind == "rate_limit":
                    ra = parse_retry_after(r.headers.get("retry-after"), utcnow())
                    delay = min(MAX_RETRY_AFTER_S, ra if ra is not None else 10.0)
                await asyncio.sleep(delay)
        assert answer is not None
        answer.attempts = attempts
        answer.elapsed_ms = int((monotonic() - t_all) * 1000)
        answer.cost_usd = spent_usd
        return answer
