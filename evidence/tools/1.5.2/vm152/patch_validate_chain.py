from pathlib import Path
p = Path(r"C:\w7\tools\vm152\validate.sh")
t = p.read_bytes().decode("utf-8")
n = t.count("-e PSYCOPG_IMPL=python ")
assert n == 2, n
t = t.replace("-e PSYCOPG_IMPL=python ", "")
old = """  replay)
    step docker_net net_up || exit 1
    replay_chain
    ;;
"""
new = old + """  chain) replay_chain ;;
"""
assert t.count(old) == 1
t = t.replace(old, new)
p.write_bytes(t.encode("utf-8"))
print("patched", n)
