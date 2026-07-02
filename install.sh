#!/usr/bin/env bash
# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Nemo Clawd installer.
# Installs the README-facing nemoclawd CLI, builds the bundled Solana MCP
# server, and seeds local Solana-native runtime defaults.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NEMOCLAWD_HOME="${NEMOCLAWD_HOME:-${HOME}/.nemoclawd}"
NPM_PACKAGE="@mawdbotsonsolana/nemoclawd"
MIN_NODE_MAJOR=20
MIN_NPM_MAJOR=10
RUNTIME_REQUIREMENT_MSG="Nemo Clawd requires Node.js >=${MIN_NODE_MAJOR} and npm >=${MIN_NPM_MAJOR}."

info() { printf '[INFO] %s\n' "$*"; }
warn() { printf '[WARN] %s\n' "$*" >&2; }
fail() {
  printf '[ERROR] %s\n' "$*" >&2
  exit 1
}

command_exists() {
  command -v "$1" >/dev/null 2>&1
}

version_major() {
  printf '%s\n' "${1#v}" | cut -d. -f1
}

ensure_node_runtime() {
  command_exists node || fail "${RUNTIME_REQUIREMENT_MSG} Node.js was not found on PATH."
  command_exists npm || fail "${RUNTIME_REQUIREMENT_MSG} npm was not found on PATH."

  local node_version npm_version node_major npm_major
  node_version="$(node --version 2>/dev/null || true)"
  npm_version="$(npm --version 2>/dev/null || true)"
  node_major="$(version_major "$node_version")"
  npm_major="$(version_major "$npm_version")"

  [[ "$node_major" =~ ^[0-9]+$ ]] || fail "Could not parse Node.js version: ${node_version}"
  [[ "$npm_major" =~ ^[0-9]+$ ]] || fail "Could not parse npm version: ${npm_version}"

  if ((node_major < MIN_NODE_MAJOR || npm_major < MIN_NPM_MAJOR)); then
    fail "Unsupported runtime detected: Node.js ${node_version:-unknown}, npm ${npm_version:-unknown}. ${RUNTIME_REQUIREMENT_MSG} Upgrade Node.js and rerun the installer."
  fi

  info "Runtime OK: Node.js ${node_version}, npm ${npm_version}"
}

refresh_global_npm_path() {
  local npm_bin
  npm_bin="$(npm config get prefix 2>/dev/null)/bin" || true
  if [[ -n "${npm_bin}" && -d "${npm_bin}" && ":${PATH}:" != *":${npm_bin}:"* ]]; then
    export PATH="${npm_bin}:${PATH}"
  fi
}

package_name() {
  node -p "try { require(process.argv[1]).name || '' } catch { '' }" "$1" 2>/dev/null || true
}

install_cli() {
  local local_package_name=""
  if [[ -f "${ROOT_DIR}/package.json" ]]; then
    local_package_name="$(package_name "${ROOT_DIR}/package.json")"
  fi

  if [[ "${local_package_name}" == "${NPM_PACKAGE}" ]]; then
    info "Installing Nemo Clawd from local source at ${ROOT_DIR}"
    npm install --prefix "${ROOT_DIR}"
    npm run --prefix "${ROOT_DIR}" build
    npm link --prefix "${ROOT_DIR}"
  else
    info "Installing Nemo Clawd from npm: ${NPM_PACKAGE}"
    npm install -g "${NPM_PACKAGE}"
  fi

  refresh_global_npm_path
  command_exists nemoclawd || fail "nemoclawd was installed but is not on PATH."
  info "CLI ready: $(command -v nemoclawd)"
}

install_mcp() {
  local mcp_dir="${ROOT_DIR}/nemo-clawd-mcp"
  if [[ ! -f "${mcp_dir}/package.json" ]]; then
    warn "Bundled MCP server not found at ${mcp_dir}; skipping MCP build."
    return
  fi

  info "Building bundled Solana MCP server"
  npm install --prefix "${mcp_dir}"
  npm run --prefix "${mcp_dir}" build
}

