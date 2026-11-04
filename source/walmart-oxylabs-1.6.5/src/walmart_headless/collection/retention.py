"""The store's verified products, kept across runs (assortment separate from the current offer).

A product belongs to the store's assortment once a run observed it with a fulfillment line for the store
(a Pickup line, or another local line such as Delivery from the store). Out of stock alone, without a line
for the store, is not that evidence. The verification is kept, indefinitely:

* a later run that shows the product only with a shipping or marketplace offer, or with no line for the
  store (out of stock), exports it with its identity and size and empty prices (``NO_LOCAL_OFFER``), never
  with that other price;
* a later run that does not show the product at all (a partial run, a listing not read, or a product
  missing from its listing) carries the last verified observation forward unchanged, with its own crawl
  date, as ``historical`` (``CARRIED_FORWARD``), and says why it was not observed and how old it is.

Nothing verified is ever dropped because a later listing was incomplete, the product became unavailable,
or its observation is old: there is no age limit (the client requires indefinite retention).

The current rules are applied to every earlier observation before it counts: its stored fulfillment lines
must name the store (an observation accepted by an earlier release on "out of stock" alone does not count),
and a product that displayed approximate or estimated-weight wording (shared requirements §5: its own size
wording, or since release 1.4.0 an estimate stated next to its price, "each (est.)") is never carried. When an
earlier LIVE run has been read again by ``replay`` (the current code on its stored pages), the replay's
corrected observations stand for that run's.

A product shown without a store line and never verified at the store is ``ASSORTMENT_UNRESOLVED``: it is
recorded with the reason and not exported as the store's product.

A run's record holds the product's latest state in that run (release 1.3.1). Its earlier tiles in the same
run are kept in the observation's ``earlier_in_run``. When the latest state is not a verification (out of
stock without a store line), the latest earlier tile of that run that is one stands for the run.

Which earlier observations may serve (release 1.3.1): only those of runs with the receiving run's own
lineage (``acquisition/lineage.py``: a run whose pages came from the network never takes observations
of a run whose transport was substituted, such as a test or the fault-injection harness, nor of a run
made before 1.3.1 that no operator attested); not those of a run that failed a check that invalidates its
observations (:data:`INVALIDATING_GATES`: the store, access, canaries, price reconciliation, the site
contract, integrity); and not one read from a page that was a challenge or failed its store check. A run
rejected only for its coverage, yield or completeness keeps its authentic observations. A carried record
is checked again against the record schema, the formats and the deal-price rule before it is added (a
carried record is not checked by the receiving run's own record gates), and :func:`carried_problems`
re-checks every carried record of a run for its validation (G13).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any, cast

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from walmart_headless.acquisition import lineage
from walmart_headless.core import jsonvalues as jv
from walmart_headless.core.findings import DataMode, RecordFlag
from walmart_headless.core.ids import new_id
from walmart_headless.core.schema import (
    OUTPUT_FIELDS,
    apply_output_policy,
    format_violations,
    ordered_record,
    shape_violations,
)
from walmart_headless.core.timeutil import iso
from walmart_headless.db.models import (
    NodeCoverage,
    PageFetch,
    ProductObservation,
    RecordRow,
    Run,
    StoreAttestation,
    ValidationFinding,
)
from walmart_headless.publishing.exports import record_sha256
from walmart_headless.sites.walmart import records as wrec
from walmart_headless.validation.gates import deal_price_supported

# Statuses of a fresh observation that verifies a product locally (a local offer, priced or not).
VERIFYING_STATUSES = ("valid", "exported_not_valid")
# Checks whose failure makes a run's observations untrustworthy (a run rejected only by others keeps them).
INVALIDATING_GATES = ("G1", "G2", "G9", "G10", "G12", "G13")
CARRIED_STATUS = "historical"
SHIP_KINDS = wrec.SHIP_KINDS


@dataclass(frozen=True)
class Verified:
    """The latest observation of a product with a fulfillment line of the store."""

    key: str
    run_id: str
    observed_at: datetime
    record: dict[str, Any]
    flags: tuple[str, ...]
    category_source_id: str | None
    listing: str | None
    page_fetch_id: str
    # The LIVE run the observation belongs to, when it was read again by a replay (``run_id`` is the replay).
    source_run: str | None = None

    def summary(self, now: datetime | None = None) -> dict[str, Any]:
        out: dict[str, Any] = {
            "run_id": self.run_id,
            "observed_at": iso(self.observed_at),
            "crawl_date": str(self.record.get("crawl_date", "")),
            "page_fetch_id": self.page_fetch_id,
            "listing": self.listing,
            "regular_price": str(self.record.get("regular_price", "")),
            "sale_price": str(self.record.get("sale_price", "")),
        }
        if self.source_run:
            out["replay_of"] = self.source_run
        if now is not None:
            out["age_days"] = max(0, (now - self.observed_at).days)
        return out


def weight_priced_by(log: Mapping[str, Any]) -> list[str]:
    """What an observation's stored log shows stating that the product's final cost depends on the weight
    ([] when nothing): its own reading (release 1.3.1), else, for an observation of an earlier release, its
    sales unit and price codes read with the current rule (release 1.3.0 read a WEIGHT sales unit and the
    finalCostByWeight code only, so an EACH_WEIGHT item's estimated "each (est.)" price was kept)."""
    stated = log.get("weight_priced")
    if isinstance(stated, Mapping):
        return [str(x) for x in stated.get("by") or []] if stated.get("value") else []
    unit = str(log.get("sales_unit") or "").upper()
    codes = {str(c) for c in (log.get("price_strings") or {}).get("codes") or []}
    return [
        what
        for what, shown in (
            (f"sales unit {unit}", unit in ("WEIGHT", "EACH_WEIGHT")),
            ("price line SOLD_BY_WEIGHT", "line:SOLD_BY_WEIGHT" in codes),
            ("priceDisplayCodes.finalCostByWeight", "finalCostByWeight" in codes),
        )
        if shown
    ]


def estimated_wording(log: Mapping[str, Any]) -> str:
    """The approximate or estimated-weight wording an observation's stored log shows ("" when none): its own
    release's reading (``approx_weight``), else Walmart's wording next to the price read with the current
    rule (release 1.4.0: "est." in "each (est.)")."""
    approx = log.get("approx_weight")
    if isinstance(approx, Mapping) and approx.get("text"):
        return str(approx["text"])
    shown = log.get("price_condition")
    return wrec.estimated_price_wording(str(shown.get("text") or "")) if isinstance(shown, Mapping) else ""


def store_line_rule(
    structured: dict[str, Any] | None,
    title: str,
    location_id: str,
    modality: str,
    exclude_relative: bool = False,
) -> str | None:
    """Why an earlier observation does not verify the product at the store under the current rules, or
    ``None`` when it does: its stored fulfillment lines must name the store with no other store's line of
    the configured kind, and it must have displayed no approximate or estimated-weight wording (its own
    size wording ``title``, or an estimate next to its price). A product whose final cost depends on the
    weight is refused while relative prices are excluded (``records.exclude_relative_price_items``), and
    when its release kept no reading of the wording next to its price (before 1.3.1)."""
    log = (structured or {}).get("walmart") or {}
    lines = [(str(k).upper(), str(sid)) for k, sid in (log.get("fulfillment_lines") or [])]
    if not any(sid == location_id and k not in SHIP_KINDS for k, sid in lines):
        return f"its observation shows no fulfillment line for store {location_id}"
    if any(k == modality.upper() and sid and sid != location_id for k, sid in lines):
        return f"its observation shows a {modality} line for another store"
    if wrec.approx_weight_text(title):
        return "its own size wording is approximate"
    wording = estimated_wording(log)
    if wording:
        return f"it displayed approximate or estimated-weight wording ({wording!r}): not exported"
    by = weight_priced_by(log)
    if by and exclude_relative:
        return f"its final cost depends on the weight ({', '.join(by)}): a relative price, not exported"
    if by and "price_condition" not in log:
        return (
            f"its final cost depends on the weight ({', '.join(by)}) and its release kept no reading of "
            "Walmart's wording next to the price (release 1.3.1 does): whether the price was shown as an "
            "estimate is unknown"
        )
    return None


def wording_in_run(
    reasons: Sequence[str], structured: Mapping[str, Any] | None, prov: Mapping[str, Any] | None
) -> str:
    """The approximate or estimated-weight wording a run displayed for a product on any of its tiles ("" when
    none; release 1.4.0): the run's record excluded for it, its kept tile's log or an earlier tile's. Such a
    run verifies the product on none of its tiles: the whole product is excluded."""
    if RecordFlag.APPROX_WEIGHT.value in reasons:
        return "its record is excluded for approximate or estimated-weight wording"
    logs = [(structured or {}).get("walmart") or {}]
    logs += [(st.get("structured") or {}).get("walmart") or {} for st in earlier_in_run(prov)]
    return next((w for w in map(estimated_wording, logs) if w), "")


def earlier_in_run(provenance: Mapping[str, Any] | None) -> list[dict[str, Any]]:
    """The states a run's earlier tiles of a product showed before the tile its record is kept from, oldest
    first (release 1.3.1; an observation's ``earlier_in_run``)."""
    return [dict(e) for e in (provenance or {}).get("earlier_in_run") or [] if isinstance(e, Mapping)]


def state_refusal(
    state: Mapping[str, Any], location_id: str, modality: str, exclude_relative: bool = False
) -> str | None:
    """Why one stored state of a product (an ``earlier_in_run`` entry, or a record with its tile) does not
    verify it at the store, or ``None`` when it does: as for an observation in :func:`verified_local`."""
    if state.get("status") not in VERIFYING_STATUSES:
        return f"its status is {state.get('status')}"
    flags = {str(f) for f in state.get("flags") or []}
    if {RecordFlag.NO_LOCAL_OFFER.value, RecordFlag.CARRIED_FORWARD.value} & flags:
        return "it showed no local offer"
    title = str((state.get("record") or {}).get("product_title") or "")
    return store_line_rule(state.get("structured"), title, location_id, modality, exclude_relative)


class Sources:
    """Which runs' observations may serve a run of lineage ``want`` (each run judged once)."""

    def __init__(self, s: Session, want: str):
        self.s, self.want = s, want
        self.why: dict[str, str | None] = {}

    def refusal(self, run_id: str) -> str | None:
        """None when the run's observations may serve; else why not."""
        if run_id not in self.why:
            self.why[run_id] = self._judge(run_id)
        return self.why[run_id]

    def _judge(self, run_id: str) -> str | None:
        lin = lineage.of_run(self.s, run_id)
        if lin.lineage != self.want or self.want == lineage.UNRECORDED:
            return f"run {run_id} has lineage {lin.lineage} ({lin.basis}); the receiving run's is {self.want}"
        gates = sorted(
            set(
                self.s.scalars(
                    select(ValidationFinding.gate).where(
                        ValidationFinding.run_id == run_id,
                        ValidationFinding.severity == "FAIL",
                        ValidationFinding.gate.in_(INVALIDATING_GATES),
                    )
                )
            )
        )
        if gates:
            return f"run {run_id} failed {', '.join(gates)}: its observations are not trusted"
        return None


def refused_pages(s: Session, run_ids: set[str]) -> set[tuple[str, str]]:
    """(run, page fetch) of the pages that were a challenge or failed their store check."""
    if not run_ids:
        return set()
    out = {
        (run_id, fetch_id)
        for run_id, fetch_id in s.execute(
            select(PageFetch.run_id, PageFetch.id).where(
                PageFetch.run_id.in_(run_ids), PageFetch.challenge.is_(True)
            )
        )
    }
    for run_id, checks in s.execute(
        select(StoreAttestation.run_id, StoreAttestation.checks).where(
            StoreAttestation.run_id.in_(run_ids), StoreAttestation.result == "FAIL"
        )
    ):
        fid = jv.text(jv.obj(checks, f"attestation of run {run_id}").get("fetch_id"), "attestation fetch_id")
        if fid:
            out.add((run_id, fid))
    return out


def record_problems(record: Mapping[str, Any]) -> list[str]:
    """What the receiving run's record gates (G5, G6, G11) would find in a carried record. The record is
    read back from the database (JSONB keeps no key order), so it is checked in the output order; a
    missing or unknown key is a problem, never filled in or dropped."""
    keys = set(record)
    if keys != set(OUTPUT_FIELDS):
        missing, unknown = sorted(set(OUTPUT_FIELDS) - keys), sorted(keys - set(OUTPUT_FIELDS))
        return [f"its keys are not the output fields (missing {missing}, unknown {unknown})"]
    item = {key: record[key] for key in OUTPUT_FIELDS}
    problems = [*shape_violations(item), *format_violations({k: str(v) for k, v in item.items()})]
    for desc, price in (
        ("volume_deals_description", "volume_deals_price"),
        ("digital_deals_description", "digital_deals_price"),
    ):
        if not deal_price_supported(str(item[desc] or ""), str(item[price] or "")):
            problems.append(f"{price} not in {desc}")
    return problems


def _source_runs(s: Session, store_id: str) -> dict[str, str]:
    """Replay run id -> the LIVE run it reads again, for the store's replay runs."""
    out: dict[str, str] = {}
    for row in s.execute(
        select(Run.id, Run.config_snapshot).where(Run.store_id == store_id, Run.mode == DataMode.REPLAY.value)
    ).all():
        run_id, snap = cast(tuple[str, dict[str, Any] | None], tuple(row))
        src = str(((snap or {}).get("replay") or {}).get("source_run") or "")
        if src:
            out[str(run_id)] = src
    return out


def verified_local(
    s: Session,
    store_id: str,
    location_id: str,
    modality: str,
    exclude_run: str | None = None,
    *,
    before: datetime | None = None,
    rejected: dict[str, str] | None = None,
    refused: dict[str, str] | None = None,
    exclude_relative: bool = False,
) -> dict[str, Verified]:
    """Every product an earlier run of the store observed with a fulfillment line for the store, with its
    latest such observation (observed before ``before``, when given). An observation without a local offer
    (``NO_LOCAL_OFFER``) and a carried-forward row are not verifications; nor is an observation the current
    rules do not accept (``rejected`` collects why, by product) or one of a run that may not serve the
    receiving run ``exclude_run``: its lineage, its invalidating checks, a challenged or failed page (see
    the module docstring; ``refused`` collects why, by product). A LIVE run read again by a replay counts
    through the replay's observations, never twice. Without a receiving run, only ``network`` runs
    serve. A run whose record of a product ends without a local offer counts through its latest earlier
    tile of the product that verified it (``earlier_in_run``, release 1.3.1)."""
    want = lineage.of_run(s, exclude_run).lineage if exclude_run is not None else lineage.NETWORK
    if want == lineage.UNRECORDED:
        return {}  # a run without a recorded or attested lineage takes no earlier observation
    sources = Sources(s, want)
    replays = _source_runs(s, store_id)
    replaced = set(replays.values())
    q = (
        select(
            RecordRow,
            ProductObservation.observed_at,
            ProductObservation.provenance,
            ProductObservation.page_fetch_id,
            ProductObservation.structured,
            Run.mode,
        )
        .join(Run, Run.id == RecordRow.run_id)
        .join(
            ProductObservation,
            (ProductObservation.run_id == RecordRow.run_id) & (ProductObservation.upc == RecordRow.upc),
        )
        .where(
            Run.store_id == store_id,
            Run.mode.in_((DataMode.LIVE.value, DataMode.REPLAY.value)),
            or_(
                RecordRow.status.in_(VERIFYING_STATUSES),
                ProductObservation.provenance.has_key("earlier_in_run"),
            ),
            # A sponsored placement is no verification: an advertisement shows no local assortment.
            ProductObservation.source.in_(("card", "pdp")),
        )
        .order_by(ProductObservation.observed_at, RecordRow.id)
    )
    if exclude_run is not None:
        q = q.where(Run.id != exclude_run)
    if before is not None:
        q = q.where(ProductObservation.observed_at < before)
    out: dict[str, Verified] = {}
    rows = [
        cast(tuple[RecordRow, datetime, dict[str, Any] | None, str, dict[str, Any] | None, str], tuple(item))
        for item in s.execute(q).all()
    ]
    bad_pages = refused_pages(s, {r[0].run_id for r in rows})
    for row, observed_at, prov, fetch_id, structured, mode in rows:
        if mode == DataMode.LIVE.value and row.run_id in replaced:
            continue  # the replay of this run stands for it
        if mode == DataMode.REPLAY.value and row.run_id not in replays:
            continue
        if exclude_run is not None and replays.get(row.run_id) == exclude_run:
            continue  # a replay of the run being assembled is not its history
        wording = wording_in_run(row.reasons or [], structured, prov)
        if wording:
            if rejected is not None:
                rejected[row.upc] = (
                    f"it displayed approximate or estimated-weight wording in that run ({wording}; run "
                    f"{row.run_id}, {iso(observed_at)})"
                )
            continue
        flags = tuple(row.flags or [])
        if (
            row.status not in VERIFYING_STATUSES
            or RecordFlag.NO_LOCAL_OFFER.value in flags
            or RecordFlag.CARRIED_FORWARD.value in flags
        ):
            # Its latest state in its run is no verification; an earlier tile of that run may be one.
            if sources.refusal(row.run_id) is not None:
                continue
            for state in reversed(earlier_in_run(prov)):
                page = str(state.get("page_fetch_id") or "")
                if (row.run_id, page) in bad_pages:
                    continue
                if state_refusal(state, location_id, modality, exclude_relative) is not None:
                    continue
                at = datetime.fromisoformat(str(state["observed_at"]).replace("Z", "+00:00"))
                if row.upc not in out or at > out[row.upc].observed_at:
                    out[row.upc] = Verified(
                        row.upc,
                        row.run_id,
                        at,
                        dict(state.get("record") or {}),
                        tuple(str(f) for f in state.get("flags") or []),
                        row.primary_category_source_id,
                        state.get("listing"),
                        page,
                        replays.get(row.run_id),
                    )
                break
            continue
        refusal = sources.refusal(row.run_id)
        if refusal is None and (row.run_id, fetch_id) in bad_pages:
            refusal = f"its page {fetch_id} was a challenge or failed its store check"
        if refusal is not None:
            if refused is not None:
                refused[row.upc] = f"{refusal} ({iso(observed_at)})"
            continue
        why = store_line_rule(
            structured, str(row.record.get("product_title") or ""), location_id, modality, exclude_relative
        )
        if why is not None:
            # Not a verification now; an earlier observation of the product that is one still stands.
            if rejected is not None:
                rejected[row.upc] = f"{why} (run {row.run_id}, {iso(observed_at)})"
            continue
        p = prov or {}
        out[row.upc] = Verified(
            row.upc,
            row.run_id,
            observed_at,
            dict(row.record),
            flags,
            row.primary_category_source_id,
            p.get("parent") or p.get("listing") or p.get("node"),
            fetch_id,
            replays.get(row.run_id),
        )
    return out


def coverage_status(s: Session, run_id: str) -> dict[str, str]:
    """This run's listing (or node) statuses, by listing id."""
    return {
        c.taxonomy_id: c.status for c in s.scalars(select(NodeCoverage).where(NodeCoverage.run_id == run_id))
    }


def why_not_observed(listing: str | None, coverage: dict[str, str], run_complete: bool) -> str:
    if listing is None:
        return "not observed by this run (the earlier observation names no listing)"
    status = coverage.get(listing)
    if status is None:
        return f"its listing {listing} was not read by this run" + (
            "" if run_complete else " (a partial run)"
        )
    if status in ("DONE", "EMPTY"):
        return (
            f"not shown by its listing {listing}, read to its end by this run (unavailable or delisted now)"
        )
    return f"its listing {listing} was read only in part by this run ({status})"


def carry_forward(
    s: Session,
    run_id: str,
    store_id: str,
    now: datetime,
    *,
    location_id: str,
    modality: str,
    run_complete: bool,
    before: datetime | None = None,
    mode: str = DataMode.LIVE.value,
    exclude_relative: bool = False,
) -> dict[str, int]:
    """Products verified by earlier runs of the store and not observed by this one: the latest verified
    observation is added to this run unchanged (status ``historical``, flag ``CARRIED_FORWARD``, its own
    record and crawl date), with where it came from, how old it is and why this run did not observe it.
    Never dropped for age. Only observations of runs that may serve this one are carried (its lineage, the
    source's invalidating checks and page: ``refused_sources`` counts the products whose only earlier
    observations were refused), and a record that fails the record checks now is not carried
    (``not_valid_now``). Idempotent."""
    counts = {
        "carried_forward": 0,
        "not_verified_by_current_rules": 0,
        "refused_sources": 0,
        "not_valid_now": 0,
    }
    present = set(s.scalars(select(RecordRow.upc).where(RecordRow.run_id == run_id)))
    coverage = coverage_status(s, run_id)
    rejected: dict[str, str] = {}
    refused: dict[str, str] = {}
    registry = verified_local(
        s,
        store_id,
        location_id,
        modality,
        exclude_run=run_id,
        before=before,
        rejected=rejected,
        refused=refused,
        exclude_relative=exclude_relative,
    )
    counts["not_verified_by_current_rules"] = len(set(rejected) - set(registry) - present)
    counts["refused_sources"] = len(set(refused) - set(rejected) - set(registry) - present)
    source_lineage: dict[str, lineage.RunLineage] = {}
    for key, v in registry.items():
        if key in present:
            continue
        # Release 1.6.0: an earlier release's row may hold deal values; the carried row never does. The values
        # stay in the carried row's lineage (``withheld_by_policy``), with the source record's own hash.
        kept_record, withheld = (
            apply_output_policy(v.record) if set(v.record) == set(OUTPUT_FIELDS) else (dict(v.record), {})
        )
        if record_problems(kept_record):
            counts["not_valid_now"] += 1  # never carried past the record checks it would now fail
            continue
        if v.run_id not in source_lineage:
            source_lineage[v.run_id] = lineage.of_run(s, v.run_id)
        lin = source_lineage[v.run_id]
        info = {
            **v.summary(now),
            "lineage": lin.lineage,
            "lineage_basis": lin.basis,
            "why_not_observed": why_not_observed(v.listing, coverage, run_complete),
            "note": "an earlier run's verified local observation, carried forward unchanged: its prices are "
            "the ones observed on its crawl date, not verified by this run",
            "kept": True,
        }
        if withheld:
            info["withheld_by_policy"] = {
                "fields": withheld,
                "rule": "release 1.6.0: Walmart's four deal fields are always empty strings",
                "source_record_sha256": record_sha256(ordered_record(v.record)),
            }
        flags = [
            *(f for f in v.flags if f != RecordFlag.CARRIED_FORWARD.value),
            RecordFlag.CARRIED_FORWARD.value,
        ]
        s.add(
            RecordRow(
                id=new_id(),
                run_id=run_id,
                mode=mode,
                upc=key,
                record=kept_record,
                record_sha256=record_sha256(ordered_record(kept_record)),
                primary_category_source_id=v.category_source_id,
                status=CARRIED_STATUS,
                reasons=[RecordFlag.CARRIED_FORWARD.value],
                flags=flags,
                provenance={"historical": info},
            )
        )
        counts["carried_forward"] += 1
    s.flush()
    return counts


def carried_problems(s: Session, run_id: str) -> list[str]:
    """Each carried record of the run whose source may not serve it now (its lineage, its invalidating
    checks, its page) or which fails the record checks: a G13 (integrity) failure of the run."""
    want = lineage.of_run(s, run_id).lineage
    sources = Sources(s, want)
    rows = list(
        s.scalars(select(RecordRow).where(RecordRow.run_id == run_id, RecordRow.status == CARRIED_STATUS))
    )
    origin: list[tuple[RecordRow, str, str]] = []
    for r in rows:
        info = jv.obj(
            jv.obj(r.provenance, f"record {r.upc}").get("historical"), f"record {r.upc}: historical"
        )
        src = jv.text(info.get("run_id"), f"record {r.upc}: historical.run_id")
        fetch = jv.text(info.get("page_fetch_id"), f"record {r.upc}: historical.page_fetch_id")
        origin.append((r, src, fetch))
    refused = refused_pages(s, {src for _, src, _ in origin if src})
    out: list[str] = []
    for r, src, fetch in origin:
        why = sources.refusal(src) if src else "it names no source run"
        if why is None and (src, fetch) in refused:
            why = f"its page {fetch} was a challenge or failed its store check"
        if why is None and (problems := record_problems(dict(r.record))):
            why = "; ".join(problems)
        if why is not None:
            out.append(f"carried record {r.upc}: {why}")
    return out
