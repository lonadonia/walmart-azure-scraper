"""Read-only SQL against the campaign database (usage: python -I q.py "SELECT ..." ...)."""

import json
import os
import sys

os.environ["PSYCOPG_IMPL"] = "python"
os.environ["PATH"] = (
    "C:/w9/live/ed/walmart-oxylabs-1.6.0/.venv/Lib/site-packages/pgserver/pginstall/bin"
    + os.pathsep
    + os.environ.get("PATH", "")
)

sys.path.insert(0, "C:/w9/live")
import live160_run as h  # noqa: E402
from sqlalchemy import create_engine, text  # noqa: E402

eng = create_engine(h.db_url())
with eng.connect() as c:
    c.execute(text("SET TRANSACTION READ ONLY"))
    for sql in sys.argv[1:]:
        res = c.execute(text(sql))
        cols = list(res.keys())
        rows = res.fetchall()
        print(json.dumps({"sql": sql[:200], "n": len(rows)}))
        for r in rows[:400]:
            print(json.dumps(dict(zip(cols, r, strict=True)), default=str))
