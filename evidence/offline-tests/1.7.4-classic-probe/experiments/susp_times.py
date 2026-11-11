"""Experiment: what Windows reports for a process created suspended and ended without ever being resumed.

For N rounds: create `python -I -c pass` with CREATE_SUSPENDED, read its cycle time (QueryProcessCycleTime) and
its user and kernel times (GetProcessTimes) BEFORE ending it, then end it (half the rounds through a job object and
TerminateJobObject, half with TerminateProcess) and read them again AFTER. Prints a summary.
usage: python -I susp_times.py N
"""

from __future__ import annotations

import ctypes
import subprocess
import sys
from ctypes import wintypes

k = ctypes.WinDLL("kernel32", use_last_error=True)
k.GetProcessTimes.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4
k.QueryProcessCycleTime.argtypes = [wintypes.HANDLE, ctypes.POINTER(ctypes.c_ulonglong)]
k.CreateJobObjectW.restype = wintypes.HANDLE
k.CreateJobObjectW.argtypes = [wintypes.LPVOID, wintypes.LPCWSTR]
k.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
k.TerminateJobObject.argtypes = [wintypes.HANDLE, wintypes.UINT]
k.CloseHandle.argtypes = [wintypes.HANDLE]
CREATE_SUSPENDED = 0x4


def times(h: int) -> tuple[int, int, int]:
    t = [wintypes.FILETIME() for _ in range(4)]
    assert k.GetProcessTimes(h, *(ctypes.byref(x) for x in t))
    cyc = ctypes.c_ulonglong(0)
    assert k.QueryProcessCycleTime(h, ctypes.byref(cyc))
    kern = (t[2].dwHighDateTime << 32) | t[2].dwLowDateTime
    user = (t[3].dwHighDateTime << 32) | t[3].dwLowDateTime
    return cyc.value, kern, user


def main() -> int:
    n = int(sys.argv[1])
    exe = getattr(sys, "_base_executable", sys.executable)
    rows = []
    for i in range(n):
        p = subprocess.Popen([exe, "-I", "-c", "pass"], creationflags=CREATE_SUSPENDED,
                             stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        h = int(p._handle)  # type: ignore[attr-defined]
        via_job = i % 2 == 0
        job = None
        if via_job:
            job = k.CreateJobObjectW(None, None)
            assert job and k.AssignProcessToJobObject(job, h)
        before = times(h)
        if via_job:
            assert k.TerminateJobObject(job, 1)
        else:
            p.kill()
        p.wait(10)
        after = times(h)
        if job:
            k.CloseHandle(job)
        rows.append((via_job, before, after, p.returncode))
    def count(pred):
        return sum(1 for r in rows if pred(r))
    print("rounds", n)
    print("before end: cycles>0", count(lambda r: r[1][0] > 0), "kernel>0", count(lambda r: r[1][1] > 0),
          "user>0", count(lambda r: r[1][2] > 0))
    print("after end:  cycles>0", count(lambda r: r[2][0] > 0), "kernel>0", count(lambda r: r[2][1] > 0),
          "user>0", count(lambda r: r[2][2] > 0))
    print("after end, user>0 by way: job", count(lambda r: r[0] and r[2][2] > 0), "terminate",
          count(lambda r: (not r[0]) and r[2][2] > 0))
    print("max before:", max(r[1] for r in rows), "max user after:", max(r[2][2] for r in rows))
    print("examples with user>0 after:", [(r[0], r[1], r[2], r[3]) for r in rows if r[2][2] > 0][:5])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
