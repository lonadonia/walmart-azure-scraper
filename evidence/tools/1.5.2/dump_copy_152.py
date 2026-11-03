"""pg_dump of the pristine campaign copy in C:/w7/r152b, for the VM's isolated container database. Offline."""
import subprocess, sys
from pathlib import Path
import pgserver
from sqlalchemy.engine import make_url
PGDATA = Path(r"C:\w7\r152b\pgdata")
srv = pgserver.get_server(str(PGDATA), cleanup_mode=None)
url = make_url(srv.get_uri()).set(database="walmart_live150")
bin_ = Path(sys.executable).parent.parent / "Lib" / "site-packages" / "pgserver" / "pginstall" / "bin"
out = r"C:\w7\pack152\vm\campaign_copy.dump"
cmd = [str(bin_ / "pg_dump.exe"), "-Fc", "-f", out, "--no-owner", "--no-privileges", url.render_as_string(hide_password=False)]
subprocess.run(cmd, check=True)
print("dumped", Path(out).stat().st_size)
