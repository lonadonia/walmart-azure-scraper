#!/usr/bin/env bash
# Owner VM, after the Walmart 1.6.7/1.6.8 work of 2026-11-05: drop this work's own test databases (owned by the role
# walmart_q167 that this work created; never a database of another owner), then record the host's state and compare it
# with the state recorded before the 1.6.7 Docker gate (~/q167/docker/logs/host_before.txt, 2026-11-05T10:49Z).
# Refuses to run while any of this work's processes is still running. Keeps the role walmart_q167 and ~/q167 (the
# campaign dump and the stored pages), and every folder of earlier work. Writes ~/q168d/housekeeping/.
set -u
OUT="$HOME/q168d/housekeeping"
mkdir -p "$OUT"
exec > "$OUT/housekeeping.log" 2>&1
echo "started $(date -u +%FT%TZ)"
if pgrep -af "[b]ash drive168d|[b]ash vm_walk_168d|[b]ash vm_mem_168d|[d]ockerd|[c]ontainerd|[w]almart-collector"; then
  echo "processes of this work still running: refusing"; exit 2
fi
q() { sudo -n -u postgres psql -Atc "$1"; }
echo "== databases before"
q "select datname||' '||pg_get_userbyid(datdba)||' '||pg_size_pretty(pg_database_size(datname)) from pg_database order by 1"
mine=$(q "select datname from pg_database where pg_get_userbyid(datdba) = 'walmart_q167' and datname ~ '^walmart_q16(7|8|8d)_' order by 1")
other=$(q "select count(*) from pg_database where pg_get_userbyid(datdba) = 'walmart_q167' and datname !~ '^walmart_q16(7|8|8d)_'")
[ "$other" = 0 ] || { echo "a database of the role walmart_q167 outside this work's names: refusing"; exit 2; }
for db in $mine; do
  if sudo -n -u postgres dropdb "$db"; then echo "dropped $db"; else echo "FAILED to drop $db"; fi
done
echo "== databases after"
q "select datname||' '||pg_get_userbyid(datdba) from pg_database order by 1"
# the same host_state as vm_docker_168d.sh (the gate's), so the two can be compared line for line
host_state() {
  echo "== packages"; dpkg-query -W -f '${Package} ${Version}\n' | sha256sum; dpkg-query -W | wc -l
  echo "== links"; ip -br link | awk '{print $1, $2}'
  echo "== addresses"; ip -br addr | awk '{print $1, $3, $4}'
  echo "== iptables (filter, nat)"; sudo -n iptables -S | sha256sum; sudo -n iptables -t nat -S | sha256sum
  echo "== ip6tables"; sudo -n ip6tables -S | sha256sum
  echo "== nft ruleset, counters removed"; sudo -n nft list ruleset | sed -E 's/counter packets [0-9]+ bytes [0-9]+/counter/' | sha256sum
  echo "== sysctl"; sysctl net.ipv4.ip_forward net.ipv6.conf.all.forwarding net.bridge.bridge-nf-call-iptables 2>&1
  echo "== apparmor profiles"; sudo -n aa-status 2>/dev/null | sed -n '/profiles are loaded/,/profiles are in complain/p' | sha256sum
  echo "== mounts naming docker, containerd, q167 or q168"; findmnt -rn -o TARGET | grep -E "docker|containerd|q16[78]" || echo none
  echo "== /etc/docker, /var/lib/docker, /var/lib/containerd"; ls -d /etc/docker /var/lib/docker /var/lib/containerd 2>&1
  echo "== /run entries"; sudo -n ls -A /run | sort | tr '\n' ' '; echo
  echo "== /run/containerd, /run/docker (left by the 2026-11-01 test)"; sudo -n ls -A /run/containerd /run/docker 2>&1 | tr '\n' ' '; echo
  echo "== /opt"; ls -A /opt | tr '\n' ' '; echo; sudo -n find /opt/containerd | sort | sha256sum
  echo "== units naming docker or containerd"; systemctl list-units --all --no-pager --plain 2>/dev/null | grep -E "docker|containerd" || echo none
  echo "== processes naming dockerd or containerd"; pgrep -a -f "dockerd|containerd" | grep -v pgrep || echo none
  echo "== groups"; getent group docker || echo "no docker group"
  echo "== databases"; sudo -n -u postgres psql -Atc "select datname||' '||pg_get_userbyid(datdba) from pg_database order by 1"
  echo "== listening sockets"; ss -ltnH | awk '{print $4}' | sort
}
host_state > "$OUT/host_now.txt" 2>&1
echo "== the host now against 2026-11-05T10:49Z (before the 1.6.7 gate)"
diff "$HOME/q167/docker/logs/host_before.txt" "$OUT/host_now.txt" && echo "host state unchanged"
echo "== this work's folders"
du -sh "$HOME/q167" "$HOME/q168" "$HOME/q168d" 2>/dev/null
df -h / | tail -1
free -m | sed -n 2p
echo "ended $(date -u +%FT%TZ)"
