"""Assemble the evidence tree of Walmart release 1.5.1 (offline) into a NEW folder, by evidence class.

- Refuses an output folder that exists; every source is read only.
- Copies byte for byte, except:
  (a) text naming the VM's public IP, the operator's IP or the full Azure subscription ID, or a workstation user's folder: abbreviated.
      The rules come from a local file that names the full values and is never packaged (C:/w6/tools/redaction_rules.local.json);
  (b) stored Walmart pages (*.html.gz): the release's own sanitizer (walmart_headless.sites.walmart.sanitize) is applied and the page is
      recompressed (gzip, mtime 0). Each page is checked: its page data differs only in values now "[REDACTED]", and the HTML outside the page
      data is unchanged. Source and package SHA-256 are both recorded.
- Lists every file in EVIDENCE_MANIFEST.csv (path, class, source, source SHA-256, package SHA-256, change) and every changed file in SANITIZATION_LOG.csv.
- The providers' raw answers (live/raw/*.body.gz) stay on the workstation: each is listed with its SHA-256 in RAW_ORIGINALS_MANIFEST.csv of its run.
- Checks the result (ASSEMBLY_CHECK.txt) and exits 1 if a check fails.

usage: <worktree venv python> -I -X utf8 assemble_evidence_151.py OUT_DIR
"""

from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, r"C:\w7\wt\headless\walmart-azure-headless\src")
from walmart_headless.sites.walmart.sanitize import sanitize_html

W7 = Path(r"C:\w7")
E = W7 / "evidence"
L = E / "live150"
DATA = W7 / "live" / "data" / "runs" / "walmart-3891-pickup"
RULES_FILE = Path(r"C:\w6\tools\redaction_rules.local.json")
DOCS = W7 / "stage151" / "evidence_docs"
REPO = Path(r"<repository>")
OLD = REPO / "deliverables" / "20261028_walmart_1.4.1_dual_provider"
REDACTED = "[REDACTED]"
NEXT_DATA = re.compile(r"(<script[^>]*\bid=[\"']__NEXT_DATA__[\"'][^>]*>)(?P<json>.*?)(</script>)", re.S | re.I)
TEXT_SUFFIX = {".txt", ".json", ".jsonl", ".csv", ".md", ".py", ".sh", ".log", ".err", ".xml", ".sql", ".yaml", ".yml", ".html"}
# The operator's own path on this PC, and its user name, in logs and tools. Not a secret; abbreviated so that nothing personal travels.
USER_PATH = (re.compile(rb"<projects>(\\\\|\\|/)marianos-scraper"), b"<repository>")
USER_HOME = (re.compile(rb"C:(\\\\|\\|/)Users(\\\\|\\|/)<user>\b"), b"<home>")
# The workstation's host name, which the collector writes into worker names ("<host>:<pid>:w<n>") and pytest into JUnit XML.
HOST = (re.compile(rb"<workstation>"), b"<workstation>")


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def rules() -> list[tuple[re.Pattern[bytes], bytes, str]]:
    doc = json.loads(RULES_FILE.read_text("utf-8"))
    out = []
    for r in doc["rules"]:
        out.append((re.compile(r["pattern"].encode("utf-8")), r["replacement"].encode("utf-8"), r.get("what", "abbreviated value")))
    return out


RULES = rules()


def abbreviate(data: bytes) -> tuple[bytes, list[str]]:
    changed = []
    for rx, repl, what in RULES:
        data, n = rx.subn(repl, data)
        if n:
            changed.append(f"{what}: {n}")
    for rx, repl in (USER_PATH, USER_HOME):
        data, n = rx.subn(repl, data)
        if n:
            changed.append(f"{repl.decode()} path: {n}")
    data, n = HOST[0].subn(HOST[1], data)
    if n:
        changed.append(f"workstation host name: {n}")
    return data, changed


