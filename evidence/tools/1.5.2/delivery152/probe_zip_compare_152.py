"""The Classic probe ZIP tested on the owner VM against the delivered one, member by member (offline).

The ZIP built at 2026-11-01T19:52Z (SHA-256 20de284c...) was tested on the VM. On 2026-11-02 the verifier's personal-data
check found the workstation's host name in its offline_results/junit_standalone.xml (pytest's "hostname" attribute),
which 1.5.1's probe ZIP had replaced with "(workstation)". The ZIP was rebuilt from the same revision with that one
attribute replaced. This lists every member of both, its SHA-256, and what differs.

usage: python -I -X utf8 probe_zip_compare_152.py TESTED.zip DELIVERED.zip OUT.json
"""

import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path


def members(path: Path) -> dict[str, bytes]:
    with zipfile.ZipFile(path) as z:
        return {i.filename: z.read(i) for i in z.infolist() if not i.is_dir()}


a, b, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
ma, mb = members(a), members(b)
names = sorted(set(ma) | set(mb))
differ = [n for n in names if ma.get(n) != mb.get(n)]
detail = {}
for n in differ:
    x, y = ma.get(n), mb.get(n)
    if x is None or y is None:
        detail[n] = "present in one ZIP only"
        continue
    blank = (lambda t: re.sub(rb'hostname="[^"]*"', b'hostname=""', t))
    detail[n] = ("the same once the hostname attribute is set aside" if blank(x) == blank(y)
                 else "differs beyond the hostname attribute")
report = {
    "tested_on_the_vm": {"zip": a.name, "sha256": hashlib.sha256(a.read_bytes()).hexdigest(), "members": len(ma)},
    "delivered": {"zip": b.name, "sha256": hashlib.sha256(b.read_bytes()).hexdigest(), "members": len(mb)},
    "members_identical": len(names) - len(differ),
    "members_differing": {n: {"tested_sha256": hashlib.sha256(ma[n]).hexdigest() if n in ma else None,
                              "delivered_sha256": hashlib.sha256(mb[n]).hexdigest() if n in mb else None,
                              "difference": detail[n]} for n in differ},
}
out.write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8", newline="\n")
print(json.dumps(report, indent=1))
