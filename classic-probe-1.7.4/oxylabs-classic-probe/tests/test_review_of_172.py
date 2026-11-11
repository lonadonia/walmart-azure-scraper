"""The client's review of probe 1.7.2's process supervision on Windows, kept as tests (1.7.4).

1.7.2 fell back to ``taskkill /T`` when no job object could be made, and when the session's process could not
join one it resumed the process anyway and fell back the same way. ``taskkill /T`` finds descendants through
their parent's process id, so a child whose parent had exited was out of its reach; and with the parent gone,
1.7.2 could not tell whether anything of the tree was left, yet reported nothing left running and no problem.

Each test named ``test_w_...`` was first run against the frozen code of probe 1.7.2 (the reviewed delivery),
with this file copied in, and failed there by its output; 1.7.4 makes it pass. A test named
``..._control_...`` passes on both: the first reproduces, on Windows itself, the limitation behind 1.7.2's
fallback (a parent that exits leaves its child running, and ``taskkill /T`` cannot reach the child); the
second pins how a working job object ends a child whose parent exited first.

Failures are forced at the Windows API boundary only: one kernel32 function at a time (``CreateJobObjectW``,
``AssignProcessToJobObject``, ``IsProcessInJob``, or the job's accounting once the session runs) answers as
Windows answers a failure, and every other call is Windows' own. On Linux the same unreadable count is forced
on the process group's signal 0. The processes are real; a child tells it runs by writing a file (the
handshake); and every process a test starts is ended by the test's own cleanup, even when the test fails,
after its start time is checked, so a reused process id is never touched.

OFFLINE: the only connection a test process could make is to a stub on 127.0.0.1, which counts them.
"""

from __future__ import annotations

import errno
import json
import os
import signal
import subprocess
import sys
import time
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

import pytest

from classic_probe import proctree, supervisor
from tests import loopback_stub as stub
from tests.test_c2_c4_reproduction import ROOT, campaign_files, drill

WINDOWS = sys.platform == "win32"
BASE = getattr(sys, "_base_executable", sys.executable)  # the interpreter itself, not a venv's launcher
TOLERANCE_S = 0.5  # supervisor.TOLERANCE_S, kept as a number so the reviewed code can run these tests
LATE_S = 3.0  # how long a child waits before it connects: well past the end of its tree
HARD_END_S = 30.0
GOOD = json.dumps({"results": [{"status_code": 200, "content": {}}]}).encode()
ERROR_ACCESS_DENIED = 5
STILL_ACTIVE = 259

only_windows = pytest.mark.skipif(
    not WINDOWS,
    reason="job objects and taskkill exist only on Windows; the Linux tree (a process group) is ended by the "
    "tests here that run on both",
)

# A process's start time, which a reused process id cannot share: written by each test process about itself,
# and read by the test about a process id before it says anything about it or ends it.
IDENTITY = r"""
import os, sys

def identity(pid=None):
    if sys.platform == "win32":
        import ctypes
        from ctypes import wintypes
        k = ctypes.WinDLL("kernel32", use_last_error=True)
        k.OpenProcess.restype = wintypes.HANDLE
        k.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        k.GetCurrentProcess.restype = wintypes.HANDLE
        k.GetProcessTimes.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4
        k.CloseHandle.argtypes = [wintypes.HANDLE]
        h = k.GetCurrentProcess() if pid is None else k.OpenProcess(0x1000, False, pid)
        if not h:
            return None
        try:
            t = [wintypes.FILETIME() for _ in range(4)]
            if not k.GetProcessTimes(h, *(ctypes.byref(x) for x in t)):
                return None
            return f"{t[0].dwHighDateTime}:{t[0].dwLowDateTime}"
        finally:
            if pid is not None:
                k.CloseHandle(h)
    try:
        with open(f"/proc/{'self' if pid is None else pid}/stat", "rb") as f:
            return f.read().rsplit(b")", 1)[1].split()[19].decode()
    except OSError:
        return None
"""