def leaves(a, b, key, out):
    if isinstance(a, dict) and isinstance(b, dict):
        if set(a) != set(b):
            out.append(f"{key}: keys differ")
            return
        for k in a:
            leaves(a[k], b[k], str(k), out)
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            out.append(f"{key}: lengths differ")
            return
        for x, y in zip(a, b, strict=True):
            leaves(x, y, key, out)
    elif a != b:
        out.append(f"redacted:{key}" if b == REDACTED else f"{key}: changed")


def page(data: bytes) -> tuple[bytes, str, dict[str, str]]:
    before_b = gzip.decompress(data)
    before = before_b.decode("utf-8")
    after, rep = sanitize_html(before)
    if after == before:
        return data, "", {}
    mb, ma = NEXT_DATA.search(before), NEXT_DATA.search(after)
    if bool(mb) != bool(ma):
        raise SystemExit("page data on one side only")
    keys: Counter[str] = Counter()
    if mb and ma:
        diffs: list[str] = []
        leaves(json.loads(mb.group("json")), json.loads(ma.group("json")), "", diffs)
        unexplained = [d for d in diffs if not d.startswith("redacted:")]
        same = (before[: mb.start("json")] + before[mb.end("json") :]) == (after[: ma.start("json")] + after[ma.end("json") :])
        if unexplained or not same:
            raise SystemExit(f"unexplained change: {unexplained[:5]}; HTML outside the page data unchanged: {same}")
        keys = Counter(d.split(":", 1)[1] for d in diffs)
    after_b = after.encode("utf-8")
    change = (f"sanitizer of release 1.5.1: {rep.page_data_values_redacted + rep.other_values_redacted} values replaced with {REDACTED} (" + ", ".join(f"{k} {n}" for k, n in sorted(keys.items())) + ")")
    buf = io.BytesIO()
    with gzip.GzipFile(fileobj=buf, mode="wb", compresslevel=9, mtime=0, filename="") as gz:
        gz.write(after_b)
    return buf.getvalue(), change, {"content_sha256_source": sha(before_b), "content_sha256_package": sha(after_b)}


class Tree:
    def __init__(self, out: Path) -> None:
        self.out = out
        self.manifest: list[dict[str, str]] = []
        self.log: list[dict[str, str]] = []
        self.counts: Counter[str] = Counter()

    def add_bytes(self, rel: str, data: bytes, source: str, cls: str, apply_rules: bool = True) -> None:
        src_sha = sha(data)
        change, extra = "", {}
        name = rel.rsplit("/", 1)[-1]
        if name.endswith(".html.gz"):
            data, change, extra = page(data)
        elif apply_rules and Path(name).suffix.lower() in TEXT_SUFFIX:
            new, changed = abbreviate(data)
            if changed:
                data, change = new, "abbreviated: " + "; ".join(changed)
        path = self.out / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        pkg_sha = sha(data)
        self.manifest.append({"path": rel, "class": cls, "source": source, "source_sha256": src_sha, "package_sha256": pkg_sha, "change": change})
        self.counts[cls] += 1
        if change:
            self.log.append({"path": rel, "source": source, "source_sha256": src_sha, "package_sha256": pkg_sha, "change": change, **extra})

    def add(self, src: Path, rel: str, cls: str, apply_rules: bool = True) -> None:
        self.add_bytes(rel, src.read_bytes(), str(src), cls, apply_rules)

    def tree(self, src: Path, rel: str, cls: str, skip: tuple[str, ...] = ()) -> None:
        for p in sorted(src.rglob("*")):
            if p.is_file() and not any(s in p.as_posix() for s in skip):
                self.add(p, f"{rel}/{p.relative_to(src).as_posix()}", cls)


