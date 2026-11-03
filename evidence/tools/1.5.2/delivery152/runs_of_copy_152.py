"""RUNS_OF_THE_COPY.json: the live runs in the database copy that B3's replay read, each with its mode, status and
revision, so that a reader can tell which run an observed_by_run names. Reads only.

usage: <venv python> -I -X utf8 runs_of_copy_152.py PGDATA DB OUT.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pgserver
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

pgdata, db, out = sys.argv[1], sys.argv[2], Path(sys.argv[3])
srv = pgserver.get_server(pgdata, cleanup_mode=None)
url = make_url(srv.get_uri()).set(drivername="postgresql+psycopg", database=db)
with create_engine(url).connect() as c:
    rows = c.execute(
        text("select id, mode, status, started_at, config_snapshot->>'source_revision' from runs where mode = 'LIVE' order by started_at")
    ).all()
    all_modes = c.execute(text("select mode, count(*) from runs group by 1 order by 1")).all()
print(all_modes)
doc = {r[0]: {"mode": r[1], "status": r[2], "started_at": str(r[3]), "source_revision": r[4]} for r in rows}
out.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8", newline="\n")
print(len(doc), "live runs")
