# ==============================
# run.sh
# ==============================
#!/usr/bin/env bash
set -euo pipefail
APP_DIR="$HOME/.soundsscheduler"
VENV_DIR="$APP_DIR/venv"
export PYTHONPATH="$APP_DIR/repo:$PYTHONPATH"
cd "$APP_DIR"
export PYTHONPATH="$APP_DIR:$PYTHONPATH"
exec "$VENV_DIR/bin/python" -m app.main
