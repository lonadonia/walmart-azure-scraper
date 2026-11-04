"""Each answer kept on disk, durably, before the next paid step (1.7.0, finding C4).

A capture is written in three moves: the kept copy and its metadata to ``.part`` files (flushed and synced),
each renamed into place (an atomic rename on the same disk), then indexed in the ledger's ``capture`` table.
A crash leaves at worst ``.part`` files (removed on recovery: never indexed, never evidence) or a complete
pair not yet indexed (indexed on recovery once its hash checks out). The evidence export reads this index and
these files only, never the memory of a process, so it can be rebuilt after any crash.

The copy kept is sanitized: values under credential-like keys are replaced, and each raw page goes through the
retailer collector's own sanitizer. The response as received is never written; only its SHA-256 is kept
(private: it cannot be checked by a reader), beside the SHA-256 of the copy kept (public: anyone can check it
against the file), so the two are matched without publishing the original.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import os
import re
import urllib.parse
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import TYPE_CHECKING, Any

from classic_probe.transport import ProviderResponse

if TYPE_CHECKING:
    from classic_probe.ledger import Ledger

_SECRET_KEYS = re.compile(r"(?i)authori[sz]ation|cookie|password|token|secret|session")


def sanitize(value: Any) -> Any:
    """A response as it may be kept: values under credential-like keys are replaced."""
    if isinstance(value, Mapping):
        return {k: "[REMOVED]" if _SECRET_KEYS.search(str(k)) else sanitize(v) for k, v in value.items()}
    if isinstance(value, list):
        return [sanitize(v) for v in value]
    return value


def kept_response(original: bytes, retailer: str = "walmart") -> tuple[bytes, list[dict[str, Any]]]:
    """A response as it may be kept as evidence: values under credential-like keys replaced, and each raw page
    passed through the retailer collector's sanitizer (vendor/walmart_sanitize.py: session and trace
    identifiers, tokens, other scripts and inlined data removed; product, price, store and fulfillment data
    untouched; vendor/marianos_sanitize.py for Mariano's). A body that is not JSON is kept only as its hash
    and length: it was not the documented structure."""
    from classic_probe.vendor import marianos_sanitize, walmart_sanitize

    try:
        body = json.loads(original)
    except ValueError:
        note = {"not_json": True, "bytes": len(original), "sha256": hashlib.sha256(original).hexdigest()}
        return json.dumps(note, sort_keys=True).encode("utf-8"), []
    pages: list[dict[str, Any]] = []
    if isinstance(body, Mapping) and isinstance(body.get("results"), list):
        for i, result in enumerate(body["results"]):
            if isinstance(result, dict) and isinstance(result.get("content"), str) and retailer == "marianos":
                # 1.6.0: a Mariano's page through the Mariano's collector's own sanitizer (scripts other than
                # the page state removed, styles emptied, inlined data URIs replaced).
                kept_page, mreport = marianos_sanitize.sanitize_html(result["content"])
                result["content"] = kept_page
                pages.append(
                    {
                        "result": i,
                        "state_script_kept": mreport.state_script_kept,
                        "scripts_removed": mreport.scripts_removed,
                        "styles_emptied": mreport.styles_emptied,
                        "data_uris_replaced": mreport.data_uris_replaced,
                        "input_sha256": mreport.input_sha256,
                        "output_sha256": mreport.output_sha256,
                    }
                )
            elif isinstance(result, dict) and isinstance(result.get("content"), str):
                clean, report = walmart_sanitize.sanitize_html(result["content"])
                result["content"] = clean
                pages.append(
                    {
                        "result": i,
                        "page_data_kept": report.page_data_kept,
                        "page_data_values_redacted": report.page_data_values_redacted,
                        "other_values_redacted": report.other_values_redacted,
                        "scripts_removed": report.scripts_removed,
                        "input_sha256": report.input_sha256,
                        "output_sha256": report.output_sha256,
                    }
                )
    return json.dumps(sanitize(body), sort_keys=True).encode("utf-8"), pages


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def atomic_write(path: Path, data: bytes) -> None:
    """``path`` holds ``data`` whole or not at all: a ``.part`` file, flushed, synced, renamed into place."""
    part = path.with_name(path.name + ".part")
    with open(part, "wb") as fh:
        fh.write(data)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(part, path)
    if os.name == "posix":  # the rename itself made durable (a directory cannot be synced on Windows)
        fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)


def _location(value: str | None) -> str | None:
    """A redirect's target as it may be kept: scheme, host and path only (a query could carry a token)."""
    if not value:
        return None
    u = urllib.parse.urlsplit(value)
    return urllib.parse.urlunsplit((u.scheme, u.netloc.rpartition("@")[2], u.path, "", ""))


