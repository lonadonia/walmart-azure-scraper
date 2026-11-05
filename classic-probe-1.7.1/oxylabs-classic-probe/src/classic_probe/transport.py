"""How a request leaves the probe, if it ever does.

:class:`ReplayTransport` answers from saved responses and has no way to reach a network.
:class:`IsolatedHttpTransport` is the only code that can reach Oxylabs. In this build it reaches only a
loopback test stub: the documented endpoint is refused while live mode is disabled (gates.py), here and again
in the worker. Importing this module opens nothing.

1.7.0 corrections (the client's second review):

- C1, redirects: nothing follows a redirect. The worker uses ``http.client``, which has no redirect handling,
  and a 3xx answer comes back as the answer (the campaign then stops, checks.py). The credentials go only to
  the documented scheme, host and port; a request naming any other URL is refused before a worker starts.
- C2, cancellation and bounds: each exchange runs in a child process that the transport kills and reaps at the
  request's deadline (a queue timeout and a daemon thread are not cancellation; a killed process is). The
  body is bounded on success and error alike, decompression is bounded, and every socket wait is clamped to
  the time left. A killed exchange may still have reached the provider: its reservation stays held as unknown.

1.7.1 correction (finding C4): nothing received is deleted. The worker writes each answer under the dispatch's
own number (``ProviderRequest.raw_stem``, given by the campaign: ``dispatch_NNN`` in the campaign's private
folder), with its status beside it, both synced and renamed durably (networker.py). The campaign keeps its
sanitized copy from there; a crash before that copy is kept loses nothing, because the recovery keeps it from
these files (captures.py). A body cut by a deadline, an error or a kill is kept as ``dispatch_NNN.partial``
and reported with its length and SHA-256 (:attr:`TransportFailed.partial`), never as an answer.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import subprocess
import sys
import time
import urllib.parse
import uuid
import zlib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from classic_probe import contract, durable, gates

REAP_TIMEOUT_S = 10.0


@dataclass(frozen=True)
class ProviderRequest:
    step: str
    payload: Mapping[str, Any]
    query_string: str = ""  # e.g. type=raw,parsed
    # 1.7.1 (C4): where the answer is written, by the dispatch's own number (the campaign's private folder)
    raw_stem: str | None = None

    @property
    def url(self) -> str:
        return contract.ENDPOINT + (f"?{self.query_string}" if self.query_string else "")


@dataclass(frozen=True)
class ProviderResponse:
    http_status: int
    body: bytes
    headers: Mapping[str, str] = field(default_factory=dict)
    truncated: bool = False  # the body was cut at the byte limit: never a complete capture
    redirect_location: str | None = None  # recorded, never followed (C1)
    elapsed_s: float = 0.0


@dataclass(frozen=True)
class ResponseLimits:
    max_body_bytes: int = 8_000_000
    max_header_bytes: int = 64_000
    max_decoded_bytes: int = 32_000_000


class Transport(Protocol):
    def send(self, request: ProviderRequest, allowance_s: float) -> ProviderResponse: ...


class TransportFailed(RuntimeError):
    """No HTTP answer. The request may have reached the provider: the remote outcome is unknown."""

    def __init__(
        self, message: str, *, sent: bool | None = None, partial: dict[str, Any] | None = None
    ) -> None:
        super().__init__(message)
        self.sent = sent  # False only when the worker proves it never sent the request
        # 1.7.1 (C4): the part of a body that arrived before the failure, kept on disk: length, SHA-256, file
        self.partial = partial


class BodyTooLarge(ValueError):
    """A body (or its decoding) is above its limit: it is evidence of a truncation, never parsed whole."""


class ReplayTransport:
    """Saved responses, by step, in order. A step with nothing left is an error, never a request."""

    def __init__(self, responses: Mapping[str, Sequence[ProviderResponse]]) -> None:
        self.responses = {k: list(v) for k, v in responses.items()}
        self.dispatched: list[ProviderRequest] = []

    def send(self, request: ProviderRequest, allowance_s: float) -> ProviderResponse:
        self.dispatched.append(request)
        left = self.responses.get(request.step)
        if not left:
            raise TransportFailed(f"the replay holds no response for {request.step}", sent=False)
        return left.pop(0)


def decode_body(response: ProviderResponse, limits: ResponseLimits) -> bytes:
    """The body as bytes to parse, decompressed within ``max_decoded_bytes`` (a compression bomb is refused).
    A truncated body is refused: half a response is never read as a whole one."""
    if response.truncated:
        raise BodyTooLarge("the body was truncated at the byte limit")
    enc = {k.lower(): v for k, v in response.headers.items()}.get("content-encoding", "").strip().lower()
    if enc in ("", "identity"):
        return response.body
    if enc not in ("gzip", "deflate"):
        raise BodyTooLarge(f"unsupported content encoding {enc!r}")
    d = zlib.decompressobj(zlib.MAX_WBITS | 32 if enc == "gzip" else zlib.MAX_WBITS)
    out = d.decompress(response.body, limits.max_decoded_bytes + 1)
    if len(out) > limits.max_decoded_bytes or d.unconsumed_tail:
        raise BodyTooLarge(f"the decoded body is above {limits.max_decoded_bytes} bytes")
    return out


class IsolatedHttpTransport:
    """HTTP Basic authentication over the documented endpoint, one supervised child process per exchange.

    ``loopback_port`` points every request at ``http://127.0.0.1:<port>`` instead (offline tests of the live
    path's mechanics); it is the only target this build allows."""

    def __init__(
        self,
        credentials: gates.Credentials,
        *,
        work_dir: Path,
        limits: ResponseLimits | None = None,
        loopback_port: int | None = None,
        python: str = sys.executable,
    ) -> None:
        if loopback_port is None and not gates.LIVE_ENABLED:
            raise gates.LiveDisabled("live mode is disabled in this build")
        token = f"{credentials.username}:{credentials.password}".encode()
        self._authorization = "Basic " + base64.b64encode(token).decode("ascii")
        self.work_dir = work_dir
        self.limits = limits or ResponseLimits()
        self.loopback_port = loopback_port
        self.python = python
        self.workers_started = 0
        self.workers_killed = 0
        self.last_pid: int | None = None
        self.last_returncode: int | None = None

    def preflight(self, request: ProviderRequest) -> None:
        """Refuse, before anything is sent or marked sent, a request this transport would never send."""
        self._target(request)

    def _target(self, request: ProviderRequest) -> tuple[str, str, int, str]:
        u = urllib.parse.urlsplit(request.url)
        if (
            u.scheme,
            u.hostname,
            u.port or 443,
        ) != contract.ENDPOINT_PARTS or u.path != contract.ENDPOINT_PATH:
            raise TransportFailed(f"refused: {request.url} is not the documented endpoint", sent=False)
        path = u.path + (f"?{u.query}" if u.query else "")
        if self.loopback_port is not None:
            return "http", "127.0.0.1", self.loopback_port, path
        return u.scheme, str(u.hostname), 443, path

    def _stem(self, request: ProviderRequest) -> Path:
        """Where this exchange's files go: the dispatch's own name, or a fresh name in the work folder."""
        if request.raw_stem:
            return Path(request.raw_stem)
        return self.work_dir / f"{request.step}-{uuid.uuid4().hex[:16]}"

    def send(self, request: ProviderRequest, allowance_s: float) -> ProviderResponse:
        if allowance_s <= 0:
            raise TransportFailed("no time is left for this request", sent=False)
        scheme, host, port, path = self._target(request)
        stem = self._stem(request)
        durable.private_dir(stem.parent)
        files = {
            "out_path": stem.with_name(stem.name + ".body.part"),
            "final_path": stem.with_name(stem.name + ".body"),
            "partial_path": stem.with_name(stem.name + ".partial"),
            "status_path": stem.with_name(stem.name + ".status.json"),
        }
        for existing in files.values():
            if existing.exists():  # a dispatch number is used once: its files are never overwritten
                raise TransportFailed(f"refused: {existing.name} already exists", sent=False)
        spec = {
            "method": "POST",
            "scheme": scheme,
            "host": host,
            "port": port,
            "path": path,
            "headers": {
                "Content-Type": "application/json",
                "Accept-Encoding": "identity",
                "Authorization": self._authorization,
            },
            "body_b64": base64.b64encode(json.dumps(request.payload).encode("utf-8")).decode("ascii"),
            "allowance_s": max(0.05, allowance_s - 0.25),  # the worker stops itself a little before its kill
            "max_body_bytes": self.limits.max_body_bytes,
            "max_header_bytes": self.limits.max_header_bytes,
            "loopback_stub": self.loopback_port is not None,
            **{k: os.fspath(v) for k, v in files.items()},
        }
        t0 = time.monotonic()
        proc = subprocess.Popen(
            [self.python, "-I", "-m", "classic_probe.networker"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.workers_started += 1
        self.last_pid = proc.pid
        try:
            out, _err = proc.communicate(json.dumps(spec).encode("utf-8"), timeout=allowance_s)
        except subprocess.TimeoutExpired:
            proc.kill()
            self.workers_killed += 1
            try:
                proc.communicate(timeout=REAP_TIMEOUT_S)
            except subprocess.TimeoutExpired:  # pragma: no cover - a killed process that cannot be reaped
                pass
            raise TransportFailed(
                f"no answer within {allowance_s:.1f} s: the worker was killed and reaped (the provider may "
                "still run and charge the request)",
                sent=None,
                partial=_keep_after_kill(files),
            ) from None
        finally:
            if proc.poll() is None:  # pragma: no cover - communicate returned, so the worker has exited
                proc.kill()
                proc.wait(REAP_TIMEOUT_S)
            self.last_returncode = proc.returncode
        status = _read_status(out, files["status_path"])
        if status is None:
            raise TransportFailed(
                "the worker gave no readable status", sent=None, partial=_keep_after_kill(files)
            )
        if not status.get("ok"):
            sent = status.get("sent")
            raise TransportFailed(
                f"{status.get('error')}: {status.get('detail', '')}".strip(": "),
                sent=False if sent is False else None,
                partial=_described_partial(status, files["partial_path"]),
            )
        final = files["final_path"]
        data = final.read_bytes()[: self.limits.max_body_bytes]
        if hashlib.sha256(data).hexdigest() != status.get("sha256"):
            raise TransportFailed(
                f"the answer on disk ({final.name}) does not match the worker's account of it", sent=None
            )
        return ProviderResponse(
            int(status["status"]),
            data,
            {str(k): str(v) for k, v in status.get("headers") or []},
            truncated=bool(status.get("truncated")),
            redirect_location=status.get("redirect_location"),
            elapsed_s=round(time.monotonic() - t0, 3),
        )


def _read_status(out: bytes, status_path: Path) -> dict[str, Any] | None:
    """The worker's status line, or the copy it wrote to disk when its output was lost."""
    try:
        status = json.loads(out.decode("utf-8").strip().splitlines()[-1])
        if isinstance(status, dict):
            return status
    except (ValueError, IndexError):
        pass
    try:
        status = json.loads(status_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return status if isinstance(status, dict) else None


def _described_partial(status: Mapping[str, Any], partial_path: Path) -> dict[str, Any] | None:
    if not status.get("partial_bytes"):
        return None
    return {
        "bytes": int(status["partial_bytes"]),
        "sha256": str(status.get("partial_sha256")),
        "http_status": status.get("http_status"),
        "error": status.get("error"),
        "file": partial_path.name,
        "complete": False,
    }


def _keep_after_kill(files: Mapping[str, Path]) -> dict[str, Any] | None:
    """A worker killed mid-body leaves its ``.part`` file: what arrived is kept as the dispatch's partial
    body, described by its length and SHA-256 (1.7.1, C4). An empty file holds nothing and is removed."""
    part = files["out_path"]
    try:
        data = part.read_bytes()
    except OSError:
        return None
    if not data:
        _unlink(os.fspath(part))
        return None
    durable.replace(part, files["partial_path"])
    described = {
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "http_status": None,
        "error": "Killed",
        "file": files["partial_path"].name,
        "complete": False,
    }
    durable.write(
        files["status_path"],
        (
            json.dumps(
                {
                    "ok": False,
                    "error": "Killed",
                    "sent": None,
                    "partial_bytes": len(data),
                    "partial_sha256": described["sha256"],
                    "partial_file": True,
                },
                sort_keys=True,
            )
            + "\n"
        ).encode(),
        private=True,
    )
    return described


def _unlink(path: str) -> None:
    try:
        os.unlink(path)
    except OSError:
        pass
