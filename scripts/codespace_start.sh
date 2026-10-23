#!/usr/bin/env bash
# Démarre Huntboard avec les données fictives de démonstration (Codespaces / devcontainer).
set -e
cd "$(dirname "$0")/.."
DATA="${HUNTBOARD_DATA_DIR:-/workspaces/huntboard-demo}"
if [ ! -f "$DATA/huntboard.sqlite3" ]; then
  pip install -q -r app/backend/requirements.txt
  HUNTBOARD_DATA_DIR="$DATA" python scripts/demo_data.py
fi
echo "Huntboard : http://localhost:8000 (onglet Ports > Huntboard > Open in Browser)"
cd app/backend
exec env HUNTBOARD_DATA_DIR="$DATA" python -m uvicorn huntboard.main:app --host 0.0.0.0 --port 8000
