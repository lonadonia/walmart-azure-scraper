"""Stage S4's forced kill (brief section 1A, S4): once the run's log shows N collected result pages, every process
of the collector installed under C:/w7/live/ed (walmart-collector.exe and the Python it starts) is killed at
once (taskkill /F /T: no signal handler, no checkpoint written at exit), and the kill is recorded with its time,
the pages collected before it and the processes killed. Nothing else is touched.
usage: python -I s4_kill.py N
"""

import glob
import json
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

OUT = Path(r"C:\w7\evidence\live150")
MARK = r"C:\w7\live\ed\walmart-oxylabs-1.5.0"


def collector_pids() -> list[dict]:
    ps = (
        "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*walmart-oxylabs-1.5.0*' -and "
        "$_.CommandLine -like '* run *' } | Select-Object ProcessId,ParentProcessId,Name,CommandLine | ConvertTo-Json"
    )
    out = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True).stdout.strip()
    if not out:
        return []
    d = json.loads(out)
    return d if isinstance(d, list) else [d]


def main() -> None:
    n = int(sys.argv[1])
    deadline = time.monotonic() + 900
    log = None
    while time.monotonic() < deadline:
        logs = sorted(glob.glob(str(OUT / "logs" / "*_s4_run.jsonl")))
        if logs:
            log = Path(logs[-1])
            text = log.read_text(encoding="utf-8", errors="replace")
            pages = text.count('"event": "PAGE_COLLECTED"')
            if pages >= n:
                procs = [p for p in collector_pids() if MARK.lower() in (p.get("CommandLine") or "").lower()]
                at = datetime.now(UTC).isoformat(timespec="milliseconds")
                killed = []
                for p in procs:
                    r = subprocess.run(["taskkill", "/F", "/T", "/PID", str(p["ProcessId"])], capture_output=True,
                                       text=True)
                    killed.append({"pid": p["ProcessId"], "name": p["Name"], "rc": r.returncode,
                                   "out": (r.stdout + r.stderr).strip()[:300]})
                rec = {"killed_at": at, "pages_collected_before_kill": pages, "log": str(log),
                       "method": "taskkill /F /T (forced: no handler, no exit checkpoint)",
                       "processes": [{k: v for k, v in p.items() if k != "CommandLine"} | {"command": (p.get("CommandLine") or "")[:400]} for p in procs],
                       "taskkill": killed}
                (OUT / "s4_kill_record.json").write_text(json.dumps(rec, indent=1) + "\n", encoding="utf-8")
                print(json.dumps(rec, indent=1)[:3000])
                return
        time.sleep(2)
    raise SystemExit(f"no kill: the threshold of {n} pages was not reached in 15 minutes (log {log})")


if __name__ == "__main__":
    main()
