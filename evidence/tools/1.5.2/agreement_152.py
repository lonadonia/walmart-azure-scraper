"""An independent check that provenance.json, record_map.json and field_dispositions.json of one export agree, and that
what they name exists in the store. Reads only.

usage: <venv python> -I -X utf8 agreement_152.py EXPORTS PGDATA DB OUT.json DATA_DIR
"""

from __future__ import annotations

import collections
import gzip
import hashlib
import json
import sys
from pathlib import Path

import pgserver
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

x, pgdata, db, out, data_dir = Path(sys.argv[1]), sys.argv[2], sys.argv[3], Path(sys.argv[4]), Path(sys.argv[5])
INDEX = json.loads(Path("C:/w7/b/detail_capture_index_150.json").read_text("utf-8"))
INDEX_ROWS = INDEX if isinstance(INDEX, list) else INDEX.get("captures") or INDEX.get("rows") or list(INDEX.values())
imported_runs = {str(r.get("run_id") or r.get("source_run")) for r in INDEX_ROWS if isinstance(r, dict)}
imported = {str(r["page_fetch_id"]): r for r in INDEX_ROWS}
prod = json.loads((x / "products.json").read_text("utf-8"))
rows = prod["products"] if isinstance(prod, dict) else prod
prov = json.loads((x / "provenance.json").read_text("utf-8"))["records"]
rm = json.loads((x / "record_map.json").read_text("utf-8"))
disp = {r["key"]: r for r in json.loads((x / "field_dispositions.json").read_text("utf-8"))}
maps = {r["key"]: r for r in rm["rows"]}
srv = pgserver.get_server(pgdata, cleanup_mode=None)
url = make_url(srv.get_uri()).set(drivername="postgresql+psycopg", database=db)
with create_engine(url).connect() as c:
    runs = {
        r: (m, (s or {}).get("replay", {}).get("source_run"), st)
        for r, m, s, st in c.execute(text("select id, mode, config_snapshot, started_at from runs")).all()
    }
    fetches = {
        i: (r, p, sa, u)
        for i, r, p, sa, u in c.execute(text("select id, run_id, purpose, started_at, url from page_fetches")).all()
    }
    same_page = collections.defaultdict(list)
    for i, v in fetches.items():
        same_page[(v[0], v[3], v[1])].append(i)
    hashes = collections.defaultdict(set)
    dom_key = {}
    for i, h, k in c.execute(
        text(
            "select p.id, a.sha256, a.key from page_fetches p join artifacts a on a.id = p.dom_artifact_id"
        )
    ).all():
        hashes[i].add(h)
        dom_key[i] = k


raw_memo: dict[str, set[str]] = {}


def raw_hash(fid: str) -> set[str]:
    """The SHA-256 of the raw provider response of a fetch, read from its stored file. A replay's read has no raw file:
    the raw response is the source run's, of the same page."""
    if fid in raw_memo:
        return raw_memo[fid]
    found: set[str] = set()
    owner, purpose, _, url_ = fetches[fid]
    source = runs.get(owner, ("", None))[1]
    for one in same_page.get((source, url_, purpose), []) if source else [fid]:
        key = dom_key.get(one)
        if key and "/live/" in key:
            folder = data_dir / key.split("/live/")[0] / "live" / "raw"
            for f in folder.glob(f"{one}.*.body.gz"):
                found.add(hashlib.sha256(gzip.decompress(f.read_bytes())).hexdigest())
    raw_memo[fid] = found
    return found

problems: collections.Counter[str] = collections.Counter()
examples: dict[str, list] = collections.defaultdict(list)
combos: collections.Counter[tuple] = collections.Counter()


def bad(code: str, key: str, detail: object) -> None:
    problems[code] += 1
    if len(examples[code]) < 5:
        examples[code].append((key, detail))


