"""Oxylabs Web API as a collection provider: the key, the spending ledger and the transport.

Documentation read 2026-10-26 (developers.oxylabs.io): ``/scrape`` (``POST /v1/scrape`` with ``url``,
``output``, ``location``, ``device``, ``run_js``; the answer ``{status, results[{html, markdown, json,
screenshot, metadata}], params, metadata{timestamp, request_id}}``; a 150 s client timeout), the Walmart
scraper (``POST /v1/scrape/walmart``: ``url`` "a Walmart product or search URL", ``fulfillment_type``,
``store_id``; its OPTIONS answer of 2026-10-26 also lists ``delivery_zip``), Troubleshooting (status codes;
``500 REQUEST_FAILED_AFTER_TOO_MANY_RETRIES`` is not charged; retry 408, 429 and 5xx with backoff, about
three attempts; a 429 that persists for more than 30 s is an exhausted quota), Authentication
(``Authorization: Bearer <key>``; Basic is refused) and the price page oxylabs.io/products/web-api (per
1,000 results).

This is the Web API, used with its Bearer key. The Classic Web Scraper API (realtime.oxylabs.io, an API
username and password) is another product: a Bearer key is never used as a username and password here.

Key. ``OXYLABS_WEB_API_KEY``, or ``OXYLABS_WEB_API_KEY_FILE`` naming a secret file that holds the key alone
or one ``NAME=value`` or ``NAME: value`` line. Only its fingerprint is stored or shown; the key travels in
the Authorization header only, never in a URL, a log, an error or a stored file.

Ledger. Oxylabs documents no balance or usage API, so spending is bounded here. Each submission (every
attempt is one) reserves one result at the configured rate in ``provider_usage`` under advisory locks,
against the ceiling an operator set (``set-ceiling --provider oxylabs``: submissions, US dollars, minutes
from the first submission) and the task's budget across providers (``budget.py``). With no ceiling set no
request is sent. A 200 answer is settled as one charged result; the documented free failure (500
REQUEST_FAILED_AFTER_TOO_MANY_RETRIES) and an authentication refusal (no account was reached) as not
charged; any other answer, and a request cancelled or cut after it was sent, keeps its reserved cost as
possibly charged (``cost_source`` "unknown").

Account gate (1.6.0). When several collectors share one provider account and one allowance, an operator's
harness can set :attr:`OxylabsTransport.account_gate_factory` to an account-wide controller outside this
collector (:class:`AccountGate`). It is consulted for every submission after this collector's own ledger has
reserved it: the gate reserves the submission's worst case before anything is sent, is told just before the
request leaves, and then learns the outcome. A refusal sends nothing and stops the run as a spending ceiling
does. A submission sent without a usable answer is reported to the gate as unknown, never as free. Without a
gate (the default) nothing changes.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import random
import re
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from time import monotonic
from typing import Any, ClassVar, Protocol

import httpx
from pydantic import SecretStr
from sqlalchemy import func, select, text, update
from sqlalchemy.orm import Session, sessionmaker

from walmart_headless.acquisition import budget
from walmart_headless.acquisition.challenge import parse_retry_after
from walmart_headless.acquisition.errors import ProviderError, ProviderErrorKind
from walmart_headless.acquisition.scrapedo import Answer, Key
from walmart_headless.core.timeutil import iso, utcnow
from walmart_headless.db.models import ProviderUsage, SettingRow

PROVIDER = "oxylabs"
API_PRODUCT = "oxylabs web api"
API_BASE = "https://webapi.oxylabs.io"
WALMART_ENDPOINT = "/v1/scrape/walmart"
GENERAL_ENDPOINT = "/v1/scrape"
ENV_KEY = "OXYLABS_WEB_API_KEY"
ENV_KEY_FILE = "OXYLABS_WEB_API_KEY_FILE"
KEY_NAMES = (ENV_KEY, "OXYLABS_API", "OXYLABS_API_KEY")
SETTINGS_ROW = "provider:oxylabs"
# The highest per-result rate the price page lists without AI parsing (custom domain with JavaScript,
# $1.50 per 1,000 results; Walmart is listed under "other targets" at $1.00): the default reservation.
DEFAULT_USD_PER_RESULT = 0.0015
MAX_RETRY_AFTER_S = 60.0
RATE_LIMIT_PAUSE_S = 16.0  # three attempts then span more than 30 s: a 429 that lasts is a quota
QUOTA_AFTER_S = 30.0
STALE_RESERVATION_S = 600  # longer than three attempts of a request can last
ERROR_BODY_BYTES = 20_000
REDACTED = "[REDACTED]"
_LOCK_ID = int.from_bytes(hashlib.sha256(b"walmart_headless:provider:oxylabs").digest()[:4], "big")
_NAMED = re.compile(r"^(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*[=:]\s*(.*)$")

# Answer kinds (None: a usable page) and whether the request is charged: True, False, or None (unknown).
CHARGED: dict[str | None, bool | None] = {
    None: True,
    "auth": False,
    "provider_failed_free": False,
}
# Kinds never retried: retrying the same request cannot change them.
FINAL_KINDS = frozenset({None, "auth", "entitlement", "bad_request", "empty_result", "quota"})


# -- the key -------------------------------------------------------------------------------------------


def _file_token(path: Path) -> str:
    """A secret file: the key alone, or a ``NAME=value`` / ``NAME: value`` line (``KEY_NAMES``)."""
    lines = [
        x.strip()
        for x in path.read_text(encoding="utf-8-sig").splitlines()
        if x.strip() and not x.strip().startswith("#")
    ]
    for line in lines:
        m = _NAMED.match(line)
        if m and m.group(1) in KEY_NAMES:
            value = m.group(2).strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            return value.strip()
    return lines[0] if len(lines) == 1 and not _NAMED.match(lines[0]) else ""


def load_key(environ: Mapping[str, str] | None = None) -> Key | None:
    env = os.environ if environ is None else environ
    token = (env.get(ENV_KEY) or "").strip()
    path = (env.get(ENV_KEY_FILE) or "").strip()
    if not token and path and Path(path).is_file():
        token = _file_token(Path(path))
    return Key("primary", SecretStr(token)) if token else None


def redact(text_: str, key: Key | None) -> str:
    if key is not None and key.token.get_secret_value():
        text_ = text_.replace(key.token.get_secret_value(), REDACTED)
    return re.sub(r"(?i)\bbearer\s+[^\s'\"<>,;]+", f"Bearer {REDACTED}", text_)


# -- the ceiling ------------------------------------------------------------------------------------------


def ceiling(s: Session) -> dict[str, Any]:
    row = s.get(SettingRow, SETTINGS_ROW)
    return dict(row.value) if row else {}


def set_ceiling(
    s: Session,
    *,
    max_submissions: int | None,
    max_usd: float | None,
    max_minutes: float | None,
    usd_per_result: float | None,
    basis: str,
    actor: str,
) -> dict[str, Any]:
    """The Oxylabs spending ceiling from now on (counted from this moment, over every run and process)."""
    if max_submissions is None and max_usd is None:
        raise ValueError("an Oxylabs ceiling needs a number of submissions or an amount of US dollars")
    value = {
        "max_submissions": max_submissions,
        "max_usd": max_usd,
        "max_minutes": max_minutes,
        "usd_per_result": usd_per_result if usd_per_result is not None else DEFAULT_USD_PER_RESULT,
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


def usage_since(s: Session, since: str | None) -> dict[str, Any]:
    """Submissions, results and dollars recorded since ``since`` (every outcome counts: a retry is one)."""
    q = select(
        func.count(),
        func.coalesce(func.sum(ProviderUsage.credits), 0.0),
        func.coalesce(func.sum(ProviderUsage.cost_usd), 0.0),
        func.min(ProviderUsage.at),
        func.count().filter(ProviderUsage.cost_source == "unknown"),
    ).where(ProviderUsage.provider == PROVIDER)
    if since:
        q = q.where(ProviderUsage.at >= datetime.fromisoformat(since.replace("Z", "+00:00")))
    n, results, usd, first, unknown = s.execute(q).one()
    return {
        "submissions": int(n or 0),
        "results": float(results or 0.0),
        "usd": float(usd or 0.0),
        "first_at": first,
        "possibly_charged": int(unknown or 0),
    }


def ceiling_room(s: Session) -> tuple[int | None, dict[str, Any]]:
    """How many more submissions the operator's ceiling and the task's budget allow now (None: no ceiling
    is set, so none), with the reading recorded by the collector."""
    cap = ceiling(s)
    if not cap:
        return None, {}
    rate = float(cap.get("usd_per_result") or DEFAULT_USD_PER_RESULT)
    used = usage_since(s, cap.get("since"))
    rooms: dict[str, int] = {}
    if cap.get("max_submissions") is not None:
        rooms["submissions"] = int(cap["max_submissions"]) - used["submissions"]
    if cap.get("max_usd") is not None:
        rooms["usd"] = int((float(cap["max_usd"]) - used["usd"] + 1e-9) // rate)
    minutes, first = cap.get("max_minutes"), used["first_at"]
    window_end = (
        first + timedelta(minutes=float(minutes)) if minutes is not None and first is not None else None
    )
    if window_end is not None and utcnow() > window_end:
        rooms["window"] = 0
    left = budget.room(s)
    if left is not None:
        rooms["task_budget"] = int((left + 1e-9) // rate)
    n = max(0, min(rooms.values())) if rooms else 0
    return n, {
        "ceiling": cap,
        "used": {k: (iso(v) if isinstance(v, datetime) else v) for k, v in used.items()},
        "usd_per_result": rate,
        "rooms": rooms,
        "room": n,
        "window_end": iso(window_end) if window_end else None,
    }


# -- the ledger -------------------------------------------------------------------------------------------


class OxylabsLedger:
    """Reservations and settlements in ``provider_usage`` (shared by every worker and process)."""

    def __init__(self, factory: sessionmaker[Session], key: Key):
        self.factory, self.key = factory, key

    def _lock(self, s: Session) -> None:
        budget.lock(s)
        s.execute(text("SELECT pg_advisory_xact_lock(:id)"), {"id": _LOCK_ID})

    def reserve(
        self,
        *,
        run_id: str | None,
        retailer: str | None,
        purpose: str,
        endpoint: str,
        target_url: str,
        attempt: int,
        segment_id: str | None = None,
        worker: str | None = None,
    ) -> tuple[str, float]:
        """A reservation row and its dollar figure, or :class:`ProviderError` (CEILING) when the ceiling,
        its time window or the task's budget leaves no room for one more submission."""
        with self.factory() as s:
            self._lock(s)
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
            if not cap:
                raise ProviderError(
                    ProviderErrorKind.CEILING,
                    "no Oxylabs ceiling is set ('walmart-collector set-ceiling --provider oxylabs'): no "
                    "request is sent without one",
                )
            rate = float(cap.get("usd_per_result") or DEFAULT_USD_PER_RESULT)
            used = usage_since(s, cap.get("since"))
            n_max = cap.get("max_submissions")
            if n_max is not None and used["submissions"] + 1 > int(n_max):
                raise ProviderError(
                    ProviderErrorKind.CEILING,
                    f"the Oxylabs ceiling: {used['submissions']} of {int(n_max)} submissions used",
                )
            usd_max = cap.get("max_usd")
            if usd_max is not None and used["usd"] + rate > float(usd_max) + 1e-9:
                raise ProviderError(
                    ProviderErrorKind.CEILING,
                    f"the Oxylabs ceiling: ${used['usd']:.4f} of ${float(usd_max):.4f} recorded, the next "
                    f"submission may cost ${rate:.4f}",
                )
            minutes = cap.get("max_minutes")
            first = used["first_at"]
            if (
                minutes is not None
                and first is not None
                and utcnow() > first + timedelta(minutes=float(minutes))
            ):
                raise ProviderError(
                    ProviderErrorKind.CEILING,
                    f"the Oxylabs ceiling's window of {float(minutes):g} minutes from the first submission "
                    f"({iso(first)}) has ended",
                )
            budget.check(s, rate, PROVIDER)
            usage = ProviderUsage(
                provider=PROVIDER,
                key_role=self.key.role,
                key_fingerprint=self.key.fingerprint,
                run_id=run_id,
                retailer=retailer,
                purpose=purpose[:32],
                endpoint=endpoint[:64],
                target_url=target_url,
                outcome="reserved",
                credits=1.0,
                cost_source="reserved",
                elapsed_ms=0,
                attempt=attempt,
                api_product=f"{API_PRODUCT} {endpoint}"[:64],
                segment_id=segment_id,
                worker=(worker or "")[:64] or None,
                cost_usd=rate,
            )
            s.add(usage)
            s.flush()
            rid = usage.id
            s.commit()
            return rid, rate

    def settle(self, row_id: str, answer: Answer, charged: bool | None, rate: float) -> None:
        with self.factory() as s:
            self._lock(s)
            row = s.get(ProviderUsage, row_id)
            if row is None:
                return
            row.status = answer.status
            row.outcome = (answer.kind or "ok")[:32]
            row.request_id = answer.request_id or None
            row.elapsed_ms = answer.elapsed_ms
            if charged is None:
                row.credits, row.cost_usd, row.cost_source = 1.0, rate, "unknown"
            else:
                row.credits = 1.0 if charged else 0.0
                row.cost_usd = rate if charged else 0.0
                row.cost_source = "rule"
            s.commit()

    def release(self, row_id: str, outcome: str, *, charged_unknown: bool) -> None:
        """A reservation without an answer: never sent (no cost), or sent and unanswered (the reserved
        cost is kept as possibly charged)."""
        with self.factory() as s:
            self._lock(s)
            row = s.get(ProviderUsage, row_id)
            if row is not None and row.outcome == "reserved":
                row.outcome = outcome[:32]
                if charged_unknown:
                    row.cost_source = "unknown"
                else:
                    row.credits, row.cost_usd, row.cost_source = 0.0, 0.0, "rule"
            s.commit()


