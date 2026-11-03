"""Offline reprocessing of Oxylabs B3 (run 01M60V2DCCWR72BGVVG3EM9R74, release 1.4.1) with release 1.5.0:
a local copy of the VM's walmart_oxylabs database and B3's stored pages (2026-10-31 work, brief section 4).

Steps (nothing here contacts a provider or Walmart; "dump" reads the VM over the established SSH access):
  dump    read-only on the VM: the exact row count of every table of walmart_oxylabs, its Alembic version,
          then "sudo -u postgres pg_dump -Fc walmart_oxylabs" streamed to this PC (nothing is written on
          the VM). Kept in C:\\w7\\reproc\\vm_dump with its SHA-256 and size.
  start   a throwaway PostgreSQL 16 (pgserver) in C:\\w7\\reproc\\pgdata (left running), database
          walmart_reproc150 restored from the dump (--no-owner --no-privileges: the VM's roles do not
          exist here); its row counts compared with the VM's. Prints the database URL (pgserver's local
          server: no password).
  data    B3's stored pages from the 1.4.1 evidence (live.tar, checked against its SHA256SUMS) into
          C:\\w7\\reproc\\data\\runs\\walmart-3891-pickup\\<run>\\live (tarfile "data" filter), and every
          artifact the database lists for B3 checked against its recorded SHA-256 and size.
  stop    stop the server (the data directory is kept).
usage: python -I reproc150_setup.py dump|start|counts|data|stop
"""

from __future__ import annotations

import hashlib
import os
import subprocess
import sys
import tarfile
from datetime import UTC, datetime
from pathlib import Path

WORK = Path(r"C:\w7\reproc")
DUMPDIR = WORK / "vm_dump"
PGDATA = WORK / "pgdata"
DATA = WORK / "data"
DB = os.environ.get("REPROC_DB", "walmart_reproc150")  # attempt 1: walmart_reproc150
VM_DB = "walmart_oxylabs"
B3 = "01M60V2DCCWR72BGVVG3EM9R74"
STORE_KEY = "walmart-3891-pickup"
EVID = Path(r"C:\w6\c140\evidence\runs\walmart_oxylabs") / B3
SSH = [
    r"C:\Windows\System32\OpenSSH\ssh.exe",
    "-F",
    r"C:\w6\ssh\config",
    "-o",
    "BatchMode=yes",
    "-o",
    "ConnectTimeout=20",
    "wvm",
]
BIN = Path(sys.executable).parent.parent / "Lib" / "site-packages" / "pgserver" / "pginstall" / "bin"
COUNTS_SQL = (
    "select string_agg(format('%s=%s', table_name, (xpath('/row/c/text()', query_to_xml(format("
    "'select count(*) as c from %I.%I', table_schema, table_name), false, true, '')))[1]::text), ' ' "
    "order by table_name) from information_schema.tables where table_schema = 'public' "
    "and table_type = 'BASE TABLE'"
)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(1 << 20):
            h.update(chunk)
    return h.hexdigest()


def remote(script: str) -> str:
    out = subprocess.run([*SSH, "bash -s"], input=script, capture_output=True, text=True, timeout=300)
    if out.returncode != 0:
        raise SystemExit(f"ssh exit {out.returncode}: {out.stderr.strip()[-800:]}")
    return out.stdout


