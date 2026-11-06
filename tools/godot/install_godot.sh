#!/usr/bin/env bash
set -euo pipefail

GODOT_VERSION="${GODOT_VERSION:-4.7.2-stable}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_NAME="Godot_v${GODOT_VERSION}_linux.x86_64"
BIN_PATH="${SCRIPT_DIR}/${BIN_NAME}"

if [[ ! -x "${BIN_PATH}" ]]; then
  echo "Downloading ${BIN_NAME}..."
  curl -L -o "${SCRIPT_DIR}/godot4.zip" \
    "https://github.com/godotengine/godot/releases/download/${GODOT_VERSION}/${BIN_NAME}.zip"
  unzip -o "${SCRIPT_DIR}/godot4.zip" -d "${SCRIPT_DIR}/"
  rm -f "${SCRIPT_DIR}/godot4.zip"
  chmod +x "${BIN_PATH}"
fi

ln -sf "${BIN_PATH}" "${SCRIPT_DIR}/godot"
if command -v sudo >/dev/null 2>&1; then
  sudo ln -sf "${BIN_PATH}" /usr/local/bin/godot
  sudo ln -sf "${BIN_PATH}" /usr/local/bin/godot4
fi

"${SCRIPT_DIR}/godot" --version
