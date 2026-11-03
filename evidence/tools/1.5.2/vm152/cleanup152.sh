#!/usr/bin/env bash
# Cleanup of the 1.5.2 owner test on Hamza's Azure test VM, 2026-11-01. Removes what this work added: Docker's
# containers, volumes, network and images, then the 166 packages installed for it (Docker, ffmpeg, asciinema and their
# dependencies), Docker's state folders and the docker group they created, asciinema's settings, and the extracted copies
# and tool environment under ~/v152. Keeps ~/v152's logs, backups, ZIPs and archive. The VM's own six databases are not
# touched; their row counts are taken again at the end and compared with those taken before any Docker or collector step.
# The VM stays running.
set -u
V="$HOME/v152"
L="$V/logs/cleanup.log"
DBS="walmart_collector walmart_oxylabs walmart_pubtest walmart_pubtest_oxylabs walmart_pubtest_scrapedo walmart_scrapedo"
exec >> "$L" 2>&1
echo "== cleanup start $(date -u +%FT%TZ)"
echo "== images, before removal"
sudo docker image ls 2>/dev/null | tee "$V/logs/docker_image_sizes.log"
echo "== the test database after the container replays, dumped before its volume is removed"
sudo docker exec v152pg pg_dump -U postgres -Fc walmart_live150 > "$V/replay/walmart_live150_container_after_replays.dump" \
  && sha256sum "$V/replay/walmart_live150_container_after_replays.dump"
echo "== containers"
sudo docker ps -a
ids=$(sudo docker ps -aq); [ -n "$ids" ] && sudo docker rm -f $ids
echo "== volumes and network"
sudo docker volume rm v152data v152pgdata
sudo docker network rm v152net
echo "== images and build cache"
sudo docker image prune -a -f
sudo docker builder prune -a -f
sudo docker system df
echo "== purge of the 166 packages installed for this work"
sudo systemctl stop docker.socket docker containerd 2>/dev/null
sudo DEBIAN_FRONTEND=noninteractive apt-get purge -y $(cat /tmp/pkgs_added_152.txt)
left=0
for p in $(cat /tmp/pkgs_added_152.txt); do
  if dpkg-query -W -f='${db:Status-Abbrev}' "$p" 2>/dev/null | grep -q '^ii'; then echo "STILL INSTALLED: $p"; left=$((left + 1)); fi
done
echo "packages from the list still installed: $left"
sudo rm -rf /var/lib/docker /var/lib/containerd /etc/docker
if getent group docker >/dev/null; then sudo groupdel docker && echo "docker group removed"; fi
rm -rf "$HOME/.config/asciinema"; rmdir "$HOME/.config" 2>/dev/null
rm -rf "$V/castenv" "$V/src" "$V/probe/oxylabs-classic-offline-probe-1.5.2"
echo "== row counts of the VM's six databases, after cleanup"
for d in $DBS; do
  echo "== $d"
  sudo -u postgres psql -At -d "$d" -c "select table_name, (xpath('/row/c/text()', query_to_xml(format('select count(*) as c from %I.%I', table_schema, table_name), false, true, '')))[1]::text from information_schema.tables where table_schema='public' order by 1"
done > "$V/logs/counts_after_cleanup.log"
diff "$V/archive_2ed64b7/logs/counts_before.log" "$V/logs/counts_after_cleanup.log" && echo "row counts unchanged since 2026-11-01T19:25:59Z"
echo "== left on the VM"
command -v docker ffmpeg asciinema || echo "docker, ffmpeg and asciinema: not installed"
systemctl list-timers --all --no-pager | grep -i -E 'walmart|collector' || echo "no timer names the collector"
(sudo crontab -l 2>/dev/null; crontab -l 2>/dev/null) | grep -i -E 'walmart|collector' || echo "no cron entry names the collector"
du -sh "$V"; ls "$V"
df -h / | tail -1
echo "== cleanup end $(date -u +%FT%TZ)"
echo CLEANUP_DONE
