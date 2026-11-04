"""Generalizes w3_decisions.py (written for the 1.6.0 runs) to the delivery's runs on 1.6.0 and 1.6.1: each decision
names the release of the run that made it (L1 and L2 ran 1.6.0; L2b and later 1.6.1), the columns say "this delivery"
and the files are named for the delivery's release, 1.6.1. Run once."""

from pathlib import Path

P = Path(r"C:\w9\live\stepdefs\w3_decisions.py")
s = P.read_text(encoding="utf-8")
if "RELEASE_OF" in s:
    raise SystemExit("already patched")
reps = [
    ("outcomes of the 1.6.0 runs that read them", "outcomes of this delivery's runs that read them (1.6.0 and 1.6.1)"),
    ("A product no 1.6.0 run read keeps", "A product no run of this delivery read keeps"),
    ("# Every follow-up outcome of the 1.6.0 runs, by item", "# Every follow-up outcome of this delivery's runs, by item"),
    (
        '        decision, cls = "not read by a 1.6.0 run", "NOT TESTED (1.6.0)"\n'
        '        limitation = "its own page was not requested in 1.6.0: the 1.5.2 state stands"\n',
        '        decision, cls = "not read by a run of this delivery", "NOT TESTED (1.6.0, 1.6.1)"\n'
        '        limitation = "its own page was not requested by this delivery: the 1.5.2 state stands"\n',
    ),
    (
        '        decision, cls, limitation = final["status"], "LIVE VERIFIED (1.6.0)", ""\n',
        '        decision, cls, limitation = final["status"], f"LIVE VERIFIED ({RELEASE_OF(final)})", ""\n',
    ),
    (
        '        decision, cls = f"unresolved: {final[\'status\']}", "LIVE ATTEMPTED (1.6.0), UNRESOLVED"\n',
        '        decision, cls = f"unresolved: {final[\'status\']}", f"LIVE ATTEMPTED ({RELEASE_OF(final)}), UNRESOLVED"\n',
    ),
    ("rows_out = []\n", "rows_out = []\n\n\ndef RELEASE_OF(o: dict) -> str:  # noqa: N802\n"
     '    return "1.6.0" if o.get("run_label") in ("L1", "L2") else "1.6.1"\n\n\n'),
]
for a, b in reps:
    assert s.count(a) == 1, a[:80]
    s = s.replace(a, b)
for a, b in [
    ("decision_1_6_0", "decision_this_delivery"),
    ("all_1_6_0_outcomes", "all_outcomes_this_delivery"),
    ("W3_DECISIONS_1_6_0", "W3_DECISIONS_1_6_1"),
    ("W3_CLIENT_CASES_1_6_0", "W3_CLIENT_CASES_1_6_1"),
    ("W3_SUMMARY_1_6_0", "W3_SUMMARY_1_6_1"),
]:
    s = s.replace(a, b)
assert "1_6_0" not in s and "1.6.0 run" not in s, [ln for ln in s.splitlines() if "1_6_0" in ln or "1.6.0 run" in ln]
P.write_bytes(s.encode("utf-8"))
print("patched")
