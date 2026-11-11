"""A process and every process it starts, ended together (1.7.2, finding C2; fail-closed on Windows in 1.7.4).

A session's command may start other processes (a request worker, or anything a broken session leaves
behind). 1.7.1 killed the session's tree only when the session overran its time: a session that exited by
itself left its children running, and one of them could still send a request after the supervisor had
returned. A :class:`ProcessTree` is ended whole whenever the session ends, by itself or not:

- on Linux and macOS the command leads a new session and process group; :meth:`ProcessTree.end` sends
  SIGKILL to the whole group, reaps the leader, and waits (bounded) until no process of the group is left.
  A process that left the group on purpose (a new session of its own) is outside this bound; the probe's own
  processes never do that;
- on Windows the command is held by a job object, which every process it starts joins (1.7.4, below).
  :meth:`ProcessTree.end` terminates the job and waits (bounded) until the job's own accounting shows no
  active process. The job is closed with the kill-on-close flag, so a supervisor that dies takes the tree
  with it. A process started for the tree by another service (WMI, the task scheduler) is outside this
  bound; the probe's own processes never do that.

1.7.4 (the client's review of probe 1.7.2 on Windows). 1.7.2 fell back to ``taskkill /T`` when no job object
could be made, and when the command's process could not join the job it resumed the process anyway and fell
back the same way. ``taskkill /T`` finds a process's descendants through their parent's process id, so a child
whose parent had already exited was out of its reach; and once that parent had exited, 1.7.2 could no longer
tell whether anything of the tree was left, yet reported that nothing was left running. Now:

- **nothing runs before the job holds it.** The job is made with kill-on-close and without any breakaway
  limit, both read back from the job. The command's process is created suspended, assigned to the job,
  confirmed a member by ``IsProcessInJob``, and the job's accounting must show that one process and no other.
  Only then is it resumed, so it cannot run its own code, start a process or send anything outside the job;
- **a failure refuses, with no fallback.** If the job cannot be made (no process is created then), or the
  process cannot be assigned, confirmed or resumed, the suspended process is terminated and reaped and the
  job closed before :class:`TreeRefused` is raised. The refusal names the step and says whether the end and
  the reap were confirmed;
- **gone means counted gone.** Whether any process of the tree is left is read only from the tree's own
  account: the job's accounting on Windows, the process group on Linux and macOS. The leading process's exit,
  a ``taskkill`` result or an account that cannot be read is never taken for it. :meth:`ProcessTree.end`
  says ``cleanup``: ``verified`` (the account shows nothing left), ``failed`` (it shows a process left) or
  ``unknown`` (it could not be read), and an unknown stays unknown: ``left_running`` and ``gone`` are then
  None, never False.

Every wait is bounded by the seconds the caller gives: nothing here can hold a supervisor past its end.
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import IO, Any

POLL_S = 0.01
REFUSAL_S = 5.0  # the longest a refused process's end and reap are waited for, unless the caller gives less
VERIFIED, FAILED, UNKNOWN = "verified", "failed", "unknown"


class TreeRefused(RuntimeError):
    """The command was not run: its process tree could not be held (1.7.4). Raised only after any process made
    for it was ended and reaped, or after both were tried: ``terminated`` and ``reaped`` say whether each was
    confirmed, ``pid`` is None when no process was made."""

    def __init__(
        self,
        *,
        stage: str,
        why: str,
        pid: int | None = None,
        terminated: bool | None = None,
        reaped: bool | None = None,
        cleanup: str = VERIFIED,
        basis: str = "",
    ) -> None:
        super().__init__(f"refused before the command ran ({stage}): {why}")
        self.stage, self.why, self.pid = stage, why, pid
        self.terminated, self.reaped = terminated, reaped
        self.cleanup = cleanup
        self.basis = basis or ("no process was created" if pid is None else "")

    def as_dict(self) -> dict[str, Any]:
        return {
            "held_by": None,
            "refused": True,
            "stage": self.stage,
            "why": self.why,
            "process_created": self.pid is not None,
            "pid": self.pid,
            "ran": False,
            "terminated": self.terminated,
            "reaped": self.reaped,
            "cleanup": self.cleanup,
            "basis": self.basis,
        }


if sys.platform == "win32":
    import ctypes
    from ctypes import wintypes

    CREATE_SUSPENDED = 0x00000004
    JOB_OBJECT_LIMIT_BREAKAWAY_OK = 0x00000800
    JOB_OBJECT_LIMIT_SILENT_BREAKAWAY_OK = 0x00001000
    JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000
    JOB_OBJECT_BASIC_ACCOUNTING_INFORMATION_CLASS = 1
    JOB_OBJECT_EXTENDED_LIMIT_INFORMATION_CLASS = 9

    class _IoCounters(ctypes.Structure):
        _fields_ = [
            ("ReadOperationCount", ctypes.c_ulonglong),
            ("WriteOperationCount", ctypes.c_ulonglong),
            ("OtherOperationCount", ctypes.c_ulonglong),
            ("ReadTransferCount", ctypes.c_ulonglong),
            ("WriteTransferCount", ctypes.c_ulonglong),
            ("OtherTransferCount", ctypes.c_ulonglong),
        ]

    class _BasicLimits(ctypes.Structure):
        _fields_ = [
            ("PerProcessUserTimeLimit", ctypes.c_int64),
            ("PerJobUserTimeLimit", ctypes.c_int64),
            ("LimitFlags", wintypes.DWORD),
            ("MinimumWorkingSetSize", ctypes.c_size_t),
            ("MaximumWorkingSetSize", ctypes.c_size_t),
            ("ActiveProcessLimit", wintypes.DWORD),
            ("Affinity", ctypes.c_size_t),
            ("PriorityClass", wintypes.DWORD),
            ("SchedulingClass", wintypes.DWORD),
        ]

    class _ExtendedLimits(ctypes.Structure):
        _fields_ = [
            ("BasicLimitInformation", _BasicLimits),
            ("IoInfo", _IoCounters),
            ("ProcessMemoryLimit", ctypes.c_size_t),
            ("JobMemoryLimit", ctypes.c_size_t),
            ("PeakProcessMemoryUsed", ctypes.c_size_t),
            ("PeakJobMemoryUsed", ctypes.c_size_t),
        ]

    class _Accounting(ctypes.Structure):
        _fields_ = [
            ("TotalUserTime", ctypes.c_int64),
            ("TotalKernelTime", ctypes.c_int64),
            ("ThisPeriodTotalUserTime", ctypes.c_int64),
            ("ThisPeriodTotalKernelTime", ctypes.c_int64),
            ("TotalPageFaultCount", wintypes.DWORD),
            ("TotalProcesses", wintypes.DWORD),
            ("ActiveProcesses", wintypes.DWORD),
            ("TotalTerminatedProcesses", wintypes.DWORD),
        ]

    def _kernel32() -> Any:
        k = ctypes.WinDLL("kernel32", use_last_error=True)
        k.CreateJobObjectW.restype = wintypes.HANDLE
        k.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
        k.SetInformationJobObject.restype = wintypes.BOOL
        k.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
        k.AssignProcessToJobObject.restype = wintypes.BOOL
        k.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
        k.IsProcessInJob.restype = wintypes.BOOL
        k.IsProcessInJob.argtypes = [wintypes.HANDLE, wintypes.HANDLE, ctypes.POINTER(wintypes.BOOL)]
        k.QueryInformationJobObject.restype = wintypes.BOOL
        k.QueryInformationJobObject.argtypes = [
            wintypes.HANDLE,
            ctypes.c_int,
            ctypes.c_void_p,
            wintypes.DWORD,
            ctypes.POINTER(wintypes.DWORD),
        ]
        k.TerminateJobObject.restype = wintypes.BOOL
        k.TerminateJobObject.argtypes = [wintypes.HANDLE, wintypes.UINT]
        k.CloseHandle.restype = wintypes.BOOL
        k.CloseHandle.argtypes = [wintypes.HANDLE]
        return k

    def _resume(proc: subprocess.Popen[bytes]) -> None:
        """Resume a process started suspended (``NtResumeProcess``, as psutil's ``resume`` does)."""
        ntdll = ctypes.WinDLL("ntdll")
        ntdll.NtResumeProcess.restype = ctypes.c_long
        ntdll.NtResumeProcess.argtypes = [wintypes.HANDLE]
        status = ntdll.NtResumeProcess(int(getattr(proc, "_handle")))  # noqa: B009 - Popen's process handle
        if status != 0:
            raise OSError(f"NtResumeProcess failed with status {status & 0xFFFFFFFF:#010x}")

    class _Job:
        """A job object that kills its processes when its last handle closes and lets none break away."""

        def __init__(self, k: Any, handle: int) -> None:
            self.k, self.handle = k, handle

        @classmethod
        def make(cls) -> _Job:
            """A new job object with its limits set and read back (1.7.4). Raises :class:`TreeRefused` (stage
            ``create``) when it cannot be made or its limits are not as set; no process exists then."""
            k = _kernel32()
            handle = k.CreateJobObjectW(None, None)
            if not handle:
                error = ctypes.get_last_error()
                raise TreeRefused(
                    stage="create",
                    why=f"no job object could be made (CreateJobObjectW, Windows error {error})",
                )
            job = cls(k, handle)
            limits = _ExtendedLimits()
            limits.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
            if not k.SetInformationJobObject(
                handle,
                JOB_OBJECT_EXTENDED_LIMIT_INFORMATION_CLASS,
                ctypes.byref(limits),
                ctypes.sizeof(limits),
            ):
                error = ctypes.get_last_error()
                job.close()
                raise TreeRefused(
                    stage="create",
                    why=f"the job object's kill-on-close limit could not be set (Windows error {error})",
                )
            flags = job.limit_flags()
            breakaway = JOB_OBJECT_LIMIT_BREAKAWAY_OK | JOB_OBJECT_LIMIT_SILENT_BREAKAWAY_OK
            if flags is None or not flags & JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE or flags & breakaway:
                job.close()
                shown = "could not be read" if flags is None else f"read back as {flags:#x}"
                raise TreeRefused(
                    stage="create",
                    why=f"the job object's limits {shown}, not kill-on-close without breakaway",
                )
            return job

        def limit_flags(self) -> int | None:
            limits = _ExtendedLimits()
            if not self.k.QueryInformationJobObject(
                self.handle,
                JOB_OBJECT_EXTENDED_LIMIT_INFORMATION_CLASS,
                ctypes.byref(limits),
                ctypes.sizeof(limits),
                None,
            ):
                return None
            return int(limits.BasicLimitInformation.LimitFlags)

        def assign(self, proc: subprocess.Popen[bytes]) -> int:
            """0 once the process has joined the job, else the Windows error (1.7.4: never ignored)."""
            if self.k.AssignProcessToJobObject(self.handle, int(getattr(proc, "_handle"))):  # noqa: B009
                return 0
            return ctypes.get_last_error() or -1

        def holds(self, proc: subprocess.Popen[bytes]) -> bool | None:
            """Whether Windows confirms the process is in this job (``IsProcessInJob``); None if not asked."""
            member = wintypes.BOOL(0)
            if not self.k.IsProcessInJob(int(getattr(proc, "_handle")), self.handle, ctypes.byref(member)):  # noqa: B009
                return None
            return bool(member.value)

        def active(self) -> int | None:
            info = _Accounting()
            if not self.k.QueryInformationJobObject(
                self.handle,
                JOB_OBJECT_BASIC_ACCOUNTING_INFORMATION_CLASS,
                ctypes.byref(info),
                ctypes.sizeof(info),
                None,
            ):
                return None
            return int(info.ActiveProcesses)

        def terminate(self) -> bool:
            return bool(self.k.TerminateJobObject(self.handle, 1))

        def close(self) -> None:
            if self.handle:
                self.k.CloseHandle(self.handle)
                self.handle = 0


def _end_unstarted(
    proc: subprocess.Popen[bytes], job: Any, *, joined: bool, seconds: float
) -> tuple[bool, bool, str, str]:
    """End and reap a process refused before it ran (1.7.4): whether its end and its reap were confirmed, the
    cleanup verdict and what the verdict rests on.

    A process that was never resumed ran nothing and started nothing, so its own end, confirmed by its handle,
    is the end of its tree. One that had joined the job is counted gone only by the job's accounting."""
    until = time.monotonic() + max(0.05, seconds)
    terminated = bool(joined and job.terminate())
    if not terminated:
        try:
            proc.kill()  # TerminateProcess on the suspended process
            terminated = True
        except OSError:
            terminated = False
    try:
        proc.wait(max(0.0, until - time.monotonic()))
        reaped = True
    except subprocess.TimeoutExpired:
        reaped = False
    if not joined:
        cleanup = VERIFIED if reaped else (FAILED if proc.poll() is None else UNKNOWN)
        basis = "the process was created suspended and never resumed; its own end is confirmed by its handle"
        return terminated, reaped, cleanup, basis
    active = job.active()
    while active not in (0, None) and time.monotonic() < until:
        time.sleep(POLL_S)
        active = job.active()
    cleanup = UNKNOWN if active is None else (VERIFIED if active == 0 else FAILED)
    return terminated, reaped, cleanup, "the job object's accounting (active processes)"


class ProcessTree:
    """A command's process and everything it starts. Use :meth:`start`; end it with :meth:`end`."""

    def __init__(self, proc: subprocess.Popen[bytes], job: Any = None, note: str = "") -> None:
        self.proc = proc
        self._job = job
        self.note = note  # how the tree is held: "process group" or "job object (verified ...)"

    @classmethod
    def start(
        cls,
        args: Sequence[str],
        *,
        cwd: Path | None = None,
        env: Mapping[str, str] | None = None,
        stdout: IO[bytes] | int | None = None,
        refusal_s: float = REFUSAL_S,
    ) -> ProcessTree:
        """Start ``args`` as a held process tree. On Windows (1.7.4) raises :class:`TreeRefused`, after ending
        and reaping any process made for it (within ``refusal_s``), when the tree cannot be held."""
        common: dict[str, Any] = {
            "cwd": cwd,
            "env": None if env is None else dict(env),
            "stdin": subprocess.DEVNULL,
            "stdout": stdout,
            "stderr": subprocess.STDOUT if stdout is not None else None,
        }
        if sys.platform == "win32":
            return cls._start_held(args, common, refusal_s)
        return cls(subprocess.Popen(list(args), start_new_session=True, **common), note="process group")

    @classmethod
    def _start_held(cls, args: Sequence[str], common: dict[str, Any], refusal_s: float) -> ProcessTree:
        """Windows (1.7.4): the job first, then the process, suspended, until the job is shown to hold it."""
        if sys.platform == "win32":  # start() calls this only on Windows; mypy checks it for Windows alone
            job = _Job.make()  # TreeRefused (stage "create") before any process exists
            try:
                proc = subprocess.Popen(list(args), creationflags=CREATE_SUSPENDED, **common)
            except BaseException:
                job.close()
                raise
            stage, why, joined = "assign", "", False
            error = job.assign(proc)
            if error:
                why = (
                    "the process could not be assigned to the job object "
                    f"(AssignProcessToJobObject, Windows error {error})"
                )
            else:
                joined, stage = True, "verify"
                member = job.holds(proc)
                active = job.active()
                if member is not True:
                    answer = "could not be asked" if member is None else "says it is not"
                    why = (
                        f"Windows did not confirm the process is in the job object (IsProcessInJob {answer})"
                    )
                elif active != 1:
                    shown = "could not be read" if active is None else f"shows {active} active processes"
                    why = f"the job object's accounting {shown}, not this one process alone"
            if not why:
                try:
                    _resume(proc)
                except OSError as exc:
                    stage, why = "resume", f"the process could not be resumed ({exc})"
                else:
                    return cls(proc, job, note="job object (verified before the process ran)")
            terminated, reaped, cleanup, basis = _end_unstarted(proc, job, joined=joined, seconds=refusal_s)
            job.close()
            raise TreeRefused(
                stage=stage,
                why=why,
                pid=proc.pid,
                terminated=terminated,
                reaped=reaped,
                cleanup=cleanup,
                basis=basis,
            )
        raise TreeRefused(stage="create", why="a job object exists only on Windows")

    @property
    def pid(self) -> int:
        return self.proc.pid

    def wait(self, timeout: float) -> int | None:
        """The leading process's exit code once it has exited, or None when ``timeout`` ran out first."""
        try:
            return self.proc.wait(max(0.0, timeout))
        except subprocess.TimeoutExpired:
            return None

    @property
    def basis(self) -> str:
        """What tells whether the tree has gone (1.7.4): never the leading process alone."""
        if sys.platform == "win32":
            return "the job object's accounting (active processes)"
        return "the process group (a signal 0 to the group)"

    def members_left(self) -> bool | None:
        """Whether any process of the tree still exists, read from the tree's own account: the job's
        accounting on Windows, the process group elsewhere. None when that account cannot be read (1.7.4:
        never guessed from the leading process, which may have exited before its children)."""
        if sys.platform == "win32":
            if self._job is None:
                return None
            active = self._job.active()
            return None if active is None else active > 0
        try:
            os.killpg(self.proc.pid, 0)
        except ProcessLookupError:
            return False
        except PermissionError:
            return True
        except OSError:
            return None
        return True

    def end(self, seconds: float) -> dict[str, Any]:
        """Kill every process of the tree, reap the leader and wait until none is left, all within
        ``seconds``. Returns what happened: whether processes were still there (``left_running``: None when
        that could not be told), whether the tree is gone (``gone``: None when that cannot be told), the
        verdict (``cleanup``: ``verified``, ``failed`` or ``unknown``, 1.7.4), what the verdict rests on
        (``basis``) and any problem."""
        until = time.monotonic() + max(0.0, seconds)
        problems: list[str] = []
        before = self.members_left()
        if sys.platform == "win32":
            if self._job is None:
                problems.append("the tree is no longer held by its job object: it cannot be ended or counted")
            elif not self._job.terminate() and self.members_left() is not False:
                problems.append("the job object could not be terminated")
        else:
            try:
                os.killpg(self.proc.pid, signal.SIGKILL)  # the command leads its own process group
            except ProcessLookupError:
                pass
            except OSError as exc:
                problems.append(f"the process group could not be killed: {type(exc).__name__}")
        reaped = self.wait(until - time.monotonic()) is not None
        if not reaped:
            problems.append("the leading process had not exited when the time to reap it ran out")
        state = self.members_left()
        while state is not False and time.monotonic() < until:
            time.sleep(POLL_S)
            state = self.members_left()
        if state is None:
            cleanup = UNKNOWN
            problems.append(
                f"whether any process of the tree is left could not be told ({self.basis} could not be "
                "read): it is not taken as gone"
            )
        elif state:
            cleanup = FAILED
            problems.append("a process of the tree was still running when the time to end it ran out")
        else:
            cleanup = VERIFIED
        return {
            "held_by": self.note,
            "left_running": before,
            "reaped": reaped,
            "gone": None if state is None else not state,
            "cleanup": cleanup,
            "basis": self.basis,
            "problems": problems,
        }

    def close(self) -> None:
        if self._job is not None:
            self._job.close()
            self._job = None
