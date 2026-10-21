#!/bin/sh
# Brickarr container entrypoint (*arr / LinuxServer conventions).
# - Applies UMASK first, so every folder and file created afterwards honours it.
# - Applies the timezone from TZ.
# - Adjusts the brickarr uid/gid to the requested PUID/PGID.
# - Creates missing folders. Owns /config and the folders it creates itself;
#   never a recursive chown of the library or cache (they hold the user's files).
# - Runs Alembic migrations on every start.
# - Drops privileges via gosu and exec's the CMD as the brickarr user.

set -eu

PUID="${PUID:-1000}"
PGID="${PGID:-1000}"
TZ="${TZ:-Etc/UTC}"
UMASK="${UMASK:-022}"

CONFIG_DIR="${BRICKARR_CONFIG_DIR:-/config}"
LIBRARY_DIR="${BRICKARR_LIBRARY_DIR:-/library}"
CACHE_DIR="${BRICKARR_CACHE_DIR:-${LIBRARY_DIR}}"

case "${UMASK}" in
    [0-7][0-7][0-7] | [0-7][0-7][0-7][0-7]) umask "${UMASK}" ;;
    *) echo "brickarr: UMASK '${UMASK}' is not an octal mask such as 022 or 002 — refusing to start." >&2; exit 1 ;;
esac

# Timezone. /etc/localtime may be bind-mounted read-only; then TZ alone applies.
if [ -f "/usr/share/zoneinfo/${TZ}" ]; then
    ln -snf "/usr/share/zoneinfo/${TZ}" /etc/localtime 2>/dev/null || true
    echo "${TZ}" > /etc/timezone 2>/dev/null || true
fi

# Re-align the brickarr user/group with the requested PUID/PGID.
current_uid=$(id -u brickarr)
current_gid=$(id -g brickarr)

if [ "${current_gid}" != "${PGID}" ]; then
    groupmod -o -g "${PGID}" brickarr
fi
if [ "${current_uid}" != "${PUID}" ]; then
    usermod  -o -u "${PUID}" brickarr
fi

# Create a missing folder and own it; leave an existing one exactly as it is.
ensure_dir() {
    if [ ! -d "$1" ]; then
        mkdir -p "$1"
        chown brickarr:brickarr "$1"
    fi
}

ensure_dir "${CONFIG_DIR}"
ensure_dir "${CONFIG_DIR}/logs"
ensure_dir "${LIBRARY_DIR}"
ensure_dir "${CACHE_DIR}"

# /config is Brickarr's own (settings, SQLite database, logs), so all of it
# follows PUID/PGID.
chown -R brickarr:brickarr "${CONFIG_DIR}"

# Run Alembic from /app where alembic.ini lives.
cd /app
echo "brickarr: running database migrations…"
if ! gosu brickarr alembic upgrade head; then
    echo "brickarr: migrations failed — refusing to start." >&2
    exit 1
fi

echo "brickarr: starting as PUID=${PUID} PGID=${PGID} UMASK=${UMASK} TZ=${TZ}"
exec gosu brickarr "$@"
