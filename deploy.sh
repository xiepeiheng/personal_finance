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
envsubst < .env.production.template > .env.production
echo "  → backend/.env.production generated"

uv sync
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

pnpm build
echo "  → Frontend built to dist/"

echo ""
echo "=== Deploy complete ==="
echo "Restart the backend service (Gunicorn) in 宝塔面板 to apply changes."
