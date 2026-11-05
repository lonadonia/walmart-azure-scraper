"""Writes assemble_campaign_166.py and assemble_data_166.py from their 1.6.5 versions: the harness backup before the
1.6.6 patch, the 1.6.6 edition ZIP, and the summary's wording for the final release 1.6.6. Run once."""

from pathlib import Path

T = Path(r"C:\w9\live\tools")


def make(src: str, dst: str, reps: list[tuple[str, str]]) -> None:
    s = (T / src).read_text(encoding="utf-8")
    for a, b in reps:
        assert s.count(a) == 1, (src, a[:80], s.count(a))
        s = s.replace(a, b)
    (T / dst).write_bytes(s.encode("utf-8"))
    print("written", dst)


make("assemble_campaign_165.py", "assemble_campaign_166.py", [
    ("usage: python -I assemble_campaign_165.py OUT_DIR   (the harness backups before each patch, 1.6.1 to 1.6.5, and the",
     "usage: python -I assemble_campaign_166.py OUT_DIR   (the harness backups before each patch, 1.6.1 to 1.6.6, and the"),
    ('"live160_run.before_163.REBUILT.txt", "live160_run.before_164.py", "live160_run.before_165.py"):',
     '"live160_run.before_163.REBUILT.txt", "live160_run.before_164.py", "live160_run.before_165.py",\n'
     '                 "live160_run.before_166.py"):'),
])
make("assemble_data_165.py", "assemble_data_166.py", [
    ('"""Write the data/ folder of the 1.6.5 publication (assemble_data_164.py with the 1.6.5 edition ZIP)',
     '"""Write the data/ folder of the 1.6.6 publication (assemble_data_165.py with the 1.6.6 edition ZIP)'),
    ("usage: python -I assemble_data_165.py PUB_ROOT", "usage: python -I assemble_data_166.py PUB_ROOT"),
    ('    "1.6.5": "edd60bb8435e7abd8293d7c2b5b76eaaaff0051d18c053d715afc2533070ba6b",\n}',
     '    "1.6.5": "edd60bb8435e7abd8293d7c2b5b76eaaaff0051d18c053d715afc2533070ba6b",\n'
     '    "1.6.6": "0859a2f693527bab073252edf941928bb4f118ea4a63d581078d96ddd2324e22",\n}'),
    ('"(2026-11-03/04; releases 1.6.0 to 1.6.4 and the final 1.6.5): each entry',
     '"(2026-11-03/04; releases 1.6.0 to 1.6.5 and the final 1.6.6): each entry'),
])
