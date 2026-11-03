"""COST_AND_RUNTIME_REPORT.md of release 1.5.1, written offline: the campaign's measurements (CAMPAIGN_MEASURES.json, CAMPAIGN_SUMMARY.json) and the
cost model (COST_MODEL_1_5_1.json, cost_model_151.py). The tables are computed from those files; the text quotes figures from the same files, from
CAMPAIGN_BUDGET.json and from the campaign's command log. Requests nothing.

    python -I -X utf8 cost_report_151.py OUT.md
"""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

E = Path(r"C:\w7\evidence")
MODEL = E / "cost_model_151" / "COST_MODEL_1_5_1.json"
OLD = Path(r"C:\w6\c140\audit\final\cost_model\COST_SCENARIOS_1_4_1.csv")
NEW = E / "cost_model_151" / "COST_SCENARIOS_1_5_1.csv"
SCOPE = Path(r"C:\w6\c140\audit\final\scope\SCOPE_AUDIT_1_4_1.json")
MEAS = E / "campaign_measures_151" / "CAMPAIGN_MEASURES.json"
SUMMARY = E / "campaign_summary_151" / "CAMPAIGN_SUMMARY.json"
BLANKS = E / "b3_blanks_after_campaign" / "B3_BLANKS_AFTER_CAMPAIGN_SUMMARY.json"
SV = E / "reconciliation_151" / "sv_reconcile_151_summary.json"
EV = "WALMART_EVIDENCE_1.5.1.zip"


def n(x: float, d: int = 0) -> str:
    return f"{x:,.{d}f}"


