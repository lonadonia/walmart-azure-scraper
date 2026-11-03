"""Build one edition's source ZIP from a committed revision (release 1.4.0; docs/EDITIONS.md).

    python deploy/build_edition.py --rev <commit> --edition scrapedo --out <folder>

The collector folder of the revision is exported with ``git archive`` (committed files only: never the
working tree, a virtual environment, data or keys). The edition is built from it
(``walmart_headless.editions.build``: two configuration lines, the environment example, ``BUILD_INFO.json``
and ``EDITION.json``) and written as ``WALMART_<EDITION>_SOURCE_<version>.zip`` with one top folder,
``walmart-<edition>-<version>/``. The ZIP is reproducible: its entries are sorted, every time stamp is the
revision's commit time and the permissions are the committed ones, so the same revision always gives the same
bytes. A JSON summary is printed: the ZIP's SHA-256 and size, and the edition record without its file list.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import subprocess
import sys
import tarfile
import zipfile
from datetime import UTC, datetime
from pathlib import Path

COLLECTOR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(COLLECTOR / "src"))

from walmart_headless import editions  # noqa: E402

_VERSION = re.compile(r'^version = "([^"]+)"$', re.M)


def git(*args: str, cwd: Path = COLLECTOR) -> bytes:
    return subprocess.run(["git", "-C", str(cwd), *args], check=True, capture_output=True).stdout


def export(commit: str) -> tuple[dict[str, bytes], dict[str, int]]:
    """The committed files of the collector folder (paths relative to it) and their permissions."""
    top = Path(git("rev-parse", "--show-toplevel").decode().strip())
    prefix = git("rev-parse", "--show-prefix").decode().strip()
    files: dict[str, bytes] = {}
    modes: dict[str, int] = {}
    archive = git("archive", "--format=tar", commit, "--", prefix or ".", cwd=top)
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        for m in tar.getmembers():
            if m.isdir() or m.name == "pax_global_header":
                continue
            if not m.isfile():
                raise SystemExit(f"{m.name}: not a regular file (links are not shipped)")
            rel = m.name.removeprefix(prefix)
            data = tar.extractfile(m)
            assert data is not None
            files[rel] = data.read()
            modes[rel] = m.mode & 0o777
    return files, modes


def write_zip(path: Path, top: str, files: dict[str, bytes], modes: dict[str, int], when: datetime) -> None:
    stamp = when.astimezone(UTC).timetuple()[:6]
    with zipfile.ZipFile(path, "w") as z:
        for rel in sorted(files):
            info = zipfile.ZipInfo(f"{top}/{rel}", date_time=stamp)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3  # permissions in the Unix form
            info.external_attr = (0o100000 | modes.get(rel, 0o644)) << 16
            z.writestr(info, files[rel], compresslevel=9)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--rev", required=True, help="the committed revision to build from")
    p.add_argument("--edition", required=True, choices=sorted(editions.EDITIONS))
    p.add_argument("--out", required=True, type=Path, help="the folder the ZIP is written to")
    args = p.parse_args()
    commit = git("rev-parse", "--verify", f"{args.rev}^{{commit}}").decode().strip()
    committed = datetime.fromisoformat(git("show", "-s", "--format=%cI", commit).decode().strip())
    files, modes = export(commit)
    found = _VERSION.search(files["pyproject.toml"].decode("utf-8"))
    if found is None:
        raise SystemExit("no version in pyproject.toml")
    version = found.group(1)
    out = editions.build(
        files,
        args.edition,
        revision=commit,
        committed_at=committed.astimezone(UTC).isoformat(),
        version=version,
    )
    for added in (editions.BUILD_INFO, editions.RECORD):
        modes[added] = 0o644
    args.out.mkdir(parents=True, exist_ok=True)
    zip_path = args.out / f"WALMART_{args.edition.upper()}_SOURCE_{version}.zip"
    write_zip(zip_path, f"walmart-{args.edition}-{version}", out, modes, committed)
    record = json.loads(out[editions.RECORD])
    record.pop("file_sha256")
    data = zip_path.read_bytes()
    summary = {
        "zip": zip_path.name,
        "sha256": hashlib.sha256(data).hexdigest(),
        "size": len(data),
        "top_folder": f"walmart-{args.edition}-{version}",
        "entries": len(out),
        "edition": record,
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
