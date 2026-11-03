"""The isolated campaign database of the 1.5.0 live validation: a local PostgreSQL (pgserver) cluster under
C:/w7/live/pgdata with one database, walmart_live150. Nothing on Azure, no other database touched.
usage: <edition venv python> -I live150_db.py start|stop|url
"""

import sys
from pathlib import Path

import pgserver
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

PGDATA = Path(r"C:\w7\live\pgdata")
DB = "walmart_live150"


def main() -> None:
    action = sys.argv[1]
    srv = pgserver.get_server(str(PGDATA), cleanup_mode=None)
    if action == "stop":
        srv.cleanup()  # stops the server; the data folder stays
        print("stopped; data kept at", PGDATA)
        return
    url = make_url(srv.get_uri())
    if action == "start":
        eng = create_engine(url.render_as_string(hide_password=False), isolation_level="AUTOCOMMIT")
        with eng.connect() as c:
            have = c.execute(text("select 1 from pg_database where datname = :d"), {"d": DB}).scalar()
            if not have:
                c.execute(text(f'create database "{DB}"'))
                print("created", DB)
            else:
                print("exists", DB)
            print([r[0] for r in c.execute(text("select datname from pg_database order by 1"))])
    print("server", url.set(database=DB).render_as_string(hide_password=True))


if __name__ == "__main__":
    main()
