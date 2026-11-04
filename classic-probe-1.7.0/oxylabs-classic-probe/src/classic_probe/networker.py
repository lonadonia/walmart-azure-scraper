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
from typing import Any

from classic_probe import contract, gates

CHUNK = 65536


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
        return {"ok": False, "error": "Refused", "detail": refused, "sent": False}

    def left() -> float:
        return deadline - time.monotonic()

    if left() <= 0:
        return {"ok": False, "error": "DeadlinePassed", "sent": False}
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
    try:
        body = base64.b64decode(spec["body_b64"]) if spec.get("body_b64") else None
        conn.connect()
        if left() <= 0:
            return {"ok": False, "error": "DeadlinePassed", "sent": False}
        sent = None
        conn.request(spec["method"], spec["path"], body=body, headers=spec["headers"])
        sent = True
        if conn.sock is not None:
            conn.sock.settimeout(max(0.05, left()))
        resp = conn.getresponse()
        headers = [(k, v) for k, v in resp.getheaders() if k.lower() != "set-cookie"]
        header_bytes = sum(len(k) + len(v) for k, v in headers)
        total, truncated = 0, False
        digest = hashlib.sha256()
        with open(out_path, "wb") as fh:
            while True:
                if left() <= 0:
                    return {"ok": False, "error": "DeadlinePassed", "sent": True, "partial_bytes": total}
                if conn.sock is not None:
                    conn.sock.settimeout(max(0.05, left()))
                chunk = resp.read(min(CHUNK, max_body + 1 - total))
                if not chunk:
                    break
                if total + len(chunk) > max_body:
                    chunk = chunk[: max_body - total]
                    truncated = True
                fh.write(chunk)
                digest.update(chunk)
                total += len(chunk)
                if truncated:
                    break
            fh.flush()
            os.fsync(fh.fileno())
        return {
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
    except Exception as exc:  # noqa: BLE001 - reported to the supervisor; no credential is in the message
        return {"ok": False, "error": type(exc).__name__, "sent": sent}
    finally:
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