# -- an account-wide gate (1.6.0) ----------------------------------------------------------------------------


class GateRefused(RuntimeError):
    """The account-wide gate refused this submission: nothing is sent."""


class AccountGate(Protocol):
    """An optional spending controller outside this collector, shared with the other collectors that use the
    same provider account. For one submission, in order: :meth:`reserve` (a refusal raises
    :class:`GateRefused`: nothing is sent), :meth:`dispatched` just before the request leaves (a refusal:
    :meth:`unsent`, nothing is sent), then exactly one of :meth:`settled` (an answer came), :meth:`unknown`
    (sent, no answer: its reservation stays held)."""

    def reserve(
        self, *, purpose: str, endpoint: str, target_url: str, attempt: int, usd: float, key: str
    ) -> str:
        """Reserve one submission's worst case; returns the gate's own reference for it."""
        ...

    def dispatched(self, ref: str) -> None: ...

    def unsent(self, ref: str, reason: str) -> None: ...

    def settled(
        self, ref: str, *, status: int, kind: str | None, charged: bool | None, usd: float
    ) -> None: ...

    def unknown(self, ref: str, reason: str) -> None: ...


# -- answers ----------------------------------------------------------------------------------------------


def classify(status: int, body: bytes, html: str | None) -> str | None:
    """None for a usable page; else the failure's kind (Troubleshooting: status codes)."""
    if status == 200:
        return None if html else "empty_result"
    if status == 401:
        return "auth"
    if status in (402, 403):
        return "entitlement"
    if status in (400, 404, 405, 422) or status == 202:
        return "bad_request"
    if status == 408:
        return "timeout"
    if status == 429:
        return "rate_limit"
    if status >= 500 and b"REQUEST_FAILED_AFTER_TOO_MANY_RETRIES" in body[:4000]:
        return "provider_failed_free"
    return "provider_failure"


