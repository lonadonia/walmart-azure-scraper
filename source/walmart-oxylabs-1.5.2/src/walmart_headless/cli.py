"""``walmart-collector``: the headless collector's command line.

Every command writes structured logs (one JSON object per line) on standard output and ends with a
``RESULT`` line (``--pretty`` prints the result indented instead). The exit code says how it ended
(:class:`walmart_headless.operations.Exit`): 0 done, 2 configuration, 3 credentials, 4 credits, 5 site
refusal, 6 rejected, 7 store or source checks, 8 held, 9 busy, 75 interrupted (resumable), 1 unexpected.

A termination signal (SIGTERM from Azure at the job's timeout or a stop, or Ctrl+C) stops a collection at
once: the provider session is closed, the run's checkpoints are kept, the run is left ``interrupted`` with
the reason ``TERMINATED``, the store lock is released and the command exits with 75.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import shlex
import signal
import sys
from collections.abc import Coroutine
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from walmart_headless import __version__, operations
from walmart_headless.acquisition import oxylabs
from walmart_headless.acquisition.scrapedo import load_keys, redact
from walmart_headless.core import logs
from walmart_headless.core.paths import DERIVED_FROM
from walmart_headless.core.version import source_version
from walmart_headless.db import migrate
from walmart_headless.operations import CommandError, Context, Exit

ENV_CONFIG = "WALMART_COLLECTOR_CONFIG"
ENV_LOG_LEVEL = "WALMART_COLLECTOR_LOG_LEVEL"
ENV_ACTOR = "WALMART_COLLECTOR_ACTOR"
ENV_COMMAND = "WALMART_COLLECTOR_COMMAND"
LIMIT_FLAGS = {
    "max_products": "max_products_per_run",
    "max_products_per_category": "max_products_per_category",
    "max_pages_per_listing": "max_pages_per_listing",
    "max_subcategories_per_category": "max_subcategories_per_category",
    "max_credits": "max_credits_per_run",
    "max_minutes": "max_run_minutes",
}


# SIGTERM (Azure, systemd, docker stop), SIGINT (Ctrl+C) and, on Windows, SIGBREAK (Ctrl+Break: the signal
# another process can send to a console process group there).
STOP_SIGNALS = (signal.SIGTERM, signal.SIGINT, *([signal.SIGBREAK] if hasattr(signal, "SIGBREAK") else []))


class Terminated(Exception):
    pass


def run_async(coro: Coroutine[Any, Any, Exit]) -> Exit:
    """Run a collection; a termination signal cancels it (the pipeline then leaves the run resumable)."""
    loop = asyncio.new_event_loop()
    task = loop.create_task(coro)
    received: list[str] = []

    def on_signal(signum: int, _frame: Any) -> None:
        name = signal.Signals(signum).name
        received.append(name)
        logs.log("WARN", "SIGNAL_RECEIVED", signal=name)
        loop.call_soon_threadsafe(task.cancel)

    previous = {sig: signal.signal(sig, on_signal) for sig in STOP_SIGNALS}
    try:
        return loop.run_until_complete(task)
    except asyncio.CancelledError:
        raise Terminated(received[0] if received else "cancelled") from None
    finally:
        for sig, handler in previous.items():
            signal.signal(sig, handler)
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()


def _categories(value: str) -> list[int]:
    try:
        return sorted({int(x) for x in value.split(",") if x.strip()})
    except ValueError:
        raise argparse.ArgumentTypeError("categories are CSV row numbers, e.g. 3,7") from None


def _at_least_one(value: str) -> int:
    n = int(value)
    if n < 1:
        raise argparse.ArgumentTypeError("at least 1 (a pilot with no detail page says --pilot-no-detail)")
    return n


def _safe(text: object) -> str:
    """An error message with any configured key value removed (never printed or logged)."""
    return oxylabs.redact(redact(str(text), load_keys()), oxylabs.load_key())[:2000]


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="walmart-collector", description=__doc__.split("\n\n")[0])
    p.add_argument("--version", action="version", version=f"walmart-azure-headless {__version__}")
    p.add_argument(
        "--config",
        type=Path,
        default=Path(os.environ.get(ENV_CONFIG, "config/collector.yaml")),
        help=f"collector configuration file (default: ${ENV_CONFIG} or config/collector.yaml)",
    )
    p.add_argument("--pretty", action="store_true", help="print the result indented")
    sub = p.add_subparsers(dest="command", required=True)

    v = sub.add_parser("validate-config", help="check the configuration files and the environment")
    v.add_argument(
        "--require-credentials",
        action="store_true",
        help="fail (3) without the key of every provider the stores' configuration names",
    )
    v.add_argument("--check-db", action="store_true", help="also connect and check the schema revision")

    sub.add_parser("db-upgrade", help="create or upgrade the database schema")
    sub.add_parser("sync-config", help="load the stores and the category CSV into the database")

    r = sub.add_parser("run", help="collect a store (a new run)")
    r.add_argument("--store", required=True)
    r.add_argument(
        "--scheduled",
        action="store_true",
        help="a scheduled execution: act only when it is the store's due local occurrence",
    )
    r.add_argument("--categories", type=_categories, help="CSV row numbers (default: the configuration)")
    r.add_argument(
        "--subcategory",
        action="append",
        metavar="ROW:LISTING",
        help="narrow a category row to one subcategory listing its category page names, by path or URL "
        "(repeatable), e.g. 0:/browse/food/fresh-fruits/976759_976793_9756351",
    )
    r.add_argument("--pdp-sample", type=int, help=argparse.SUPPRESS)  # refused, with the reason
    r.add_argument(
        "--pilot-detail-pages",
        type=_at_least_one,
        metavar="N",
        help="a pilot's budget: at most N product detail pages this run (default: every exported product "
        "missing a UPC or a size). A run with a budget is never published as the store's dataset; the "
        "products it leaves stay in the store's queue, recorded as interrupted by the budget",
    )
    r.add_argument(
        "--pilot-no-detail",
        action="store_true",
        help="a pilot with no product detail page: its blank UPCs and sizes are recorded as not attempted, "
        "never as absent from the source",
    )
    r.add_argument(
        "--provider",
        choices=("scrapedo", "oxylabs"),
        help="the run's page provider (default: the configuration); one provider per run",
    )
    r.add_argument("--workers", type=int, help="parallel workers of this run (default: the configuration)")
    r.add_argument(
        "--follow-up-pages",
        type=int,
        metavar="N",
        help="at most N product pages per follow-up kind (sponsored-only, variant siblings); 0 = none",
    )
    for flag in LIMIT_FLAGS:
        r.add_argument("--" + flag.replace("_", "-"), dest=flag, type=int)

    for name, text in (
        ("resume", "continue an interrupted run from its checkpoints"),
        ("finalize", "check and export what an unfinished run collected (no provider request)"),
    ):
        c = sub.add_parser(name, help=text)
        c.add_argument("--run")
        c.add_argument("--store")
        if name == "resume":
            c.add_argument("--workers", type=int, help="parallel workers of this execution")

    rp = sub.add_parser(
        "replay",
        help="read an earlier live run's stored pages again with this code (offline; a REPLAY run, never "
        "published)",
    )
    rp.add_argument("--run", required=True, help="the LIVE run whose stored pages are read again")

    s = sub.add_parser("stop", help="stop collecting; the run is finalized with what it collected")
    s.add_argument("--run")
    s.add_argument("--store")
    s.add_argument("--reason", default="stopped by an operator")

    pb = sub.add_parser("publish", help="publish a complete validated run")
    pb.add_argument("--run", required=True)
    pb.add_argument("--accept-warnings", metavar="REASON")

    st = sub.add_parser("status", help="runs, holds, the published dataset and the provider ledger")
    st.add_argument("--store")
    st.add_argument("--run")
    st.add_argument("--limit", type=int, default=5)

    e = sub.add_parser("export", help="copy a run's verified export files to a folder")
    e.add_argument("--run")
    e.add_argument("--store", help="the store's published dataset (when --run is not given)")
    e.add_argument("--out", type=Path, required=True)

    ve = sub.add_parser("validate-export", help="the 22-field contract (and, for a run, the source check)")
    ve.add_argument("--file", type=Path)
    ve.add_argument("--run")

    pv = sub.add_parser(
        "provider-balance",
        help="the provider's balance (Scrape.do: free /info) or, for Oxylabs, its ceiling and ledger",
    )
    pv.add_argument("--provider", choices=("scrapedo", "oxylabs"), default="scrapedo")

    sc = sub.add_parser("set-ceiling", help="a provider's spending ceiling across every run from now on")
    sc.add_argument("--provider", choices=("scrapedo", "oxylabs"), default="scrapedo")
    sc.add_argument("--credits", type=float, help="Scrape.do: total credits")
    sc.add_argument(
        "--usd-per-credit", type=float, help="Scrape.do: the plan's price of one credit (0: free)"
    )
    sc.add_argument("--submissions", type=int, help="Oxylabs: total submissions (every attempt counts)")
    sc.add_argument("--usd", type=float, help="Oxylabs: total US dollars (each submission at its rate)")
    sc.add_argument("--minutes", type=float, help="Oxylabs: minutes from the first submission")
    sc.add_argument("--usd-per-result", type=float, help="Oxylabs: the rate reserved per submission")
    sc.add_argument("--basis", required=True, help="why this ceiling (recorded)")

    sb = sub.add_parser("set-budget", help="the task's money budget across every provider from now on")
    sb.add_argument("--usd", type=float, required=True)
    sb.add_argument("--basis", required=True, help="why this budget (recorded)")

    cr = sub.add_parser("coverage-report", help="a run's coverage reconciliation and follow-up outcomes")
    cr.add_argument("--run", required=True)
    cr.add_argument("--out", type=Path, help="write CSV and JSON files to this folder")

    fq = sub.add_parser(
        "follow-ups",
        help="the store's follow-up queue: sponsored-only products and variant siblings its runs named, and "
        "whether a run has read them to a decision",
    )
    fq.add_argument("--store", required=True)
    fq.add_argument("--state", choices=("pending", "resolved", "all"), default="pending")
    fq.add_argument("--kind", choices=("sponsored", "variant", "detail"))

    ss = sub.add_parser(
        "schedule-status",
        help="the store's scheduled occurrences: backlog, lateness, missed deadlines and the capacity gap "
        "(reads only)",
    )
    ss.add_argument("--store", required=True)

    fd = sub.add_parser(
        "field-dispositions",
        help="why each exported product's UPC and size are filled or empty, in a run (reads only)",
    )
    fd.add_argument("--run", required=True)
    fd.add_argument("--csv", type=Path, metavar="FILE", help="also write the table to this CSV file")

    ic = sub.add_parser(
        "import-detail-captures",
        help="load saved product pages, with their original time, run, revision and hash, for runs to reuse "
        "(offline: no provider request; pages of another item are refused)",
    )
    ic.add_argument("--store", required=True)
    ic.add_argument("--index", required=True, type=Path, help="a JSON list: see docs/OPERATIONS.md")

    al = sub.add_parser(
        "attest-lineage",
        help="record that a LIVE run made before release 1.3.1 read its pages from the network (its "
        "observations may then serve later runs)",
    )
    al.add_argument("--run", required=True)
    al.add_argument("--reason", required=True)
    al.add_argument("--evidence", required=True, help="what the attestation rests on (recorded)")

    rh = sub.add_parser("release-hold", help="let a held store collect again")
    rh.add_argument("--store", required=True)
    rh.add_argument("--reason", required=True)

    si = sub.add_parser("schedule-info", help="the store's schedule and the Azure cron expression (UTC)")
    si.add_argument("--store", required=True)

    sub.add_parser(
        "ops",
        help=f"run the command written in ${ENV_COMMAND} (the Azure operations job; default: status)",
    )
    return p


def _result(args: argparse.Namespace, data: Any, code: Exit) -> int:
    if args.pretty:
        print(json.dumps(data, indent=2, ensure_ascii=False, default=str))
    else:
        logs.log("INFO", "RESULT", command=args.command, exit_code=int(code), result=data)
    return int(code)


def _ctx(args: argparse.Namespace) -> Context:
    return Context(args.config)


def dispatch(args: argparse.Namespace) -> int:
    actor = os.environ.get(ENV_ACTOR) or "operator"
    cmd = args.command
    if cmd == "ops":
        command = shlex.split(os.environ.get(ENV_COMMAND) or "status")
        if not command or command[0] == "ops":
            raise CommandError(Exit.CONFIG, f"{ENV_COMMAND} must name another command")
        logs.log("INFO", "OPS_COMMAND", command=command)
        return main(["--config", str(args.config), *(["--pretty"] if args.pretty else []), *command])
    if cmd == "validate-config":
        ctx = _ctx(args)
        try:
            data = operations.describe_config(ctx)
            code = Exit.OK
            needed = {s["provider"] for s in data["stores"] if s["enabled"]}
            have = {
                "scrapedo": data["environment"]["scrapedo_key"]["configured"],
                "oxylabs": data["environment"]["oxylabs_key"]["configured"],
            }
            if args.require_credentials and not all(have[p] for p in needed):
                code = Exit.CREDENTIALS
            if any(s["scheduled_scope_problem"] for s in data["stores"]):
                code = Exit.CONFIG  # a schedule never runs a narrowed scope (operations.scheduled_run)
            if args.check_db:
                current, head = migrate.state(ctx.engine)
                data["database"] = {"revision": current, "head": head, "current": current == head}
                if current != head:
                    code = Exit.CONFIG
            data["code"] = {"version": __version__, "derived_from": DERIVED_FROM, **source_version()}
            return _result(args, data, code)
        finally:
            ctx.close()
    if cmd == "schedule-info":
        ctx = _ctx(args)
        data = next(s for s in operations.describe_config(ctx)["stores"] if s["key"] == args.store)
        return _result(args, {"store": args.store, "schedule": data["schedule"]}, Exit.OK)
    if cmd == "validate-export" and args.run is None:
        code, data = operations.validate_export(None, args.file, None)
        return _result(args, data, code)

    ctx = _ctx(args)
    try:
        if cmd == "db-upgrade":
            before, after = migrate.upgrade(ctx.engine)
            return _result(args, {"before": before, "after": after}, Exit.OK)
        ctx.require_schema()
        if cmd == "sync-config":
            return _result(args, operations.sync_config(ctx, actor), Exit.OK)
        if cmd == "run":
            overrides: dict[str, Any] = {
                LIMIT_FLAGS[k]: getattr(args, k) for k in LIMIT_FLAGS if getattr(args, k)
            }
            if args.categories:
                overrides["categories"] = args.categories
            if args.subcategory:
                chosen: dict[str, list[str]] = {}
                for item in args.subcategory:
                    row, sep, listing = item.partition(":")
                    if not sep or not row.strip().isdigit() or not listing.strip():
                        raise CommandError(Exit.CONFIG, f"--subcategory takes ROW:LISTING, not {item!r}")
                    chosen.setdefault(row.strip(), []).append(listing.strip())
                overrides["subcategories"] = chosen
            if args.pdp_sample is not None:
                raise CommandError(
                    Exit.CONFIG,
                    "--pdp-sample was removed in release 1.5.0: production reads every exported product "
                    "missing a UPC or a size; a pilot uses --pilot-detail-pages N or --pilot-no-detail",
                )
            if args.pilot_detail_pages is not None and args.pilot_no_detail:
                raise CommandError(
                    Exit.CONFIG, "--pilot-detail-pages and --pilot-no-detail exclude each other"
                )
            if args.pilot_detail_pages is not None:
                overrides["pilot_detail_pages"] = args.pilot_detail_pages
            if args.pilot_no_detail:
                overrides["pilot_no_detail"] = True
            if args.provider:
                overrides["provider"] = args.provider
            if args.workers:
                overrides["workers"] = args.workers
            if args.follow_up_pages is not None:
                overrides["follow_up_pages"] = args.follow_up_pages
            if args.scheduled:
                if overrides:
                    raise CommandError(
                        Exit.CONFIG, "a scheduled run takes its settings from the configuration"
                    )
                code = run_async(operations.scheduled_run(ctx, args.store))
            else:
                code = run_async(operations.start_run(ctx, args.store, overrides, actor))
            return _result(args, {"store": args.store}, code)
        if cmd == "resume":
            return _result(
                args, {}, run_async(operations.resume_run(ctx, args.run, args.store, args.workers))
            )
        if cmd == "finalize":
            return _result(args, {}, run_async(operations.finalize_run(ctx, args.run, args.store)))
        if cmd == "replay":
            return _result(
                args, {"source_run": args.run}, run_async(operations.replay_run(ctx, args.run, actor))
            )
        if cmd == "stop":
            return _result(args, operations.stop_run(ctx, args.run, args.store, args.reason, actor), Exit.OK)
        if cmd == "publish":
            return _result(args, operations.publish(ctx, args.run, args.accept_warnings, actor), Exit.OK)
        if cmd == "status":
            return _result(args, operations.status(ctx, args.store, args.run, args.limit), Exit.OK)
        if cmd == "export":
            return _result(args, operations.export(ctx, args.run, args.store, args.out), Exit.OK)
        if cmd == "validate-export":
            code, data = operations.validate_export(ctx, args.file, args.run)
            return _result(args, data, code)
        if cmd == "provider-balance":
            code, data = operations.provider_balance(ctx, actor, args.provider)
            return _result(args, data, code)
        if cmd == "set-ceiling":
            value = operations.set_ceiling(
                ctx,
                args.credits,
                args.basis,
                actor,
                provider=args.provider,
                usd_per_credit=args.usd_per_credit,
                submissions=args.submissions,
                usd=args.usd,
                minutes=args.minutes,
                usd_per_result=args.usd_per_result,
            )
            return _result(args, value, Exit.OK)
        if cmd == "set-budget":
            return _result(args, operations.set_budget(ctx, args.usd, args.basis, actor), Exit.OK)
        if cmd == "coverage-report":
            return _result(args, operations.coverage_report(ctx, args.run, args.out), Exit.OK)
        if cmd == "attest-lineage":
            value = operations.attest_lineage(ctx, args.run, args.reason, args.evidence, actor)
            return _result(args, value, Exit.OK)
        if cmd == "schedule-status":
            return _result(args, operations.schedule_status(ctx, args.store), Exit.OK)
        if cmd == "field-dispositions":
            return _result(args, operations.run_field_dispositions(ctx, args.run, args.csv), Exit.OK)
        if cmd == "import-detail-captures":
            return _result(args, operations.import_detail_captures(ctx, args.store, args.index), Exit.OK)
        if cmd == "follow-ups":
            state = None if args.state == "all" else args.state
            return _result(args, operations.follow_ups(ctx, args.store, state, args.kind), Exit.OK)
        if cmd == "release-hold":
            return _result(args, operations.release_hold(ctx, args.store, args.reason, actor), Exit.OK)
        raise CommandError(Exit.CONFIG, f"unknown command {cmd}")
    finally:
        ctx.close()


def main(argv: list[str] | None = None) -> int:
    logs.configure(level=os.environ.get(ENV_LOG_LEVEL, "INFO"))
    args = build_parser().parse_args(argv)
    try:
        return dispatch(args)
    except CommandError as exc:
        logs.log(
            "ERROR",
            "COMMAND_REFUSED",
            command=args.command,
            exit_code=int(exc.code),
            message=_safe(exc),
            **exc.data,
        )
        return int(exc.code)
    except Terminated as exc:
        logs.log("WARN", "TERMINATED", command=args.command, signal=str(exc), exit_code=int(Exit.INTERRUPTED))
        return int(Exit.INTERRUPTED)
    except (ValidationError, FileNotFoundError, KeyError, ValueError) as exc:
        logs.log(
            "ERROR", "CONFIG_INVALID", command=args.command, exit_code=int(Exit.CONFIG), message=_safe(exc)
        )
        return int(Exit.CONFIG)
    except RuntimeError as exc:
        if "DATABASE_URL" in str(exc):
            logs.log(
                "ERROR",
                "CONFIG_INVALID",
                command=args.command,
                exit_code=int(Exit.CONFIG),
                message=_safe(exc),
            )
            return int(Exit.CONFIG)
        logs.log("ERROR", "UNEXPECTED", command=args.command, error=type(exc).__name__, message=_safe(exc))
        return int(Exit.UNEXPECTED)
    except Exception as exc:
        logs.log("ERROR", "UNEXPECTED", command=args.command, error=type(exc).__name__, message=_safe(exc))
        return int(Exit.UNEXPECTED)


def entrypoint() -> None:
    sys.exit(main())


if __name__ == "__main__":
    entrypoint()
