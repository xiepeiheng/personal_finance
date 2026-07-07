#!/usr/bin/env bash
#
# Deploy script — run on the server after pushing to GitHub.
# Usage: ./deploy.sh
#
# Secrets are read from /opt/personal_finance/personal_finance.env
# (NOT committed to git). Edit that file with real values.

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SECRETS_FILE="/opt/personal_finance/personal_finance.env"
BACKEND_DIR="${PROJECT_DIR}/backend"
FRONTEND_DIR="${PROJECT_DIR}/frontend"

echo "=== Pulling latest code ==="
cd "${PROJECT_DIR}"
git pull

# Deploy as xph, gunicorn runs as www — need to swap ownership
sudo chown -R xph:xph "${BACKEND_DIR}"

# -------------------------------------------------------------------
# Backend
# -------------------------------------------------------------------
echo "=== Setting up backend ==="

# Load secrets and generate .env.production
if [ ! -f "${SECRETS_FILE}" ]; then
    echo "ERROR: ${SECRETS_FILE} not found. Create it first:"
    echo "  cp /opt/personal_finance/personal_finance.env.example /opt/personal_finance/personal_finance.env"
    echo "  vim /opt/personal_finance/personal_finance.env   # fill in real values"
    exit 1
fi
set -a; source "${SECRETS_FILE}"; set +a

cd "${BACKEND_DIR}"
envsubst < .env.production.template > /tmp/env_production
sudo mv /tmp/env_production .env.production
sudo chown www:www .env.production
echo "  → backend/.env.production generated"

uv sync --extra dev
echo "  → Python dependencies up to date"

uv run python manage.py migrate
echo "  → Migrations applied"

# -------------------------------------------------------------------
# Frontend
# -------------------------------------------------------------------
echo "=== Building frontend ==="

cd "${FRONTEND_DIR}"

# Load secrets for VITE_ vars
set -a; source "${SECRETS_FILE}"; set +a
envsubst < .env.production.template > .env.production
echo "  → frontend/.env.production generated"

pnpm install
echo "  → Node dependencies up to date"

pnpm build-prod
echo "  → Frontend built to dist/"

# Copy to web root (Nginx serves from here)
WEBROOT="/www/wwwroot/xph.silyahuukou.cn/personal_finance"
echo "  → Copying to ${WEBROOT} ..."
sudo cp -r dist/* "${WEBROOT}/"
sudo chown -R www:www "${WEBROOT}/"
echo "  → Web root updated"

# Restore logs ownership for gunicorn (runs as www)
sudo mkdir -p "${BACKEND_DIR}/logs"
sudo chown -R www:www "${BACKEND_DIR}/logs"

echo ""
echo "=== Deploy complete ==="
