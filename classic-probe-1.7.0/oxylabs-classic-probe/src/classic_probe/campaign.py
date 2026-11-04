"""The Walmart part of a campaign: a short fixed sequence of documented requests, each reserved before it is
sent.

Steps, in order (docs/PAYLOAD_MATRIX.md):

1. ``walmart-search-p1``: ``walmart_search`` for the target's query, store and Pickup, raw and parsed.
2. ``walmart-search-p2``: the same with ``start_page`` 2, only when page 1 says a page 2 exists.
3. ``walmart-product``: ``walmart_product`` for the first product of page 1 that Walmart.com sells with a
Pickup line. 4. ``walmart-category-url``: a required category page by its URL alone. The documentation states
no store or
   fulfillment parameter for this form, so this step finds out whether the page comes for the store, and a
   page for any other store stops the campaign as the limits require. It is last for that reason.

A response is inspected before anything else is sent (checks.py). A stop ends the campaign (a retailer's own
quota ends only that retailer's part) and nothing more is sent. A documented temporary error may be retried
within every limit, and each retry is a new dispatch with its own reservation. Evidence is exported whatever
happened, and an export or cleanup error never sends anything, never touches the ledger's history and never
replaces the reason the campaign stopped.

1.7.0 (the client's second review):

- C2/C3: one session clock bounds every wait (the ledger's lock, the request, a backoff), on the monotonic
  clock as well as the wall clock; the reservation and the last check before sending read the time under the
  ledger's lock, and a request refused at that check is recorded as never sent;
- C4: each answer is kept on disk and indexed in the ledger before the next paid step (captures.py); the
  evidence is exported from that index, never from memory, and says whether every capture was checked;
- C5: a backoff is a real wait (``time.sleep``) unless a test injects another, bounded by the deadline;
  a ``Retry-After`` the provider sends is honoured, and a longer wait than :data:`MAX_RETRY_AFTER_S` ends the
  step.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from classic_probe import checks, contract
from classic_probe.captures import CaptureStore, kept_response, sanitize
from classic_probe.deadline import SessionClock, parse_retry_after
from classic_probe.ledger import BILLABLE, NOT_BILLED, Ledger, LimitReached
from classic_probe.money import RateCard, UnknownRate
from classic_probe.stops import Stop
from classic_probe.targets import Target
from classic_probe.transport import (
    ProviderRequest,
    Transport,
    TransportFailed,
)

__all__ = ["Campaign", "CampaignResult", "StepPlan", "kept_response", "sanitize", "write_json"]

Sleep = Callable[[float], None]

RETRY_WAIT_S = {429: 2.0}  # the documented low-success-rate limit is 1 request a second
DEFAULT_RETRY_WAIT_S = 5.0  # "Please try again a bit later"
MAX_RETRY_AFTER_S = (
    60.0  # 1.7.0 (C5): a provider asking for a longer wait ends the step; nothing waits longer
)
LOCK_WAIT_S = (
    10.0  # 1.7.0 (C3): the most a reservation waits for the ledger's lock (less if less time is left)
)
EXPORT_CHECK_MIN_S = 5.0  # 1.7.0 (C4): captures are checked while at least this much of the session is left


@dataclass(frozen=True)
class StepPlan:
    step: str
    purpose: str
    kind: str  # search | product | category
    request_class: str
    payload: Mapping[str, Any]
    query_string: str
    max_results: int  # the most billable result entries one dispatch can return


@dataclass
class CampaignResult:
    campaign_id: str
    retailer: str
    stop: str | None = None
    detail: str = ""
    steps: list[dict[str, Any]] = field(default_factory=list)
    export_errors: list[str] = field(default_factory=list)
    cleanup_errors: list[str] = field(default_factory=list)
    out_dir: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "campaign_id": self.campaign_id,
            "retailer": self.retailer,
            "stop": self.stop,
            "detail": self.detail,
            "steps": self.steps,
            "export_errors": self.export_errors,
            "cleanup_errors": self.cleanup_errors,
            "out_dir": self.out_dir,
        }


def search_step(target: Target, page: int, last_visible_page: int | None = None) -> StepPlan:
    payload = contract.walmart_search(target.search_query, target.store_id)
    if page > 1:
        payload = contract.next_page_payload(payload, page, last_visible_page)
    return StepPlan(
        f"walmart-search-p{page}",
        f"result page {page} of the store's Pickup search: store, fulfillment, seller, parsing"
        + ("; does the page advance" if page > 1 else ""),
        "search",
        contract.WALMART_SEARCH,
        payload,
        contract.RAW_AND_PARSED,
        2,
    )


def product_step(target: Target, product_id: str) -> StepPlan:
    return StepPlan(
        "walmart-product",
        "the product's own page for the store's Pickup: identity, UPC, store, seller",
        "product",
        contract.WALMART_PRODUCT,
        contract.walmart_product(product_id, target.store_id),
        contract.RAW_AND_PARSED,
        2,
    )


def category_step(target: Target) -> StepPlan:
    return StepPlan(
        "walmart-category-url",
        "a required category page by its URL alone: is it served for the store at all (undocumented)",
        "category",
        contract.URL_ONLY,
        contract.url_only(target.category_probe_url),
        "",
        1,
    )


def planned_steps(target: Target) -> list[StepPlan]:
    """The steps as they are planned before any response (page 2 and the product depend on page 1)."""
    steps = [search_step(target, 1), search_step(target, 2, 2), product_step(target, "<from page 1>")]
    if target.category_probe_url:
        steps.append(category_step(target))
    return steps


class Campaign:
    adapter = "walmart"  # the adapter this class implements (1.6.0 adds marianos.MarianosCampaign)

    def __init__(
        self,
        ledger: Ledger,
        transport: Transport,
        target: Target,
        rates: RateCard,
        *,
        out_dir: Path,
        request_timeout_s: float = 120.0,
        max_attempts: int = 2,
        sleep: Sleep | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        if target.adapter != self.adapter:
            raise ValueError(f"{target.retailer}: this campaign class is the {self.adapter} adapter")
        self.ledger = ledger
        self.transport = transport
        self.target = target
        self.rates = rates
        self.out_dir = out_dir
        self.request_timeout_s = request_timeout_s
        self.max_attempts = max_attempts
        # 1.7.0 (C5): a real wait unless a test injects another; every wait is bounded by the deadline first.
        self.sleep: Sleep = sleep or time.sleep
        self.clock = clock or ledger.clock
        self.result = CampaignResult(ledger.campaign_id, target.retailer, out_dir=str(out_dir))
        self.captures = CaptureStore(out_dir, target.retailer)
        self._session: SessionClock | None = None

    # -- one step --------------------------------------------------------------------------------------

    def session_clock(self) -> SessionClock | None:
        """The session's clock, once the campaign has started (its start is durable in the ledger)."""
        if self._session is None:
            ends = self.ledger.deadlines()
            if ends is None:
                return None
            self._session = SessionClock(
                ends[0],
                export_reserve_s=float(self.ledger.limits.export_reserve_seconds),
                wall=self.clock,
                sleeper=self.sleep,
            )
        return self._session

    def _seconds_left(self) -> float | None:
        """Seconds a request or a wait may still use: the lesser of the wall clock's and the monotonic
        clock's reading (a wall-clock jump never extends it)."""
        session = self.session_clock()
        return None if session is None else session.dispatch_remaining()

    def _dispatch(
        self, plan: StepPlan, inspect: Callable[[checks.Inspection], checks.Inspection]
    ) -> checks.Inspection | None:
        request = ProviderRequest(plan.step, plan.payload, plan.query_string)
        sha = hashlib.sha256(json.dumps(plan.payload, sort_keys=True).encode("utf-8")).hexdigest()
        record: dict[str, Any] = {
            "step": plan.step,
            "purpose": plan.purpose,
            "payload": dict(plan.payload),
            "query_string": plan.query_string,
            "attempts": [],
        }
        self.result.steps.append(record)
        for attempt in range(1, self.max_attempts + 1):
            try:
                amount = self.rates.worst_case(plan.request_class, plan.max_results)
            except UnknownRate as exc:
                self._stop(Stop.FUNDS, f"no reliable upper bound: {exc}")
                return None
            timeout = self._allowance()
            if timeout <= 0:
                self._stop(Stop.DEADLINE, "no time is left before the time kept for export and cleanup")
                return None
            try:
                seq = self.ledger.reserve(
                    retailer=self.target.retailer,
                    step=plan.step,
                    purpose=plan.purpose,
                    request_class=plan.request_class,
                    attempt=attempt,
                    payload_sha256=sha,
                    amount_usd=amount,
                    request_timeout_s=timeout,
                    lock_wait_s=min(LOCK_WAIT_S, timeout),
                )
            except LimitReached as exc:
                self._stop(exc.stop, exc.detail)
                return None
            sent: dict[str, Any] = {"seq": seq, "attempt": attempt, "reserved_usd": str(amount)}
            record["attempts"].append(sent)
            preflight = getattr(self.transport, "preflight", None)
            if preflight is not None:
                try:
                    preflight(request)
                except TransportFailed as exc:
                    self.ledger.release_unsent(seq, str(exc))
                    sent["outcome"] = f"not sent: {exc}"
                    self._stop(Stop.OPERATOR, f"{plan.step}: {exc}")
                    return None
            # The allowance again, after any wait for the ledger's lock, checked under the lock (C3).
            allowance = self._allowance()
            try:
                if allowance <= 0:
                    self.ledger.release_unsent(seq, "no time was left at dispatch")
                    raise LimitReached(Stop.DEADLINE, "at dispatch, no time was left for the request")
                self.ledger.mark_sent(seq, allowance_s=allowance, lock_wait_s=min(LOCK_WAIT_S, allowance))
            except LimitReached as exc:
                sent["outcome"] = f"not sent: {exc.detail}"
                self._stop(exc.stop, f"{plan.step}: {exc.detail}")
                return None
            try:
                response = self.transport.send(request, allowance)
            except TransportFailed as exc:
                self.ledger.mark_unknown(seq, f"no answer: {exc}")
                sent["outcome"] = (
                    "unknown: no answer; the request may have reached the provider and been charged"
                )
                self._stop(Stop.IN_FLIGHT_UNKNOWN, f"{plan.step}: {exc}; its reservation stays")
                return None
            # C4: the answer is kept on disk and indexed before anything else happens.
            try:
                self.ledger.record_capture(seq, self.captures.persist(seq, plan.step, response))
            except Exception as exc:  # noqa: BLE001 - recorded; nothing more is sent
                self.ledger.settle(
                    seq,
                    billing=checks.provider(response).billing,
                    estimated_usd=None,
                    provider_status=response.http_status,
                    retailer_status=None,
                    parser_status=None,
                    job_id=None,
                    note=f"answered, but the answer could not be kept: {type(exc).__name__}",
                )
                sent["outcome"] = "answered, but the answer could not be kept"
                self._stop(
                    Stop.EVIDENCE,
                    f"{plan.step}: the answer could not be kept ({type(exc).__name__}: {exc}); nothing more "
                    "is sent",
                )
                return None
            ins = checks.provider(response)
            if not ins.stop:
                ins = inspect(ins)
            estimate = self._estimate(plan, ins)
            self.ledger.settle(
                seq,
                billing=ins.billing,
                estimated_usd=estimate,
                provider_status=ins.provider_status,
                retailer_status=ins.retailer_statuses[0] if ins.retailer_statuses else None,
                parser_status=ins.parser_status,
                job_id=ins.job_id,
                note=(ins.stop.value + ": " + ins.detail) if ins.stop else "ok",
            )
            facts = {k: v for k, v in ins.facts.items() if k != "results"}
            sent.update(
                provider_status=ins.provider_status,
                retailer_statuses=list(ins.retailer_statuses),
                parser_status=ins.parser_status,
                billing=ins.billing,
                estimated_usd=None if estimate is None else str(estimate),
                facts=facts,
                outcome=(ins.stop.value if ins.stop else "ok"),
                detail=ins.detail,
            )
            if ins.transient and attempt < self.max_attempts:
                wait = RETRY_WAIT_S.get(ins.provider_status, DEFAULT_RETRY_WAIT_S)
                headers = {k.lower(): v for k, v in response.headers.items()}
                asked = parse_retry_after(headers.get("retry-after"), self.clock())
                if asked is not None and asked > MAX_RETRY_AFTER_S:
                    self._stop(
                        Stop.RETRIES_EXHAUSTED,
                        f"{plan.step}: HTTP {ins.provider_status} asks to wait {asked:.0f} s, more than the "
                        f"{MAX_RETRY_AFTER_S:.0f} s this campaign waits: not retried",
                    )
                    return None
                if asked is not None:
                    wait = max(wait, asked)
                left = self._seconds_left()
                if left is not None and wait + 1.0 > left:
                    self._stop(
                        Stop.DEADLINE, f"{plan.step}: a retry after {wait} s would end past the deadline"
                    )
                    return None
                self.ledger.event(
                    "RETRY",
                    f"{plan.step}: HTTP {ins.provider_status}, attempt {attempt + 1} in {wait} s"
                    + (f" (Retry-After {asked:.0f} s)" if asked is not None else ""),
                )
                self.sleep(wait)
                continue
            if ins.stop:
                self._stop(ins.stop, f"{plan.step}: {ins.detail}")
                return None
            return ins
        return None  # pragma: no cover - the loop always returns

    def _allowance(self) -> float:
        """A request's whole allowance now: its own limit, clamped to the time left before the reserve."""
        left = self._seconds_left()
        return self.request_timeout_s if left is None else min(self.request_timeout_s, left)

    def _estimate(self, plan: StepPlan, ins: checks.Inspection) -> Decimal | None:
        """The charge the documented rules suggest, with a confirmed rate: never an invoice."""
        if ins.billing == NOT_BILLED:
            return Decimal(0)
        if ins.billing != BILLABLE:
            return None
        results = ins.billable_results or (1 if ins.provider_status in checks.CALLER_FAULT_HTTP else 0)
        try:
            return self.rates.estimate(plan.request_class, results, rendered=ins.render_forced)
        except KeyError:
            return None

    def _stop(self, code: Stop, detail: str) -> None:
        self.result.stop, self.result.detail = code.value, detail
        self.ledger.stop(code, detail, retailer=self.target.retailer)

    # -- the sequence ----------------------------------------------------------------------------------

    def run(self) -> CampaignResult:
        try:
            self._run()
        finally:
            self._export()
        return self.result

    def _run(self) -> None:
        problems = self.target.live_problems()
        if problems:
            self._stop(Stop.UNVERIFIED_CONTEXT, "; ".join(problems))
            return
        first = self._dispatch(
            search_step(self.target, 1), lambda i: checks.search_page(i, self.target.store_id, 1, None)
        )
        if first is None:
            return
        ids = frozenset(first.facts["item_ids"])
        last = first.facts.get("last_visible_page")
        if isinstance(last, int) and last >= 2:
            second = self._dispatch(
                search_step(self.target, 2, last),
                lambda i: checks.search_page(i, self.target.store_id, 2, ids),
            )
            if second is None:
                return
        else:
            self.ledger.event(
                "SKIPPED", f"walmart-search-p2: page 1 shows no page 2 (last_visible_page {last})"
            )
        product = self._first_local_product(first)
        if product:
            got = self._dispatch(
                product_step(self.target, product),
                lambda i: checks.product_page(i, self.target.store_id, product),
            )
            if got is None:
                return
        else:
            self.ledger.event(
                "SKIPPED", "walmart-product: page 1 shows no Walmart.com product with a Pickup line"
            )
        if self.target.category_probe_url:
            self._dispatch(
                category_step(self.target), lambda i: checks.category_page(i, self.target.store_id)
            )

    def _first_local_product(self, first: checks.Inspection) -> str:
        """The first product of page 1 that Walmart.com sells with a Pickup line, from the page's own data."""
        raw = next(
            (
                r
                for r in first.facts.get("results") or []
                if r.get("type") == "raw" or isinstance(r.get("content"), str)
            ),
            None,
        )
        if raw is None:
            return ""
        from classic_probe.vendor import walmart_page_data as wpd

        for it in wpd.page_items(wpd.next_data(str(raw["content"]))):
            pickup = any(
                f.kind == "PICKUP" and f.store_id in ("", self.target.store_id) for f in it.fulfillment
            )
            if it.seller_name.casefold() == "walmart.com" and pickup and not it.sponsored:
                return it.item_id
        return ""

    # -- evidence --------------------------------------------------------------------------------------

    def _export(self) -> None:
        """Write the evidence from the durable capture index (C4), never from memory. A failure here is
        recorded beside the campaign's own stop and sends nothing. Captures are checked against their files
        while the session has time; the manifest says whether every one was (``complete``)."""
        try:
            self.out_dir.mkdir(parents=True, exist_ok=True)
            recovery = self.captures.recover(self.ledger)
            session = self.session_clock()

            def time_left() -> float:
                return float("inf") if session is None else session.remaining()

            responses, checked = self.captures.verify(
                self.ledger, time_left=time_left, min_left_s=EXPORT_CHECK_MIN_S
            )
            export = {
                "campaign_id": self.ledger.campaign_id,
                "ledger_genesis_id": self.ledger.genesis_id,
                "offline": self.ledger.offline,
                "limits": json.loads(self.ledger.limits.as_json()),
                "totals": self.ledger.totals().as_dict(),
                "dispatches": self.ledger.rows(),
                "events": self.ledger.events(),
                "result": self.result.as_dict(),
                "responses": responses,
                "complete": checked,
                "capture_recovery": recovery,
            }
            write_json(self.out_dir / "campaign_evidence.json", export)
        except Exception as exc:  # noqa: BLE001 - recorded; the campaign's own outcome stands
            self.result.export_errors.append(f"{type(exc).__name__}: {exc}")

    def close(self) -> None:
        try:
            self.ledger.close()
        except Exception as exc:  # noqa: BLE001 - recorded; nothing is retried
            self.result.cleanup_errors.append(f"{type(exc).__name__}: {exc}")


def write_json(path: Path, data: Any) -> None:
    """``path`` holds the JSON whole or not at all (a ``.part`` file renamed into place; 1.7.0)."""
    part = path.with_name(path.name + ".part")
    part.write_bytes((json.dumps(data, indent=1, sort_keys=True, default=str) + "\n").encode("utf-8"))
    os.replace(part, path)