verify_blueprint() {
  local blueprint_dir="${ROOT_DIR}/nemoclaw-blueprint"
  if [[ ! -f "${blueprint_dir}/blueprint.yaml" ]]; then
    warn "Blueprint not found at ${blueprint_dir}; sandbox launch will require a packaged blueprint."
    return
  fi

  info "Blueprint available: ${blueprint_dir}"
  if command_exists python3; then
    python3 -m py_compile \
      "${blueprint_dir}/orchestrator/runner.py" \
      "${blueprint_dir}/migrations/snapshot.py"
  fi
}

seed_runtime_profile() {
  mkdir -p "${NEMOCLAWD_HOME}"
  chmod 700 "${NEMOCLAWD_HOME}"

  local solana_config="${NEMOCLAWD_HOME}/solana.json"
  if [[ ! -f "${solana_config}" ]]; then
    cat >"${solana_config}" <<'JSON'
{
  "cluster": "mainnet-beta",
  "rpcUrl": "https://rpc.solanatracker.io/public",
  "wsUrl": "wss://rpc.solanatracker.io/public"
}
JSON
    chmod 600 "${solana_config}"
    info "Wrote Solana defaults to ${solana_config}"
  else
    info "Keeping existing Solana config at ${solana_config}"
  fi

  cat >"${NEMOCLAWD_HOME}/install.json" <<JSON
{
  "package": "${NPM_PACKAGE}",
  "repo": "${ROOT_DIR}",
  "mcp": "${ROOT_DIR}/nemo-clawd-mcp",
  "blueprint": "${ROOT_DIR}/nemoclaw-blueprint",
  "pythonBlueprint": "${ROOT_DIR}/nemo-clawd-python",
  "agentCatalog": "${ROOT_DIR}/agents/agents-catalog.json",
  "birthAgents": "${ROOT_DIR}/agents/locales",
  "skills": "${ROOT_DIR}/skills",
  "userGuideSkill": "${ROOT_DIR}/skills/nemoclawd-user-guide"
}
JSON
  chmod 600 "${NEMOCLAWD_HOME}/install.json"
}

verify_birth_agents() {
  local locales_dir="${ROOT_DIR}/agents/locales"
  if [[ ! -d "${locales_dir}" ]]; then
    warn "Birth agent locales not found at ${locales_dir}; nemoclawd birth will be limited."
    return
  fi

  local count
  count="$(find "${locales_dir}" -mindepth 1 -maxdepth 1 -type d | wc -l | tr -d '[:space:]')"
  info "Birth agents available: ${count} localized Clawd personas"
}

verify_skill_bundle() {
  local skill_dir="${ROOT_DIR}/skills/nemoclawd-user-guide"
  if [[ ! -f "${skill_dir}/SKILL.md" ]]; then
    warn "Nemo Clawd user-guide skill not found at ${skill_dir}; skipping skill verification."
    return
  fi

  info "User-guide skill available: ${skill_dir}"
}

check_solana_tools() {
  if command_exists solana; then
    info "Solana CLI: $(solana --version 2>/dev/null || echo available)"
  else
    warn "Solana CLI not found. Nemo Clawd can still use RPC/MCP tools, but local validator commands will be unavailable."
  fi
}

post_install() {
  cat <<EOF

Nemo Clawd is installed.

Recommended environment:
  export XAI_API_KEY="<XAI_API_KEY>"
  export HELIUS_API_KEY="<HELIUS_API_KEY>"
  export SOLANA_RPC_URL="https://rpc.solanatracker.io/public"

Next commands:
  nemoclawd doctor
  nemoclawd birth
  nemoclawd solana
  nemoclawd launch

MCP server:
  npx --prefix "${ROOT_DIR}/nemo-clawd-mcp" nemoclawd-mcp

EOF
}

main() {
  info "Nemo Clawd installer"
  ensure_node_runtime
  install_cli
  install_mcp
  verify_blueprint
  verify_birth_agents
  verify_skill_bundle
  seed_runtime_profile
  check_solana_tools
  post_install
}

main "$@"
