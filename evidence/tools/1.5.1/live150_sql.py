"""A read-only query on the campaign database walmart_live150 (default_transaction_read_only on).
usage: <edition venv python> -I live150_sql.py "SELECT ..."
"""

import json
import sys
from pathlib import Path

import pgserver
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

srv = pgserver.get_server(str(Path(r"C:\w7\live\pgdata")), cleanup_mode=None)
url = make_url(srv.get_uri()).set(database="walmart_live150").render_as_string(hide_password=False)
eng = create_engine(url.replace("postgresql://", "postgresql+psycopg://", 1))
with eng.connect() as c:
    c.execute(text("set default_transaction_read_only = on"))
    c.execute(text("begin read only"))
    res = c.execute(text(sys.argv[1]))
    cols = list(res.keys())
    print("|".join(cols))
    for row in res:
        print("|".join(json.dumps(v, default=str) if isinstance(v, (dict, list)) else str(v) for v in row))
