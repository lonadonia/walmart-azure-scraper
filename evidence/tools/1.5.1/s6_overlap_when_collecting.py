"""Stage S6, brief section 1A item 5: the overlap refusal while a run is collecting. Waits until S6's run log shows at
least N collected pages and fewer than the kill's threshold, records the moment, then runs the same `run` command as
step s6_overlap_during_run through the campaign's runner. The step must exit 9 with no provider request. No request is
made here; the runner's log and commands.csv hold the result.
usage: <edition venv python> -I -X utf8 s6_overlap_when_collecting.py N
"""

import glob
import json
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

OUT = Path(r"C:\w7\evidence\live150")


def pages() -> int:
    logs = sorted(glob.glob(str(OUT / "logs" / "*_s6_run.jsonl")))
    if not logs:
        return 0
    return Path(logs[-1]).read_text(encoding="utf-8", errors="replace").count('"event": "PAGE_COLLECTED"')


def main() -> int:
    wanted = int(sys.argv[1])
    deadline = time.monotonic() + 300
    while time.monotonic() < deadline:
        seen = pages()
        if seen >= wanted:
            started = datetime.now(UTC).isoformat(timespec="milliseconds")
            done = subprocess.run(
                [sys.executable, "-I", "-X", "utf8", r"C:\w7\tools\live150_run.py", "s6_overlap_during_run"],
                capture_output=True,
                text=True,
            )
            after = pages()
            record = {
                "started_at": started,
                "ended_at": datetime.now(UTC).isoformat(timespec="milliseconds"),
                "pages_collected_by_s6_when_started": seen,
                "pages_collected_by_s6_when_ended": after,
                "runner_exit": done.returncode,
                "runner_output": done.stdout.strip()[:400],
            }
            (OUT / "s6_overlap_during_run_record.json").write_text(json.dumps(record, indent=1) + "\n", encoding="utf-8")
            print(json.dumps(record, indent=1))
            return done.returncode
        time.sleep(1)
    raise SystemExit("S6 did not reach the page count in 5 minutes")


if __name__ == "__main__":
    raise SystemExit(main())