class CaptureStore:
    """The kept answers of one retailer's part of a campaign, in ``directory``."""

    def __init__(self, directory: Path, retailer: str) -> None:
        self.directory = directory
        self.retailer = retailer

    def data_name(self, seq: int) -> str:
        return f"response_{seq:03d}.json.gz"

    def meta_name(self, seq: int) -> str:
        return f"response_{seq:03d}.meta.json"

    def persist(self, seq: int, step: str, response: ProviderResponse) -> dict[str, Any]:
        """Write one answer's kept copy and metadata durably; returns the record to index."""
        self.directory.mkdir(parents=True, exist_ok=True)
        kept, pages = kept_response(response.body, self.retailer)
        data = gzip.compress(kept, mtime=0)
        record: dict[str, Any] = {
            "seq": seq,
            "file": self.data_name(seq),
            "http_status": response.http_status,
            "body_bytes": len(response.body),
            "truncated": response.truncated,
            "original_sha256": sha256(response.body),
            "kept_sha256": sha256(kept),
            "sanitized": kept != response.body,
            "detail": {
                "step": step,
                "file_sha256": sha256(data),
                "raw_pages": pages,
                "headers": sanitize(dict(response.headers)),
                "redirect_location": _location(response.redirect_location),
                "elapsed_s": response.elapsed_s,
            },
        }
        atomic_write(self.directory / self.data_name(seq), data)
        atomic_write(
            self.directory / self.meta_name(seq),
            (json.dumps(record, sort_keys=True, indent=1) + "\n").encode("utf-8"),
        )
        return record

    def recover(self, ledger: Ledger) -> dict[str, Any]:
        """After a crash: ``.part`` files are removed (never indexed, never evidence), and a complete pair the
        index lacks is indexed when its file matches its recorded hash."""
        if not self.directory.is_dir():
            return {"part_files_removed": [], "indexed_on_recovery": [], "refused": []}
        removed = []
        for part in sorted(self.directory.glob("response_*.part")):
            part.unlink()
            removed.append(part.name)
        indexed = {int(c["seq"]) for c in ledger.captures()}
        known = {int(r["seq"]) for r in ledger.rows()}
        added: list[int] = []
        refused: list[dict[str, Any]] = []
        for meta in sorted(self.directory.glob("response_*.meta.json")):
            record = json.loads(meta.read_text(encoding="utf-8"))
            seq = int(record["seq"])
            if seq in indexed:
                continue
            path = self.directory / str(record["file"])
            if seq not in known:
                refused.append({"file": meta.name, "why": "no dispatch of this number in the ledger"})
            elif not path.is_file() or sha256(path.read_bytes()) != record["detail"]["file_sha256"]:
                refused.append({"file": meta.name, "why": "its data file is missing or does not match"})
            else:
                ledger.record_capture(seq, record)
                added.append(seq)
        return {"part_files_removed": removed, "indexed_on_recovery": added, "refused": refused}

    def verify(
        self, ledger: Ledger, *, time_left: Callable[[], float], min_left_s: float
    ) -> tuple[list[dict[str, Any]], bool]:
        """Each indexed capture against its file, while time is left. Returns the entries and whether every
        capture was checked; one not checked in time is listed as unverified, never as good."""
        entries: list[dict[str, Any]] = []
        complete = True
        for c in ledger.captures():
            entry = {
                "seq": c["seq"],
                "file": c["file"],
                "step": c["detail"].get("step"),
                "http_status": c["http_status"],
                "body_bytes": c["body_bytes"],
                "truncated": bool(c["truncated"]),
                "original_sha256": c["original_sha256"],
                "kept_sha256": c["kept_sha256"],
                "sanitized": bool(c["sanitized"]),
                "raw_pages": c["detail"].get("raw_pages", []),
                "headers": c["detail"].get("headers", {}),
                "redirect_location": c["detail"].get("redirect_location"),
            }
            if time_left() < min_left_s:
                entry["verified"] = None
                entry["why"] = "not checked: the session's time ran out"
                complete = False
            else:
                path = self.directory / str(c["file"])
                try:
                    ok = sha256(gzip.decompress(path.read_bytes())) == c["kept_sha256"]
                except (OSError, EOFError, gzip.BadGzipFile):
                    ok = False
                entry["verified"] = ok
                if not ok:
                    complete = False
            entries.append(entry)
        return entries, complete
