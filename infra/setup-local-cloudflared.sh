#!/usr/bin/env bash
# setup-local-cloudflared.sh — Install cloudflared on macOS.
#
# This is only needed for SSH-through-tunnel or private network access.
# The public HTTPS endpoints (e.g. https://gpu.alexkreidler.com) work
# from any machine without cloudflared installed.
set -euo pipefail

if command -v cloudflared &> /dev/null; then
  echo "cloudflared already installed: $(cloudflared --version)"
  exit 0
fi

if [[ "$(uname)" == "Darwin" ]]; then
  if ! command -v brew &> /dev/null; then
    echo "ERROR: Homebrew not found. Install from https://brew.sh"
    exit 1
  fi
  echo "==> Installing cloudflared via Homebrew..."
  brew install cloudflared
else
  echo "==> Installing cloudflared for Linux..."
  curl -sL https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb -o /tmp/cloudflared.deb
  sudo dpkg -i /tmp/cloudflared.deb
fi

echo "Installed: $(cloudflared --version)"
echo ""
echo "cloudflared is now available. For most use cases you don't need to run"
echo "it locally — just access the tunnel endpoints via their public URLs:"
echo "  https://gpu.alexkreidler.com/v1/models"
