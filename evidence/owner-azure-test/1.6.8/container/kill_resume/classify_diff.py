"""Classifies a normal-format `diff A B` output: a changed line pair whose two sides are equal once ULIDs and ISO
timestamps are masked is an identifier/time difference; anything else (another change, or a line added or deleted) is
printed with its line numbers. Usage: python -I -X utf8 classify_diff.py DIFF_FILE"""

import re
import sys
from collections import Counter

ULID = re.compile(r"\b[0-9A-HJKMNP-TV-Z]{26}\b")
TS = re.compile(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?Z?")
HEAD = re.compile(r"^(\d+)(?:,(\d+))?([acd])(\d+)(?:,(\d+))?$")


def mask(s: str) -> str:
    return TS.sub("<TS>", ULID.sub("<ULID>", s))


def main(path: str) -> None:
    kinds: Counter[str] = Counter()
    other: list[str] = []
    old: list[str] = []
    new: list[str] = []
    head = ""

    def flush() -> None:
        if not head:
            return
        m = HEAD.match(head)
        assert m, head
        op = m.group(3)
        if op == "c" and len(old) == len(new) and all(mask(a) == mask(b) for a, b in zip(old, new)):
            for a, b in zip(old, new):
                key = re.sub(r'^\s*"([^"]+)".*$', r"\1", a) if a.strip().startswith('"') else "(value line)"
                kinds[key] += 1
            return
        kinds["OTHER:" + op] += 1
        if len(other) < 60:
            other.append(head + "\n" + "\n".join("< " + x[:200] for x in old[:12]) + "\n" + "\n".join("> " + x[:200] for x in new[:12]))

    with open(path, encoding="utf-8", errors="strict") as fh:
        for raw in fh:
            line = raw.rstrip("\n")
            if HEAD.match(line):
                flush()
                head, old, new = line, [], []
            elif line.startswith("< "):
                old.append(line[2:])
            elif line.startswith("> "):
                new.append(line[2:])
            elif line == "---":
                pass
            else:
                raise SystemExit(f"unexpected diff line: {line[:120]!r}")
        flush()
    for k, v in kinds.most_common():
        print(f"{v:>8}  {k}")
    print("--- changes that are not identifier/time substitutions:", sum(v for k, v in kinds.items() if k.startswith("OTHER")))
    for o in other:
        print(o)
        print("....")


if __name__ == "__main__":
    main(sys.argv[1])
