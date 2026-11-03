"""Runs a stage's resume step once the killed worker's task lease has expired, so that the first claim takes it back.
usage: <edition venv python> -I -X utf8 resume_after_lease.py STEP_LABEL LEASE_UNTIL_ISO
"""

import subprocess
import sys
import time
from datetime import UTC, datetime

label, until = sys.argv[1], datetime.fromisoformat(sys.argv[2])
while datetime.now(UTC) < until:
    time.sleep(0.5)
print(f"resume started {datetime.now(UTC).isoformat(timespec='milliseconds')}", flush=True)
raise SystemExit(subprocess.run([sys.executable, "-I", "-X", "utf8", r"C:\w7\tools\live150_run.py", label]).returncode)
