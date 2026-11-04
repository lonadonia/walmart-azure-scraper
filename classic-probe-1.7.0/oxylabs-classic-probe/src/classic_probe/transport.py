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
"""

from __future__ import annotations

import base64
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.parse
import zlib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from classic_probe import contract, gates

REAP_TIMEOUT_S = 10.0


@dataclass(frozen=True)
class ProviderRequest:
    step: str
    payload: Mapping[str, Any]
    query_string: str = ""  # e.g. type=raw,parsed

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

    def __init__(self, message: str, *, sent: bool | None = None) -> None:
        super().__init__(message)
        self.sent = sent  # False only when the worker proves it never sent the request


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

    def send(self, request: ProviderRequest, allowance_s: float) -> ProviderResponse:
        if allowance_s <= 0:
            raise TransportFailed("no time is left for this request", sent=False)
        scheme, host, port, path = self._target(request)
        self.work_dir.mkdir(parents=True, exist_ok=True)
        fd, part = tempfile.mkstemp(prefix=f"{request.step}-", suffix=".part", dir=self.work_dir)
        os.close(fd)
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
            "out_path": part,
            "loopback_stub": self.loopback_port is not None,
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
            _unlink(part)
            raise TransportFailed(
                f"no answer within {allowance_s:.1f} s: the worker was killed and reaped (the provider may "
                "still run and charge the request)",
                sent=None,
            ) from None
        finally:
            if proc.poll() is None:  # pragma: no cover - communicate returned, so the worker has exited
                proc.kill()
                proc.wait(REAP_TIMEOUT_S)
            self.last_returncode = proc.returncode
        try:
            status = json.loads(out.decode("utf-8").strip().splitlines()[-1])
        except (ValueError, IndexError):
            _unlink(part)
            raise TransportFailed("the worker gave no readable status", sent=None) from None
        if not status.get("ok"):
            _unlink(part)
            sent = status.get("sent")
            raise TransportFailed(
                f"{status.get('error')}: {status.get('detail', '')}".strip(": "),
                sent=False if sent is False else None,
            )
        data = Path(part).read_bytes()[: self.limits.max_body_bytes]
        _unlink(part)
        return ProviderResponse(
            int(status["status"]),
            data,
            {str(k): str(v) for k, v in status.get("headers") or []},
            truncated=bool(status.get("truncated")),
            redirect_location=status.get("redirect_location"),
            elapsed_s=round(time.monotonic() - t0, 3),
        )


def _unlink(path: str) -> None:
    try:
        os.unlink(path)
    except OSError:
        pass