def envelope(content: bytes) -> tuple[str | None, dict[str, Any]]:
    """The page's markup (``results[0].html``) and the answer's own metadata (no page content)."""
    try:
        env = json.loads(content) if content else None
    except ValueError:
        return None, {"envelope": "not JSON"}
    if not isinstance(env, dict):
        return None, {"envelope": type(env).__name__}
    meta: dict[str, Any] = {}
    raw_md = env.get("metadata")
    md: dict[str, Any] = raw_md if isinstance(raw_md, dict) else {}
    meta["request_id"] = str(md.get("request_id") or "")
    meta["timestamp"] = md.get("timestamp")
    for k in ("status", "state", "title", "detail", "errors"):
        if env.get(k) is not None:
            meta[k] = env[k]
    if isinstance(env.get("params"), dict):
        meta["params"] = env["params"]
    html: str | None = None
    results = env.get("results")
    if isinstance(results, list) and results and isinstance(results[0], dict):
        r0 = results[0]
        meta["result_metadata"] = r0.get("metadata")
        meta["result_formats"] = sorted(k for k, v in r0.items() if v is not None and k != "metadata")
        if isinstance(r0.get("html"), str):
            html = r0["html"]
    return html, meta


# -- the transport ------------------------------------------------------------------------------------------


@dataclass
class OxyRequest:
    endpoint: str  # WALMART_ENDPOINT | GENERAL_ENDPOINT
    body: dict[str, Any]  # the JSON body (never the key)
    purpose: str

    @property
    def url(self) -> str:
        return str(self.body.get("url") or "")


