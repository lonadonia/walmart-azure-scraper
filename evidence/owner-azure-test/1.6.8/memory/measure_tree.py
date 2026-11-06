"""Run a command and measure it (Linux): wall time; the peak of the summed resident memory (VmRSS) of the command's
whole process tree, sampled every 0.25 s from /proc; the largest single process; the most processes and threads seen
at once; the kernel's peak resident size of the largest process the command left (getrusage RUSAGE_CHILDREN, which
is exact, not sampled); and the lowest MemAvailable of the host during the run. Writes a JSON line to the file
named first. Standard library only.

usage: python3 measure_tree.py OUT.json -- command args...
"""

from __future__ import annotations

import json
import os
import resource
import subprocess
import sys
import threading
import time
from pathlib import Path


def tree(root: int) -> list[int]:
    kids: dict[int, list[int]] = {}
    for d in os.listdir("/proc"):
        if not d.isdigit():
            continue
        try:
            with open(f"/proc/{d}/stat", encoding="ascii", errors="replace") as f:
                ppid = int(f.read().rsplit(")", 1)[1].split()[1])
        except (OSError, ValueError, IndexError):
            continue
        kids.setdefault(ppid, []).append(int(d))
    out, todo = [], [root]
    while todo:
        p = todo.pop()
        out.append(p)
        todo.extend(kids.get(p, []))
    return out


def status(pid: int) -> tuple[int, int]:
    rss = threads = 0
    try:
        with open(f"/proc/{pid}/status", encoding="ascii", errors="replace") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    rss = int(line.split()[1])
                elif line.startswith("Threads:"):
                    threads = int(line.split()[1])
    except OSError:
        pass
    return rss, threads


def available_kb() -> int:
    with open("/proc/meminfo", encoding="ascii") as f:
        for line in f:
            if line.startswith("MemAvailable:"):
                return int(line.split()[1])
    return -1


def main(argv: list[str]) -> int:
    out = Path(argv[0])
    cmd = argv[2:] if argv[1] == "--" else argv[1:]
    peak = {"tree_rss_kb": 0, "single_rss_kb": 0, "processes": 0, "threads": 0, "min_available_kb": available_kb()}
    samples = 0
    t0 = time.monotonic()
    started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    proc = subprocess.Popen(cmd)
    stop = threading.Event()

    def sample() -> None:
        nonlocal samples
        while not stop.is_set():
            pids = tree(proc.pid)
            stats = [status(p) for p in pids]
            total = sum(r for r, _ in stats)
            peak["tree_rss_kb"] = max(peak["tree_rss_kb"], total)
            peak["single_rss_kb"] = max(peak["single_rss_kb"], max((r for r, _ in stats), default=0))
            peak["processes"] = max(peak["processes"], len(pids))
            peak["threads"] = max(peak["threads"], sum(t for _, t in stats))
            peak["min_available_kb"] = min(peak["min_available_kb"], available_kb())
            samples += 1
            stop.wait(0.25)

    th = threading.Thread(target=sample, daemon=True)
    th.start()
    rc = proc.wait()
    stop.set()
    th.join()
    wall = time.monotonic() - t0
    ru = resource.getrusage(resource.RUSAGE_CHILDREN)
    rec = {"command": cmd, "exit": rc, "started_at": started,
           "ended_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "wall_seconds": round(wall, 1),
           "samples": samples, "sample_interval_s": 0.25, **peak,
           "maxrss_kb_largest_child_getrusage": ru.ru_maxrss,
           "user_cpu_s": round(ru.ru_utime, 1), "system_cpu_s": round(ru.ru_stime, 1)}
    out.write_text(json.dumps(rec) + "\n", encoding="utf-8")
    print(json.dumps(rec))
    return rc


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
