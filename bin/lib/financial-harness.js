// SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: Apache-2.0
//
// Dry-run financial harness state for Solana/OpenShell onboarding.

const DEFAULT_RPC_URL = "https://rpc.solanatracker.io/public";
const LIVE_TRADING_ENV = "NEMOCLAWD_ENABLE_LIVE_TRADING";
const DEFAULT_SPEND_LIMIT_LAMPORTS = 100_000_000;

function inferRpcNetwork(rpcUrl) {
  if (!rpcUrl) return "unconfigured";
  const value = String(rpcUrl).toLowerCase();
  if (value.includes("localhost") || value.includes("127.0.0.1")) return "local-validator";
  if (value.includes("devnet")) return "devnet";
  if (value.includes("testnet")) return "testnet";
  if (
    value.includes("mainnet") ||
    value.includes("solanatracker") ||
    value.includes("ankr.com/solana")
  ) {
    return "mainnet";
  }
  return "custom";
}

function redactUrl(rawUrl) {
  if (!rawUrl) return null;
  try {
    const url = new URL(rawUrl);
    for (const key of ["api-key", "apiKey", "key", "token"]) {
      if (url.searchParams.has(key)) {
        url.searchParams.set(key, "redacted");
      }
    }
    return url.toString();
  } catch {
    return rawUrl;
  }
}

function resolveWallet(input = {}) {
  const wallet = input.wallet || null;
  const env = input.env || {};
  const solanaConfig = input.solanaConfig || {};
  const address = env.DEVELOPER_WALLET || (wallet && wallet.address) || solanaConfig.developerWallet || null;
  let provider = "none";
  if (wallet && wallet.provider) {
    provider = wallet.provider;
  } else if (wallet && wallet.walletId) {
    provider = "privy";
  } else if (env.DEVELOPER_WALLET) {
    provider = "env";
  } else if (solanaConfig.developerWallet) {
    provider = "config";
  }

  return {
    configured: Boolean(address),
    address,
    provider,
  };
}

function buildFinancialHarnessReport(input = {}) {
  const env = input.env || process.env;
  const solanaConfig = input.solanaConfig || {};
  const rpcUrl = env.SOLANA_RPC_URL || solanaConfig.rpcUrl || input.rpcUrl || DEFAULT_RPC_URL;
  const network = inferRpcNetwork(rpcUrl);
  const appliedPolicies = Array.isArray(input.policies) ? input.policies : [];
  const wallet = resolveWallet({ ...input, env, solanaConfig });
  const requiredPolicies = network === "local-validator" ? [] : ["solana-rpc"];
  const hasPrivyConfig = Boolean(input.privyConfigured || env.PRIVY_APP_ID || env.PRIVY_APP_SECRET);
  if (hasPrivyConfig || wallet.provider === "privy") {
    requiredPolicies.push("privy");
  }
  const missingPolicies = requiredPolicies.filter((name) => !appliedPolicies.includes(name));
  const liveTradingRequested = env[LIVE_TRADING_ENV] === "1";
  const blockers = [];

  blockers.push("live trading execution is not implemented by this harness");
  if (!liveTradingRequested) {
    blockers.push(`${LIVE_TRADING_ENV}=1 is not set`);
  }
  if (!wallet.configured) {
    blockers.push("no agent wallet is configured");
  }
  if (missingPolicies.length > 0) {
    blockers.push(`missing policy preset(s): ${missingPolicies.join(", ")}`);
  }

  return {
    name: "nemoclawd-financial-harness",
    mode: "dry-run",
    sandbox: input.sandboxName || null,
    rpc: {
      url: redactUrl(rpcUrl),
      network,
    },
    wallet,
    policy: {
      appliedPresets: appliedPolicies,
      requiredPresets: requiredPolicies,
      missingPresets: missingPolicies,
    },
    guardrails: {
      signingEnabled: false,
      transactionSubmissionEnabled: false,
      liveTradingRequested,
      liveTradingGate: LIVE_TRADING_ENV,
      defaultSpendLimitLamports: DEFAULT_SPEND_LIMIT_LAMPORTS,
      privateKeyStorage: "not allowed in sandbox filesystem",
    },
    mechanism: [
      "observe: read Solana RPC, wallet balance, and token/account state",
      "orient: classify cluster, policy coverage, wallet readiness, and risk limits",
      "propose: produce a signed-off trade intent for operator review",
      "approve: require explicit operator approval before any signing path",
      "execute: disabled in this harness; future live execution must use wallet policy gates",
      "settle: verify chain state after confirmation and write an audit record",
    ],
    blockers,
  };
}

module.exports = {
  DEFAULT_RPC_URL,
  LIVE_TRADING_ENV,
  DEFAULT_SPEND_LIMIT_LAMPORTS,
  inferRpcNetwork,
  redactUrl,
  buildFinancialHarnessReport,
};