class OxylabsTransport:
    """Requests to the Web API with the ledger and bounded retries (at most ``max_attempts`` submissions
    for one request; backoff with jitter; a ``Retry-After`` honoured up to a minute)."""

    # Tests point this at an in-memory mock of the Web API (never at the real API).
    client_factory: ClassVar[Callable[[], httpx.AsyncClient] | None] = None
    # 1.6.0: an account-wide spending gate, set by an operator's harness (None: this collector's own ceiling
    # and budget apply alone).
    account_gate_factory: ClassVar[Callable[[], AccountGate] | None] = None

    def __init__(
        self,
        ledger: OxylabsLedger,
        *,
        run_id: str | None,
        retailer: str | None,
        actor: str = "collector",
        timeout_s: float = 150.0,
        max_attempts: int = 3,
        client: httpx.AsyncClient | None = None,
        segment_id: str | None = None,
        worker: str | None = None,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
        account_gate: AccountGate | None = None,
    ):
        self.ledger, self.run_id, self.retailer, self.actor = ledger, run_id, retailer, actor
        gate_factory = OxylabsTransport.account_gate_factory
        self.gate: AccountGate | None = account_gate or (gate_factory() if gate_factory else None)
        self.gate_errors: list[str] = []
        self.max_attempts = max_attempts
        self.segment_id, self.worker = segment_id, worker
        self.sleep = sleep
        factory = OxylabsTransport.client_factory
        self.http = client or (
            factory() if factory else httpx.AsyncClient(timeout=timeout_s, follow_redirects=False)
        )
        self.events: list[dict[str, Any]] = []

    @property
    def key(self) -> Key:
        return self.ledger.key

    async def aclose(self) -> None:
        await self.http.aclose()

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.key.token.get_secret_value()}",
            "Content-Type": "application/json",
        }

    def _gate_open(self, row_id: str, req: OxyRequest, attempt: int, rate: float) -> str | None:
        """The account-wide gate's reservation and dispatch mark, or a CEILING error with nothing sent."""
        if self.gate is None:
            return None
        ref: str | None = None
        try:
            ref = self.gate.reserve(
                purpose=req.purpose,
                endpoint=req.endpoint,
                target_url=req.url[:2000],
                attempt=attempt,
                usd=rate,
                key=row_id,
            )
            self.gate.dispatched(ref)
        except Exception as exc:  # any failure of the gate is a refusal: nothing is sent
            if ref is not None:
                try:
                    self.gate.unsent(ref, f"refused at dispatch: {type(exc).__name__}")
                except Exception as exc2:  # recorded; the reservation stays held there
                    self.gate_errors.append(f"unsent: {type(exc2).__name__}: {exc2}"[:300])
            self.ledger.release(row_id, "gate_refused", charged_unknown=False)
            raise ProviderError(
                ProviderErrorKind.CEILING,
                redact(f"the account-wide spending gate refused the submission: {exc}", self.key)[:300],
            ) from None
        return ref

    def _gate_close(self, ref: str | None, outcome: str, **detail: Any) -> None:
        """Report an outcome (``settled`` or ``unknown``) to the gate. A failure there is recorded and never
        loses the answer: the gate keeps that submission's reservation held."""
        if self.gate is None or ref is None:
            return
        try:
            if outcome == "settled":
                self.gate.settled(ref, **detail)
            else:
                self.gate.unknown(ref, str(detail.get("reason") or ""))
        except Exception as exc:
            self.gate_errors.append(redact(f"{type(exc).__name__}: {exc}", self.key)[:300])

    async def fetch(self, req: OxyRequest) -> Answer:
        attempts: list[dict[str, Any]] = []
        t_all = monotonic()
        first_429: float | None = None
        answer: Answer | None = None
        for attempt in range(1, self.max_attempts + 1):
            row_id, rate = self.ledger.reserve(
                run_id=self.run_id,
                retailer=self.retailer,
                purpose=req.purpose,
                endpoint=req.endpoint,
                target_url=req.url[:2000],
                attempt=attempt,
                segment_id=self.segment_id,
                worker=self.worker,
            )
            gate_ref = self._gate_open(row_id, req, attempt, rate)
            t0 = monotonic()
            try:
                r = await self.http.post(f"{API_BASE}{req.endpoint}", json=req.body, headers=self._headers())
            except httpx.HTTPError as exc:
                # Not connected: the provider never saw it. Otherwise it may have run (and charged) it.
                unsent = isinstance(exc, (httpx.ConnectError, httpx.ConnectTimeout))
                self.ledger.release(row_id, "network", charged_unknown=not unsent)
                # The account-wide gate keeps even an unconnected submission held: it was marked dispatched.
                self._gate_close(gate_ref, "unknown", reason=f"no answer: {type(exc).__name__}")
                attempts.append(
                    {
                        "attempt": attempt,
                        "error": type(exc).__name__,
                        "charged": False if unsent else None,
                        "usd": 0.0 if unsent else rate,
                        "elapsed_ms": int((monotonic() - t0) * 1000),
                    }
                )
                if attempt == self.max_attempts:
                    raise ProviderError(
                        ProviderErrorKind.NETWORK,
                        redact(f"Oxylabs {req.endpoint}: {type(exc).__name__}: {exc}", self.key)[:300],
                        units=float(sum(1 for a in attempts if a.get("charged") is not False)),
                        usd=round(sum(float(a.get("usd") or 0.0) for a in attempts), 6),
                    ) from None
                await self.sleep(2**attempt + random.random())
                continue
            except BaseException:
                # Cancelled in flight (the collector is stopping): it may still run and be charged.
                self.ledger.release(row_id, "cancelled", charged_unknown=True)
                self._gate_close(gate_ref, "unknown", reason="cancelled in flight")
                raise
            elapsed = int((monotonic() - t0) * 1000)
            html, meta = envelope(r.content)
            kind = classify(r.status_code, r.content, html)
            if kind == "rate_limit":
                first_429 = first_429 if first_429 is not None else t0
                if monotonic() - first_429 > QUOTA_AFTER_S:
                    kind = "quota"  # documented: a 429 lasting more than 30 s is the account's quota
            charged = CHARGED.get(kind) if kind in CHARGED else None
            body = html.encode("utf-8") if kind is None and html is not None else r.content[:ERROR_BODY_BYTES]
            answer = Answer(
                url=req.url,
                endpoint=req.endpoint,
                status=r.status_code,
                body=body,
                headers={k: v for k, v in meta.items() if v not in (None, "", [], {})},
                kind=kind,
                credits=0.0 if charged is False else 1.0,
                cost_source="rule" if charged is not None else "unknown",
                remaining=None,
                request_id=str(meta.get("request_id") or ""),
                key_role=self.key.role,
                key_fingerprint=self.key.fingerprint,
                elapsed_ms=elapsed,
                cost_usd=0.0 if charged is False else rate,
            )
            self.ledger.settle(row_id, answer, charged, rate)
            self._gate_close(
                gate_ref,
                "settled",
                status=r.status_code,
                kind=kind,
                charged=charged,
                usd=float(answer.cost_usd or 0.0),
            )
            attempts.append(
                {
                    "attempt": attempt,
                    "status": r.status_code,
                    "kind": kind,
                    "charged": charged,
                    "usd": answer.cost_usd,
                    "elapsed_ms": elapsed,
                    "request_id": answer.request_id,
                }
            )
            if kind in FINAL_KINDS or attempt == self.max_attempts:
                break
            delay = 2**attempt + random.random()
            if kind == "rate_limit":
                ra = parse_retry_after(r.headers.get("retry-after"), utcnow())
                delay = min(MAX_RETRY_AFTER_S, max(RATE_LIMIT_PAUSE_S, ra or 0.0))
            await self.sleep(delay)
        assert answer is not None
        answer.attempts = attempts
        answer.elapsed_ms = int((monotonic() - t_all) * 1000)
        # Every submission of this request: charged, or possibly charged (sent without a usable answer).
        answer.credits = float(sum(1 for a in attempts if a.get("charged") is not False))
        answer.cost_usd = round(sum(float(a.get("usd") or 0.0) for a in attempts), 6)
        if any(a.get("charged") is None for a in attempts):
            answer.cost_source = "unknown"
        return answer
