#!/usr/bin/env bash
# Spin up a clean Ubuntu environment via Docker with the defined onboarding
# prereqs (Docker CLI, OpenShell) pre-installed, then drop in the repo so
# install.sh can be tested.
#
# Usage:
#   bash test-ubuntu.sh          # defaults to Ubuntu 22.04
#   bash test-ubuntu.sh 24.04    # test against 24.04
set -euo pipefail

UBUNTU_VERSION="${1:-22.04}"
CONTAINER_NAME="nemoclaw-ubuntu-test"
REPO_DIR="/Users/aerickson/Documents/Claude Code Projects/openclaw-design-lb"
REMOTE_DIR="/root/NemoClaw"

echo "==> Removing old container (if any)..."
docker rm -f "$CONTAINER_NAME" 2>/dev/null || true

echo "==> Starting Ubuntu ${UBUNTU_VERSION} container..."
docker run -d --name "$CONTAINER_NAME" --privileged \
  -v /var/run/docker.sock:/var/run/docker.sock \
  "ubuntu:${UBUNTU_VERSION}" sleep infinity

# --- Prereqs: what we tell users to have before running install.sh ---

echo "==> Installing prereq: Docker CLI..."
docker exec "$CONTAINER_NAME" bash -c \
  "apt-get update -qq && apt-get install -y -qq docker.io curl"

echo "==> Installing prereq: OpenShell CLI..."
docker exec "$CONTAINER_NAME" bash -c '
  ARCH="$(uname -m)"
  case "$ARCH" in
    x86_64|amd64)  ASSET="openshell-x86_64-unknown-linux-musl.tar.gz" ;;
    aarch64|arm64) ASSET="openshell-aarch64-unknown-linux-musl.tar.gz" ;;
    *) echo "Unsupported arch: $ARCH"; exit 1 ;;
  esac
  tmpdir="$(mktemp -d)"
  curl -fsSL "https://github.com/NVIDIA/OpenShell/releases/latest/download/$ASSET" \
    -o "$tmpdir/$ASSET"
  tar xzf "$tmpdir/$ASSET" -C "$tmpdir"
  install -m 755 "$tmpdir/openshell" /usr/local/bin/openshell
  rm -rf "$tmpdir"
  echo "openshell $(openshell --version 2>&1 || echo installed)"
'

# --- Copy repo ---

echo "==> Copying repo into container..."
docker cp "$REPO_DIR" "${CONTAINER_NAME}:${REMOTE_DIR}"
docker exec "$CONTAINER_NAME" bash -c "rm -rf ${REMOTE_DIR}/node_modules ${REMOTE_DIR}/.git"

echo ""
echo "==> Done. Ubuntu ${UBUNTU_VERSION} with Docker + OpenShell ready."
echo ""
echo "  docker exec -it ${CONTAINER_NAME} bash"
echo "  cd ${REMOTE_DIR}"
echo "  bash install.sh"
echo ""
