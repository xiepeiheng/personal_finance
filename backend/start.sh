#!/usr/bin/env bash
#
# One-click startup script for the personal_finance backend.
#
# What it does:
#   1. Wipes ALL previous log files in backend/logs/
#   2. Ensures the logs/ directory exists
#   3. Starts the Django development server on 127.0.0.1:8000
#
# Usage:
#   cd backend && ./start.sh       # default port 8000
#   cd backend && ./start.sh 8080  # custom port

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="${SCRIPT_DIR}/logs"
PORT="${1:-8000}"

# -------------------------------------------------------------------
# Step 1: Clean old logs
# -------------------------------------------------------------------
if [ -d "${LOG_DIR}" ]; then
    echo "=== Cleaning old logs in ${LOG_DIR} ==="
    find "${LOG_DIR}" -type f \( -name "*.log" -o -name "*.log.*" \) -delete
    echo "=== All previous logs deleted ==="
else
    echo "=== Creating log directory: ${LOG_DIR} ==="
fi

mkdir -p "${LOG_DIR}"

# -------------------------------------------------------------------
# Step 2: Start Django dev server
# -------------------------------------------------------------------
echo "=== Starting Django dev server on 127.0.0.1:${PORT} ==="

# shellcheck disable=SC1091
cd "${SCRIPT_DIR}"
exec python manage.py runserver "127.0.0.1:${PORT}"