def plan(t: Tree) -> None:
    live = "LIVE VERIFIED"
    runs: dict[str, str] = json.loads((L / "runs.json").read_text("utf-8"))
    base = "1_new_live"
    t.add(W7 / "plan" / "CAMPAIGN_BUDGET.json", f"{base}/plan/CAMPAIGN_BUDGET.json", "PLAN")
    t.add(W7 / "plan" / "TEST_PLAN_150.md", f"{base}/plan/TEST_PLAN.md", "PLAN")
    for name in ("commands.csv", "runs.json", "stage_steps.json", "00_build_edition_oxylabs.json", "00_uv_sync_frozen.txt", "61_build_edition_oxylabs_1_5_1.json", "61_build_edition_oxylabs_1_5_1.err", "62_uv_sync_frozen_1_5_1.txt"):
        t.add(L / name, f"{base}/campaign/{name}", live)
    for p in sorted(L.glob("s[0-9]_*")):
        t.add(p, f"{base}/campaign/{p.name}", live)
    t.tree(L / "logs", f"{base}/campaign/logs", live)
    t.tree(L / "compare", f"{base}/campaign/compare", live)
    t.tree(E / "campaign_summary_151", f"{base}/campaign/summary", live)
    t.tree(E / "campaign_measures_151", f"{base}/campaign/summary", live)
    t.tree(E / "campaign_db_151" / "campaign", f"{base}/campaign/db", live)
    t.add(E / "campaign_db_151" / "DB_EXPORT_COUNTS.json", f"{base}/campaign/db/DB_EXPORT_COUNTS.json", live)
    for stage, run in runs.items():
        rbase = f"{base}/runs/{run}"
        t.add_bytes(f"{rbase}/STAGE.txt", f"{stage}\n".encode(), "this assembly", live, apply_rules=False)
        src = L / "runs" / stage
        t.tree(src / "exports", f"{rbase}/exports", live)
        t.tree(src / "coverage", f"{rbase}/coverage", live)
        for p in sorted(src.glob("field_dispositions_*.csv")):
            t.add(p, f"{rbase}/{p.name}", live)
        for p in sorted(src.glob("*_CHECKS.json")):
            t.add(p, f"{rbase}/{p.name}", live)
        t.tree(E / "campaign_db_151" / "runs" / run, f"{rbase}/db", live)
        for p in sorted((DATA / run / "live" / "dom").glob("*.html.gz")):
            t.add(p, f"{rbase}/pages/{p.name}", live)
        for p in sorted((DATA / run / "live" / "robots").glob("*")):
            t.add(p, f"{rbase}/robots/{p.name}", live)
        raw = io.StringIO()
        w = csv.writer(raw, lineterminator="\n")
        w.writerow(["raw_file_on_the_workstation", "sha256", "bytes"])
        for p in sorted((DATA / run / "live" / "raw").glob("*")):
            b = p.read_bytes()
            w.writerow([f"runs/walmart-3891-pickup/{run}/live/raw/{p.name}", sha(b), len(b)])
        t.add_bytes(f"{rbase}/RAW_ORIGINALS_MANIFEST.csv", raw.getvalue().encode(), "listing of the protected originals", live, apply_rules=False)
    # 2: offline reprocessing
    off = "OFFLINE REPROCESSING"
    a3 = E / "reprocessing_b3_1_5_1"
    t.tree(a3, "2_offline_reprocessing/b3_on_1_5_1", off)
    a2 = E / "reprocessing_b3"
    for name in ("commands.csv",):
        t.add(a2 / name, f"2_offline_reprocessing/attempts/attempt2_1_5_0_7b6f325/{name}", off)
    t.tree(a2 / "reconciliation", "2_offline_reprocessing/attempts/attempt2_1_5_0_7b6f325/reconciliation", off)
    a1 = E / "reprocessing_b3_attempt1_parent_net_content"
    for name in ("commands.csv",):
        t.add(a1 / name, f"2_offline_reprocessing/attempts/attempt1_1_5_0_2489013/{name}", off)
    t.tree(a1 / "reconciliation", "2_offline_reprocessing/attempts/attempt1_1_5_0_2489013/reconciliation", off)
    t.add(W7 / "b" / "detail_capture_index_150.json", "2_offline_reprocessing/capture_index/detail_capture_index_150.json", off)
    # 3: reconciliation
    rec = "3_reconciliation"
    t.tree(E / "reconciliation_151", f"{rec}/coverage_and_queues", "RECONCILIATION")
    t.tree(E / "reconciliation_150", f"{rec}/coverage_and_queues/attempts/before_the_campaign_1_5_0", "RECONCILIATION")
    t.add(E / "vm_followup_export_2026-10-31.txt", f"{rec}/coverage_and_queues/vm_queues/vm_followup_export_2026-10-31.txt", "RECONCILIATION")
    t.add(E / "vm_followup_counts_2026-10-31.txt", f"{rec}/coverage_and_queues/vm_queues/vm_followup_counts_2026-10-31.txt", "RECONCILIATION")
    t.add(E / "vm_case_rows_2026-10-31.txt", f"{rec}/coverage_and_queues/vm_queues/vm_case_rows_2026-10-31.txt", "RECONCILIATION")
    t.tree(E / "offers_audit", f"{rec}/offers_audit_saved_pages", "OFFLINE REPROCESSING")
    t.add(E / "offers_audit_run.log", f"{rec}/offers_audit_saved_pages/offers_audit_run.log", "OFFLINE REPROCESSING")
    t.tree(E / "offers_live_final", f"{rec}/offers_live_final", "OFFLINE REPROCESSING of LIVE pages")
    t.add(E / "offers_live_final_output.txt", f"{rec}/offers_live_final/offers_live_final_output.txt", "OFFLINE REPROCESSING of LIVE pages")
    t.tree(E / "offers_live_pre_s5a", f"{rec}/offers_live_final/attempts/before_S5a", "OFFLINE REPROCESSING of LIVE pages")
    t.tree(E / "linked_examples_151", f"{rec}/linked_examples", "RECONCILIATION")
    t.tree(E / "linked_examples_151_attempt1_E027_failed", f"{rec}/linked_examples/attempts/attempt1_E027_failed", "RECONCILIATION")
    t.tree(E / "linked_examples_151_attempt2_before_bulk_note", f"{rec}/linked_examples/attempts/attempt2_before_the_bulk_note", "RECONCILIATION")
    t.tree(E / "pack_fix_151", f"{rec}/pack_fix_151", "OFFLINE REPROCESSING")
    t.tree(E / "known_limitations_151", f"{rec}/known_limitations_151", "OFFLINE")
    t.tree(E / "b3_blanks_after_campaign", f"{rec}/b3_blanks_after_campaign", "RECONCILIATION")
    t.tree(E / "cost_model_151", f"{rec}/cost_model_151", "ESTIMATE")
    t.add(W7 / "tools" / "cost_model_151.py", f"{rec}/cost_model_151/cost_model_151.py", "ESTIMATE")
    t.add(W7 / "tools" / "cost_report_151.py", f"{rec}/cost_model_151/cost_report_151.py", "ESTIMATE")
    # 4: historical references
    hist = "HISTORICAL"
    # Byte-identical copies of the 1.4.1 delivery's own files, so that their hashes still match its SHA256SUMS.txt.
    t.add(OLD / "SHA256SUMS.txt", "4_historical_references/1_4_1/SHA256SUMS.txt", hist, apply_rules=False)
    t.add(OLD / "SOURCE_AND_RUN_MANIFEST.json", "4_historical_references/1_4_1/SOURCE_AND_RUN_MANIFEST.json", hist, apply_rules=False)
    t.add(E.parent / "stage151" / "HISTORICAL_REFERENCES.csv", "4_historical_references/HISTORICAL_REFERENCES.csv", hist)
    # The 1.4.1 saved pages that linked examples name (by page_file, by page_fetch_id, or by source_path), copied with an index naming the
    # 1.4.1 evidence ZIP and member each one comes from. C:/w7/b holds those ZIPs extracted: ox/ = Oxylabs, sd/ = Scrape.do, sh/ = shared.
    zips = {"ox": "walmart_oxylabs/WALMART_OXYLABS_EVIDENCE_1.4.1.zip", "sd": "walmart_scrapedo/WALMART_SCRAPEDO_EVIDENCE_1.4.1.zip",
            "sh": f"{OLD.name}/shared/WALMART_SHARED_EVIDENCE_1.4.1.zip"}
    found: dict[str, dict[str, str]] = {}
    with open(E / "linked_examples_151" / "LINKED_EXAMPLES.csv", encoding="utf-8-sig") as f:
        examples = list(csv.DictReader(f))
    for row in examples:
        cands = [v for v in (row["page_file"], row["source_path"]) if v.split("/", 1)[0] in zips and v.endswith(".html.gz")]
        if not cands and row["page_fetch_id"] and not row["page_file"]:
            cands = sorted(p.relative_to(W7 / "b").as_posix() for p in (W7 / "b").glob(f"*/*/*/runs/*/*/pages/dom/{row['page_fetch_id']}.html.gz"))[:1]
        for rel_b in cands:
            fid = rel_b.rsplit("/", 1)[-1].removesuffix(".html.gz")
            if fid in found:
                found[fid]["examples"] += f" {row['example_id']}"
                continue
            src = W7 / "b" / rel_b
            raw_b = src.read_bytes()
            found[fid] = {"page_fetch_id": fid, "examples": row["example_id"], "evidence_zip_1_4_1": zips[rel_b.split("/", 1)[0]],
                          "member": rel_b.split("/", 1)[1], "stored_file_sha256": sha(raw_b), "page_content_sha256": sha(gzip.decompress(raw_b))}
            t.add(src, f"4_historical_references/saved_pages_of_linked_examples/{fid}.html.gz", hist)
    idx = io.StringIO()
    w = csv.DictWriter(idx, fieldnames=["page_fetch_id", "examples", "evidence_zip_1_4_1", "member", "stored_file_sha256", "page_content_sha256"], lineterminator="\n")
    w.writeheader()
    w.writerows(found.values())
    t.add_bytes("4_historical_references/saved_pages_of_linked_examples/INDEX.csv", idx.getvalue().encode(), "this assembly", hist, apply_rules=False)
    # 5: fault and publication tests
    t.tree(E / "publication_faults_151", "5_fault_and_publication_tests/publication_faults", "SYNTHETIC TEST")
    # 6: the 1.5.1 regressions run against the frozen 1.5.0 source and against 1.5.1 (offline)
    t.tree(E / "regressions_151", "6_offline_regressions/before_and_after_1_5_1", "OFFLINE VERIFIED")
    # 6: accounts and tools
    t.tree(E / "accounts", "accounts", "ACCOUNT READING")
    tools = W7 / "tools"
    for name in (
        "live150_run.py", "live150_sql.py", "live150_db.py", "kill_stage.py", "s4_kill.py", "s6_overlap_when_collecting.py", "run_at.py", "resume_after_lease.py", "s6_verify.py",
        "compare_runs_150.py", "campaign_summary_151.py", "campaign_measures_151.py", "export_campaign_db_151.py", "make_config_s2.py", "add_s6_steps.py", "add_s6_resume_steps.py", "add_s7_finalize_step.py",
        "amend_a2_steps.py", "reproc150_setup.py", "reproc150_run.py", "correction_map_151.py", "b3_blanks_after_campaign.py", "provenance_recovered_scan.py", "linked_examples_151.py", "coverage_reconcile_151.py", "sv_reconcile_151.py",
        "offers_live_151.py", "offers_audit.py", "tile_promo_full.py", "pdp_offer_wording.py", "pdp_promodata.py", "size_rule_compare_151.py", "all_titles_150.py", "read_scrapedo_info.py",
    ):
        t.add(tools / name, f"tools/{name}", "TOOL")
    t.tree(tools / "delivery151", "tools/delivery151", "TOOL", skip=("__pycache__",))
    t.tree(tools / "docs151", "tools/docs151", "TOOL", skip=("__pycache__",))
    # The workstation's PDF tools: the summary PDF's maker (Edge, headless) and the page renderer the verifier uses.
    for name in ("render_report_pdf_131.py", "pdf_pages_png.ps1"):
        t.add(Path(r"C:\w6\tools") / name, f"tools/workstation/{name}", "TOOL")
    for name in ("README.md", "SANITIZATION.md"):
        t.add(DOCS / name, name, "DOCUMENT")


