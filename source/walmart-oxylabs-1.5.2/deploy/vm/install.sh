#!/usr/bin/env bash
# walmart-azure-headless on one Ubuntu 24.04 VM (docs/AZURE_VM.md): install, or upgrade to another release.
#
#   sudo bash install.sh SOURCE.tar.gz COMMIT              the core, as the service's current release
#   sudo bash install.sh SOURCE.zip COMMIT EDITION         an edition beside it (docs/EDITIONS.md)
#
# SOURCE.tar.gz is `git archive` of the collector folder with the top folder walmart-azure-headless/; an
# edition's SOURCE.zip is its source ZIP (deploy/build_edition.py; one top folder, its EDITION.json naming
# EDITION). COMMIT is the commit it was made from. The script installs PostgreSQL 16 (local socket and
# localhost only, peer authentication), uv (pinned, checksum verified), the service user `walmart`, and the
# release under /opt/walmart-collector/releases/<version>-<commit>[-<edition>]. It backs the database up
# before migrating it and migrates it with the new release. The core then becomes
# /opt/walmart-collector/current (the previous one is kept for rollback.sh). An edition never touches the
# core's release, environment, database or data: it gets its own database walmart_<edition>, data folder
# /var/lib/walmart-collector/editions/<edition>, environment file /etc/walmart-collector/env.<edition> naming
# its provider's key file only, and the link /opt/walmart-collector/edition-<edition>; its commands run with
# WC_ENV and WC_RELEASE (walmart-cmd, walmart-run). It installs no timer, cron entry or enabled collector
# service, writes no secret (keys are written separately, see AZURE_VM.md) and changes no operating-system
# security control.
set -euo pipefail
umask 022

SRC=${1:?usage: install.sh SOURCE COMMIT [EDITION]}
COMMIT=${2:?usage: install.sh SOURCE COMMIT [EDITION]}
EDITION=${3:-}
UV_VERSION=0.13.1
APP=/opt/walmart-collector
STATE=/var/lib/walmart-collector
ETC=/etc/walmart-collector
BACKUPS=/var/backups/walmart-collector
SVC=walmart
DB=walmart_collector
HERE=$(cd "$(dirname "$0")" && pwd)

log() { printf '%s install: %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*"; }

[ "$(id -u)" = 0 ] || { echo "run as root (sudo)" >&2; exit 1; }
. /etc/os-release
[ "$ID" = ubuntu ] && [ "$VERSION_ID" = 24.04 ] || { echo "Ubuntu 24.04 expected, found $PRETTY_NAME" >&2; exit 1; }
[[ "$COMMIT" =~ ^[0-9a-f]{40}$ ]] || { echo "COMMIT must be a full 40-character commit id" >&2; exit 1; }
if [ -n "$EDITION" ]; then
  [[ "$EDITION" =~ ^(scrapedo|oxylabs)$ ]] || { echo "EDITION: scrapedo or oxylabs" >&2; exit 1; }
  DB=walmart_$EDITION
fi

# 1. Disk and memory
avail_kb=$(df --output=avail -k / | tail -1 | tr -d ' ')
mem_kb=$(awk '/^MemTotal/ {print $2}' /proc/meminfo)
log "disk free on / $((avail_kb / 1024)) MiB; memory $((mem_kb / 1024)) MiB"
[ "$avail_kb" -ge $((5 * 1024 * 1024)) ] || { echo "less than 5 GiB free on /" >&2; exit 1; }
[ "$mem_kb" -ge $((3 * 1024 * 1024)) ] || { echo "less than 3 GiB of memory" >&2; exit 1; }

# 2. PostgreSQL 16 from Ubuntu: it listens on the local socket and localhost only (Ubuntu's default)
if ! dpkg -s postgresql-16 >/dev/null 2>&1; then
  log "installing postgresql-16"
  apt-get update -q
  DEBIAN_FRONTEND=noninteractive apt-get install -y -q postgresql-16 postgresql-client-16
fi
systemctl start postgresql
listen=$(sudo -u postgres psql -tAc "SHOW listen_addresses")
[ "$listen" = localhost ] || { echo "PostgreSQL listen_addresses is '$listen', expected localhost" >&2; exit 1; }

# 3. uv, pinned and checksum verified
if ! /usr/local/bin/uv --version 2>/dev/null | grep -q "^uv $UV_VERSION "; then
  log "installing uv $UV_VERSION"
  tmp=$(mktemp -d)
  url=https://github.com/astral-sh/uv/releases/download/$UV_VERSION/uv-x86_64-unknown-linux-gnu.tar.gz
  curl -fsSL --proto '=https' -o "$tmp/uv.tar.gz" "$url"
  curl -fsSL --proto '=https' -o "$tmp/uv.tar.gz.sha256" "$url.sha256"
  (cd "$tmp" && printf '%s  uv.tar.gz\n' "$(cut -d' ' -f1 uv.tar.gz.sha256)" | sha256sum -c --quiet -)
  tar -xzf "$tmp/uv.tar.gz" -C "$tmp"
  install -m 0755 "$tmp/uv-x86_64-unknown-linux-gnu/uv" /usr/local/bin/uv
  rm -rf "$tmp"
fi

# 4. The service user and the folders: code (root, read-only to the service), state, exports, evidence, logs
id "$SVC" >/dev/null 2>&1 || useradd --system --home-dir "$STATE" --shell /usr/sbin/nologin "$SVC"
install -d -m 0755 -o root -g root "$APP" "$APP/releases"
install -d -m 0750 -o "$SVC" -g "$SVC" "$STATE" "$STATE/data" "$STATE/exports" "$STATE/evidence" "$STATE/logs"
install -d -m 0750 -o root -g "$SVC" "$ETC"
install -d -m 0700 -o "$SVC" -g "$SVC" "$ETC/secrets"
install -d -m 0700 -o root -g root "$BACKUPS"
install -d -m 0700 -o root -g root /var/cache/walmart-collector-uv
DATA=$STATE/data
if [ -n "$EDITION" ]; then
  DATA=$STATE/editions/$EDITION/data
  install -d -m 0750 -o "$SVC" -g "$SVC" "$STATE/editions" "$STATE/editions/$EDITION" "$DATA" \
    "$STATE/editions/$EDITION/exports" "$STATE/editions/$EDITION/evidence"
fi

# 5. The database and its role (peer authentication on the local socket: no password exists)
if [ -z "$(sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname = '$SVC'")" ]; then
  sudo -u postgres createuser --no-superuser --no-createdb --no-createrole "$SVC"
fi
if [ -z "$(sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname = '$DB'")" ]; then
  sudo -u postgres createdb -O "$SVC" "$DB"
  log "database $DB created"
fi

# 6. The release: unpacked, the locked dependencies (uv.lock) on the system's Python 3.12, its build info
unpacked=$(mktemp -d)
trap 'rm -rf "$unpacked"' EXIT
case "$SRC" in
  *.zip) /usr/bin/python3.12 -c 'import sys, zipfile; zipfile.ZipFile(sys.argv[1]).extractall(sys.argv[2])' \
           "$SRC" "$unpacked" ;;
  *) tar -xzf "$SRC" -C "$unpacked" --no-same-owner ;;
