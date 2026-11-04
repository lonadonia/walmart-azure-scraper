"""Writes probe_results_170.py from the 1.5.1 tool (probe_results_151.py, published under evidence/tools/1.5.1): the
1.7.0 probe's rate card moved to tests/conftest.py, the replay names its retailer, and a Mariano's replay (real saved
pages in invented Classic envelopes, tests/test_marianos.py) is added. Run once."""

from pathlib import Path

SRC = Path(r"C:\w8\repo\evidence\tools\1.5.1\delivery151\probe_results_151.py")
DST = Path(r"C:\w9\live\tools\probe_results_170.py")
s = SRC.read_text(encoding="utf-8")

MARIANOS_WRITER = '''MARIANOS_WRITER = r"""
import json, sys
from pathlib import Path
sys.path.insert(0, ".")
from tests import test_marianos as tm
out = Path(sys.argv[1])
fixtures = out / "fixtures"
fixtures.mkdir(parents=True)
spec = {"steps": {}}
for step, answers in tm.complete().items():
    spec["steps"][step] = []
    for i, (status, body) in enumerate(answers):
        (fixtures / f"{step}-{i}.json").write_bytes(body)
        spec["steps"][step].append({"http_status": status, "body_file": f"{step}-{i}.json"})
(fixtures / "replay.json").write_text(json.dumps(spec, indent=1), "utf-8")
(out / "synthetic_rates.json").write_text(json.dumps(tm.RATES, indent=1), "utf-8")  # tests/test_marianos.py: invented, with Mariano's rates
print(len(spec["steps"]), "steps")
"""
'''

reps = [
    (
        '"""The Classic probe\'s offline run for the delivery:',
        '"""The Classic probe\'s offline run for the delivery (probe 1.7.0; adapted from probe_results_151.py):',
    ),
    ('REPO = Path(r"C:\\w7\\wt")', 'REPO = Path(r"C:\\w9\\wt")'),
    ('UV = r"<home>\\.local\\bin\\uv.exe"', 'UV = str(Path.home() / ".local" / "bin" / "uv.exe")'),
    ("from tests.test_offline import SYNTHETIC_RATES", "from tests.conftest import SYNTHETIC_RATES"),
    ('print(len(spec["steps"]), "steps")\n"""\n', 'print(len(spec["steps"]), "steps")\n"""\n' + MARIANOS_WRITER),
    (
        '    run("11_replay_synthetic_responses", [*cli, "replay", "--targets",',
        '    run("11_replay_synthetic_responses", [*cli, "replay", "--retailer", "walmart", "--targets",',
    ),
    (
        '    run("12_campaign_init_offline",',
        '    (root / "write_marianos_fixtures.py").write_text(MARIANOS_WRITER, encoding="utf-8")\n'
        '    run("11b_write_marianos_fixtures", [py, "write_marianos_fixtures.py", "offline_out/marianos_inputs"])\n'
        '    run("11c_replay_marianos_saved_pages", [*cli, "replay", "--retailer", "marianos", "--targets", '
        '"config/targets.json", "--fixtures", "offline_out/marianos_inputs/fixtures", "--rates", '
        '"offline_out/marianos_inputs/synthetic_rates.json", "--out", "offline_out/replay_marianos"])\n'
        '    run("12_campaign_init_offline",',
    ),
    ('    for name in ("replay", "export"):', '    for name in ("replay", "replay_marianos", "export"):'),
    (
        '    shutil.copytree(scratch / "synthetic", out / "synthetic_inputs_of_the_replay")\n',
        '    shutil.copytree(scratch / "synthetic", out / "synthetic_inputs_of_the_replay")\n'
        '    shutil.copytree(scratch / "marianos_inputs", out / "inputs_of_the_marianos_replay")\n'
        '    (out / "inputs_of_the_marianos_replay" / "README.txt").write_bytes(b"OFFLINE REPLAY inputs: real '
        "Mariano's pages (Vernon Hills, Pickup) that the Mariano's collector saved through the Oxylabs Web API on "
        "2026-11-02, each wrapped in an invented Classic envelope by tests/test_marianos.py, and an invented rate "
        'card. The pages are real; the Classic envelopes and the rates are not.\\n")\n',
    ),
    (
        "One test is skipped: it needs the collector beside the probe (README_FIRST.md).\",",
        "Skipped tests say why (-rs): see README_FIRST.md.\",",
    ),
    (
        "It shows the ledger and the stops work; it shows nothing about Classic.\",\n",
        "It shows the ledger and the stops work; it shows nothing about Classic.\",\n"
        "        \"11b, 11c, replay_marianos/, inputs_of_the_marianos_replay/   the Mariano's steps replayed against "
        "real saved Mariano's pages in invented Classic envelopes, with an invented rate card (OFFLINE REPLAY). It "
        "shows nothing about Classic.\",\n",
    ),
]
for a, b in reps:
    assert s.count(a) == 1, a[:90]
    s = s.replace(a, b)
DST.write_bytes(s.encode("utf-8"))
print("written", DST)
