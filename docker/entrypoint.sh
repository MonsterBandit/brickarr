#!/bin/sh
# Brickarr container entrypoint.
# - Adjusts the brickarr uid/gid to the requested PUID/PGID (*arr convention).
# - Ensures /config and /storage exist and are owned by the runtime user.
# - Applies the timezone from TZ.
# - Runs Alembic migrations on every start.
# - Drops privileges via gosu and exec's the CMD as the brickarr user.

set -eu

PUID="${PUID:-1000}"
PGID="${PGID:-1000}"
TZ="${TZ:-Etc/UTC}"

CONFIG_DIR="${BRICKARR_CONFIG_DIR:-/config}"
STORAGE_DIR="${BRICKARR_STORAGE_DIR:-/storage}"

# Timezone
if [ -f "/usr/share/zoneinfo/${TZ}" ]; then
    ln -snf "/usr/share/zoneinfo/${TZ}" /etc/localtime
    echo "${TZ}" > /etc/timezone
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

# Make sure the persistent volumes exist and are owned correctly.
mkdir -p "${CONFIG_DIR}" "${CONFIG_DIR}/logs" "${STORAGE_DIR}"
chown -R brickarr:brickarr "${CONFIG_DIR}" "${STORAGE_DIR}" /app

# Run Alembic from /app where alembic.ini lives.
cd /app
echo "brickarr: running database migrations…"
if ! gosu brickarr alembic upgrade head; then
    echo "brickarr: migrations failed — refusing to start." >&2
    exit 1
fi

echo "brickarr: starting as PUID=${PUID} PGID=${PGID} TZ=${TZ}"
exec gosu brickarr "$@"