SESSION = (
    IDENTITY
    + r"""
import subprocess, time
marker, child, ready, port, late_s = sys.argv[1:6]
with open(marker, "w") as f:
    f.write(f"{os.getpid()} {identity()}")
subprocess.Popen(
    [sys.executable, "-I", child, ready, port, late_s],
    stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
)
end = time.monotonic() + 30
while not os.path.exists(ready):  # the handshake: the child has written that it runs
    if time.monotonic() > end:
        sys.exit(5)
    time.sleep(0.01)
sys.exit(0)  # the parent exits first; its child keeps running
"""
)

CHILD = (
    IDENTITY
    + r"""
import socket, time
ready, port, late_s = sys.argv[1], int(sys.argv[2]), float(sys.argv[3])
with open(ready + ".tmp", "w") as f:
    f.write(f"{os.getpid()} {identity()}")
os.replace(ready + ".tmp", ready)
time.sleep(late_s)
try:
    with socket.create_connection(("127.0.0.1", port), 5) as s:  # a dispatch, as a request worker's
        s.sendall(b"POST /v1/queries HTTP/1.1\r\nHost: late\r\nContent-Length: 0\r\n\r\n")
        time.sleep(1.0)
except OSError:
    pass
time.sleep(30)  # a bounded life: it ends by itself even if every cleanup failed
"""
)

_ns: dict[str, Any] = {}
exec(IDENTITY, _ns)  # the same code the test processes run about themselves
identity: Callable[[int | None], str | None] = _ns["identity"]


def alive(pid: int, ident: str) -> bool:
    """Whether the process ``pid`` that started at ``ident`` still runs, asked of the system itself."""
    if identity(pid) != ident:
        return False  # gone, or another process now has the id
    if WINDOWS:
        import ctypes
        from ctypes import wintypes

        k = ctypes.WinDLL("kernel32", use_last_error=True)
        k.OpenProcess.restype = wintypes.HANDLE
        k.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        k.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
        k.CloseHandle.argtypes = [wintypes.HANDLE]
        h = k.OpenProcess(0x1000, False, pid)
        if not h:
            return False
        try:
            code = wintypes.DWORD()
            return bool(k.GetExitCodeProcess(h, ctypes.byref(code))) and code.value == STILL_ACTIVE
        finally:
            k.CloseHandle(h)
    try:
        with open(f"/proc/{pid}/stat", "rb") as f:
            return f.read().rsplit(b")", 1)[1].split()[0] not in (b"Z", b"X")
    except OSError:
        return False


def end_process(pid: int, ident: str) -> None:
    """The test's own cleanup: end ``pid`` only if it is still the process that started at ``ident``."""
    if WINDOWS:
        import ctypes
        from ctypes import wintypes

        k = ctypes.WinDLL("kernel32", use_last_error=True)
        k.OpenProcess.restype = wintypes.HANDLE
        k.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        k.GetProcessTimes.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4
        k.TerminateProcess.argtypes = [wintypes.HANDLE, wintypes.UINT]
        k.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        k.CloseHandle.argtypes = [wintypes.HANDLE]
        h = k.OpenProcess(0x0001 | 0x1000 | 0x00100000, False, pid)  # terminate, query, synchronize
        if not h:
            return
        try:
            t = [wintypes.FILETIME() for _ in range(4)]
            same = k.GetProcessTimes(h, *(ctypes.byref(x) for x in t)) and (
                f"{t[0].dwHighDateTime}:{t[0].dwLowDateTime}" == ident
            )
            if same:  # checked through the handle that ends it: the id cannot change in between
                k.TerminateProcess(h, 1)
                k.WaitForSingleObject(h, 5000)
        finally:
            k.CloseHandle(h)
        return
    if identity(pid) == ident:
        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass


def cpu_times_100ns(proc: subprocess.Popen[bytes]) -> tuple[int, int]:
    """The kernel and user time Windows has charged to a process, from its own handle.

    Read before a process is ended: both are 0 for a process that has never run. After its end they prove
    nothing either way: Windows may charge one clock tick of user time (156,250 x 100 ns) to a process that
    was created suspended and never resumed when it is terminated (measured on this workstation: 10 of
    300)."""
    import ctypes
    from ctypes import wintypes

    k = ctypes.WinDLL("kernel32", use_last_error=True)
    k.GetProcessTimes.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4
    t = [wintypes.FILETIME() for _ in range(4)]
    assert k.GetProcessTimes(int(getattr(proc, "_handle")), *(ctypes.byref(x) for x in t))  # noqa: B009
    return (t[2].dwHighDateTime << 32) | t[2].dwLowDateTime, (t[3].dwHighDateTime << 32) | t[3].dwLowDateTime


