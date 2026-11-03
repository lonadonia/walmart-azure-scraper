"""The title size rule of the frozen 1.5.0 edition against the fixed rule, on every distinct authentic title of the stored
result pages (C:/w7/evidence/pack_fix_151/all_titles.json, written by all_titles_150.py). No request.
Two steps, each in its own interpreter so that only one walmart_headless is loaded:
  <edition venv python> -I -X utf8 size_rule_compare_151.py dump OLD.json                 (the edition's installed code)
  <edition venv python> -I -X utf8 size_rule_compare_151.py dump NEW.json C:/w7/wt/.../src (the worktree's code)
  <any python> -I -X utf8 size_rule_compare_151.py diff OLD.json NEW.json OUT.csv
"""

import csv
import json
import sys
from pathlib import Path

ALL = Path(r"C:\w7\evidence\pack_fix_151\all_titles.json")


def dump(out: str, src: str | None) -> None:
    if src:
        sys.path.insert(0, src)
    import walmart_headless
    from walmart_headless.sites.walmart import records as wrec

    titles = json.loads(ALL.read_text(encoding="utf-8"))["titles"]
    res = {}
    for t in titles:
        ev = wrec.size_from_title(t)
        res[t] = [ev.value, ev.outcome, list(ev.candidates)]
    Path(out).write_text(json.dumps({"module": str(Path(wrec.__file__)), "version": walmart_headless.__version__,
                                     "sizes": res}, ensure_ascii=False, indent=0), encoding="utf-8")
    print(wrec.__file__, walmart_headless.__version__, len(res))


def diff(old_p: str, new_p: str, out: str) -> None:
    old = json.loads(Path(old_p).read_text(encoding="utf-8"))
    new = json.loads(Path(new_p).read_text(encoding="utf-8"))
    titles = json.loads(ALL.read_text(encoding="utf-8"))["titles"]
    assert set(old["sizes"]) == set(new["sizes"])
    rows = []
    for t, a in old["sizes"].items():
        b = new["sizes"][t]
        if a != b:
            rows.append({"product_title": t, "weight_before": a[0], "rule_before": a[1], "weight_after": b[0],
                         "rule_after": b[1], "candidates_after": " | ".join(b[2]),
                         "seen_in": " + ".join(titles[t]["sources"]), "item_ids": " ".join(titles[t]["items"]),
                         "first_seen_run": titles[t]["first"][1], "first_seen_page_fetch": titles[t]["first"][2]})
    rows.sort(key=lambda r: r["product_title"])
    with open(out, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\r\n")
        w.writeheader()
        w.writerows(rows)
    print(json.dumps({"old": old["module"], "old_version": old["version"], "new": new["module"],
                      "new_version": new["version"], "titles": len(old["sizes"]), "changed": len(rows),
                      "unchanged": len(old["sizes"]) - len(rows), "output": out}, indent=1))
    for r in rows:
        print(repr(r["weight_before"]), "->", repr(r["weight_after"]), f"[{r['rule_before']} -> {r['rule_after']}]",
              "|", r["product_title"][:95], "|", r["seen_in"])


if __name__ == "__main__":
    if sys.argv[1] == "dump":
        dump(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
    else:
        diff(sys.argv[2], sys.argv[3], sys.argv[4])
