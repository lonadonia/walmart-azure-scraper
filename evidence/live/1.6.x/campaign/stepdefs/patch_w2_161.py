"""Generalizes w2_corrections.py (written for the 1.6.0 export) to the newest export of the delivery, release 1.6.1:
the columns and files are named for the export's own release (read from its manifest), and every run of this
delivery is named with the release it ran (runs.json: L1 and L2 on 1.6.0; L3 and later on 1.6.1). Run once."""

from pathlib import Path

P = Path(r"C:\w9\live\stepdefs\w2_corrections.py")
s = P.read_text(encoding="utf-8")
if "DELIVERY_RUNS" in s:
    raise SystemExit("already patched")
reps = [
    (
        'RUNS_160 = {"01M6H5TX7R4ZWV8W3NTH0QN6HF", "01M6H72J86K5TF7A1874N7BJ2R"}  # L1, L2 (1.6.0)\n',
        "# Every run of this delivery and the release it ran (runs.json; the stages before L3 ran 1.6.0).\n"
        'RUNS_JSON = Path(r"C:\\w9\\evidence\\live160\\runs.json")\n'
        "DELIVERY_RUNS = {\n"
        "    run: (\"1.6.0\" if stage in (\"L1\", \"L2\") else \"1.6.1\")\n"
        "    for stage, run in json.loads(RUNS_JSON.read_text(encoding=\"utf-8\")).items()\n"
        "    if stage in (\"L1\", \"L2\", \"L3\", \"L2b\", \"L4r\", \"L4\", \"L5\")\n"
        "}\n",
    ),
    (
        '    new_run = json.loads((new_dir / "manifest.json").read_text("utf-8"))["run_id"]\n',
        '    manifest = json.loads((new_dir / "manifest.json").read_text("utf-8"))\n'
        '    new_run = manifest["run_id"]\n'
        "    rel = DELIVERY_RUNS[new_run]  # the release of the export compared with 1.5.2\n"
        '    tag = rel.replace(".", "_")\n',
    ),
    ('        "value_1_6_0", "outcome_1_6_0", "reason_1_6_0", "observation_1_6_0", "change", "source_path",\n',
     '        f"value_{tag}", f"outcome_{tag}", f"reason_{tag}", f"observation_{tag}", "change", "source_path",\n'),
    ('                change = "not in the 1.6.0 export"\n', '                change = f"not in the {rel} export"\n'),
    ('                cls = "HISTORICAL (1.5.1 live, not in the 1.6.0 export)"\n',
     '                cls = f"HISTORICAL (1.5.1 live, not in the {rel} export)"\n'),
    ('            elif n_out == "fetched_detail" and src_run in RUNS_160:\n'
     '                cls = "LIVE VERIFIED (1.6.0): the product\'s own page, read by this delivery"\n'
     '            elif n_out == "present_in_listing" and src_run in RUNS_160:\n'
     '                cls = "LIVE VERIFIED (1.6.0): the listing tile, read by this delivery"\n',
     '            elif n_out == "fetched_detail" and src_run in DELIVERY_RUNS:\n'
     '                cls = f"LIVE VERIFIED ({DELIVERY_RUNS[src_run]}): the product\'s own page, read by this delivery"\n'
     '            elif n_out == "present_in_listing" and src_run in DELIVERY_RUNS:\n'
     '                cls = f"LIVE VERIFIED ({DELIVERY_RUNS[src_run]}): the listing tile, read by this delivery"\n'),
    ('                    "value_1_6_0": nv if new is not None else "",\n'
     '                    "outcome_1_6_0": n_out,\n'
     '                    "reason_1_6_0": nf.get("reason", "") or "; ".join(nf.get("conflicts", []) or []),\n'
     '                    "observation_1_6_0": nd.get("observation_kind", ""),\n',
     '                    f"value_{tag}": nv if new is not None else "",\n'
     '                    f"outcome_{tag}": n_out,\n'
     '                    f"reason_{tag}": nf.get("reason", "") or "; ".join(nf.get("conflicts", []) or []),\n'
     '                    f"observation_{tag}": nd.get("observation_kind", ""),\n'),
]
for a, b in reps:
    assert s.count(a) == 1, a[:80]
    s = s.replace(a, b)
# The rest of the file: the output names, the summary's keys and texts.
for a, b in [
    ('"W2_FIELD_CORRECTIONS_1_6_0.csv"', 'f"W2_FIELD_CORRECTIONS_{tag}.csv"'),
    ('"W2_SUMMARY_1_6_0.json"', 'f"W2_SUMMARY_{tag}.json"'),
    ('f"the 1.6.0 export of run {new_run}', 'f"the {rel} export of run {new_run}'),
    ('"s6_fresh_filled_1_6_0"', 'f"s6_fresh_filled_{tag}"'),
    ('r["value_1_6_0"]', 'r[f"value_{tag}"]'),
    ('"outcome_1_6_0_by_field"', 'f"outcome_{tag}_by_field"'),
    ('r["outcome_1_6_0"]', 'r[f"outcome_{tag}"]'),
    ("r['outcome_1_6_0']", 'r[f"outcome_{tag}"]'),
    ('"Computed from W2_FIELD_CORRECTIONS_1_6_0.csv.', 'f"Computed from W2_FIELD_CORRECTIONS_{tag}.csv.'),
    (
        '        "rows_with_a_page_of_this_delivery": sum(1 for r in rows if r["source_run"] == new_run and '
        'r["page_fetch_id"]),\n',
        '        "rows_with_a_page_of_the_compared_run": sum(1 for r in rows if r["source_run"] == new_run and '
        'r["page_fetch_id"]),\n'
        '        "rows_with_a_page_of_this_delivery": sum(\n'
        '            1 for r in rows if r["source_run"] in DELIVERY_RUNS and r["page_fetch_id"]\n'
        "        ),\n",
    ),
    (
        "delivery (data/S6-1.5.1/products_retained.csv: S6's export, 706 rows, of which 580 fresh) to the newest 1.6.0\n"
        "export (offline; no request).",
        "delivery (data/S6-1.5.1/products_retained.csv: S6's export, 706 rows, of which 580 fresh) to the newest export\n"
        "of this delivery (offline; no request). The columns and files are named for that export's release (1.6.0 or\n"
        "1.6.1, from runs.json); each run of this delivery is named with the release it ran.",
    ),
]:
    if a in s:
        s = s.replace(a, b)
assert "1_6_0" not in s.split('"""', 2)[2], [line for line in s.splitlines() if "1_6_0" in line]
P.write_bytes(s.encode("utf-8"))
print("patched")