def dump() -> None:
    DUMPDIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    target = DUMPDIR / f"{VM_DB}-{stamp}.dump"
    facts = DUMPDIR / f"{VM_DB}-{stamp}.vm_facts.txt"
    if target.exists() or facts.exists():
        raise SystemExit("the dump files exist already")
    before = remote(
        "date -u +%FT%TZ\n"
        f'sudo -u postgres psql -X -At -d {VM_DB} -c "select version_num from alembic_version"\n'
        f"sudo -u postgres psql -X -At -d {VM_DB} -c \"{COUNTS_SQL}\"\n"
        f"sudo -u postgres psql -X -At -d {VM_DB} -c \"select id, status, mode, started_at, finished_at "
        f"from runs where id = '{B3}'\"\n"
    )
    with target.open("wb") as f:
        out = subprocess.run([*SSH, f"sudo -u postgres pg_dump -Fc {VM_DB}"], stdout=f, stderr=subprocess.PIPE)
    if out.returncode != 0:
        raise SystemExit(f"pg_dump over ssh exit {out.returncode}: {out.stderr.decode(errors='replace')[-800:]}")
    after = remote(f"date -u +%FT%TZ\nsudo -u postgres psql -X -At -d {VM_DB} -c \"{COUNTS_SQL}\"\n")
    digest, size = sha256(target), target.stat().st_size
    facts.write_text(
        f"# read-only facts of the VM database {VM_DB} (azureuser@scraper-test-vm over SSH), before the dump:\n"
        f"{before}"
        f"# after the dump (the same counts: nothing changed while it was taken):\n{after}"
        f"# dump {target.name}: {size} bytes, sha256 {digest}\n",
        encoding="utf-8",
        newline="\n",
    )
    print(facts.read_text(encoding="utf-8"))
    b_counts = before.strip().splitlines()[2]
    a_counts = after.strip().splitlines()[1]
    print("counts unchanged during the dump:", b_counts == a_counts)


def latest_dump() -> Path:
    dumps = sorted(DUMPDIR.glob(f"{VM_DB}-*.dump"))
    if not dumps:
        raise SystemExit("no dump: run the dump step first")
    return dumps[-1]


def server(cleanup_mode: str | None = None):  # noqa: ANN201 - pgserver has no type information
    import pgserver

    PGDATA.mkdir(parents=True, exist_ok=True)
    # None leaves the server running after this process; "stop" lets cleanup() stop it.
    return pgserver.get_server(str(PGDATA), cleanup_mode=cleanup_mode)


def libpq_of(srv) -> str:  # noqa: ANN001
    from sqlalchemy.engine import make_url

    return make_url(srv.get_uri()).set(database=DB).render_as_string(hide_password=False)


def local_counts(libpq: str) -> str:
    """The VM's COUNTS_SQL result, computed here without its XML functions (pgserver's build has no
    libxml): "table=count" for every base table of the public schema, ordered by name, space-separated."""
    import psycopg

    with psycopg.connect(libpq) as conn:
        names = [
            r[0]
            for r in conn.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' "
                "AND table_type = 'BASE TABLE'"
            ).fetchall()
        ]
        parts = []
        for name in sorted(names, key=lambda n: n.encode()):
            row = conn.execute(f'SELECT count(*) FROM public."{name}"').fetchone()
            parts.append(f"{name}={row[0] if row else '?'}")
    return " ".join(parts)


def counts() -> None:
    """Compare the restored database's row counts with the VM's (after a start that restored it)."""
    src = latest_dump()
    vm = src.with_suffix(".vm_facts.txt").read_text(encoding="utf-8").splitlines()[3]
    local = local_counts(libpq_of(server()))
    print("row counts equal to the VM's:", local == vm)
    if local != vm:
        print(" vm:   ", vm[:2000])
        print(" local:", local[:2000])
        raise SystemExit(1)


def start() -> None:
    import psycopg

    src = latest_dump()
    facts = src.with_suffix(".vm_facts.txt")
    srv = server()
    with psycopg.connect(srv.get_uri(), autocommit=True) as conn:
        if conn.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DB,)).fetchone():
            raise SystemExit(f"database {DB} exists already: this step restores into a new database only")
        conn.execute(f"CREATE DATABASE {DB}")
    libpq = libpq_of(srv)
    print("restoring", src.name, sha256(src))
    out = subprocess.run(
        [str(BIN / "pg_restore.exe"), "--no-owner", "--no-privileges", "--exit-on-error", "-d", libpq, str(src)],
        capture_output=True,
        text=True,
    )
    print("pg_restore exit", out.returncode)
    if out.stderr.strip():
        print(out.stderr.strip()[-3000:])
    if out.returncode != 0:
        raise SystemExit(out.returncode)
    local = local_counts(libpq)
    with psycopg.connect(libpq) as conn:
        rev = [r[0] for r in conn.execute("SELECT version_num FROM alembic_version").fetchall()]
    vm = facts.read_text(encoding="utf-8").splitlines()[3]
    print("alembic_version:", rev)
    print("row counts equal to the VM's:", local == vm)
    if local != vm:
        print(" vm:   ", vm[:2000])
        print(" local:", local[:2000])
        raise SystemExit(1)
    from sqlalchemy.engine import make_url

    print("DATABASE_URL", make_url(srv.get_uri()).set(drivername="postgresql+psycopg", database=DB).render_as_string(
        hide_password=False
    ))


