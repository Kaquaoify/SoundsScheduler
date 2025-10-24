# ==============================
# run.sh
# ==============================
#!/usr/bin/env bash
set -euo pipefail
APP_DIR="$HOME/.soundsscheduler"
VENV_DIR="$APP_DIR/venv"
exec "$VENV_DIR/bin/python" -m app.main