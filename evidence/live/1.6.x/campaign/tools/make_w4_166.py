"""Writes w4_coverage_166.py from w4_coverage_165.py: the 1.6.6 file names and state column, and the docstring's
account of the runs (L12 added, on release 1.6.6). Run once."""

from pathlib import Path

T = Path(r"C:\w9\live\tools")
s = (T / "w4_coverage_165.py").read_text(encoding="utf-8")
old_doc = (
    "Release 1.6.5 of this tool (from w4_coverage_164.py): today's census is two runs, L7 (rows 0 and 1, stopped on\n"
    "1.6.3) and L10 (Bidets of row 1, rows 2 to 10, on 1.6.4). Each run marked \"=census\" names the listings of its\n"
    "rows; for a listing two census runs name, the later one given counts. The census column is census_<labels>.\n"
)
new_doc = old_doc + (
    "\nRelease 1.6.6 of this tool (from w4_coverage_165.py): only the file names and the state column (1_6_6); the\n"
    "runs are those of 1.6.5 plus L12 (one page of Fabric Softeners, on 1.6.6), which is not a census run.\n"
)
assert s.count(old_doc) == 1
s = s.replace(old_doc, new_doc)
n = s.count("1_6_5")
assert n == 14, n
s = s.replace("1_6_5", "1_6_6")
s = s.replace("usage: python -I w4_coverage_165.py", "usage: python -I w4_coverage_166.py")
assert "w4_coverage_165.py OUT_DIR" not in s
(T / "w4_coverage_166.py").write_bytes(s.encode("utf-8"))
print("written w4_coverage_166.py;", n, "names changed")