def suspend_counts(pid: int) -> list[int]:
    """Each thread of ``pid`` with the suspend count Windows holds for it, read without changing it
    (``SuspendThread`` returns the count before, ``ResumeThread`` puts it back).

    A process created suspended and never resumed has one thread, suspended once: ``[1]``. Once resumed, its
    count is 0 and the loader starts more threads (measured: ``[1]`` 100 of 100, and ``[0, 0, 0, 0]`` 100 of
    100 50 ms after a resume)."""
    import ctypes
    from ctypes import wintypes

    class Entry(ctypes.Structure):
        _fields_ = [
            ("dwSize", wintypes.DWORD),
            ("cntUsage", wintypes.DWORD),
            ("th32ThreadID", wintypes.DWORD),
            ("th32OwnerProcessID", wintypes.DWORD),
            ("tpBasePri", wintypes.LONG),
            ("tpDeltaPri", wintypes.LONG),
            ("dwFlags", wintypes.DWORD),
        ]

    k = ctypes.WinDLL("kernel32", use_last_error=True)
    k.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    k.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
    k.Thread32First.argtypes = [wintypes.HANDLE, ctypes.POINTER(Entry)]
    k.Thread32Next.argtypes = [wintypes.HANDLE, ctypes.POINTER(Entry)]
    k.OpenThread.restype = wintypes.HANDLE
    k.OpenThread.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    k.SuspendThread.restype = wintypes.DWORD
    k.SuspendThread.argtypes = [wintypes.HANDLE]
    k.ResumeThread.restype = wintypes.DWORD
    k.ResumeThread.argtypes = [wintypes.HANDLE]
    k.CloseHandle.argtypes = [wintypes.HANDLE]
    snap = k.CreateToolhelp32Snapshot(0x00000004, 0)  # TH32CS_SNAPTHREAD
    assert snap and snap != ctypes.c_void_p(-1).value, ctypes.get_last_error()
    counts: list[int] = []
    try:
        entry = Entry()
        entry.dwSize = ctypes.sizeof(entry)
        more = k.Thread32First(snap, ctypes.byref(entry))
        while more:
            if entry.th32OwnerProcessID == pid:
                h = k.OpenThread(0x0002, False, entry.th32ThreadID)  # THREAD_SUSPEND_RESUME
                assert h, ctypes.get_last_error()
                try:
                    before = k.SuspendThread(h)
                    assert before != 0xFFFFFFFF, ctypes.get_last_error()
                    k.ResumeThread(h)
                finally:
                    k.CloseHandle(h)
                counts.append(int(before))
            more = k.Thread32Next(snap, ctypes.byref(entry))
    finally:
        k.CloseHandle(snap)
    return counts


class Scene:
    """A session that starts a child and exits once the child runs, and what a test needs to observe it and
    to clean it up."""

    def __init__(self, folder: Path, server: stub.Stub) -> None:
        folder.mkdir()
        self.server = server
        self.marker = folder / "session_ran.txt"
        self.ready = folder / "child_runs.txt"
        self.session = folder / "session.py"
        self.session.write_text(SESSION, encoding="utf-8")
        child = folder / "child.py"
        child.write_text(CHILD, encoding="utf-8")
        self.command = [
            BASE,
            "-I",
            str(self.session),
            str(self.marker),
            str(child),
            str(self.ready),
            str(server.port),
            str(LATE_S),
        ]
        self.seen: list[tuple[int, str]] = []

    def _read(self, path: Path) -> tuple[int, str] | None:
        try:
            pid, ident = path.read_text(encoding="utf-8").split()
        except (OSError, ValueError):
            return None
        entry = (int(pid), ident)
        if entry not in self.seen:
            self.seen.append(entry)
        return entry

    def child(self) -> tuple[int, str] | None:
        return self._read(self.ready)

    def parent(self) -> tuple[int, str] | None:
        return self._read(self.marker)

    def created(self, made: list[subprocess.Popen[bytes]]) -> list[subprocess.Popen[bytes]]:
        return [p for p in made if str(self.session) in " ".join(map(str, p.args))]  # type: ignore[arg-type]

    def cleanup(self) -> None:
        self.parent()
        self.child()
        for pid, ident in self.seen:
            if alive(pid, ident):
                end_process(pid, ident)


