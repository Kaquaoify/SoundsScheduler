# ==============================
# install.sh
# ==============================
#!/usr/bin/env bash
set -euo pipefail

# Usage: curl -fsSL https://raw.githubusercontent.com/<user>/<repo>/main/install.sh | bash
# Or: ./install.sh <git_repo_url>

REPO_URL=${1:-"https://github.com/youruser/py-spotify-interrupter.git"}
APP_DIR="$HOME/.py-spotify-interrupter"
VENV_DIR="$APP_DIR/venv"

sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip git playerctl vlc libvlc-dev libqt6svg6

mkdir -p "$APP_DIR"
if [ ! -d "$APP_DIR/repo/.git" ]; then
  rm -rf "$APP_DIR/repo" || true
  git clone "$REPO_URL" "$APP_DIR/repo"
else
  git -C "$APP_DIR/repo" pull --ff-only
fi

python3 -m venv "$VENV_DIR"
"$VENV_DIR/bin/pip" install --upgrade pip
"$VENV_DIR/bin/pip" install -r "$APP_DIR/repo/requirements.txt"

# If a custom icon is present in repo, copy it to app data dir (prefer SVG, fallback PNG)
if [ -f "$APP_DIR/repo/app/ui/icon.svg" ]; then
  cp "$APP_DIR/repo/app/ui/icon.svg" "$APP_DIR/icon.svg"
elif [ -f "$APP_DIR/repo/app/ui/icon.png" ]; then
  cp "$APP_DIR/repo/app/ui/icon.png" "$APP_DIR/icon.png"
fi

cat > "$HOME/.local/share/applications/spotify-interrupter.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Spotify Interrupter
Exec=$VENV_DIR/bin/python -m app.main
Icon=$APP_DIR/icon
Terminal=false
Categories=AudioVideo;Utility;
EOF

# Symlink app into venv site-packages path to allow -m app.main
if [ ! -e "$VENV_DIR/app" ]; then
  ln -s "$APP_DIR/repo/app" "$VENV_DIR/app"
fi

echo "Installed. Launch via Applications menu or: $VENV_DIR/bin/python -m app.main"