# ==============================
# run.sh
# ==============================
#!/usr/bin/env bash
set -euo pipefail
APP_DIR="$HOME/.soundsscheduler"
VENV_DIR="$APP_DIR/venv"
export PYTHONPATH="$APP_DIR/repo:$PYTHONPATH"
exec "$VENV_DIR/bin/python" -m app.main