# ==============================
# install.sh
# ==============================
#!/usr/bin/env bash
set -euo pipefail

# Usage: curl -fsSL https://raw.githubusercontent.com/<user>/<repo>/main/install.sh | bash
# Or: ./install.sh <zip_url_or_leave_empty_for_default>

APP_DIR="$HOME/.soundsscheduler"
VENV_DIR="$APP_DIR/venv"

# Detect architecture (amd64 vs arm64, etc.)
ARCH=$(dpkg --print-architecture || echo unknown)

# Hard stop on non-amd64 (e.g., Raspberry Pi ARM)
if [ "$ARCH" != "amd64" ]; then
  echo "[SoundsScheduler] Architecture $ARCH détectée (ARM/Raspberry Pi)."
  echo "[SoundsScheduler] Impossible d'utiliser cette app sur ARM. Nettoyage et fin de l'installation."
  # Clean anything that might exist already
  rm -rf "$APP_DIR" || true
  rm -f "$HOME/.local/share/applications/soundsscheduler.desktop" || true
  sudo rm -f /etc/apt/sources.list.d/spotify.list /etc/apt/keyrings/spotify.gpg || true
  exit 0
fi

sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip unzip rsync playerctl vlc libvlc-dev libqt6svg6 dos2unix qt6-wayland libxcb-cursor0

# --- Spotify installation policy ---
# - amd64: try Snap first, then APT repo fallback.
# - non‑amd64 (Raspberry Pi, etc.): SKIP Spotify installation and inform the user to use 'web_api' mode in the app.
if ! command -v spotify >/dev/null 2>&1; then
  if [ "$ARCH" = "amd64" ]; then
    # Prefer snap
    if command -v snap >/dev/null 2>&1; then
      echo "Installing Spotify via snap (amd64)..."
      sudo snap install spotify || true
    fi
    # APT fallback on amd64 only
    if ! command -v spotify >/dev/null 2>&1; then
      echo "Installing Spotify via APT repository (amd64 only)..."
      sudo install -d /etc/apt/keyrings || true
      if ! sudo test -f /etc/apt/keyrings/spotify.gpg; then
        if curl -fsSL https://download.spotify.com/debian/pubkey_7A3A762FAFD4A51F.gpg | sudo gpg --dearmor -o /etc/apt/keyrings/spotify.gpg; then
          echo "Imported Spotify key (official URL)."
        else
          echo "Official key fetch failed, trying keyserver for NO_PUBKEY issues..."
          sudo rm -f /etc/apt/keyrings/spotify.gpg || true
          for KEY in C85668DF69375001 7A3A762FAFD4A51F; do
            if sudo gpg --keyserver keyserver.ubuntu.com --recv-keys "$KEY"; then
              sudo gpg --export "$KEY" | sudo gpg --dearmor -o /etc/apt/keyrings/spotify.gpg && break
            fi
          done
        fi
      fi
      echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/spotify.gpg] http://repository.spotify.com stable non-free" | \
        sudo tee /etc/apt/sources.list.d/spotify.list >/dev/null || true
      if sudo apt-get update; then
        sudo apt-get install -y spotify-client || true
      else
        echo "APT update failed for Spotify repo. Cleaning up to avoid future warnings..."
        sudo rm -f /etc/apt/sources.list.d/spotify.list || true
        sudo rm -f /etc/apt/keyrings/spotify.gpg || true
        sudo apt-get update || true
      fi
    fi
  else
    echo "[SoundsScheduler] Architecture $ARCH detected (ex: Raspberry Pi). Skipping Spotify installation."
    echo "[SoundsScheduler] Astuce: dans l'app, choisissez 'Contrôle Spotify' = 'web_api' pour piloter un appareil Spotify Connect."
  fi
fi

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
  sed -i 's/\r$//' "$APP_DIR/run.sh" || true
  find "$APP_DIR" -type f -name "*.sh" -exec sed -i 's/\r$//' {} \; || true
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