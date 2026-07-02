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
DEFAULT_MODEL="8bit/DeepSolana"
DEFAULT_MODEL_PROVIDER="ollama-local"
DEFAULT_TRADING_MODE="dry-run"

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

now_utc() {
  date -u +"%Y-%m-%dT%H:%M:%SZ"
}

lobster_banner() {
  if [[ -t 1 && "${NEMOCLAWD_NO_ANIMATION:-0}" != "1" ]]; then
    local frames=(
      "🦞  Nemo Clawd install deck"
      "🦞> Nemo Clawd install deck"
      "🦞>> Nemo Clawd install deck"
      "🦞>>> Nemo Clawd install deck"
    )
    local frame
    for frame in "${frames[@]}"; do
      printf '\r[INFO] %s' "${frame}"
      sleep 0.06
    done
    printf '\n'
  else
    info "Nemo Clawd lobster install deck"
  fi
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

seed_private_solana_wallet() {
  local wallet_dir="${NEMOCLAWD_HOME}/wallets"
  local keypair_path="${wallet_dir}/nemoclawd-local-private-keypair.json"
  local wallets_file="${wallet_dir}/wallets.json"

  mkdir -p "${wallet_dir}"
  chmod 700 "${wallet_dir}"

  if ! command_exists solana-keygen; then
    local message="Solana CLI not found; skipping local private keypair generation. Use 'nemoclawd wallet create' for a managed wallet or install Solana CLI and rerun."
    if [[ "${NEMOCLAWD_REQUIRE_LOCAL_WALLET:-0}" == "1" ]]; then
      fail "${message}"
    fi
    warn "${message}"
    return
  fi

  if [[ ! -f "${keypair_path}" ]]; then
    info "Creating local private Solana wallet keypair at ${keypair_path}"
    (umask 077 && solana-keygen new --no-bip39-passphrase --silent --outfile "${keypair_path}" >/dev/null)
    chmod 600 "${keypair_path}"
  else
    info "Keeping existing local private Solana wallet keypair at ${keypair_path}"
  fi

  local public_key
  public_key="$(solana-keygen pubkey "${keypair_path}" 2>/dev/null || true)"
  if [[ -z "${public_key}" ]]; then
    warn "Could not read public key for ${keypair_path}; wallet metadata was not updated."
    return
  fi

  NEMOCLAWD_WALLETS_FILE="${wallets_file}" \
  NEMOCLAWD_WALLET_ADDRESS="${public_key}" \
  NEMOCLAWD_WALLET_KEYPAIR_PATH="${keypair_path}" \
  NEMOCLAWD_WALLET_CREATED_AT="$(now_utc)" \
  node <<'NODE'
const fs = require("node:fs");

const file = process.env.NEMOCLAWD_WALLETS_FILE;
const record = {
  walletId: "local-private",
  address: process.env.NEMOCLAWD_WALLET_ADDRESS,
  chainType: "solana",
  provider: "local-keypair",
  privateKeyPath: process.env.NEMOCLAWD_WALLET_KEYPAIR_PATH,
  createdAt: process.env.NEMOCLAWD_WALLET_CREATED_AT,
  funding: "unfunded",
  liveTradingEnabled: false,
};

let wallets = [];
try {
  const parsed = JSON.parse(fs.readFileSync(file, "utf8"));
  wallets = Array.isArray(parsed) ? parsed : [];
} catch {}

const existing = wallets.findIndex(
  (wallet) => wallet.provider === "local-keypair" && wallet.privateKeyPath === record.privateKeyPath,
);
if (existing >= 0) {
  wallets[existing] = { ...wallets[existing], ...record, createdAt: wallets[existing].createdAt || record.createdAt };
} else {
  wallets.unshift(record);
}

fs.writeFileSync(file, `${JSON.stringify(wallets, null, 2)}\n`, { mode: 0o600 });
NODE
  chmod 600 "${wallets_file}"
  info "Registered local private Solana wallet metadata at ${wallets_file}"
}

seed_agent_and_trading_box() {
  local agent_profile="${NEMOCLAWD_HOME}/agent.json"
  local trading_box="${NEMOCLAWD_HOME}/trading-box.json"
  local wallets_file="${NEMOCLAWD_HOME}/wallets/wallets.json"

  NEMOCLAWD_AGENT_PROFILE="${agent_profile}" \
  NEMOCLAWD_TRADING_BOX="${trading_box}" \
  NEMOCLAWD_WALLETS_FILE="${wallets_file}" \
  NEMOCLAWD_DEFAULT_MODEL="${DEFAULT_MODEL}" \
  NEMOCLAWD_DEFAULT_MODEL_PROVIDER="${DEFAULT_MODEL_PROVIDER}" \
  NEMOCLAWD_TRADING_MODE="${DEFAULT_TRADING_MODE}" \
  NEMOCLAWD_CREATED_AT="$(now_utc)" \
  node <<'NODE'
const fs = require("node:fs");

function readWallet() {
  try {
    const wallets = JSON.parse(fs.readFileSync(process.env.NEMOCLAWD_WALLETS_FILE, "utf8"));
    if (!Array.isArray(wallets)) return null;
    return wallets.find((wallet) => wallet.provider === "local-keypair") || wallets[0] || null;
  } catch {
    return null;
  }
}

function publicWalletView(wallet) {
  if (!wallet) return null;
  return {
    walletId: wallet.walletId || null,
    address: wallet.address || null,
    chainType: wallet.chainType || "solana",
    provider: wallet.provider || "unknown",
    funding: wallet.funding || "unfunded",
    liveTradingEnabled: wallet.liveTradingEnabled === true,
  };
}

const wallet = readWallet();
const walletView = publicWalletView(wallet);
const now = process.env.NEMOCLAWD_CREATED_AT;
const model = {
  id: process.env.NEMOCLAWD_DEFAULT_MODEL,
  provider: process.env.NEMOCLAWD_DEFAULT_MODEL_PROVIDER,
  source: "ai-training/model-kit",
  ownedBy: "nemoclawd",
};

const agentProfile = {
  theme: "lobster",
  symbol: "🦞",
  createdAt: now,
  defaultAgent: "clawd-onboarding-guide",
  model,
  wallet: walletView,
  commands: {
    doctor: "nemoclawd doctor",
    birth: "nemoclawd birth",
    harness: "nemoclawd financial-harness",
    launch: "nemoclawd launch",
  },
};

const tradingBox = {
  name: "nemoclawd-trading-box",
  theme: "lobster",
  mode: process.env.NEMOCLAWD_TRADING_MODE,
  createdAt: now,
  model,
  wallet: walletView,
  guardrails: {
    liveTradingEnabled: false,
    signingEnabledByInstaller: false,
    transactionSubmissionEnabledByInstaller: false,
    operatorApprovalRequired: true,
    financialHarnessRequired: true,
    privateKeyMaterialAllowedInSandbox: false,
  },
  services: [
    "nemoclawd financial-harness",
    "nemoclawd solana",
    "nemoclawd solana start <sandbox>",
  ],
  requiredPolicies: ["solana-rpc", "privy"],
};

fs.writeFileSync(process.env.NEMOCLAWD_AGENT_PROFILE, `${JSON.stringify(agentProfile, null, 2)}\n`, { mode: 0o600 });
fs.writeFileSync(process.env.NEMOCLAWD_TRADING_BOX, `${JSON.stringify(tradingBox, null, 2)}\n`, { mode: 0o600 });
NODE
  chmod 600 "${agent_profile}" "${trading_box}"
  info "Wrote lobster agent profile to ${agent_profile}"
  info "Wrote dry-run trading box to ${trading_box}"
}

seed_runtime_profile() {
  mkdir -p "${NEMOCLAWD_HOME}"
  chmod 700 "${NEMOCLAWD_HOME}"

  local solana_config="${NEMOCLAWD_HOME}/solana.json"
  NEMOCLAWD_SOLANA_CONFIG="${solana_config}" \
  NEMOCLAWD_DEFAULT_MODEL="${DEFAULT_MODEL}" \
  NEMOCLAWD_DEFAULT_MODEL_PROVIDER="${DEFAULT_MODEL_PROVIDER}" \
  NEMOCLAWD_TRADING_MODE="${DEFAULT_TRADING_MODE}" \
  node <<'NODE'
const fs = require("node:fs");
const file = process.env.NEMOCLAWD_SOLANA_CONFIG;
let config = {};
try {
  config = JSON.parse(fs.readFileSync(file, "utf8"));
} catch {}

config = {
  cluster: config.cluster || "mainnet-beta",
  rpcUrl: config.rpcUrl || "https://rpc.solanatracker.io/public",
  wsUrl: config.wsUrl || "wss://rpc.solanatracker.io/public",
  ...config,
  model: config.model || process.env.NEMOCLAWD_DEFAULT_MODEL,
  provider: config.provider || process.env.NEMOCLAWD_DEFAULT_MODEL_PROVIDER,
  ownModel: {
    id: process.env.NEMOCLAWD_DEFAULT_MODEL,
    source: "ai-training/model-kit",
    runtime: process.env.NEMOCLAWD_DEFAULT_MODEL_PROVIDER,
    ...(config.ownModel || {}),
  },
  trading: {
    mode: process.env.NEMOCLAWD_TRADING_MODE,
    liveTradingEnabled: false,
    financialHarnessRequired: true,
    operatorApprovalRequired: true,
    ...(config.trading || {}),
  },
};

fs.writeFileSync(file, `${JSON.stringify(config, null, 2)}\n`, { mode: 0o600 });
NODE
  chmod 600 "${solana_config}"
  info "Wrote Solana/model/trading defaults to ${solana_config}"

  seed_private_solana_wallet
  seed_agent_and_trading_box

  cat >"${NEMOCLAWD_HOME}/install.json" <<JSON
{
  "package": "${NPM_PACKAGE}",
  "repo": "${ROOT_DIR}",
  "mcp": "${ROOT_DIR}/nemo-clawd-mcp",
  "blueprint": "${ROOT_DIR}/nemoclaw-blueprint",
  "pythonBlueprint": "${ROOT_DIR}/nemo-clawd-python",
  "modelKit": "${ROOT_DIR}/ai-training/model-kit",
  "tradingFactory": "${ROOT_DIR}/ai-training/trading_factory",
  "defaultModel": "${DEFAULT_MODEL}",
  "defaultModelProvider": "${DEFAULT_MODEL_PROVIDER}",
  "tradingBox": "${NEMOCLAWD_HOME}/trading-box.json",
  "agentProfile": "${NEMOCLAWD_HOME}/agent.json",
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

Seeded local runtime:
  Solana profile: ${NEMOCLAWD_HOME}/solana.json
  Agent profile:  ${NEMOCLAWD_HOME}/agent.json
  Trading box:    ${NEMOCLAWD_HOME}/trading-box.json
  Wallet index:   ${NEMOCLAWD_HOME}/wallets/wallets.json
  Default model:  ${DEFAULT_MODEL} (${DEFAULT_MODEL_PROVIDER})

Next commands:
  nemoclawd doctor
  nemoclawd birth
  nemoclawd financial-harness
  nemoclawd solana
  nemoclawd launch

MCP server:
  npx --prefix "${ROOT_DIR}/nemo-clawd-mcp" nemoclawd-mcp

EOF
}

main() {
  lobster_banner
  ensure_node_runtime

  if [[ "${NEMOCLAWD_INSTALL_SEED_ONLY:-0}" == "1" ]]; then
    seed_runtime_profile
    post_install
    return
  fi

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