esac
tops=("$unpacked"/*)
[ "${#tops[@]}" = 1 ] && [ -d "${tops[0]}" ] || { echo "the source must have one top folder" >&2; exit 1; }
top=${tops[0]}
version=$(sed -n 's/^version = "\(.*\)"$/\1/p' "$top/pyproject.toml")
[ -n "$version" ] || { echo "no version in the source's pyproject.toml" >&2; exit 1; }
if [ -n "$EDITION" ]; then
  [ -f "$top/EDITION.json" ] || { echo "not an edition's source: no EDITION.json" >&2; exit 1; }
  named=$(/usr/bin/python3.12 -c 'import json, sys; print(json.load(open(sys.argv[1]))["edition"])' "$top/EDITION.json")
  [ "$named" = "$EDITION" ] || { echo "the source is the $named edition, not $EDITION" >&2; exit 1; }
  built=$(/usr/bin/python3.12 -c 'import json, sys; print(json.load(open(sys.argv[1]))["source_revision"])' "$top/EDITION.json")
  [ "$built" = "$COMMIT" ] || { echo "the edition was built from $built, not $COMMIT" >&2; exit 1; }
  REL="$APP/releases/$version-${COMMIT:0:12}-$EDITION"
else
  [ ! -f "$top/EDITION.json" ] || { echo "an edition's source: give its EDITION" >&2; exit 1; }
  REL="$APP/releases/$version-${COMMIT:0:12}"
fi
if [ ! -f "$REL/.installed" ]; then
  log "installing release $version (${COMMIT:0:12}${EDITION:+, $EDITION edition}) into $REL"
  rm -rf "$REL"
  install -d -m 0755 "$REL"
  cp -a "$top/." "$REL/"
  chown -R root:root "$REL"
  # The core gets its BUILD_INFO.json here. An edition keeps the one it was built with (EDITION.json records
  # its hash); the source's hash and the installation time go to INSTALL_INFO.json beside it.
  info=BUILD_INFO.json
  [ -z "$EDITION" ] || info=INSTALL_INFO.json
  /usr/bin/python3.12 - "$REL/$info" "$COMMIT" "$(sha256sum "$SRC" | cut -d' ' -f1)" "$EDITION" <<'PY'
import datetime, json, sys
path, commit, source_sha256, edition = sys.argv[1:5]
now = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
info = {"commit": commit, "built_at": now, "source_sha256": source_sha256}
if edition:
    info = {"commit": commit, "edition": edition, "installed_at": now, "source_sha256": source_sha256}
with open(path, "w", encoding="utf-8") as f:
    f.write(json.dumps(info) + "\n")
PY
  (cd "$REL" && UV_PYTHON_DOWNLOADS=never UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy \
    UV_CACHE_DIR=/var/cache/walmart-collector-uv /usr/local/bin/uv sync --frozen --no-dev --python /usr/bin/python3.12)
  /usr/bin/python3.12 -m compileall -q "$REL/src"
  chmod -R go-w "$REL"
  touch "$REL/.installed"
fi
"$REL/.venv/bin/python" -c "import walmart_headless, sys; print('python', sys.version.split()[0], 'walmart_headless', walmart_headless.__version__)"

# 7. The environment of every command (no secret in it: the keys are files in $ETC/secrets). The core's
#    names both key files; an edition's names its provider's only, its database and its data folder.
if [ -n "$EDITION" ]; then
  ENV_FILE=$ETC/env.$EDITION
  if [ "$EDITION" = scrapedo ]; then
    key_line="SCRAPEDO_API_KEY_FILE=$ETC/secrets/scrapedo.env"
  else
    key_line="OXYLABS_WEB_API_KEY_FILE=$ETC/secrets/oxylabs.env"
  fi
  cat >"$ENV_FILE" <<EOF
WALMART_COLLECTOR_CONFIG=$REL/config/collector.yaml
WALMART_COLLECTOR_DATA_DIR=$DATA
WALMART_COLLECTOR_DATABASE_URL=postgresql://$SVC@/$DB?host=/var/run/postgresql
$key_line
PYTHONUNBUFFERED=1
PYTHONDONTWRITEBYTECODE=1
EOF
else
  ENV_FILE=$ETC/env
  cat >"$ENV_FILE" <<EOF
WALMART_COLLECTOR_CONFIG=$APP/current/config/collector.yaml
WALMART_COLLECTOR_DATA_DIR=$DATA
WALMART_COLLECTOR_DATABASE_URL=postgresql://$SVC@/$DB?host=/var/run/postgresql
SCRAPEDO_API_KEY_FILE=$ETC/secrets/scrapedo.env
OXYLABS_WEB_API_KEY_FILE=$ETC/secrets/oxylabs.env
PYTHONUNBUFFERED=1
PYTHONDONTWRITEBYTECODE=1
EOF
fi
chown root:"$SVC" "$ENV_FILE"
chmod 0640 "$ENV_FILE"

# 8. The command wrappers
install -m 0755 "$HERE/walmart-cmd" "$HERE/walmart-run" "$HERE/walmart-sample" /usr/local/bin/

# 9. Back the database up, migrate it with the new release; then the core switches `current`, an edition
#    points its own link at its release
if [ -n "$(sudo -u postgres psql -d "$DB" -tAc "SELECT 1 FROM information_schema.tables WHERE table_name = 'alembic_version'")" ]; then
  dump="$BACKUPS/$DB-before-$version-${COMMIT:0:12}-$(date -u +%Y%m%dT%H%M%SZ).dump"
  sudo -u postgres pg_dump -Fc "$DB" >"$dump"
  chmod 0600 "$dump"
  log "database backup $dump sha256 $(sha256sum "$dump" | cut -d' ' -f1)"
fi
WC_ENV="$ENV_FILE" WC_RELEASE="$REL" /usr/local/bin/walmart-cmd db-upgrade
if [ -n "$EDITION" ]; then
  ln -sfn "$REL" "$APP/edition-$EDITION.new"
  mv -T "$APP/edition-$EDITION.new" "$APP/edition-$EDITION"
  log "edition-$EDITION -> $(readlink -f "$APP/edition-$EDITION"); current unchanged: $(readlink -f "$APP/current" 2>/dev/null || echo none)"
  WC_ENV="$ENV_FILE" WC_RELEASE="$APP/edition-$EDITION" /usr/local/bin/walmart-cmd validate-config --check-db >/dev/null
else
  prev=$(readlink -f "$APP/current" 2>/dev/null || true)
  ln -sfn "$REL" "$APP/current.new"
  mv -T "$APP/current.new" "$APP/current"
  if [ -n "$prev" ] && [ "$prev" != "$REL" ]; then
    echo "$prev" >"$APP/previous"
  fi
  log "current -> $(readlink -f "$APP/current")"
  /usr/local/bin/walmart-cmd validate-config --check-db >/dev/null
fi
log "validate-config --check-db: exit 0"

# 10. Nothing is scheduled
if ls /etc/systemd/system/*walmart*.timer /etc/cron.d/*walmart* 2>/dev/null | grep -q .; then
  echo "a walmart timer or cron entry exists; schedules must stay off" >&2
  exit 1
fi
log "done: no timer or cron entry installed; collection starts only by hand (walmart-run)"