def main(out: Path) -> int:
    m = json.loads(MODEL.read_text("utf-8"))
    inp, sc = m["inputs"], m["scenarios"]
    me = json.loads(MEAS.read_text("utf-8"))
    su = json.loads(SUMMARY.read_text("utf-8"))
    blanks = json.loads(BLANKS.read_text("utf-8"))["tally"]
    sv = json.loads(SV.read_text("utf-8"))["tally"]
    old = {r["scenario"]: r for r in csv.DictReader(OLD.open(encoding="utf-8"))}
    stages = me["stages"]
    by = {s["stage"]: s for s in stages}
    led = su["ledger_by_outcome"]
    L: list[str] = []
    a = L.append
    a("# Cost and runtime report: Walmart release 1.5.1")
    a("")
    a(f"Written offline by `cost_report_151.py` (in `{EV}: 3_reconciliation/cost_model_151/`) from the campaign's ledger and measures and the cost model: "
      "the tables are computed from those files, and the text quotes figures from the same files, from `CAMPAIGN_BUDGET.json` and from the campaign's "
      "command log. This report made no request. Store 3891 (3900 Fountain Square Pl, Waukegan, IL 60085), fulfillment PICKUP. Times are UTC.")
    a("")
    a("Three kinds of figure are kept apart: **measured** (ledger rows and stored pages of real runs), **published** (the providers' and Azure's "
      "price pages, with the date they were read) and **estimate** (a model over an assumed scope). Nothing here is an invoice or a quote. "
      "A pilot's cost is the cost of that pilot: **no figure in sections 1 to 6 is the cost of a complete production run.** The full store size and "
      "the full-run runtime have not been measured.")
    a("")
    a("## 1. What this task used")
    a("")
    total = su["submissions_total"]
    ok = led["ok"]["submissions"]
    ab = led["abandoned"]["submissions"]
    free = led["provider_failed_free"]["submissions"]
    a(f"- **Oxylabs Web API (Bearer key; not Classic), measured:** {total} ledger rows of the campaign's limit of 120: {ok} answered, {ab} reserved "
      f"and never answered because a forced kill stopped them (`abandoned`, kept as possibly charged), {free} provider failure the documentation "
      f"says is not charged (`provider_failed_free`). Last request {led['ok']['last'][:19]}Z. At the campaign's reserve rate of USD 0.0015 per row "
      f"that is USD {su['usd_at_reserve_rate']}; at USD 0.0010, the price Oxylabs publishes for 'Other targets' (it publishes none for Walmart itself), "
      f"it is USD {su['usd_at_published_rate']} (both counting every row). These are estimates from the collector's ledger, not an invoice.")
    a("- **Balance:** not verified. The Web API documents no balance endpoint for a Bearer key, and the owner's dashboard was not opened in this "
      "task. The campaign was sized against a worst-case reconciliation (`CAMPAIGN_BUDGET.json`): USD 4.3444 of the USD 5 welcome credit used if "
      "every earlier request is counted at the reserve rate, USD 0.4261 kept for Mariano's, USD 0.0495 of headroom left below this campaign's "
      "USD 0.18. Oxylabs documents no overage in the self-service flow.")
    a("- **Scrape.do:** no request. See `DELIVERY_INDEX.md` for the free `/info` reading made before packaging. A canary needs about 21 credits, so "
      "its final-version demonstration stays NOT MET; nothing here qualifies it.")
    a("- **Oxylabs Classic:** no request, no credential. The client's proposed campaign is separate and unapproved (`CLASSIC_TEST_PLAN.md`).")
    a("- **Azure:** not used by this task. The test VM was only read over SSH (read-only, 2026-10-31). Its power state is Hamza's decision. It costs "
      f"USD {m['azure_prices']['vm_usd_per_hour']} an hour at the retail price read on 2026-10-28 while it runs; no Azure bill was read.")
    a("- **No purchase, top-up, new account, subscription change or schedule activation.**")
    a("")
    a("## 2. Measured per stage (2026-10-31, this PC, isolated PostgreSQL)")
    a("")
    a(f"Source: `{EV}: 1_new_live/campaign/summary/CAMPAIGN_MEASURES_BY_STAGE.csv`. *Rows* are all of a run's ledger rows (result pages, product pages, "
      "robots.txt, store page, abandoned and free ones). *Valid fresh* are the products the run observed itself. The money columns are an estimate at "
      "the rate named. S1 to S5 ran release 1.5.0 (commit 7b6f325); S6 and S7 ran release 1.5.1 (commit 488a033).")
    a("")
    a("| Stage | Release | Purpose | Rows | Listing pages | Product pages (detail + follow-up) | Valid fresh | Valid per listing page | Rows per 1,000 valid | USD per 1,000 valid at 0.0010 / 0.0015 | Active s | End |")
    a("|---|---|---|---:|---:|---:|---:|---:|---:|---|---:|---|")
    purpose = {"S1": "canary", "S2": "targeted product pages", "S3": "one category, several pages", "S4": "B3's scope, kill and resume, 2 workers",
               "S5b_serial": "1 worker", "S5b_parallel": "2 workers", "S5a": "repeat of S4's first pages, about 40 min later", "S6": "the demonstration on 1.5.1, kill and resume",
               "S7": "repeat of S6's first page, about 39 min later"}
    for s in stages:
        end = s["stop_code"] or "completed its steps"
        a(f"| {s['stage']} | {s['release']} | {purpose[s['stage']]} | {s['ledger_rows']} | {s['listing_pages']} | {s['product_detail_pages']} + {s['follow_up_pages']} | "
          f"{s['valid_fresh']} | {s['valid_fresh_per_listing_page']} | {s['rows_per_1000_valid_fresh']} | {s['usd_per_1000_valid_fresh_at_0_0010']} / {s['usd_per_1000_valid_fresh_at_0_0015']} | "
          f"{s['active_seconds']} | {end} |")
    a("")
    a("Every run's status is `rejected` by the coverage gate (G3): each read capped pages. That is correct. They were pilots and none replaced a dataset. "
      "The figures differ by stage because the stages did different things: they are not comparable as rates of a full run.")
    a("")
    a("## 3. Answer times (measured)")
    a("")
    a("Seconds per answered request, all stages, ledger `elapsed_ms`:")
    a("")
    a("| Purpose | n | Median | Mean | p90 | Max |")
    a("|---|---:|---:|---:|---:|---:|")
    for k, v in me["answer_seconds_ok_by_purpose"].items():
        a(f"| {k} | {v['n']} | {v['median']} | {v['mean']} | {v['p90']} | {v['max']} |")
    a("")
    a(f"The spread is the provider's: the same kind of page took about 10 s or more than 60 s (S7's one listing page took {by['S7']['listing_answer_mean_s']} s). "
      "A run's time cannot be read from the median alone.")
    a("")
    a("## 4. Product-detail enrichment and refresh policy")
    a("")
    a("Policy as shipped: a run reads a product's own page when its UPC or size is blank. An earlier read (fetched or imported) is reused when it was "
      "observed within `detail.reuse_days` (30 days), with its original time, run and revision, and is never described as newly fetched. A pilot states "
      "its budget on the command line: `--pilot-detail-pages N` (at least 1), or `--pilot-no-detail`, which reads no product page and records those "
      "blanks as `not_attempted` (S5b used it). The configuration has no zero-detail setting any more (`detail.max_per_run: 0` is refused, "
      "`--pilot-detail-pages 0` too, and `--pdp-sample` was removed), and a scheduled run refuses any pilot budget. Since 1.5.1 a page budget never "
      "stops reuse.")
    a("")
    a("| Stage | UPC outcomes of its fresh products | Weight outcomes of its fresh products |")
    a("|---|---|---|")
    for s in stages:
        a(f"| {s['stage']} | {s['upc_outcomes']} | {s['weight_outcomes']} |")
    a("")
    a("`budget_deadline_interruption` and `not_attempted` mean the page was not read. They do not mean the value is absent from Walmart. S7 stopped at its "
      "ceiling before its detail and reuse step, so all its UPCs carry that label.")
    a("")
    a("B3's blanks after offline reprocessing and the campaign's reads (`3_reconciliation/b3_blanks_after_campaign/`):")
    a("")
    a("| Field and state | Products |")
    a("|---|---:|")
    for k, v in blanks.items():
        a(f"| {k} | {v} |")
    a("")
    unread = blanks.get("upc: seen by the campaign, its page not read within the budget", 0) + blanks.get("upc: not in any listing page the campaign read", 0)
    a(f"So {unread} of B3's 662 products still need their own page read for a UPC: about {n(unread)} submissions if nothing is reused and no retry is needed, "
      f"USD {unread * 0.001:.2f} to {unread * 0.0015:.2f} at the rates above, an estimate. This budget did not reach them.")
    a("")
    a("## 5. Sponsored and variant follow-ups")
    a("")
    closed = sv.get("closed_live_product_page", 0) + sv.get("closed_live_own_tile", 0)
    a(f"Of the earlier 41 cases (11 sponsored-only placements and 30 tile-only siblings), {closed} are closed live on 2026-10-31 "
      f"({sv.get('closed_live_product_page', 0)} by their own product page in S2, {sv.get('closed_live_own_tile', 0)} seen as their own organic tile) and "
      f"{sv.get('case:PENDING', 0)} stay PENDING, each needing 1 product page; reading them needs about 29 submissions (robots, store, 2 listings and "
      f"{sv.get('case:PENDING', 0)} pages), more than the campaign had left. Of the 610 variant identities of the 1.4.1 reconciliation, {sv.get('identity:HISTORICAL (carried)', 0)} "
      f"keep a 1.4.1 decision not re-observed, {sv.get('identity:PENDING (1.4.1 decision carried)', 0)} were named again with that decision carried, and "
      f"{sv.get('identity:PENDING', 0)} are open.")
    a("")
    a("As shipped, every candidate a run names is read in that run: a sponsored or variant candidate costs one product page per run (unless it is seen as its own "
      "organic tile). Since 1.5.0 those pages are shared among the workers. That sharing is covered by offline tests only: no live run has measured it.")
    a("")
    a("## 6. Failures, retries, restarts and concurrency (measured)")
    a("")
    for r in me["not_ok_rows"]:
        if r["outcome"] == "provider_failed_free":
            a(f"- **Provider failure:** one, on stage {r['stage']} at {r['at'][:19]}Z: HTTP {r['status']} after {r['elapsed_ms'] / 1000:.1f} s on a product page, 0 credits in the ledger; "
              "retried once as the documented transient rule allows, answered in "
              f"{me['retries_answered'][0]['elapsed_ms'] / 1000:.1f} s. That retry used the stage's last room, so the run stopped at its ceiling. The time and the row are the "
              "cost of a transient, even when no credit is charged.")
    aband = [r for r in me["not_ok_rows"] if r["outcome"] == "abandoned"]
    a(f"- **Forced kills:** S4 and S6, one each. The kill left {len(aband)} reservations in total ({sum(1 for r in aband if r['stage'] == 'S4')} in S4, "
      f"{sum(1 for r in aband if r['stage'] == 'S6')} in S6) whose billing outcome is unknown: they stay counted. A resume verifies robots.txt and the store page again: **2 more submissions per resumed worker session** "
      "(S4 and S6 each paid them). S6 lost no record. Its one request in flight at the kill (page 3 of Shampoo) stays counted, and the resume asked for that page again; "
      "no page already answered was asked for again: 15 answered listing fetches of 15 distinct listing URLs. The killed session's segment is abandoned, with no invented end time.")
    a("- **Overlap refusals:** exit 9, no request, in both states (another execution running, and an unfinished run not yet resumed). A first "
      "attempt during S6 named `--max-credits 2`, below the configuration's minimum of 5: it was refused as an invalid configuration (exit 2) before "
      f"any check or request, and repeated with 5 (`{EV}: 1_new_live/campaign/commands.csv`, steps 65 and 66).")
    a("- **`finalize`:** closes an unfinished run with no request. S6 and S7 used it at their ceilings. A resume would have cost 2 submissions.")
    sp, pa = by["S5b_serial"], by["S5b_parallel"]
    a(f"- **Serial against parallel through the real pipeline (S5b, release 1.5.0; not repeated on 1.5.1, no budget):** the same 2 first pages and the same 80 products with 0 field differences. "
      f"Serial: {sp['ledger_rows']} requests, {sp['active_seconds']} s active. Two workers: {pa['ledger_rows']} requests, {pa['active_seconds']} s active: each worker verifies robots.txt and the store page itself. "
      f"The difference of {sp['active_seconds'] - pa['active_seconds']:.1f} s is smaller than the variation in provider latency, so this says **nothing about throughput at scale**. "
      f"It does measure the cost of a second worker's session: {pa['ledger_rows'] - sp['ledger_rows']} submissions.")
    a("")
    a("## 7. Historical measurements (2026-10-28, carried)")
    a("")
    a(f"The 1.4.1 campaign's measurements are carried unchanged in `{EV}: 3_reconciliation/cost_model_151/MEASURED_COST_PER_RUN_1_4_1_CARRIED.csv` and "
      "`THROUGHPUT_1_4_1_CARRIED.csv`. They belong to releases 1.4.0 and 1.4.1 and are the only measurements with up to 4 workers. The per-worker rates the estimates use:")
    a("")
    tp = inp["throughput_requests_per_min_per_worker"]["value"]
    for e, name in (("oxylabs", "Oxylabs"), ("scrapedo", "Scrape.do")):
        a(f"- {name}, requests a minute per worker: result pages {tp[e]['result'][0]} to {tp[e]['result'][1]}; UPC pages {tp[e]['upc'][0]} to {tp[e]['upc'][1]}; follow-up pages {tp[e]['follow'][0]} to {tp[e]['follow'][1]}.")
    a(f"- Valid fresh products per Pickup result page: {inp['valid_products_per_result_page']['value']} ({inp['valid_products_per_result_page']['source']}). The campaign's pages above agree in order of magnitude; they were not used to change the model.")
    a("")
    a("## 8. Full scope: estimates, not measurements")
    a("")
    a("**No run has read the full scope, and the store's Pickup assortment has not been counted.** N, the distinct products of store 3891's Pickup assortment in the 11 required CSV rows, is an assumption: "
      "20,000, 40,000 and 80,000, with 120,000 kept only as the historical reference to Walmart's unfiltered online assortment. Two cases (lean, heavy) bracket overlap, variant candidates and sponsored-only products "
      "per product; two follow-up policies: *shipped* (every candidate a run names is read in that run) and *reuse* (a design option, **not implemented**: an exclusion is reused for 30 days).")
    a("")
    a("The model is the 1.4.1 model with one change, the one thing release 1.5.0 changed in it: follow-up pages are shared among the workers. Its prices are those read on 2026-10-28. The Oxylabs plan step depends on a "
      "rate Oxylabs does not publish for Walmart: USD 0.50, 1.00 or 1.50 per 1,000 results are readings of its price page.")
    a("")
    a("| Scenario | Edition | Units first run | Units later month | Plan, later month | Provider USD a later month | First-run hours (workers) | Later-run hours (workers) | 1.4.1 model: later-run hours (workers) | Fits 72 h on paper | Azure USD a later month |")
    a("|---|---|---:|---:|---|---|---|---|---|---|---|")
    for key, s in sc.items():
        scen, edition = key.rsplit("/", 1)
        unit = s["unit"]
        if edition == "oxylabs":
            lm = [s["money"][r]["later_month"] for r in ("low", "central", "worst")]
            plan = " / ".join(x["plan"] for x in lm) + " (low / central / worst rate)"
            usd = " / ".join(n(x["usd_month"]) for x in lm) + " (at the rate alone: " + " / ".join(f"{x['usd_at_rate']:.0f}" for x in lm) + ")"
        else:
            mo = s["money"]["later_month"]
            plan = mo["plan"]
            usd = n(mo["usd_month"]) if mo.get("usd_month") else "custom quote"
        hf, hl = s["hours_first_run"]["total"], s["hours_later_run"]["total"]
        azl = s["azure_later_month_usd"]
        o = old[key]
        need = o["workers_needed_72h"]
        was = f"{o['hours_later_run_fast_slow']} ({need if len(need) < 4 else 'more than 8'})"
        a(f"| {scen} | {edition} | {n(s['units_first_run'])} {unit} | {n(s['units_later_month'])} | {plan} | {usd} | {hf[0]} to {hf[1]} ({s['workers_first_run']}) | {hl[0]} to {hl[1]} ({s['workers_used']}) | {was} | "
          f"{'yes' if s['later_run_fits_72h_slow_end'] else 'no'} | {azl[0]} to {azl[1]} |")
    a("")
    a("The hours assume the per-worker rates of section 7 hold: 8 workers were never run (4 is the most measured), and sharing follow-ups among workers has never been measured live.")
    a("")
    a("## 9. Twice-weekly cadence: capacity")
    a("")
    fits = sum(1 for s in sc.values() if s["later_run_fits_72h_slow_end"])
    a(f"**Status: UNKNOWN, not met and not refuted.** The requirement is the full required scope twice weekly per store. A full run has never been timed, so no measured runtime shows that the cadence is met. On paper, {fits} of {len(sc)} "
      "scenarios now fit the 72 hours between the Tuesday and Friday occurrences with 1 to 8 workers, where the 1.4.1 model had many beyond it because the follow-up stage ran one worker per kind. That is an estimate resting on rates not measured for this design.")
    a("")
    a("What the collector does meanwhile: it does not drop an occurrence. A scheduled occurrence keeps its identity and backlog in `schedule_occurrences`; a late, held, deferred or overlapped one is reported, overlapping writes are refused, and `schedule-status` "
      "reports capacity as GAP or UNKNOWN. Queuing alone does not meet the cadence. Schedules stay off: none has run in this campaign.")
    a("")
    a("If one full run shows a gap, the changes available are, in order of cost: more workers up to the configured maximum of 8 (each worker session costs 2 submissions per segment, and a Scrape.do plan's concurrency must allow them); reuse of exclusions for follow-ups "
      "for 30 days (a design option, not implemented; it would need a new release); and a higher provider tier. The scope is not narrowed in any of them.")
    a("")
    a("## 10. Azure (estimates)")
    a("")
    az = m["azure_prices"]
    ex = sc["N40k/lean/shipped/oxylabs"]["azure_later_month"]
    a(f"Retail prices read on 2026-10-28 (none re-read in this task): VM USD {az['vm_usd_per_hour']}/h; public IP USD {az['public_ip_usd_month']}/month; OS disk (E4) USD {az['os_disk_e4_usd_month']}/month; data disk " +
      ", ".join(f"{t} {g} GiB USD {u}" for t, g, u in az["standard_ssd_tiers"]) + f" a month; Blob hot LRS USD {az['blob_hot_lrs_usd_per_gb_month']}/GB-month; Internet egress free for the first {n(az['egress_free_gb_month'])} GB a month, then USD {az['egress_usd_per_gb_after']}/GB.")
    a("")
    a(f"Example, N40k lean shipped (Oxylabs): VM {ex['vm_collection_hours']} collection hours USD {ex['vm_usd_collection_only']} (always on USD {ex['vm_usd_always_on']}), OS disk USD {ex['os_disk_usd']}, IP USD {ex['public_ip_usd']}, data disk {ex['data_disk']} USD {ex['data_disk_usd']} for "
      f"{ex['retained_gb']} GB retained, Blob copy option USD {ex['off_vm_dump_copy_blob_hot_usd_option']}, egress {ex['egress_gb_exports']} GB USD {ex['egress_usd']}. Release 1.5.1 has not been deployed on Azure: the historical Azure runs belong to releases up to 1.4.1 on Hamza's test VM.")
    a("")
    a("## 11. What would turn the estimates into measurements")
    a("")
    roots = json.loads(SCOPE.read_text("utf-8"))["roots"]
    rate = inp["oxylabs_usd_per_1000_results"]["value"]
    census = roots + 2
    a(f"1. A scope census: one Pickup result page per root listing ({roots} roots) reads each root's Pickup total. The sum bounds N from above and fixes the result pages of a full run: about {n(census)} Oxylabs results, USD {census * rate['low'] / 1000:.2f} to {census * rate['worst'] / 1000:.2f} as an estimate.")
    a("2. A written Oxylabs rate for the walmart source, and a current reading of the owner's dashboard.")
    a("3. One full run of the configured scope on the final revision, timed by stage, with the follow-ups read.")
    a("")
    a(f"Model: `{m['model']}`; tool SHA-256 `{m['tool_sha256']}`; requests made: {m['requests_made']}. In `{EV}: 3_reconciliation/cost_model_151/`.")
    text = "\n".join(L) + "\n"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(text.encode("utf-8"))
    print(out, len(L), "lines", hashlib.sha256(text.encode()).hexdigest()[:16], "fits", fits, "of", len(sc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1])))
