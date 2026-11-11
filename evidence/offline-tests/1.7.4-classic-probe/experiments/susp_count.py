"""Experiment: the threads and suspend counts Windows reports for a process created suspended (never resumed), and
for one resumed. Reads each thread's suspend count without changing it (SuspendThread returns the count before,
ResumeThread puts it back).
usage: python -I susp_count.py N
"""

from __future__ import annotations

import ctypes
import subprocess
import sys
import time
from ctypes import wintypes

k = ctypes.WinDLL("kernel32", use_last_error=True)
ntdll = ctypes.WinDLL("ntdll")


class THREADENTRY32(ctypes.Structure):
    _fields_ = [("dwSize", wintypes.DWORD), ("cntUsage", wintypes.DWORD), ("th32ThreadID", wintypes.DWORD),
                ("th32OwnerProcessID", wintypes.DWORD), ("tpBasePri", wintypes.LONG), ("tpDeltaPri", wintypes.LONG),
                ("dwFlags", wintypes.DWORD)]


k.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
k.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
k.Thread32First.argtypes = [wintypes.HANDLE, ctypes.POINTER(THREADENTRY32)]
k.Thread32Next.argtypes = [wintypes.HANDLE, ctypes.POINTER(THREADENTRY32)]
k.OpenThread.restype = wintypes.HANDLE
k.OpenThread.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
k.SuspendThread.restype = wintypes.DWORD
k.SuspendThread.argtypes = [wintypes.HANDLE]
k.ResumeThread.restype = wintypes.DWORD
k.ResumeThread.argtypes = [wintypes.HANDLE]
k.CloseHandle.argtypes = [wintypes.HANDLE]
ntdll.NtResumeProcess.restype = ctypes.c_long
ntdll.NtResumeProcess.argtypes = [wintypes.HANDLE]


def counts(pid: int) -> list[int]:
    snap = k.CreateToolhelp32Snapshot(0x4, 0)
    assert snap and snap != ctypes.c_void_p(-1).value
    out = []
    try:
        e = THREADENTRY32()
        e.dwSize = ctypes.sizeof(e)
        ok = k.Thread32First(snap, ctypes.byref(e))
        while ok:
            if e.th32OwnerProcessID == pid:
                h = k.OpenThread(0x0002, False, e.th32ThreadID)
                assert h
                try:
                    before = k.SuspendThread(h)
                    assert before != 0xFFFFFFFF
                    k.ResumeThread(h)
                finally:
                    k.CloseHandle(h)
                out.append(before)
            ok = k.Thread32Next(snap, ctypes.byref(e))
    finally:
        k.CloseHandle(snap)
    return out


def main() -> int:
    n = int(sys.argv[1])
    exe = getattr(sys, "_base_executable", sys.executable)
    never, resumed = [], []
    for i in range(n):
        p = subprocess.Popen([exe, "-I", "-c", "import time; time.sleep(5)"], creationflags=0x4,
                             stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if i % 2 == 0:
            never.append(tuple(counts(p.pid)))
        else:
            assert ntdll.NtResumeProcess(int(p._handle)) == 0  # type: ignore[attr-defined]
            time.sleep(0.05)
            resumed.append(tuple(counts(p.pid)))
        p.kill()
        p.wait(10)
    from collections import Counter
    print("never resumed:", Counter(never))
    print("resumed (50 ms later):", Counter(resumed))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