@pytest.fixture
def scene(tmp_path: Path) -> Iterator[Scene]:
    with stub.Stub(stub.hang) as server:
        made = Scene(tmp_path / "scene", server)
        try:
            yield made
        finally:
            made.cleanup()  # on failure too: no test leaves a process behind


class FaultyKernel32:
    """kernel32 as Windows gives it, but for one function that answers as Windows answers a failure: a zero
    result with an error code, or, for ``IsProcessInJob``, a successful call that says "not a member"."""

    def __init__(self, real: Any, fault: str) -> None:
        self._real, self.fault = real, fault
        self.armed = fault != "accounting"  # the accounting fault starts once the session runs
        self.calls: list[str] = []

    def __getattr__(self, name: str) -> Any:
        return getattr(self._real, name)

    def _failed(self, name: str) -> int:
        import ctypes

        self.calls.append(f"{name}: forced failure")
        ctypes.set_last_error(ERROR_ACCESS_DENIED)
        return 0

    def CreateJobObjectW(self, *args: Any) -> Any:
        if self.fault == "create":
            return self._failed("CreateJobObjectW")
        return self._real.CreateJobObjectW(*args)

    def AssignProcessToJobObject(self, *args: Any) -> Any:
        if self.fault == "assign":
            return self._failed("AssignProcessToJobObject")
        return self._real.AssignProcessToJobObject(*args)

    def IsProcessInJob(self, process: Any, job: Any, member: Any) -> Any:
        if self.fault == "verify":
            self.calls.append("IsProcessInJob: forced answer, not a member")
            member._obj.value = 0
            return 1
        return self._real.IsProcessInJob(process, job, member)

    def QueryInformationJobObject(self, job: Any, info_class: int, *rest: Any) -> Any:
        if self.fault == "accounting" and self.armed and info_class == 1:
            return self._failed("QueryInformationJobObject(accounting)")
        return self._real.QueryInformationJobObject(job, info_class, *rest)


class _OsWithUnreadableGroup:
    """``os`` as it is, but a signal 0 to a process group fails once armed (Linux: an unreadable count)."""

    def __init__(self) -> None:
        self.armed = False

    def __getattr__(self, name: str) -> Any:
        return getattr(os, name)

    def killpg(self, pgid: int, sig: int) -> None:
        if sig == 0 and self.armed:
            raise OSError(errno.EIO, "forced: the process group cannot be asked")
        os.killpg(pgid, sig)


def force(monkeypatch: pytest.MonkeyPatch, fault: str) -> list[Any]:
    """Make one step of holding or counting the tree fail (see the module's docstring). Returns the fault
    objects, for their record of what was forced."""
    faults: list[Any] = []
    if fault == "unreadable-count" and not WINDOWS:
        proxy = _OsWithUnreadableGroup()
        monkeypatch.setattr(proctree, "os", proxy)
        faults.append(proxy)
    else:
        real = proctree._kernel32  # type: ignore[attr-defined]
        kind = "accounting" if fault == "unreadable-count" else fault

        def faulty() -> FaultyKernel32:
            k = FaultyKernel32(real(), kind)
            faults.append(k)
            return k

        monkeypatch.setattr(proctree, "_kernel32", faulty)
    if fault == "unreadable-count":  # armed once the tree runs, so its start is Windows' (or Linux') own
        real_start = proctree.ProcessTree.start.__func__  # type: ignore[attr-defined]

        def start(cls: type, *args: Any, **kwargs: Any) -> Any:
            tree = real_start(cls, *args, **kwargs)
            for f in faults:
                f.armed = True
            return tree

        monkeypatch.setattr(proctree.ProcessTree, "start", classmethod(start))
    return faults