def main() -> int:
    out = Path(sys.argv[1])
    if out.exists():
        raise SystemExit(f"{out} exists")
    out.mkdir(parents=True)
    t = Tree(out)
    plan(t)
    fields = ["path", "class", "source", "source_sha256", "package_sha256", "change"]
    for row in t.manifest:
        new, _ = abbreviate(row["source"].encode("utf-8"))
        row["source"] = new.decode("utf-8")
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=fields, lineterminator="\n")
    w.writeheader()
    w.writerows(t.manifest)
    (out / "EVIDENCE_MANIFEST.csv").write_bytes(buf.getvalue().encode("utf-8"))
    buf = io.StringIO()
    lf = ["path", "source", "source_sha256", "package_sha256", "change", "content_sha256_source", "content_sha256_package"]
    w = csv.DictWriter(buf, fieldnames=lf, lineterminator="\n", restval="")
    w.writeheader()
    for row in t.log:
        row["source"] = abbreviate(row["source"].encode("utf-8"))[0].decode("utf-8")
    w.writerows(t.log)
    (out / "SANITIZATION_LOG.csv").write_bytes(buf.getvalue().encode("utf-8"))
    # Check.
    problems = []
    listed = {r["path"] for r in t.manifest}
    present = {p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()} - {"EVIDENCE_MANIFEST.csv", "SANITIZATION_LOG.csv", "ASSEMBLY_CHECK.txt"}
    if listed != present:
        problems.append(f"manifest and tree differ: {sorted(listed ^ present)[:5]}")
    for r in t.manifest:
        if sha((out / r["path"]).read_bytes()) != r["package_sha256"]:
            problems.append(f"hash differs: {r['path']}")
    raw_named = [p for p in present if "/live/raw/" in p or p.endswith(".body.gz")]
    if raw_named:
        problems.append(f"raw originals in the package: {raw_named[:3]}")
    runs = json.loads((L / "runs.json").read_text("utf-8"))
    pages_expected, pages_found = 0, 0
    for run in runs.values():
        pages_expected += len(list((DATA / run / "live" / "dom").glob("*.html.gz")))
        pages_found += sum(1 for p in present if p.startswith(f"1_new_live/runs/{run}/pages/"))
    if pages_expected != pages_found:
        problems.append(f"pages {pages_found} of {pages_expected}")
    lines = [
        "ASSEMBLY CHECK of the Walmart 1.5.1 evidence tree (offline; no request)",
        f"files listed: {len(listed)}",
        f"by class: {json.dumps(dict(sorted(t.counts.items())))}",
        f"files changed when packaged: {len(t.log)}",
        f"stored pages of the {len(runs)} campaign runs: {pages_found} of {pages_expected}",
        f"raw originals in the package: {len(raw_named)}",
        f"RESULT: {'PASS' if not problems else 'FAIL ' + '; '.join(problems)}",
    ]
    (out / "ASSEMBLY_CHECK.txt").write_bytes(("\n".join(lines) + "\n").encode("utf-8"))
    print("\n".join(lines))
    return 0 if not problems else 1


if __name__ == "__main__":
    raise SystemExit(main())
