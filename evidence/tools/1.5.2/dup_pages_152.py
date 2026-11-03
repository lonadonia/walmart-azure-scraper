"""Pages read more than once in a replay and in the run it replays, read from a copy of the database. Reads only.

usage: <venv python> -I -X utf8 dup_pages_152.py PGDATA DB SOURCE_RUN
"""

from __future__ import annotations

import sys

import pgserver
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

pgdata, db, source = sys.argv[1], sys.argv[2], sys.argv[3]
srv = pgserver.get_server(pgdata, cleanup_mode=None)
url = make_url(srv.get_uri()).set(drivername="postgresql+psycopg", database=db)
Q = """select url, purpose, count(*) from page_fetches where run_id = :r
       group by 1, 2 having count(*) > 1 order by 3 desc, 1"""
with create_engine(url).connect() as c:
    replays = [
        r
        for (r,) in c.execute(
            text("select id from runs where mode='REPLAY' and config_snapshot->'replay'->>'source_run' = :s order by started_at"),
            {"s": source},
        )
    ]
    print("source", source, "replays", replays)
    for r in [source, *replays]:
        rows = c.execute(text(Q), {"r": r}).all()
        n = c.execute(text("select count(*) from page_fetches where run_id = :r"), {"r": r}).scalar()
        print(r, "pages", n, "read twice or more", len(rows))
        for u, p, k in rows[:6]:
            print("   ", k, p, str(u)[:110])
