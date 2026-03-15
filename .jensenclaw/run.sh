#!/usr/bin/env bash
# 🦀 You found the easter egg.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
[ -n "${NVIDIA_API_KEY:-}" ] || { echo "NVIDIA_API_KEY required"; exit 1; }
exec node "$SCRIPT_DIR/server.js"
