"""The production cost and runtime estimate of release 1.4.1 (offline, read-only; requests nothing): version 4
of the cost model (brief of 2026-10-28, section 11).

Versions 2 (C:/w6/tools/cost_model.py) and 3 (C:/w6/tools/cost_model_131.py, the 1.3.1 delivery) and their
outputs are left as they were. Version 4:
- measures, for every live run of 2026-10-28 (real keys only), the provider units it used and their value per
  1,000 valid fresh products and per completed branch (a listing every result page of which the run read under
  its grid filter), with the denominators;
- replaces the historical scope (947 links counted as independent listings, about 120,000 products, 22,000 to
  50,000 result pages: Walmart's unfiltered online assortment, scope_audit_141.py) by a parameter N, the
  distinct products of store #3891's Pickup assortment in the required categories, which no run has measured:
  N = 20,000, 40,000 and 80,000 (assumption), and 120,000 for reference only;
- prices each scenario for both editions: Oxylabs Web API results at USD 0.50, 1.00 and 1.50 per 1,000 (no
  Walmart row is published) with its plans; Scrape.do credits (10 per store-endpoint page, 1 per general-API
  page) with its plans;
- counts every page a full run needs: result pages, UPC product pages (the first acquisition, new products and
  the 30-day reuse), follow-ups (sponsored-only products and variant siblings; as shipped, every candidate in
  every run), offer pages (none as shipped), sessions (robots.txt and the store page per worker and segment),
  charged retries and interruptions;
- the run time from the throughput measured on 2026-10-28 by stage and number of workers, and the measured limit
  of the follow-up stage (one task per kind, so one worker per kind);
- Azure: the VM (collection hours, or always on), the OS disk, the public IP, a data disk for a stated
  retention, database dumps (on the data disk, or a Blob copy) and Internet egress, from the retail prices read
  on 2026-10-28;
- the errata of the 1.3.1 reply's "about USD 590 to 610 a month".

Every input carries its kind: measured, published, configuration, requirement, historical estimate, assumption
or design assumption (a choice of how production would run that nobody has approved).

Revision 2 (2026-10-28): the Internet egress tiers are those of the general meter (revision 1 also took the "to
China" meter, whose 0 GB row was read as the paid tier: 0 GB free and USD 0 a GB recorded; no scenario reaches the
100 GB free tier, so no estimate changed through it) and the valid products per result page are pooled over the two
runs (revision 1 averaged the rounded per-run figures: 35.1 for 35.2); the columns of MEASURED_COST_PER_RUN_1_4_1.csv
that the first run lacks follow in name order (revision 1: in set order, which changes between runs); two notes are
made exact: a census of the roots bounds N (revision 1: "would measure N"), and the hours with 8 workers assume the
per-worker rates measured with up to 4 hold. Revision 1's output is kept as it was.

usage: python -I -X utf8 cost_model_141.py OUT_DIR
writes COST_MODEL_1_4_1.json, COST_SCENARIOS_1_4_1.csv, MEASURED_COST_PER_RUN_1_4_1.csv, THROUGHPUT_1_4_1.csv
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import statistics
import sys
import tarfile
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

C140 = Path("C:/w6/c140")
FINAL = C140 / "audit/final"
USAGE = FINAL / "usage/USAGE_1_4_1.json"
PROFILES = FINAL / "profiles/RUN_PROFILES_1_4_1.jsonl"
RUNS = FINAL / "runs_all.json"
COVERAGE = FINAL / "coverage/COVERAGE_RECONCILIATION.csv"
SCOPE = FINAL / "scope/SCOPE_AUDIT_1_4_1.json"
AZURE = C140 / "evidence/pricing_20261028/azure_retail_prices_20261028/AZURE_PRICES.json"
AZURE_SE = C140 / "evidence/pricing_20261028/azure_storage_egress_prices_20261028/AZURE_STORAGE_EGRESS_PRICES.json"
DB_SIZES = next((C140 / "evidence/commands").glob("367_*.txt"))
EV_RUNS = C140 / "evidence/runs"
V3 = Path("C:/w6/evidence131/costs/cost_model_131.json")

INPUTS: dict[str, dict[str, Any]] = {}
READ: dict[str, str] = {}


def inp(name: str, value: Any, kind: str, source: str) -> Any:
    INPUTS[name] = {"value": value, "kind": kind, "source": source}
    return value


def sha(p: Path) -> str:
    h = hashlib.sha256(p.read_bytes()).hexdigest()
    READ[p.as_posix()] = h
    return h


def load_json(p: Path) -> Any:
    sha(p)
    return json.loads(p.read_text("utf-8"))


def jsonl(p: Path) -> list[dict[str, Any]]:
    sha(p)
    dec, s, i, out = json.JSONDecoder(), p.read_text("utf-8"), 0, []
    while i < len(s):
        while i < len(s) and s[i].isspace():
            i += 1
        if i < len(s):
            o, i = dec.raw_decode(s, i)
            out.append(o)
    return out


def ts(s: str) -> datetime:
    return datetime.fromisoformat(s.replace(" ", "T").replace("+00", "+00:00"))


def rng(xs: list[float], nd: int = 2) -> list[float]:
    return [round(min(xs), nd), round(max(xs), nd)]


# ---- published and required inputs ------------------------------------------------------------------------
RUNS_PER_MONTH = inp("runs_per_month", round(52 / 12 * 2, 4), "requirement",
                     "twice weekly (the client's requirement; the shipped schedule: Tuesday and Friday, off)")
HOURS_PER_MONTH = 730
WINDOW_H = inp("schedule_interval_hours", {"tuesday_to_friday": 72, "friday_to_tuesday": 96}, "requirement",
               "twice weekly at 06:00 store time; a run longer than 72 h makes the next occurrence start nothing "
               "(on_overlap: continue), so the cadence drops, never the scope")
OXY_RATES = inp("oxylabs_usd_per_1000_results", {"low": 0.50, "central": 1.00, "worst": 1.50}, "published",
                "oxylabs_web_api_pricing_read_20261028.md: no Walmart row; 'Scrape (from)' 0.50, 'Other targets' "
                "and 'Custom domain non-JS' 1.00 (first two bands), 'Custom domain JS' 1.50 (the collector's "
                "reserve of USD 0.0015 a result)")
# Plans: (name, monthly USD, results covered at the rate of that band). The band limits are the published
# 'up to' volumes of each plan for the row of each rate (the reading of 2026-10-28).
OXY_PLANS = inp("oxylabs_plans", {
    "low": [("Starter", 30, 60_000), ("Basic", 100, 222_000), ("Flexible", 500, 1_430_000),
            ("Enterprise", 2500, 10_000_000)],
    "central": [("Starter", 30, 30_000), ("Basic", 100, 111_000), ("Flexible", 500, 625_000),
                ("Enterprise", 2500, 3_330_000)],
    "worst": [("Starter", 30, 20_000), ("Basic", 100, 71_000), ("Flexible", 500, 384_000),
              ("Enterprise", 2500, 2_050_000)]}, "published",
    "the band limits of the 'Scrape (from)', 'Other targets' and 'Custom domain JS' rows; the page says nothing "
    "about overage or pay-as-you-go: a volume above a band is priced at the next plan; above Enterprise's "
    "band, a quote")
SD_PLANS = inp("scrapedo_plans", [("Hobby", 29, 250_000, 10), ("Pro", 99, 1_250_000, 50),
                                  ("Business", 249, 3_500_000, 100), ("Advanced", 699, 10_000_000, 200)],
               "published", "scrapedo_pricing_read_20261028.md (monthly price, credits, concurrent requests); "
               "requests stop at the monthly limit; annual billing: pay 10 months for 12")
SD_CREDITS = inp("scrapedo_credits_per_page", {"store_endpoint": 10, "general_api": 1}, "measured",
                 "the campaign's ledger (Scrape.do-Request-Cost answer header): result pages and follow-up product "
                 "pages through /plugin/walmart/store 10; UPC product pages, robots.txt and the store page "
                 "through the general API 1; a Walmart 404 is charged; failed store-endpoint requests are free")
CONFIG = inp("shipped_configuration", {"parallel.workers": 1, "parallel.max_in_flight": 2,
                                       "parallel.workers_and_in_flight_maximum": 8,
                                       "limits.max_segment_minutes": 300, "detail.reuse_days": 30,
                                       "follow_up.sponsored": True, "follow_up.variants": True,
                                       "follow_up.max_pages": None},
             "configuration", "config/collector.yaml of 37ffca8 (ParallelConfig: workers and max_in_flight 1 to 8)")
SEGMENT_H = CONFIG["limits.max_segment_minutes"] / 60

# ---- assumptions of the scenarios ------------------------------------------------------------------------
N_SCOPE = inp("distinct_pickup_products_N", {"20k": 20_000, "40k": 40_000, "80k": 80_000,
                                              "120k_historical_reference": 120_000},
              "assumption",
              "not measured: no run read the full scope. 20k to 80k brackets a supercenter's Pickup assortment "
              "in the 11 required CSV rows; 120k is the 1.2.1 figure, kept only for comparison (it described "
              "Walmart's unfiltered online catalogue, scope_audit_141.py). A census (one result page per root "
              "listing, about 615 pages) would read each root's Pickup total: their sum bounds N from above (a "
              "product under several roots counts once per root) and fixes the result pages of a full run")
CASES = inp("cases", {
    "lean": {"overlap": 1.2, "variant_candidates_per_product": 0.5, "sponsored_only_per_product": 0.03,
             "new_products_per_run": 0.02, "charged_retry_share": None, "offer_pages_per_product": 0.0,
             "interruptions_per_run": 1},
    "heavy": {"overlap": 2.0, "variant_candidates_per_product": 1.0, "sponsored_only_per_product": 0.18,
              "new_products_per_run": 0.10, "charged_retry_share": 0.10, "offer_pages_per_product": 0.02,
              "interruptions_per_run": 2}}, "assumption",
    "overlap: result pages read per (N / valid products per page), for products listed in several root listings, "
    "partitions of listings Walmart does not serve to the end, and partial last pages (measured on small runs "
    "only, see measured.overlap_in_runs); variant candidates (siblings a tile names and no tile of the run shows) "
    "per product: measured 0.78 to 1.54 on bounded runs, expected lower at full scope where more siblings have "
    "their own tile, so 0.5 to 1.0; sponsored-only products per product: measured 0.03 to 0.18 on bounded runs "
    "(an upper reference: at full scope most sponsored products also appear organically); new products per run: "
    "1.2.1 assumed 10 %, 2 % is the lean case; charged retries: lean = the campaign's measured share, heavy = "
    "the 1.3.1 allowance of 10 %; offer pages: none as shipped (offers are read from the pages already read; 0 "
    "deal candidates in 5,470 tiles), heavy = a product page re-read every run for 2 % of products; "
    "interruptions: each re-sends the requests in flight (one per worker)")
FOLLOW_REUSE = inp("follow_up_reuse_of_exclusions", {"as_shipped": False, "design_option": True}, "design assumption",
                   "as shipped (walmart.py follow_up of 37ffca8) every candidate a run names is read in that run, "
                   "whatever an earlier run decided; the design option, not implemented, reuses an exclusion (out "
                   "of scope, no local offer) for the 30-day reuse period, while included candidates are read in "
                   "every run (their price must be fresh)")
RETENTION = inp("retention_policy", {"stored_pages_runs": 2, "observations_days": 90, "dumps_kept": 2},
                "design assumption",
                "no retention policy is configured or approved: the stored pages of the last 2 runs, 90 days of "
                "observations in the database (records kept indefinitely), and the last 2 database dumps")


def follow_rates(case: dict[str, float]) -> float:
    return case["variant_candidates_per_product"] + case["sponsored_only_per_product"]


def oxy_plan(results: float, basis: str) -> dict[str, Any]:
    rate = OXY_RATES[basis] / 1000
    for name, usd, band in OXY_PLANS[basis]:
        if results <= band:
            return {"plan": name, "usd_month": usd, "band_results": band, "used_share": round(results / band, 3),
                    "usd_at_rate": round(results * rate, 2)}
    return {"plan": "quote (above Enterprise's band)", "usd_month": None, "band_results": None,
            "used_share": None, "usd_at_rate": round(results * rate, 2)}


def sd_plan(credits: float) -> dict[str, Any]:
    for name, usd, quota, conc in SD_PLANS:
        if credits <= quota:
            return {"plan": name, "usd_month": usd, "credits": quota, "concurrent": conc,
                    "used_share": round(credits / quota, 3), "usd_month_annual_billing": round(usd * 10 / 12, 2)}
    return {"plan": "custom quote (above Advanced's 10M credits)", "usd_month": None, "credits": None,
            "concurrent": None, "used_share": None, "usd_month_annual_billing": None}


def main() -> int:
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    usage = load_json(USAGE)
    profiles = {p["run_id"]: p for p in jsonl(PROFILES)}
    runs = load_json(RUNS)
    scope = load_json(SCOPE)
    azure = load_json(AZURE)["selected"]
    azure_se = load_json(AZURE_SE)["selected"]
    v3 = load_json(V3)
    sha(COVERAGE)
    cov = [r for r in csv.DictReader(COVERAGE.open(encoding="utf-8", newline="")) if r["level"] == "listing_run"]

    # 1. Per run: units, money, valid fresh, completed branches; per segment: throughput by stage.
    by_run_cov: dict[str, list[dict[str, str]]] = defaultdict(list)
    for r in cov:
        by_run_cov[r["run"]].append(r)
    run_rows, thr_rows = [], []
    lat: dict[tuple[str, str], list[float]] = defaultdict(list)
    ok_by_provider: Counter[str] = Counter()
    charged_non_ok: Counter[str] = Counter()
    free_fail: Counter[str] = Counter()
    for spec in runs:
        key = f"{spec['database']}/{spec['run']}"
        u = usage["runs"][key]
        prov = u["provider"]
        pu_path = EV_RUNS / spec["database"] / spec["run"] / "db/provider_usage.csv"
        sha(pu_path)
        pu = list(csv.DictReader(pu_path.open(encoding="utf-8", newline="")))
        purposes = Counter(r["purpose"] for r in pu)
        for r in pu:
            if r["outcome"] == "ok" and r["elapsed_ms"]:
                lat[(prov, r["purpose"])].append(int(r["elapsed_ms"]) / 1000)
            if r["outcome"] == "ok":
                ok_by_provider[prov] += 1
            elif float(r["credits"] or 0) > 0:
                charged_non_ok[prov] += 1
            else:
                free_fail[prov] += 1
        units = float(u["credits"])
        prof = profiles[spec["run"]]
        fresh = int(prof["products_fresh"])
        rows = by_run_cov.get(spec["run"], [])
        done = [r for r in rows if r.get("status") == "DONE"]
        unit_per_page = 10 if prov == "scrapedo" else 1
        done_pages = sum(len([x for x in (r.get("page_fetches") or "").split(";") if x]) for r in done)
        row = {
            "edition": prov, "release": spec["release"], "phase": spec["phase"], "run": spec["run"],
            "database": spec["database"], "requests": u["requests"],
            "units": units, "unit": "Oxylabs results (counted)" if prov == "oxylabs" else "Scrape.do credits",
            "requests_by_purpose": dict(sorted(purposes.items())),
            "valid_fresh": fresh, "exported_rows": int(prof["products_all"]),
            "units_per_1000_valid_fresh": round(units / fresh * 1000, 1) if fresh else None,
            "completed_branches": len(done),
            "units_per_completed_branch_whole_run": round(units / len(done), 1) if done else None,
            "result_page_units_of_completed_branches": done_pages * unit_per_page if done else None,
            "completed_branch_names": "; ".join(sorted({r["listing_name"] for r in done})),
        }
        if prov == "oxylabs":
            for b, rate in OXY_RATES.items():
                row[f"usd_at_{b}_rate"] = round(units * rate / 1000, 4)
                row[f"usd_per_1000_valid_fresh_at_{b}_rate"] = (round(units * rate / fresh, 4) if fresh else None)
            row["money_basis"] = ("an estimate at published rates, drawn from the account's USD 5 welcome credit "
                                  "(presumed; Oxylabs offers no balance endpoint): no cash, no invoice")
        else:
            lo, hi = SD_PLANS[-1][1] / SD_PLANS[-1][2], SD_PLANS[0][1] / SD_PLANS[0][2]
            row["usd_at_plan_rates_low_high"] = [round(units * lo, 4), round(units * hi, 4)]
            row["usd_per_1000_valid_fresh_at_plan_rates"] = ([round(units * lo / fresh * 1000, 4),
                                                              round(units * hi / fresh * 1000, 4)] if fresh else None)
            row["money_basis"] = ("free plan (1,000 credits a month): no cash; the dollar figures value the credits "
                                  "at the Advanced and Hobby plans' price per credit")
        run_rows.append(row)
        # Segments: requests per minute by the workers that made requests, and the stage they were in.
        seg_purposes: dict[str, Counter[str]] = defaultdict(Counter)
        for r in pu:
            seg_purposes[r["segment_id"]][r["purpose"]] += 1
        for seg, s in u.get("segments", {}).items():
            if s["requests"] < 20 or s["span_s"] <= 0:
                continue
            p = seg_purposes[seg]
            listing_share = p["listing"] / s["requests"]
            stage = ("result pages" if listing_share >= 0.6 else
                     "follow-up pages (one task per kind)" if p["product_page"] / s["requests"] >= 0.6 else
                     "UPC product pages (mixed with some result pages)")
            rpm = s["requests"] / s["span_s"] * 60
            # The follow-up stage runs one task per kind (run D: the variant kind only), so its rate is per task,
            # whatever the number of workers that made requests in the segment.
            per = rpm if stage.startswith("follow-up") else rpm / len(s["workers"])
            thr_rows.append({"edition": prov, "release": spec["release"], "phase": spec["phase"], "run": spec["run"],
                             "segment": seg, "workers_with_requests": len(s["workers"]), "requests": s["requests"],
                             "span_s": s["span_s"], "requests_per_min": round(rpm, 1),
                             "requests_per_min_per_worker": round(per, 1),
                             "stage": stage, "purposes": dict(sorted(p.items()))})

    def thr(prov: str, stage: str) -> list[float]:
        return [t["requests_per_min_per_worker"] for t in thr_rows if t["edition"] == prov and t["stage"] == stage]

    per_worker = {
        "oxylabs": {"result": thr("oxylabs", "result pages"), "upc": thr("oxylabs", "UPC product pages (mixed with some result pages)"),
                    "follow": thr("oxylabs", "follow-up pages (one task per kind)")},
        "scrapedo": {"result": thr("scrapedo", "result pages"), "upc": thr("scrapedo", "UPC product pages (mixed with some result pages)"),
                     "follow": thr("scrapedo", "follow-up pages (one task per kind)")},
    }
    lat_summary = {f"{p}/{k}": {"n": len(v), "p50": round(statistics.median(v), 2), "mean": round(statistics.mean(v), 2)}
                   for (p, k), v in sorted(lat.items()) if len(v) >= 5}
    # The collector's own time per request: one-worker follow-up segments of run D, the segment's span per request
    # minus the mean answer time of its requests.
    d_spec = next(x for x in runs if x["phase"] == "D")
    d_pu = list(csv.DictReader((EV_RUNS / d_spec["database"] / d_spec["run"] / "db/provider_usage.csv")
                               .open(encoding="utf-8", newline="")))
    overheads = []
    for seg, s in usage["runs"][f"{d_spec['database']}/{d_spec['run']}"]["segments"].items():
        if len(s["workers"]) == 1 and s["requests"] >= 20:
            el = [int(r["elapsed_ms"]) / 1000 for r in d_pu if r["segment_id"] == seg and r["elapsed_ms"]]
            overheads.append(s["span_s"] / s["requests"] - statistics.mean(el))
    overhead = max(0.0, statistics.mean(overheads))
    inp("collector_seconds_per_request_besides_the_answer", round(overhead, 2), "measured",
        "run D's one-worker segments: span per request minus the mean answer time (" +
        ", ".join(f"{x:.2f}" for x in overheads) + " s)")
    # Scrape.do never ran a follow-up stage long enough to time it: its rate is estimated from the answer times of
    # its 5 follow-up product pages (store endpoint) plus the collector's own time (fast: median, slow: mean).
    # Its result pages were timed in one segment only (B2, 1.4.0, the heavier unfiltered grid): the fast end is
    # estimated the same way from the median answer time of all its result pages.
    if not per_worker["scrapedo"]["follow"]:
        pp = lat_summary["scrapedo/product_page"]
        per_worker["scrapedo"]["follow"] = [60 / (pp["mean"] + overhead), 60 / (pp["p50"] + overhead)]
    sl = lat_summary["scrapedo/listing"]
    per_worker["scrapedo"]["result"] = per_worker["scrapedo"]["result"] + [60 / (sl["p50"] + overhead)]
    inp("throughput_requests_per_min_per_worker", {p: {k: rng(v, 1) for k, v in d.items()} for p, d in per_worker.items()},
        "measured (Scrape.do follow-ups and the fast end of its result pages: estimated from answer times)",
        "THROUGHPUT_1_4_1.csv: segments of 2026-10-28 with at least 20 requests, by stage; workers 1, 2 and 4 "
        "measured (4 is the most measured; the configuration allows 8, not measured: the hours with 8 workers "
        "assume the per-worker rates hold); the follow-up stage runs one "
        "task per kind, so one worker per kind. Scrape.do: follow-up pages 60 / (answer time + collector time) "
        "from its 5 follow-up pages (mean and median); result pages: B2's segment (slow end) and the median "
        "answer time of its 49 result pages (fast end)")
    retry_measured = {p: round(charged_non_ok[p] / ok_by_provider[p], 4) for p in ok_by_provider}
    inp("charged_retry_share_measured", retry_measured, "measured",
        "requests with a charge (or a reservation kept: possibly charged) and no usable answer, per answered "
        f"request, all live runs of 2026-10-28: Oxylabs {charged_non_ok['oxylabs']} of {ok_by_provider['oxylabs']}, "
        f"Scrape.do {charged_non_ok['scrapedo']} of {ok_by_provider['scrapedo']} (Walmart 404s, 1 credit each); "
        f"free failures (time only): Oxylabs {free_fail['oxylabs']}, Scrape.do {free_fail['scrapedo']}")

    # 2. Yields per result page on the Pickup grid, follow-up ratios and outcomes.
    pick_runs = [r for r in runs if r["edition"] == "oxylabs" and r["phase"] in ("B2", "B3")]
    v_rows = []
    for spec in pick_runs:
        rr = next(x for x in run_rows if x["run"] == spec["run"])
        pages = rr["requests_by_purpose"].get("listing", 0)
        v_rows.append({"run": spec["run"], "phase": spec["phase"], "valid_fresh": rr["valid_fresh"],
                       "result_pages": pages, "valid_per_page": round(rr["valid_fresh"] / pages, 1)})
    # Pooled over the runs (revision 1 averaged the rounded per-run figures: 35.1 for a pooled 35.2).
    v_page = sum(x["valid_fresh"] for x in v_rows) / sum(x["result_pages"] for x in v_rows)
    inp("valid_products_per_result_page", round(v_page, 1), "measured",
        "Oxylabs runs B2 (1.4.0) and B3 (1.4.1), Pickup grid, no follow-up and no UPC page: valid fresh products "
        "per result page read, pooled over the two runs: "
        + "; ".join(f"{x['phase']} {x['valid_fresh']}/{x['result_pages']}" for x in v_rows)
        + f"; together {sum(x['valid_fresh'] for x in v_rows)}/{sum(x['result_pages'] for x in v_rows)}")
    ratios = []
    for spec in runs:
        rows = [r for r in by_run_cov.get(spec["run"], []) if r.get("status") not in ("SKIPPED", "")]
        pick = rows  # every Oxylabs grid is Pickup-filtered (the Web API's fulfillment_type: pickup)
        ident = sum(int(r["distinct_identities"] or 0) for r in pick)
        if spec["phase"] not in ("B1", "B2", "B3", "D") or spec["edition"] != "oxylabs" or not ident:
            continue
        pages = sum(len([x for x in (r["pages_visited"] or "").split(";") if x]) for r in pick)
        var = sum(int(r["variant_identities_not_own_tile"] or 0) for r in pick)
        spo = sum(int(r["sponsored_only_products"] or 0) for r in pick)
        prof = profiles[spec["run"]]
        ratios.append({"run": spec["run"], "phase": spec["phase"], "result_pages": pages,
                       "organic_identities_per_listing_sum": ident,
                       "valid_fresh_run": prof["products_fresh"],
                       "variant_candidates_per_organic_identity": round(var / ident, 2),
                       "sponsored_only_per_organic_identity": round(spo / ident, 3),
                       "sponsored_only_per_result_page": round(spo / pages, 2) if pages else None})
    outcomes: Counter[str] = Counter()
    for r in by_run_cov.get(next(x["run"] for x in runs if x["phase"] == "D"), []):
        raw = (r.get("follow_up_outcomes") or "").strip()
        if raw.startswith("{"):
            for k, v in json.loads(raw.replace("'", '"')).items():
                outcomes[k.split(":", 1)[1]] += int(v)
    read = outcomes["included"] + outcomes["excluded"] + outcomes["inaccessible"]
    fu_out = {k: round(outcomes[k] / read, 3) for k in ("included", "excluded", "inaccessible")}
    inp("follow_up_outcomes_phase_D", {"read": read, **{k: outcomes[k] for k in ("included", "excluded",
                                                                                 "inaccessible", "not_attempted")},
                                       "shares_of_read": fu_out}, "measured",
        "run D (01M60VA5, 1.4.1, variant follow-ups of 5 listings): coverage follow_up_outcomes")
    P_INC = fu_out["included"]

    # 3. Storage: bytes stored per page (gzip, as kept: the sanitizable DOM copy and the raw answer), by purpose.
    sizes: dict[tuple[str, str, str], list[int]] = defaultdict(list)
    for spec in runs:
        if spec["phase"] not in ("B1", "B3", "D", "B2"):
            continue
        d = EV_RUNS / spec["database"] / spec["run"]
        pf_path = d / "db/page_fetches.csv"
        sha(pf_path)
        purpose = {r["id"]: r["purpose"] for r in csv.DictReader(pf_path.open(encoding="utf-8", newline=""))}
        with tarfile.open(d / "live.tar") as tf:
            for m in tf.getmembers():
                parts = m.name.split("/")
                if not m.isfile() or len(parts) < 3 or parts[1] not in ("dom", "raw"):
                    continue
                fid = parts[2][:26]
                if fid in purpose:
                    sizes[(spec["edition"], parts[1], purpose[fid])].append(m.size)
    page_bytes = {f"{e}/{kind}/{p}": {"n": len(v), "mean": round(statistics.mean(v))} for (e, kind, p), v in
                  sorted(sizes.items()) if len(v) >= 5}

    def stored(purposes: tuple[str, ...]) -> float:
        # A page is kept twice: the DOM copy and the raw answer (both gzip-compressed).
        return sum(statistics.mean([x for (e, k, p), v in sizes.items() if k == kind and p in purposes for x in v])
                   for kind in ("dom", "raw"))

    b_result, b_product = stored(("listing",)), stored(("product_detail", "product_page"))
    inp("stored_bytes_per_page", {"result_page_dom_plus_raw": round(b_result), "product_page_dom_plus_raw": round(b_product),
                                  "by_edition_kind_purpose": page_bytes}, "measured",
        "live.tar of runs B1, B2, B3 and D (gzip-compressed files, as stored on the VM)")
    db_lines = [ln.split("|") for ln in DB_SIZES.read_text("utf-8").splitlines() if ln.startswith("walmart_")]
    sha(DB_SIZES)
    db = {x[0]: {"bytes": int(x[1]), "records": int(x[2]), "page_fetches": int(x[3]), "usage_rows": int(x[4]),
                 "observations": int(x[5])} for x in db_lines}
    ox = db["walmart_oxylabs"]
    db_per_obs = ox["bytes"] / ox["observations"]
    inp("database_bytes_per_observation", round(db_per_obs), "measured",
        f"walmart_oxylabs on 2026-10-28T10:22Z (command 367): {ox['bytes']:,} bytes for {ox['observations']:,} "
        f"product observations, {ox['records']:,} records and {ox['page_fetches']:,} page fetches (with their "
        "events and ledger); an order of magnitude only, never measured at production scale")
    exp_rows = []
    for spec in runs:
        if spec["phase"] in ("B3", "D"):
            d = Path(spec["export_dir"])
            b = sum(f.stat().st_size for f in d.rglob("*") if f.is_file())
            exp_rows.append(b / int(profiles[spec["run"]]["products_all"]))
    export_per_row = statistics.mean(exp_rows)
    inp("export_bytes_per_exported_row", round(export_per_row), "measured",
        "the B3 and D export folders (products, provenance, record map, memberships, offers, coverage) per row")

    # 4. Azure prices.
    vm_h = azure["vm_usd_per_hour_linux"]["price"]
    ip_month = round(azure["standard_static_ipv4_usd_per_hour"]["price"] * HOURS_PER_MONTH, 2)
    os_disk = azure["disk_E4_LRS_usd_per_month"]["price"]
    ssd = [(t, g, azure[f"disk_{t}_LRS_usd_per_month"]["price"]) for t, g in
           (("E6", 64), ("E10", 128), ("E15", 256), ("E20", 512), ("E30", 1024))]
    blob_hot = azure_se["blob_Hot_LRS_usd_per_gb_month"][0]["price"]
    # The general meter only (revision 1 also took the "to China" meter, whose 0 GB row hid the 100 GB tier).
    egress = sorted((x for x in azure_se["internet_egress_usd_per_gb"] if x["product"] == "Rtn Preference: MGN"
                     and x["meter"] == "Standard Data Transfer Out"), key=lambda x: x["tier_minimum_units"])
    free_gb = egress[1]["tier_minimum_units"]
    egress_rate = egress[1]["price"]

    def disk_for(gb: float) -> tuple[str, float]:
        gib = gb * 1e9 / 2**30
        for t, size, usd in ssd:
            if gib <= size * 0.8:
                return f"{t} {size} GiB", usd
        return f"more than {ssd[-1][0]} ({ssd[-1][1]} GiB)", float("nan")

    # 5. Scenarios.
    pw = {p: {k: (min(v), max(v)) for k, v in d.items()} for p, d in per_worker.items()}

    def run_pages(n: int, case: dict[str, Any], first: bool, reuse: bool, edition: str) -> dict[str, float]:
        result = n * case["overlap"] / v_page
        refresh = (365 / 12 / CONFIG["detail.reuse_days"]) / RUNS_PER_MONTH
        upc = n if first else n * (case["new_products_per_run"] + refresh)
        var = n * case["variant_candidates_per_product"]
        spo = n * case["sponsored_only_per_product"]
        if reuse and not first:  # exclusions reused; included candidates and new ones read again
            keep = P_INC + (1 - P_INC) * (case["new_products_per_run"] + refresh)
            var, spo = var * keep, spo * keep
        offers = n * case["offer_pages_per_product"]
        retry = case["charged_retry_share"] if case["charged_retry_share"] is not None else retry_measured[edition]
        return {"result": result, "upc": upc, "follow_variant": var, "follow_sponsored": spo, "offer": offers,
                "category": 11, "retry_share": retry}

    def hours(p: dict[str, float], edition: str, workers: int, slow: bool) -> dict[str, float]:
        i = 0 if slow else 1
        r_res, r_upc, r_fu = pw[edition]["result"][i], pw[edition]["upc"][i], pw[edition]["follow"][i]
        h_list = (p["result"] + p["category"]) / (workers * r_res) / 60
        h_upc = (p["upc"] + p["offer"]) / (workers * r_upc) / 60
        # Release 1.5.0 shares follow-up pages among the workers (shards with per-key locks). Tested offline only: no
        # live run has measured it, so the per-worker rate is the 1.4.1 rate, assumed to hold.
        h_fu = (p["follow_variant"] + p["follow_sponsored"]) / (workers * r_fu) / 60
        return {"listing": h_list, "upc": h_upc, "follow_up": h_fu, "total": h_list + h_upc + h_fu}

    def units(p: dict[str, float], case: dict[str, Any], edition: str, workers: int, h: float) -> dict[str, float]:
        segments = max(1, math.ceil(h / SEGMENT_H))
        session = segments * workers * 2
        resent = case["interruptions_per_run"] * workers
        base = p["result"] + p["upc"] + p["follow_variant"] + p["follow_sponsored"] + p["offer"] + p["category"]
        if edition == "oxylabs":
            total = (base + resent) * (1 + p["retry_share"]) + session
        else:
            store = (p["result"] + p["follow_variant"] + p["follow_sponsored"] + p["offer"]) * SD_CREDITS["store_endpoint"]
            general = (p["upc"] + p["category"]) * SD_CREDITS["general_api"]
            total = store + general * (1 + p["retry_share"]) + session + resent * SD_CREDITS["store_endpoint"]
        return {"units": total, "segments": segments, "session_pages": session}

    WORKER_OPTIONS = (1, 2, 4, 8)
    scen: dict[str, Any] = {}
    csv_rows = []
    for nlabel, n in N_SCOPE.items():
        for cname, case in CASES.items():
            for reuse in (False, True):
                for edition in ("oxylabs", "scrapedo"):
                    first = run_pages(n, case, True, reuse, edition)
                    later = run_pages(n, case, False, reuse, edition)
                    m1_later = dict(later)
                    m1_later["upc"] = n * case["new_products_per_run"]  # no UPC is 30 days old in month 1
                    # Workers: the fewest of 1, 2, 4, 8 whose slow-end later run fits 72 h; else 8.
                    fits = {}
                    for w in WORKER_OPTIONS:
                        hs = hours(later, edition, w, True)
                        fits[w] = hs["total"] <= WINDOW_H["tuesday_to_friday"]
                    w_need = next((w for w in WORKER_OPTIONS if fits[w]), None)
                    w_use = w_need or WORKER_OPTIONS[-1]
                    # The one-time first run uses 4 workers (the most measured), whatever later runs need.
                    w_first = max(4, w_use)
                    h_first = (hours(first, edition, w_first, False), hours(first, edition, w_first, True))
                    h_later = (hours(later, edition, w_use, False), hours(later, edition, w_use, True))
                    u_first = units(first, case, edition, w_first, h_first[1]["total"])
                    u_later = units(later, case, edition, w_use, h_later[1]["total"])
                    u_m1 = units(m1_later, case, edition, w_use, h_later[1]["total"])
                    later_month = u_later["units"] * RUNS_PER_MONTH
                    first_month = u_first["units"] + (RUNS_PER_MONTH - 1) * u_m1["units"]
                    if edition == "oxylabs":
                        money = {b: {"later_month": oxy_plan(later_month, b), "first_month": oxy_plan(first_month, b)}
                                 for b in OXY_RATES}
                    else:
                        money = {"later_month": sd_plan(later_month), "first_month": sd_plan(first_month)}
                    # Azure for the later months: collection hours (the slow end) or always on.
                    vm_hours = min(h_later[1]["total"] * RUNS_PER_MONTH, HOURS_PER_MONTH)
                    pages_stored_run = (later["result"] + later["category"]) * b_result + (
                        later["upc"] + later["follow_variant"] + later["follow_sponsored"] + later["offer"]) * b_product
                    pages_stored_first = (first["result"] + first["category"]) * b_result + (
                        first["upc"] + first["follow_variant"] + first["follow_sponsored"] + first["offer"]) * b_product
                    obs_per_run = n * (1 + follow_rates(case) * P_INC)
                    db_gb = obs_per_run * db_per_obs * RUNS_PER_MONTH * RETENTION["observations_days"] / 30.4 / 1e9
                    dumps_gb = db_gb * RETENTION["dumps_kept"]
                    exports_gb_run = obs_per_run * export_per_row / 1e9
                    keep_gb = (pages_stored_first + pages_stored_run) / 1e9 + db_gb + dumps_gb + 2 * exports_gb_run
                    disk_name, disk_usd = disk_for(keep_gb)
                    egress_gb = exports_gb_run * RUNS_PER_MONTH
                    egress_usd = max(0.0, egress_gb - free_gb) * egress_rate
                    blob_usd = round(db_gb * blob_hot, 2)  # one off-VM dump copy (option)
                    azure_month = {"vm_collection_hours": round(vm_hours, 1),
                                   "vm_usd_collection_only": round(vm_hours * vm_h, 2),
                                   "vm_usd_always_on": round(HOURS_PER_MONTH * vm_h, 2),
                                   "os_disk_usd": os_disk, "public_ip_usd": ip_month,
                                   "data_disk": disk_name, "data_disk_usd": disk_usd,
                                   "retained_gb": round(keep_gb, 1),
                                   "off_vm_dump_copy_blob_hot_usd_option": blob_usd,
                                   "egress_gb_exports": round(egress_gb, 2), "egress_usd": round(egress_usd, 2)}
                    az_lo = round(azure_month["vm_usd_collection_only"] + os_disk + ip_month + disk_usd
                                  + azure_month["egress_usd"], 2)
                    az_hi = round(azure_month["vm_usd_always_on"] + os_disk + ip_month + disk_usd
                                  + azure_month["egress_usd"] + blob_usd, 2)
                    sid = f"N{nlabel}/{cname}/{'reuse' if reuse else 'shipped'}/{edition}"
                    sc = {"pages_first_run": {k: round(v) for k, v in first.items() if k != "retry_share"},
                          "pages_later_run": {k: round(v) for k, v in later.items() if k != "retry_share"},
                          "units_first_run": round(u_first["units"]), "units_later_run": round(u_later["units"]),
                          "units_first_month": round(first_month), "units_later_month": round(later_month),
                          "unit": "results" if edition == "oxylabs" else "credits",
                          "money": money,
                          "workers_needed_for_72h": w_need, "workers_used": w_use, "workers_first_run": w_first,
                          "hours_first_run": {k: [round(h_first[0][k], 1), round(h_first[1][k], 1)] for k in h_first[0]},
                          "hours_later_run": {k: [round(h_later[0][k], 1), round(h_later[1][k], 1)] for k in h_later[0]},
                          "later_run_fits_72h_slow_end": h_later[1]["total"] <= 72,
                          "follow_up_stage_alone_hours_slow_end": round(h_later[1]["follow_up"], 1),
                          "segments_later_run": u_later["segments"],
                          "azure_later_month": azure_month, "azure_later_month_usd": [az_lo, az_hi]}
                    if edition == "scrapedo":
                        conc = money["later_month"].get("concurrent")
                        sc["plan_allows_workers"] = conc is None or conc >= w_use
                    scen[sid] = sc
                    if edition == "oxylabs":
                        pm = money["central"]["later_month"]
                        plan_txt = (f"{pm['plan']} ${pm['usd_month']}" if pm["usd_month"] else pm["plan"])
                        lo_pm, hi_pm = money["low"]["later_month"], money["worst"]["later_month"]
                        prov_range = [lo_pm["usd_month"], hi_pm["usd_month"]]
                        fm = money["central"]["first_month"]
                        first_txt = f"{fm['plan']} ${fm['usd_month']}" if fm["usd_month"] else fm["plan"]
                        at_rate = [round(later_month * OXY_RATES[b] / 1000, 2) for b in ("low", "central", "worst")]
                    else:
                        pm = money["later_month"]
                        plan_txt = f"{pm['plan']} ${pm['usd_month']}" if pm["usd_month"] else pm["plan"]
                        prov_range = [pm["usd_month"], pm["usd_month"]]
                        fm = money["first_month"]
                        first_txt = f"{fm['plan']} ${fm['usd_month']}" if fm["usd_month"] else fm["plan"]
                        at_rate = [round(later_month * usd / quota, 2) for _, usd, quota, _ in
                                   (SD_PLANS[-1], SD_PLANS[0])]
                    tot = ([round(prov_range[0] + az_lo, 2), round(prov_range[1] + az_hi, 2)]
                           if None not in prov_range else None)
                    csv_rows.append({
                        "scenario": sid, "N_distinct_pickup_products": n, "case": cname,
                        "follow_up_policy": "reuse exclusions 30 days (not implemented)" if reuse
                        else "as shipped: every candidate every run", "edition": edition,
                        "unit": sc["unit"],
                        "result_pages_later_run": round(later["result"]), "upc_pages_later_run": round(later["upc"]),
                        "follow_up_pages_later_run": round(later["follow_variant"] + later["follow_sponsored"]),
                        "units_later_run": sc["units_later_run"],
                        "units_per_1000_exported_products_later_run": round(
                            u_later["units"] / (n * (1 + follow_rates(case) * P_INC)) * 1000),
                        "units_later_month": sc["units_later_month"],
                        "units_first_run": sc["units_first_run"], "units_first_month": sc["units_first_month"],
                        "plan_later_months_central": plan_txt,
                        "provider_usd_later_month_low_high": prov_range,
                        "provider_usd_later_month_volume_at_rates": " / ".join(str(x) for x in at_rate),
                        "plan_first_month_central": first_txt,
                        "workers_needed_72h": w_need if w_need else "more than 8 (does not fit as shipped)",
                        "hours_later_run_fast_slow": sc["hours_later_run"]["total"],
                        "follow_up_stage_hours_slow": sc["follow_up_stage_alone_hours_slow_end"],
                        "workers_first_run": w_first,
                        "hours_first_run_fast_slow": sc["hours_first_run"]["total"],
                        "azure_later_month_usd_low_high": [az_lo, az_hi],
                        "data_disk": disk_name, "retained_gb": azure_month["retained_gb"],
                        "total_later_month_usd_low_high": tot,
                    })

    # 6. Errata of the 1.3.1 reply's "about USD 590 to 610 a month".
    c3 = v3["scenarios"]["central/F0"]
    c3f1 = v3["scenarios"].get("central/F1", {})
    # The Pickup share of the unfiltered totals, in the listings both were read for that are not produce (at least
    # 1,000 unfiltered results): the lowest Pickup reading against the highest unfiltered one, and the reverse.
    big = [n for n, t in scope["totals"].items() if min(t["unfiltered"]) >= 1000]
    share = [x for n in big for x in (min(scope["totals"][n]["pickup"]) / max(scope["totals"][n]["unfiltered"]),
                                      max(scope["totals"][n]["pickup"]) / min(scope["totals"][n]["unfiltered"]))]
    errata = {
        "said": "1.3.1 <client-message draft>: 'Full catalogue coverage needs a provider plan: about USD 590 to 610 a month "
                "with Oxylabs Flexible and Azure (an estimate, not a quote)'; report section 12.2: 'about USD 587 to "
                "608' (central scope, no follow-ups, a later month)",
        "what_it_was": {"model": "cost_model_131 (version 3), scenario central/F0, a later month",
                        "oxylabs_results_later_month": c3["oxylabs_results"]["later_month"],
                        "oxylabs_plan": c3["oxylabs_plan"]["later_months"],
                        "azure": "VM USD 62 to 67 (collection hours) + data disk E15 19.20 + OS disk 2.40 + IP 3.65",
                        "first_month_results": c3["oxylabs_results"]["first_month"],
                        "with_follow_ups_F1": {"oxylabs_plan": c3f1.get("oxylabs_plan", {}).get("later_months"),
                                               "fits_72h": c3f1.get("later_run_fits_72_h_with_two_workers")}},
        "why_withdrawn": [
            "scope: its 36,000 result pages a run and 120,000 products described Walmart's unfiltered online "
            "assortment (the Scrape.do store endpoint without the Pickup filter, 947 links counted as independent "
            f"listings although {scope['nested']} of the 945 named are nested in another listed listing); the "
            "configured scope is store #3891's Pickup assortment, whose measured totals are "
            f"{min(share) * 100:.1f} % to {max(share) * 100:.1f} % of the unfiltered totals in the {len(big)} "
            f"non-produce listings measured both ways ({', '.join(big)}; for example Bath & Body 2,881 to 2,897 "
            "against 108,395 to 110,434, Diapering 512 to 515 against 30,534 to 30,749)",
            "it left out the follow-ups (sponsored-only products and variant siblings) the requirements include; "
            "with them, the same model put a later run above the 72-hour interval and the volume in Enterprise",
            "the reply gave a monthly figure only; the report's one-time first run (about 6 to 6.5 days with two "
            "workers, during which the twice-weekly occurrences start nothing) was not in the reply",
            "the Oxylabs rate is not published for Walmart: USD 1.00 per 1,000 is one reading of the price page "
            "(USD 0.50 to 1.50 per 1,000 are possible), and the plan steps (USD 100, 500, 2,500) dominate the bill",
            "its run time assumed at most two requests at once; four workers were measured on 2026-10-28, and the "
            "follow-up stage (one task per kind) was found to be the limit of a full run",
            "an estimate, never an invoice or a quote",
        ],
        "replacement": "this model's scenarios by N (COST_SCENARIOS_1_4_1.csv), with a census of the scope as the "
                       "first step",
    }

    # 7. Write.
    meas = {"runs": run_rows, "throughput_segments": thr_rows, "latency_s_ok_by_purpose": lat_summary,
            "yield_per_result_page": v_rows, "follow_up_and_sponsored_ratios": ratios,
            "follow_up_outcomes_D": INPUTS["follow_up_outcomes_phase_D"]["value"],
            "database_2026_10_28": db, "campaign_totals": {
                p: {"requests": sum(r["requests"] for r in run_rows if r["edition"] == p),
                    "units": sum(r["units"] for r in run_rows if r["edition"] == p)} for p in ("oxylabs", "scrapedo")}}
    result = {"model": "cost_model_151 (cost_model_141 version 4, revision 2, with follow-up pages shared among workers)", "generated_by": "C:/w7/tools/cost_model_151.py",
              "tool_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), "requests_made": 0,
              "inputs": INPUTS, "inputs_sha256": READ, "measured": meas, "scenarios": scen,
              "azure_prices": {"vm_usd_per_hour": vm_h, "public_ip_usd_month": ip_month, "os_disk_e4_usd_month": os_disk,
                               "standard_ssd_tiers": ssd, "blob_hot_lrs_usd_per_gb_month": blob_hot,
                               "egress_free_gb_month": free_gb, "egress_usd_per_gb_after": egress_rate},
              "errata_1_3_1_monthly_figure": errata}
    (out / "COST_MODEL_1_5_1.json").write_bytes((json.dumps(result, indent=1, ensure_ascii=False) + "\n").encode("utf-8"))
    def cell(v: Any) -> Any:
        return f"{v[0]} to {v[1]}" if isinstance(v, list) and len(v) == 2 else v

    with (out / "COST_SCENARIOS_1_5_1.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(csv_rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows({k: cell(v) for k, v in r.items()} for r in csv_rows)
    flat = []
    for r in run_rows:
        f = {k: (json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v) for k, v in r.items()}
        flat.append(f)
    fields = sorted({k for r in flat for k in r}, key=lambda k: (list(flat[0]).index(k) if k in flat[0] else 99, k))
    with (out / "MEASURED_COST_PER_RUN_1_4_1_CARRIED.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        w.writerows(flat)
    with (out / "THROUGHPUT_1_4_1_CARRIED.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(thr_rows[0]), lineterminator="\n")
        w.writeheader()
        for t in thr_rows:
            w.writerow({k: (json.dumps(v) if isinstance(v, dict) else v) for k, v in t.items()})
    print(json.dumps({"inputs": {k: v["value"] for k, v in INPUTS.items()
                                 if k not in ("oxylabs_plans", "scrapedo_plans", "cases")},
                      "yield": v_rows, "ratios": ratios}, indent=1, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