def record_processes(monkeypatch: pytest.MonkeyPatch) -> list[subprocess.Popen[bytes]]:
    """Every process the code under test creates through subprocess, kept for the test to examine."""
    made: list[subprocess.Popen[bytes]] = []

    class Recorded(subprocess.Popen):  # type: ignore[type-arg]
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args, **kwargs)
            made.append(self)

    monkeypatch.setattr(proctree.subprocess, "Popen", Recorded)
    return made


def show(facts: dict[str, Any]) -> None:
    """Print what a test found, whole, so a failure's output shows every fact it rests on."""
    print("FACTS " + json.dumps(facts, sort_keys=True, default=str))


def supervise(scene: Scene, tmp_path: Path) -> tuple[supervisor.SupervisedSession, float]:
    manifest, out, _ = campaign_files(tmp_path)
    t0 = time.monotonic()
    session = supervisor.run_session(
        scene.command,
        hard_end_s=HARD_END_S,
        manifest=manifest,
        out_dir=out,
        retailer="walmart",
        cwd=ROOT,
    )
    return session, time.monotonic() - t0


def after_refusal(
    scene: Scene,
    session: supervisor.SupervisedSession,
    made: list[subprocess.Popen[bytes]],
    faults: list[Any],
) -> dict[str, Any]:
    """What happened, read once a running child would have connected: from the files, the stub and the
    system, not from the supervisor's own account (which is reported beside them)."""
    time.sleep(LATE_S + 1.5)
    child = scene.child()
    created = scene.created(made)
    return {
        "session_ran": scene.marker.exists(),
        "child_started": child is not None,
        "child_alive_after_the_supervisor_returned": bool(child and alive(*child)),
        "connections_to_the_stub": len(scene.server.connections),
        "session_processes_created": len(created),
        "session_processes_still_running": [p.pid for p in created if p.poll() is None],
        "forced": [c for f in faults for c in f.calls],
        "refused": getattr(session, "refused", None),
        "status": getattr(session, "status", None),
        "returncode": session.returncode,
        "problems": session.problems,
        "tree": session.tree,
    }


# -- the limitation behind 1.7.2's fallback, on Windows itself ----------------------------------------------


