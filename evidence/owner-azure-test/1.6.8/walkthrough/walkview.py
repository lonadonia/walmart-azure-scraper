"""For the recorded walkthrough: shows what a collector command returned, from its JSON log lines on stdin. It prints
the RESULT line's exit code and command, then each field named (a dotted path into the result); a CSV-row list
(csv_rows) is shown as a table, one line per row. Lines that are not JSON (such as --version's) are printed as they
are. Nothing is changed or left out silently: a field the result does not have is shown as null.

usage: <collector command> | python3 walkview.py [FIELD ...]
"""

from __future__ import annotations

import json
import sys


def get(v: object, path: str) -> object:
    for part in path.split("."):
        if isinstance(v, dict):
            v = v.get(part)
        elif isinstance(v, list) and part.isdigit() and int(part) < len(v):
            v = v[int(part)]
        else:
            return None
    return v


def main() -> int:
    result = None
    for line in sys.stdin:
        line = line.rstrip("\n")
        if not line.lstrip().startswith("{"):
            if line.strip():
                print(line)
            continue
        try:
            d = json.loads(line)
        except ValueError:
            print(line[:200])
            continue
        if d.get("event") == "RESULT":
            result = d
    if result is None:
        print("(no RESULT line)")
        return 1
    print(f"exit_code {result.get('exit_code')} | command {result.get('command')}")
    for key in sys.argv[1:]:
        v = get(result.get("result"), key)
        if key.endswith("csv_rows") and isinstance(v, list):
            print(f"{key}: {len(v)} CSV rows")
            for r in v:
                why = str(r.get("why_not_complete") or "")
                print(f"  row {r.get('csv_row'):>2} {str(r.get('category'))[:22]:<22} listings {r.get('listings', 0):>4} "
                      f"complete {str(r.get('complete')):<5} {why[:52]}")
            continue
        text = json.dumps(v, ensure_ascii=False)
        print(f"{key}: {text if len(text) <= 300 else text[:300] + ' ...'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