this_run = rm["run_id"]
for key, m in maps.items():
    d, p = disp.get(key), prov.get(key)
    if d is None or p is None:
        bad("row_missing_in_a_file", key, (d is None, p is None))
        continue
    if m.get("observation_kind") != d.get("observation_kind") or m.get("observation_kind") != p.get("observation_kind"):
        bad("observation_kind_differs", key, (m.get("observation_kind"), d.get("observation_kind"), p.get("observation_kind")))
    obs_run = m.get("observed_by_run")
    if obs_run and obs_run in runs and runs[obs_run][0] == "REPLAY":
        bad("row_observed_by_a_replay", key, (m.get("observation_kind"), obs_run))
    for f in ("upc", "weight"):
        a = d.get(f) or {}
        b = m.get("dispositions", {}).get(f) or {}
        if a != b:
            bad(f"{f}: map and dispositions differ", key, {k: (a.get(k), b.get(k)) for k in set(a) | set(b) if a.get(k) != b.get(k)})
        src = (p.get("fields") or {}).get(f) or {}
        msrc = (m.get("fields") or {}).get(f) or {}
        if {k: v for k, v in src.items()} != {k: v for k, v in msrc.items()}:
            bad(f"{f}: provenance and map fields differ", key, {k: (src.get(k), msrc.get(k)) for k in set(src) | set(msrc) if src.get(k) != msrc.get(k)})
        kind = a.get("disposition")
        if kind == "fetched_detail" and runs.get(a.get("source_run"), ("",))[0] != "LIVE":
            bad(f"{f}: fetched_detail not by a live run", key, (m.get("observation_kind"), a.get("source_run")))
        combos[(f, m.get("observation_kind"), kind, a.get("origin"), runs.get(a.get("source_run"), ("?",))[0])] += 1
        if a.get("source_run") and a["source_run"] not in runs and a.get("origin") != "imported":
            bad(f"{f}: unknown source_run", key, a["source_run"])
        if a.get("origin") == "imported" and a.get("source_run") not in imported_runs:
            bad(f"{f}: imported from a run not in the index", key, a.get("source_run"))
        if a.get("origin") == "imported":
            ix = imported.get(str(a.get("page_fetch_id")))
            if ix is None:
                bad(f"{f}: imported capture not in the index", key, a.get("page_fetch_id"))
            else:
                page = Path("C:/w7/b") / ix["path"]
                raw = page.read_bytes()
                html = gzip.decompress(raw)
                if hashlib.sha256(html).hexdigest() != a.get("body_sha256") and hashlib.sha256(raw).hexdigest() != a.get("body_sha256"):
                    bad(f"{f}: imported hash is not of the stored page", key, (hashlib.sha256(html).hexdigest(), hashlib.sha256(raw).hexdigest(), ix["stored_sha256"], a.get("body_sha256")))
                combos[(f, "imported page hash: " + ("of the page" if hashlib.sha256(html).hexdigest() == a.get("body_sha256") else "of the file") + ", index: " + ("of the page" if hashlib.sha256(html).hexdigest() == ix["stored_sha256"] else "of the file" if hashlib.sha256(raw).hexdigest() == ix["stored_sha256"] else "neither"))] += 1
                if ix["item_id"] != a.get("item_id"):
                    bad(f"{f}: imported page of another item", key, (ix["item_id"], a.get("item_id")))
                if ix["run_id"] != a.get("source_run"):
                    bad(f"{f}: imported run differs", key, (ix["run_id"], a.get("source_run")))
                if ix["source_revision"] != a.get("source_revision"):
                    bad(f"{f}: imported revision differs", key, (ix["source_revision"], a.get("source_revision")))
                if str(ix["observed_at"]).replace("+00:00", "Z")[:19] != str(a.get("observed_at"))[:19]:
                    bad(f"{f}: imported time differs", key, (ix["observed_at"], a.get("observed_at")))
        if a.get("source_run") and runs.get(a["source_run"], ("",))[0] == "REPLAY":
            bad(f"{f}: source_run is a replay", key, (m.get("observation_kind"), kind, a.get("origin"), a["source_run"]))
        if kind == "fetched_detail" and a.get("origin") != "fetched":
            bad(f"{f}: fetched without origin fetched", key, a.get("origin"))
        if kind == "recovered_from_saved_detail" and a.get("origin") == "fetched" and a.get("source_run") == (runs.get(this_run) or (0, 0))[1]:
            bad(f"{f}: recovered yet fetched by the source run", key, a.get("source_run"))
        if kind in ("fetched_detail", "recovered_from_saved_detail"):
            fid = a.get("page_fetch_id")
            if src.get("fetch_id") != fid:
                bad(f"{f}: fetch id differs", key, (src.get("fetch_id"), fid))
            for k1, k2 in (("body_sha256", "body_sha256"), ("observed_at", "observed_at"), ("item_id", "item_id"), ("source_run", "source_run"), ("source_revision", "source_revision"), ("origin", "origin")):
                if src.get(k1) != a.get(k2):
                    bad(f"{f}: {k1} differs", key, (src.get(k1), a.get(k2)))
            if a.get("item_id") != m.get("item_id"):
                bad(f"{f}: another item's page", key, (a.get("item_id"), m.get("item_id")))
            if not a.get("body_sha256") or not fid:
                bad(f"{f}: no capture named", key, (fid, a.get("body_sha256")))
            elif a.get("origin") != "imported":
                if fid not in fetches:
                    bad(f"{f}: fetch not in the store", key, fid)
                else:
                    if fetches[fid][1] not in ("product_detail", "product_page"):
                        bad(f"{f}: fetch of another purpose", key, fetches[fid][1])
                    if src.get("response_sha256") not in hashes.get(fid, ()):
                        bad(f"{f}: response_sha256 is not the stored page", key, (fid, src.get("response_sha256")))
                    if a["body_sha256"] not in hashes.get(fid, ()) and a["body_sha256"] not in raw_hash(fid):
                        bad(f"{f}: body_sha256 is neither the stored page nor the raw response", key, (fid, a["body_sha256"], sorted(raw_hash(fid))))
                    owner = fetches[fid][0]
                    if a.get("source_run") and owner != a["source_run"]:
                        if a.get("origin") == "read_again" and runs.get(owner, ("",))[1] == a["source_run"]:
                            combos[(f, "read_again: the fetch is the replay's read of the source run's page")] += 1
                        else:
                            bad(f"{f}: fetch belongs to another run ({runs.get(owner, ('?',))[0]})", key, (owner, a["source_run"]))
    # Every filled value names a source, every empty one a reason.
    r_missing = p.get("missing_kind") or {}
    for f in ("upc", "weight"):
        val = (d.get(f) or {}).get("value")
        if val and f in r_missing:
            bad(f"{f}: filled yet missing_kind", key, r_missing[f])
        if not val and f not in r_missing:
            bad(f"{f}: empty without missing_kind", key, (d.get(f) or {}).get("disposition"))
for r in rows:
    key = "wm:" + r["url"].split("?", 1)[0].rstrip("/").rsplit("/", 1)[-1]
    d = disp.get(key)
    if d is None:
        bad("product without disposition", key, "")
        continue
    for f in ("upc", "weight"):
        if (d.get(f) or {}).get("value", "") != r[f]:
            bad(f"{f}: products.json and dispositions differ", key, (r[f], d[f].get("value")))
report = {
    "export": str(x),
    "rows": len(rows),
    "problems": dict(problems),
    "examples": examples,
    "combinations": sorted((" | ".join(str(a) for a in k), v) for k, v in combos.items()),
}
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(report, indent=1, default=str, ensure_ascii=False) + "\n", "utf-8")
print(json.dumps({"rows": len(rows), "problems": dict(problems)}, indent=0, ensure_ascii=False))
for k, v in report["combinations"]:
    print(f"{v:6d} {k}")
for code, ex in list(examples.items())[:14]:
    print("--", code, json.dumps(ex[:2], default=str, ensure_ascii=False)[:420])
