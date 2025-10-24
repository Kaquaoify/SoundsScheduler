# ==============================
# run.sh
# ==============================
#!/usr/bin/env bash
set -euo pipefail
APP_DIR="$HOME/.soundsscheduler"
VENV_DIR="$APP_DIR/venv"
cd "$APP_DIR"
export PYTHONPATH="$APP_DIR${PYTHONPATH:+:$PYTHONPATH}"
# Force X11/XWayland for broader compatibility (avoids Wayland plugin issues)
export QT_QPA_PLATFORM=${QT_QPA_PLATFORM:-xcb}
exec "$VENV_DIR/bin/python" -m app.main