@only_windows
def test_control_a_child_outlives_its_exited_parent_and_taskkill_tree_cannot_reach_it(scene: Scene) -> None:
    """No job object: the parent starts a child, waits until the child says it runs, and exits. The child
    runs on, and ``taskkill /F /T`` on the parent cannot reach it. (The parent's handle stays open in this
    test, so its id cannot be given to another process before taskkill names it.)"""
    parent = subprocess.Popen(
        scene.command, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    code = parent.wait(30)
    child = scene.child()
    outlived = bool(child and alive(*child))
    done = subprocess.run(
        ["taskkill", "/F", "/T", "/PID", str(parent.pid)], capture_output=True, timeout=30, check=False
    )
    time.sleep(0.5)
    left = bool(child and alive(*child))
    said = done.stdout.decode("utf-8", "replace") + done.stderr.decode("utf-8", "replace")
    facts = {
        "parent_exit_code": code,
        "child": child,
        "child_alive_after_its_parent_exited": outlived,
        "taskkill_tree_returncode": done.returncode,
        "taskkill_tree_said": said.strip(),
        "child_alive_after_taskkill_tree": left,
    }
    show(facts)
    assert code == 0, f"the parent did not exit after its child's handshake: {facts}"
    assert child is not None, f"the child never wrote that it runs: {facts}"
    assert outlived, f"the child did not outlive its parent, so nothing was reproduced: {facts}"
    assert left, f"taskkill /T reached the child after all: {facts}"
    assert done.returncode != 0, facts  # the parent is gone, so taskkill finds no tree to walk
    end_process(*child)
    assert not alive(*child), "the test's own cleanup could not end the child"


# -- the job object: made and shown to hold the process before it runs, or a refusal -------------------------


@only_windows
def test_w_no_job_object_means_a_refusal_and_nothing_of_the_session_runs(
    scene: Scene, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    faults = force(monkeypatch, "create")
    made = record_processes(monkeypatch)
    session, _elapsed = supervise(scene, tmp_path)
    facts = after_refusal(scene, session, made, faults)
    show(facts)
    assert not facts["session_ran"] and not facts["child_started"], facts
    assert facts["forced"] == ["CreateJobObjectW: forced failure"], facts
    assert facts["connections_to_the_stub"] == 0, facts
    assert facts["session_processes_created"] == 0, facts  # no job, so no process is even created
    assert facts["refused"] is True and facts["status"] == "refused" and facts["returncode"] is None, facts
    assert session.tree["stage"] == "create" and session.tree["process_created"] is False, facts
    assert "no job object could be made" in session.problems[0], facts
    assert session.evidence == {"accepted": False, "why": "not read: the session was refused before it ran"}
    assert session.recovery == {}, facts  # nothing ran, so there is nothing to recover


@only_windows
@pytest.mark.parametrize(
    ("fault", "says"),
    [
        ("assign", "could not be assigned to the job object"),
        ("verify", "did not confirm the process is in the job object"),
    ],
)
def test_w_a_process_the_job_does_not_hold_is_ended_suspended_and_refused(
    scene: Scene, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fault: str, says: str
) -> None:
    faults = force(monkeypatch, fault)
    made = record_processes(monkeypatch)
    # Windows' own view of the session's process just before the refusal ends it, and every resume asked for
    seen: list[dict[str, Any]] = []
    resumed: list[int] = []
    real_resume = getattr(proctree, "_resume", None)
    real_end = getattr(proctree, "_end_unstarted", None)  # 1.7.4; 1.7.2 has none
    if real_resume is not None:

        def counting_resume(proc: subprocess.Popen[bytes]) -> None:
            resumed.append(proc.pid)
            real_resume(proc)

        monkeypatch.setattr(proctree, "_resume", counting_resume)
    if real_end is not None:

        def observed_end(proc: subprocess.Popen[bytes], *args: Any, **kwargs: Any) -> Any:
            kernel, user = cpu_times_100ns(proc)
            seen.append(
                {
                    "threads_suspend_counts": suspend_counts(proc.pid),
                    "kernel_100ns": kernel,
                    "user_100ns": user,
                }
            )
            return real_end(proc, *args, **kwargs)

        monkeypatch.setattr(proctree, "_end_unstarted", observed_end)
    session, _elapsed = supervise(scene, tmp_path)
    facts = after_refusal(scene, session, made, faults)
    facts["before_its_end"] = seen
    facts["resumed"] = len(resumed)
    show(facts)
    assert not facts["session_ran"] and not facts["child_started"], facts
    assert facts["connections_to_the_stub"] == 0, facts
    assert facts["forced"], facts
    assert facts["refused"] is True and facts["status"] == "refused" and facts["returncode"] is None, facts
    assert says in session.problems[0] and session.tree["stage"] == fault, facts
    # The process made for the session was never resumed, and was ended and reaped before the refusal. Just
    # before its end Windows showed it as created: one thread, still suspended once, no time charged.
    assert facts["resumed"] == 0, facts
    assert seen == [{"threads_suspend_counts": [1], "kernel_100ns": 0, "user_100ns": 0}], facts
    [proc] = scene.created(made)
    assert proc.poll() is not None, facts  # it has exited (asked through its own handle)
    assert session.tree["terminated"] is True and session.tree["reaped"] is True, facts
    assert session.tree["cleanup"] == "verified" and session.recovery == {}, facts


# -- the end of a held tree --------------------------------------------------------------------------------


def test_control_a_child_whose_parent_exited_first_is_ended_with_the_tree(
    scene: Scene, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A working job object (a process group on Linux). The session's process exits as soon as its child
    runs. When the supervisor starts to end the tree the parent has exited and the child is running (both
    checked independently); once the end returns, within its own time, the child has gone, and nothing
    connects afterwards."""
    seen: dict[str, Any] = {}
    real_end = proctree.ProcessTree.end

    def end(self: proctree.ProcessTree, seconds: float) -> dict[str, Any]:
        child = scene.child()
        seen.update(
            parent_exited=self.proc.poll() is not None,
            child=child,
            child_alive_before=bool(child and alive(*child)),
            seconds=seconds,
            started=time.monotonic(),
        )
        result = real_end(self, seconds)
        seen.update(returned=time.monotonic(), child_alive_after=bool(child and alive(*child)))
        return result

    monkeypatch.setattr(proctree.ProcessTree, "end", end)
    session, elapsed = supervise(scene, tmp_path)
    child = scene.child()
    gone_at_return = child is not None and not alive(*child)
    time.sleep(LATE_S + 1.5)  # past the moment the child would have connected
    facts = {
        **seen,
        "gone_when_the_supervisor_returned": gone_at_return,
        "connections_to_the_stub": len(scene.server.connections),
        "elapsed_s": elapsed,
        "returncode": session.returncode,
        "tree": session.tree,
        "problems": session.problems,
    }
    show(facts)
    assert session.returncode == 0 and not session.killed, facts
    assert seen["parent_exited"] and seen["child_alive_before"], facts  # alive before the cleanup
    assert not seen["child_alive_after"] and gone_at_return, facts  # gone after it, checked independently
    assert seen["returned"] - seen["started"] <= seen["seconds"] + TOLERANCE_S, facts  # within its time
    assert elapsed < HARD_END_S + TOLERANCE_S, facts
    assert facts["connections_to_the_stub"] == 0, facts
    assert session.tree["gone"] is True and session.tree["left_running"] is True, facts


def test_w_a_cleanup_that_cannot_be_told_is_never_reported_as_done(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The session ends by itself, exit code 0, with its own complete evidence. Then the tree's count
    cannot be read (Windows: the job's accounting; Linux: the process group). The supervisor must not say
    the tree has gone or that nothing was left: the unknown stays unknown, the evidence is not taken, a
    recovery runs and its manifest names the cleanup."""
    faults = force(monkeypatch, "unreadable-count")
    manifest, out, _ = campaign_files(tmp_path)
    with stub.Stub(stub.respond(200, GOOD)) as s:
        session = supervisor.run_session(
            drill(manifest, out, "loopback", str(s.port)),
            hard_end_s=HARD_END_S,
            manifest=manifest,
            out_dir=out,
            retailer="walmart",
            cwd=ROOT,
        )
    facts = {
        "forced": [c for f in faults for c in getattr(f, "calls", ["killpg(group, 0): forced failure"])][:3],
        "returncode": session.returncode,
        "status": getattr(session, "status", None),
        "tree": session.tree,
        "evidence": session.evidence,
        "problems": session.problems,
        "recovery_ran": bool(session.recovery),
    }
    show(facts)
    assert session.returncode == 0 and not session.killed, facts
    assert session.tree.get("cleanup") == "unknown", facts
    assert session.tree["gone"] is None and session.tree["left_running"] is None, facts  # never False
    assert facts["status"] == "cleanup-unknown", facts
    assert session.evidence.get("accepted") is False, facts
    assert any("could not be told" in p for p in session.problems), facts
    assert not any("killed with it" in p for p in session.problems), facts
    recovered = json.loads((out / "campaign_evidence.recovered.json").read_text("utf-8"))
    assert recovered["complete"] is False and recovered.get("session_tree_cleanup") == "unknown", recovered
    assert "not verified gone (cleanup unknown)" in recovered["ended_by"], recovered


def test_w_a_session_is_ok_only_once_its_tree_is_counted_gone(tmp_path: Path) -> None:
    manifest, out, _ = campaign_files(tmp_path)
    with stub.Stub(stub.respond(200, GOOD)) as s:
        session = supervisor.run_session(
            drill(manifest, out, "loopback", str(s.port)),
            hard_end_s=HARD_END_S,
            manifest=manifest,
            out_dir=out,
            retailer="walmart",
            cwd=ROOT,
        )
    facts = {
        "status": getattr(session, "status", None),
        "tree": session.tree,
        "evidence": session.evidence,
        "problems": session.problems,
    }
    show(facts)
    assert facts["status"] == "ok" and session.recovery == {}, facts
    assert session.tree.get("cleanup") == "verified" and session.tree["gone"] is True, facts
    expected = "job object's accounting" if WINDOWS else "process group"
    assert expected in session.tree.get("basis", ""), facts  # never the leading process's own exit
    if WINDOWS:
        assert session.tree["held_by"] == "job object (verified before the process ran)", facts
