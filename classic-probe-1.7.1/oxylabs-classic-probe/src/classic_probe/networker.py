"""The isolated network worker (1.7.0, findings C1 and C2): one HTTP exchange in a child process.

The supervising process (transport.IsolatedHttpTransport) starts ``python -I -m classic_probe.networker``,
writes one JSON specification to its standard input (the Authorization header travels there, never in an
argument or the environment) and kills and reaps it at the request's deadline. This worker:

- connects only to the documented endpoint over HTTPS (and only in a build with live mode enabled), or to a
  loopback test stub when the specification says so;
- never follows a redirect: ``http.client`` has no redirect handling, and a 3xx answer is reported as it is;
- reads the body in chunks, each socket wait clamped to the time left, and stops at ``max_body_bytes`` on
  every status (success and error alike): a large or endless body is cut, reported as truncated, never kept
  whole;
- writes the bytes it read to a private ``.part`` file, flushed and synced, and prints one JSON status line.

1.7.1 (finding C4): the files are named by the dispatch's number in the ledger (``dispatch_NNN``), given by
the campaign, and nothing received is deleted:

- a whole answer: its status (HTTP status, headers, length, SHA-256) is written durably to
  ``dispatch_NNN.status.json``, then the body is renamed, durably, to ``dispatch_NNN.body``. A crash at any
  point leaves either nothing, a body still named ``.part`` (with or without its status), or both files: the
  recovery keeps an answer whose body matches its status, without a paid refetch (captures.py);
- a body cut by the deadline or an error: the bytes that arrived are synced and renamed to
  ``dispatch_NNN.partial``, and the status says how many there were and their SHA-256, never that the answer
  is complete;
- reads use ``read1``, so a slow body is recorded up to the last byte that arrived.
"""

from __future__ import annotations

import base64
import hashlib
import http.client
import json
import os
import ssl
import sys
import time
from pathlib import Path
from typing import Any

from classic_probe import contract, durable, gates

CHUNK = 65536


def _open_private(path: str) -> int:
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC | getattr(os, "O_BINARY", 0)
    return os.open(path, flags, 0o600)


def _write_all(fd: int, data: bytes) -> None:
    view = memoryview(data)
    while view:
        view = view[os.write(fd, view) :]


def _status_file(spec: dict[str, Any], status: dict[str, Any]) -> dict[str, Any]:
    """The status, also written durably beside the body (1.7.1): a supervisor that dies loses the worker's
    output, not this file."""
    path = spec.get("status_path")
    if path:
        durable.write(Path(path), (json.dumps(status, sort_keys=True) + "\n").encode("utf-8"), private=True)
    return status


def _allowed(spec: dict[str, Any]) -> str | None:
    """None if this worker may connect; else why not."""
    scheme, host, port = spec["scheme"], spec["host"], int(spec["port"])
    if spec.get("loopback_stub"):
        if scheme == "http" and host == "127.0.0.1":
            return None
        return "a loopback stub must be http://127.0.0.1"
    endpoint = contract.ENDPOINT_PARTS
    if (scheme, host, port) != endpoint:
        return f"{scheme}://{host}:{port} is not the documented endpoint"
    if not gates.LIVE_ENABLED:
        return "live mode is disabled in this build"
    return None


def exchange(spec: dict[str, Any]) -> dict[str, Any]:
    t0 = time.monotonic()
    deadline = t0 + float(spec["allowance_s"])
    refused = _allowed(spec)
    if refused:
        return _status_file(spec, {"ok": False, "error": "Refused", "detail": refused, "sent": False})

    def left() -> float:
        return deadline - time.monotonic()

    if left() <= 0:
        return _status_file(spec, {"ok": False, "error": "DeadlinePassed", "sent": False})
    conn: http.client.HTTPConnection
    if spec["scheme"] == "https":
        conn = http.client.HTTPSConnection(
            spec["host"],
            int(spec["port"]),
            timeout=max(0.05, min(30.0, left())),
            context=ssl.create_default_context(),
        )
    else:
        conn = http.client.HTTPConnection(
            spec["host"], int(spec["port"]), timeout=max(0.05, min(30.0, left()))
        )
    # Whether the request left: False while nothing of it was written, None (unknown) once writing began,
    # True when it was written whole. Only False lets the supervisor treat the request as never sent.
    sent: bool | None = False
    out_path = spec["out_path"]
    max_body = int(spec["max_body_bytes"])
    fd: int | None = None
    total, truncated = 0, False
    digest = hashlib.sha256()
    http_status: int | None = None

    def partial(error: str) -> dict[str, Any]:
        """What arrived before ``error``, kept and described, never called complete (1.7.1, C4)."""
        nonlocal fd
        status: dict[str, Any] = {"ok": False, "error": error, "sent": sent, "http_status": http_status}
        if fd is not None:
            os.fsync(fd)
            os.close(fd)
            fd = None
            if total and spec.get("partial_path"):
                durable.replace(Path(out_path), Path(spec["partial_path"]))
                status.update(partial_bytes=total, partial_sha256=digest.hexdigest(), partial_file=True)
            else:
                os.unlink(out_path)  # nothing arrived: an empty file is not evidence
        return _status_file(spec, status)

    try:
        body = base64.b64decode(spec["body_b64"]) if spec.get("body_b64") else None
        conn.connect()
        if left() <= 0:
            return _status_file(spec, {"ok": False, "error": "DeadlinePassed", "sent": False})
        sent = None
        conn.request(spec["method"], spec["path"], body=body, headers=spec["headers"])
        sent = True
        if conn.sock is not None:
            conn.sock.settimeout(max(0.05, left()))
        resp = conn.getresponse()
        http_status = resp.status
        headers = [(k, v) for k, v in resp.getheaders() if k.lower() != "set-cookie"]
        header_bytes = sum(len(k) + len(v) for k, v in headers)
        fd = _open_private(out_path)
        while True:
            if left() <= 0:
                return partial("DeadlinePassed")
            if conn.sock is not None:
                conn.sock.settimeout(max(0.05, left()))
            chunk = resp.read1(min(CHUNK, max_body + 1 - total))
            if not chunk:
                break
            if total + len(chunk) > max_body:
                chunk = chunk[: max_body - total]
                truncated = True
            _write_all(fd, chunk)
            digest.update(chunk)
            total += len(chunk)
            if truncated:
                break
        os.fsync(fd)
        os.close(fd)
        fd = None
        status = {
            "ok": True,
            "status": resp.status,
            "reason": resp.reason,
            "headers": headers if header_bytes <= int(spec["max_header_bytes"]) else [],
            "headers_truncated": header_bytes > int(spec["max_header_bytes"]),
            "body_bytes": total,
            "truncated": truncated,
            "sha256": digest.hexdigest(),
            "elapsed_s": round(time.monotonic() - t0, 3),
            "redirect_location": next((v for k, v in headers if k.lower() == "location"), None)
            if 300 <= resp.status < 400
            else None,
        }
        # The status first (it names the body's hash), then the body under its final name: a crash between
        # the two leaves a body still named .part that its status describes (the recovery checks the hash).
        _status_file(spec, status)
        if spec.get("final_path"):
            durable.replace(Path(out_path), Path(spec["final_path"]))
        return status
    except Exception as exc:  # noqa: BLE001 - reported to the supervisor; no credential is in the message
        return partial(type(exc).__name__)
    finally:
        if fd is not None:
            os.close(fd)
        conn.close()


def main() -> int:
    raw = sys.stdin.buffer.read(1_000_000)
    spec = json.loads(raw)
    result = exchange(spec)
    sys.stdout.write(json.dumps(result) + "\n")
    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
