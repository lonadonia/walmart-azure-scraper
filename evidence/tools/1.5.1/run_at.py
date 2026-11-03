"""Runs campaign steps at or after a given moment (brief section 1A item 5: a time-separated repeat).
usage: <edition venv python> -I -X utf8 run_at.py ISO_TIME STEP_LABEL [STEP_LABEL...]
"""

import subprocess
import sys
import time
from datetime import UTC, datetime

at = datetime.fromisoformat(sys.argv[1])
while datetime.now(UTC) < at:
    time.sleep(1)
print(f"started {datetime.now(UTC).isoformat(timespec='milliseconds')}", flush=True)
raise SystemExit(subprocess.run([sys.executable, "-I", "-X", "utf8", r"C:\w7\tools\live150_run.py", *sys.argv[2:]]).returncode)
