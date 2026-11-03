#!/usr/bin/env bash
# Back to the release installed before the current one (install.sh recorded it in /opt/walmart-collector/
# previous), with the database as it was before the current release's migration:
#
#   sudo bash rollback.sh            # refuses while a walmart-* collection unit runs
#
# The database is restored from the newest backup install.sh took before migrating to the current release
# (/var/backups/walmart-collector/walmart_collector-before-<version>-<commit>-<time>.dump). Runs collected
# after that backup are lost from the database (their stored pages remain under the data folder); copy what
# must be kept first (walmart-cmd export --run ID --out /var/lib/walmart-collector/exports/ID).
set -euo pipefail
APP=/opt/walmart-collector
BACKUPS=/var/backups/walmart-collector
DB=walmart_collector
[ "$(id -u)" = 0 ] || { echo "run as root (sudo)" >&2; exit 1; }
if systemctl list-units --state=active --plain --no-legend 'walmart-*' | grep -v 'walmart-sample-' | grep -q .; then
  echo "a walmart-* unit is running; stop it first (systemctl kill -s SIGTERM walmart-NAME)" >&2
  exit 9
fi
[ -f "$APP/previous" ] || { echo "no previous release recorded" >&2; exit 1; }
prev=$(cat "$APP/previous")
cur=$(readlink -f "$APP/current")
[ -d "$prev" ] || { echo "previous release folder $prev is missing" >&2; exit 1; }
tag=$(basename "$cur")
dump=$(ls -1t "$BACKUPS/$DB-before-$tag-"*.dump 2>/dev/null | head -1 || true)
[ -n "$dump" ] || { echo "no backup taken before $tag" >&2; exit 1; }
echo "restoring $dump (sha256 $(sha256sum "$dump" | cut -d' ' -f1)) and switching to $prev"
# root opens the dump (root-only folder) and hands it to pg_restore on standard input
sudo -u postgres pg_restore --clean --if-exists --single-transaction -d "$DB" <"$dump"
ln -sfn "$prev" "$APP/current.new"
mv -T "$APP/current.new" "$APP/current"
echo "$cur" >"$APP/rolled-back-from"
rm -f "$APP/previous"
/usr/local/bin/walmart-cmd validate-config --check-db >/dev/null
echo "current -> $(readlink -f "$APP/current"); validate-config --check-db: exit 0"