def data(run: str = B3) -> None:
    """A run's stored pages (B3 by default; also the earlier runs whose records B3 carries forward, so that
    validate-export can compare those records with their own pages) and its export files."""
    import psycopg

    evid = EVID.parent / run
    sums = {}
    for line in (evid / "SHA256SUMS.txt").read_text().splitlines():
        digest, name = line.split(maxsplit=1)
        sums[name.lstrip("*")] = digest
    tar = evid / "live.tar"
    if sha256(tar) != sums["live.tar"]:
        raise SystemExit("live.tar does not match its SHA256SUMS")
    dest = DATA / "runs" / STORE_KEY / run
    exports = Path(r"C:\w7\b\ox\walmart-oxylabs-evidence-1.4.1\1_new_live_oxylabs\runs\walmart_oxylabs") / run
    exports = exports / "exports"
    if run != B3 and exports.is_dir() and not (dest / "exports").exists():
        (dest / "exports").mkdir(parents=True)
        for f in exports.iterdir():
            if f.is_file():
                (dest / "exports" / f.name).write_bytes(f.read_bytes())
    dest.mkdir(parents=True, exist_ok=True)
    present = (dest / "live").is_dir() and any((dest / "live").iterdir())
    n = same = 0
    with tarfile.open(tar, "r:") as t:
        for m in t:
            if not m.name.startswith("live/") and m.name != "live":
                raise SystemExit(f"unexpected member: {m.name}")
            if not (m.isfile() or m.isdir()):
                raise SystemExit(f"unexpected member type: {m.name}")
            if not present:
                t.extract(m, dest, filter="data")
                n += m.isfile()
            elif m.isfile():
                # Extracted by an earlier attempt of this step: the files must be the archive's bytes.
                f = t.extractfile(m)
                p = dest / m.name
                if f is None or not p.is_file() or p.read_bytes() != f.read():
                    raise SystemExit(f"{p} differs from the archive member {m.name}")
                same += 1
    # The run's export files (exports/) are laid next to live/ from the delivered 1.4.1 evidence: they are
    # checked below against the artifact table like the pages.
    on_disk = sum(1 for p in (dest / "live").rglob("*") if p.is_file())
    if present:
        print(f"already extracted: {same} files equal to the archive's members; {on_disk} files in live/")
        if on_disk != same:
            raise SystemExit("the folder holds files the archive does not")
    else:
        print(f"extracted {n} files into {dest}")
    srv = server()
    bad = checked = 0
    with psycopg.connect(libpq_of(srv)) as conn:
        rows = conn.execute(
            "SELECT a.key, a.sha256, a.size FROM artifacts a WHERE a.run_id = %s ORDER BY a.key", (run,)
        ).fetchall()
    for key, digest, size in rows:
        p = DATA / key
        if not p.is_file():
            print("MISSING", key)
            bad += 1
            continue
        raw = p.read_bytes()
        ok = hashlib.sha256(raw).hexdigest() == digest and len(raw) == size
        checked += 1
        if not ok:
            print("SHA MISMATCH", key)
            bad += 1
    print(f"{run} artifacts: {len(rows)} listed, {checked} present, {bad} missing or mismatched")
    if bad:
        raise SystemExit(1)


def stop() -> None:
    srv = server("stop")
    srv.cleanup()
    print("stopped")


if __name__ == "__main__":
    step = {"dump": dump, "start": start, "counts": counts, "data": data, "stop": stop}[sys.argv[1]]
    step(*sys.argv[2:])  # data [RUN]
