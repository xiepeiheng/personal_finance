#!/usr/bin/env bash
#
# Deploy script — run on the server after pushing to GitHub.
#
#   cd /opt/personal_finance/personal_finance
#   ./deploy.sh
#
# Secrets are read from /opt/personal_finance/personal_finance.env
# (NOT committed to git). Copy personal_finance.env.example and fill it in.
#
# Runtime layout:
#   systemd unit  deploy/personal-finance.service -> /etc/systemd/system/
#   service user  www
#   process       gunicorn (backend/gunicorn_conf.py) on 127.0.0.1:8013
#   logs          journald (gunicorn) + backend/logs/*.log (Django, rotating)

set -euo pipefail

SERVICE="personal-finance"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SECRETS_FILE="/opt/personal_finance/personal_finance.env"
BACKEND_DIR="${PROJECT_DIR}/backend"
FRONTEND_DIR="${PROJECT_DIR}/frontend"
WEBROOT="/www/wwwroot/xph.silyahuukou.cn/personal_finance"

echo "=== Pulling latest code ==="
cd "${PROJECT_DIR}"
git pull --ff-only

# -------------------------------------------------------------------
# Backend
# -------------------------------------------------------------------
echo "=== Setting up backend ==="

if [ ! -f "${SECRETS_FILE}" ]; then
    echo "ERROR: ${SECRETS_FILE} not found. Create it first:"
    echo "  cp ${PROJECT_DIR}/personal_finance.env.example ${SECRETS_FILE}"
    echo "  vim ${SECRETS_FILE}   # fill in real values"
    exit 1
fi

# Generate backend/.env.production from the template + secrets.
set -a; source "${SECRETS_FILE}"; set +a
cd "${BACKEND_DIR}"
envsubst < .env.production.template > /tmp/env_production
sudo mv /tmp/env_production .env.production
sudo chown www:www .env.production
echo "  → backend/.env.production generated"

# Keep the venv on the shared, world-readable interpreter (/opt/uv-python).
# An interpreter under /root or /home/<user> is not executable by www.
export UV_PYTHON_INSTALL_DIR="${UV_PYTHON_INSTALL_DIR:-/opt/uv-python}"

uv sync --frozen
echo "  → Python dependencies up to date"

# The service runs as www, but gunicorn/SQLite only need to write to the
# database, the logs and the media directory. Keep the code owned by the
# deploy user; grant www write access on the rest.
sudo mkdir -p "${BACKEND_DIR}/logs" "${BACKEND_DIR}/media"
sudo chown -R www:www "${BACKEND_DIR}/logs" "${BACKEND_DIR}/media"
[ -f "${BACKEND_DIR}/db.sqlite3" ] && sudo chown www:www "${BACKEND_DIR}/db.sqlite3"
# SQLite creates its journal next to the database file, so the directory
# itself must be writable by www as well.
sudo chgrp www "${BACKEND_DIR}"
sudo chmod 775 "${BACKEND_DIR}"

uv run python manage.py migrate --noinput
echo "  → Migrations applied"

# -------------------------------------------------------------------
# Frontend
# -------------------------------------------------------------------
echo "=== Building frontend ==="

cd "${FRONTEND_DIR}"

set -a; source "${SECRETS_FILE}"; set +a
envsubst < .env.production.template > .env.production
echo "  → frontend/.env.production generated"

pnpm install
echo "  → Node dependencies up to date"

pnpm build-prod
echo "  → Frontend built to dist/"

echo "  → Copying to ${WEBROOT} ..."
sudo cp -r dist/* "${WEBROOT}/"
sudo chown -R www:www "${WEBROOT}/"
echo "  → Web root updated"

# -------------------------------------------------------------------
# Service
# -------------------------------------------------------------------
echo "=== Restarting ${SERVICE} ==="

if ! systemctl cat "${SERVICE}" >/dev/null 2>&1; then
    echo "  → unit not installed yet, installing deploy/${SERVICE}.service"
    sudo cp "${PROJECT_DIR}/deploy/${SERVICE}.service" /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable "${SERVICE}"
fi

sudo systemctl restart "${SERVICE}"
sleep 2
systemctl --no-pager --lines=5 status "${SERVICE}" || true

echo ""
echo "=== Deploy complete ==="
