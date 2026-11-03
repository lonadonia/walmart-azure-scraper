"""A new copy of the campaign for a replay of the final revision: a new database restored from the frozen dump, and the
stored pages from the frozen archive. The campaign's own database and data are not touched.

usage: <venv python> -I -X utf8 fresh_copy_152.py WORK
"""

from __future__ import annotations

import hashlib
import subprocess
import sys
import tarfile
from pathlib import Path

import pgserver
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

PKG = Path("C:/w7/pack152/vm")
SHA = {"campaign_copy.dump": "f484a177", "campaign_data.tar.gz": "f68bfc48"}
work = Path(sys.argv[1])
for name, start in SHA.items():
    got = hashlib.sha256((PKG / name).read_bytes()).hexdigest()
    assert got.startswith(start), (name, got)
    print(name, got)
work.mkdir(parents=True, exist_ok=False)
srv = pgserver.get_server(str(work / "pgdata"), cleanup_mode=None)
base = make_url(srv.get_uri())
eng = create_engine(base.set(drivername="postgresql+psycopg"), isolation_level="AUTOCOMMIT")
with eng.connect() as c:
    c.execute(text('create database "walmart_live150"'))
url = base.set(database="walmart_live150").render_as_string(hide_password=False)
bin_ = Path(sys.executable).parent.parent / "Lib" / "site-packages" / "pgserver" / "pginstall" / "bin"
subprocess.run(
    [str(bin_ / "pg_restore.exe"), "--no-owner", "--no-privileges", "-d", url, str(PKG / "campaign_copy.dump")],
    check=True,
)
with tarfile.open(PKG / "campaign_data.tar.gz") as t:
    t.extractall(work / "data", filter="data")
with create_engine(base.set(drivername="postgresql+psycopg", database="walmart_live150")).connect() as c:
    print("runs", c.execute(text("select mode, count(*) from runs group by 1 order by 1")).all())
    print("pages", c.execute(text("select count(*) from page_fetches")).scalar())
print("files", sum(1 for p in (work / "data").rglob("*") if p.is_file()))
