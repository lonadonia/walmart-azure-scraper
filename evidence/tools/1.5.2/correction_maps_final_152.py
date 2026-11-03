"""The correction maps of the final revision: every run with exports, from run A1 of the final replay, and B3's two.
A new folder: an earlier one is never replaced."""

import json
import subprocess
from pathlib import Path

PY = r"C:\w7\wt\headless\walmart-azure-headless\.venv\Scripts\python.exe"
RUNS = json.loads(Path(r"C:\w7\evidence\live150\runs.json").read_text("utf-8"))
RP = json.loads(Path(r"C:\w7\ev152\final_a1\replay_runs.json").read_text("utf-8"))
OUT = Path(r"C:\w7\ev152\correction_maps_final")
MAP = r"C:\w7\tools\correction_map_152.py"
for st in ("S1", "S2", "S3", "S4", "S5a", "S5b_parallel", "S5b_serial", "S6", "S7"):
    before = Path(rf"C:\w7\evidence\live150\runs\{st}\exports")
    after = Path(rf"C:\w7\ev152\final_a1\runs\{st}\exports")
    if not (before / "products.json").exists() or not (after / "products.json").exists():
        print(st, "no exports:", (before / "products.json").exists(), (after / "products.json").exists())
        continue
    r = subprocess.run(
        [PY, "-I", "-X", "utf8", MAP, str(before), str(after), st, RUNS[st], RP[st], str(OUT)],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if r.returncode:
        print(st, "FAILED", r.stderr[-600:])
        continue
    s = json.loads((OUT / f"{st}_CORRECTION_SUMMARY.json").read_text("utf-8"))
    print(
        st,
        "before",
        s["products_before"],
        "after",
        s["products_after"],
        "only_before",
        len(s["only_before"]),
        "only_after",
        len(s["only_after"]),
        "rows",
        s["rows"],
        "values",
        s["exported_values_changed_by_field"],
    )
b3 = "01M60V2DCCWR72BGVVG3EM9R74"
rp = Path(r"C:\w7\ev152\final_b3\replay_run_id.txt").read_text("utf-8").strip()
r = subprocess.run(
    [
        PY,
        "-I",
        "-X",
        "utf8",
        MAP,
        r"C:\w7\evidence\reprocessing_b3_1_5_1\export_replay_1_5_1",
        r"C:\w7\ev152\final_b3\export_replay_1_5_2",
        "B3_1_5_1_TO_1_5_2",
        b3,
        rp,
        str(OUT),
    ],
    capture_output=True,
    text=True,
    encoding="utf-8",
)
print("B3 1.5.1 to 1.5.2", r.returncode, r.stdout[-900:], r.stderr[-600:])
r = subprocess.run(
    [PY, "-I", "-X", "utf8", r"C:\w7\tools\correction_map_b3_152.py", str(OUT / "b3_1_4_1_to_1_5_2")],
    capture_output=True,
    text=True,
    encoding="utf-8",
)
print("B3 1.4.1 to 1.5.2", r.returncode, r.stdout[-1500:], r.stderr[-600:])
