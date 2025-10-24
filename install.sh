# ==============================
# install.sh
# ==============================
#!/usr/bin/env bash
set -euo pipefail

# Usage: curl -fsSL https://raw.githubusercontent.com/<user>/<repo>/main/install.sh | bash
# Or: ./install.sh <git_repo_url>

REPO_URL=${1:-"https://github.com/youruser/SoundsScheduler.git"}
APP_DIR="$HOME/.soundsscheduler"
VENV_DIR="$APP_DIR/venv"

sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip unzip rsync playerctl vlc libvlc-dev libqt6svg6 dos2unix qt6-wayland libxcb-cursor0

mkdir -p "$APP_DIR"
# Download archive (no git required) directly into $APP_DIR, preserving existing data
TMP_DIR=$(mktemp -d)
ARCHIVE_URL=${1:-"https://github.com/youruser/SoundsScheduler/archive/refs/heads/main.zip"}
echo "Downloading $ARCHIVE_URL ..."
curl -L "$ARCHIVE_URL" -o "$TMP_DIR/repo.zip"
unzip -q "$TMP_DIR/repo.zip" -d "$TMP_DIR"
# Find extracted dir (e.g., SoundsScheduler-main)
SRC_DIR=$(find "$TMP_DIR" -maxdepth 1 -type d -name "SoundsScheduler-*" | head -n 1)
if [ -z "$SRC_DIR" ]; then
  echo "ERROR: Could not find extracted source directory." >&2
  exit 1
fi
rsync -a --delete --exclude='.git' "$SRC_DIR/" "$APP_DIR/"
rm -rf "$TMP_DIR"

# Normalize line endings and ensure executable permissions
if command -v dos2unix >/dev/null 2>&1; then
  dos2unix "$APP_DIR/run.sh" || true
  find "$APP_DIR" -type f -name "*.sh" -exec dos2unix {} \; || true
else
  sed -i 's/
$//' "$APP_DIR/run.sh" || true
  find "$APP_DIR" -type f -name "*.sh" -exec sed -i 's/
$//' {} \; || true
fi
chmod 755 "$APP_DIR/run.sh"
find "$APP_DIR" -type f -name "*.sh" -exec chmod 755 {} \; || true

python3 -m venv "$VENV_DIR"
"$VENV_DIR/bin/pip" install --upgrade pip
"$VENV_DIR/bin/pip" install -r "$APP_DIR/requirements.txt"

# If a custom icon is present in repo, copy it to app data dir (prefer SVG, fallback PNG)
if [ -f "$APP_DIR/app/ui/icon.svg" ]; then
  cp "$APP_DIR/app/ui/icon.svg" "$APP_DIR/icon.svg"
elif [ -f "$APP_DIR/app/ui/icon.png" ]; then
  cp "$APP_DIR/app/ui/icon.png" "$APP_DIR/icon.png"
fi

# Determine icon path with extension for .desktop
ICON_DESKTOP="applications-multimedia"
if [ -f "$APP_DIR/icon.svg" ]; then
  ICON_DESKTOP="$APP_DIR/icon.svg"
elif [ -f "$APP_DIR/icon.png" ]; then
  ICON_DESKTOP="$APP_DIR/icon.png"
fi

# Create desktop launcher that calls our wrapper run.sh
install -d "$HOME/.local/share/applications"
cat > "$HOME/.local/share/applications/soundsscheduler.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=SoundsScheduler
Exec=$APP_DIR/run.sh
Icon=$ICON_DESKTOP
Terminal=false
Categories=AudioVideo;Utility;
EOF

# (No symlink needed) We run with PYTHONPATH pointing to the repo via $APP_DIR/run.sh

echo "Installed. Launch via Applications menu or: $APP_DIR/run.sh"