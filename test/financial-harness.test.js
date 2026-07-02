// SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: Apache-2.0

const { describe, it } = require("node:test");
const assert = require("node:assert/strict");

const {
  LIVE_TRADING_ENV,
  buildFinancialHarnessReport,
  inferRpcNetwork,
  redactUrl,
} = require("../bin/lib/financial-harness");

describe("financial harness", () => {
  it("infers common Solana networks from RPC URLs", () => {
    assert.equal(inferRpcNetwork("http://127.0.0.1:8899"), "local-validator");
    assert.equal(inferRpcNetwork("https://api.devnet.solana.com"), "devnet");
    assert.equal(inferRpcNetwork("https://api.testnet.solana.com"), "testnet");
    assert.equal(inferRpcNetwork("https://mainnet.helius-rpc.com/?api-key=abc"), "mainnet");
    assert.equal(inferRpcNetwork("https://example.invalid/rpc"), "custom");
  });

  it("redacts common RPC credential query parameters", () => {
    assert.equal(
      redactUrl("https://mainnet.helius-rpc.com/?api-key=secret&cluster=mainnet"),
      "https://mainnet.helius-rpc.com/?api-key=redacted&cluster=mainnet",
    );
  });

  it("builds a dry-run report with wallet, policy, and disabled signing guardrails", () => {
    const report = buildFinancialHarnessReport({
      sandboxName: "nemo",
      solanaConfig: {
        rpcUrl: "https://mainnet.helius-rpc.com/?api-key=secret",
      },
      wallet: {
        walletId: "wallet-1",
        address: "So11111111111111111111111111111111111111112",
      },
      privyConfigured: true,
      policies: ["solana-rpc", "privy"],
      env: {
        [LIVE_TRADING_ENV]: "1",
      },
    });

    assert.equal(report.mode, "dry-run");
    assert.equal(report.sandbox, "nemo");
    assert.equal(report.rpc.url, "https://mainnet.helius-rpc.com/?api-key=redacted");
    assert.equal(report.wallet.provider, "privy");
    assert.deepEqual(report.policy.missingPresets, []);
    assert.equal(report.guardrails.signingEnabled, false);
    assert.equal(report.guardrails.transactionSubmissionEnabled, false);
    assert.ok(report.blockers.includes("live trading execution is not implemented by this harness"));
  });

  it("requires no remote policy preset for a local validator", () => {
    const report = buildFinancialHarnessReport({
      solanaConfig: { rpcUrl: "http://localhost:8899" },
      env: {},
    });

    assert.equal(report.rpc.network, "local-validator");
    assert.deepEqual(report.policy.requiredPresets, []);
  });

  it("preserves installer-created local keypair wallet provider labels", () => {
    const report = buildFinancialHarnessReport({
      wallet: {
        walletId: "local-private",
        address: "So11111111111111111111111111111111111111112",
        provider: "local-keypair",
      },
      policies: ["solana-rpc"],
      env: {},
    });

    assert.equal(report.wallet.provider, "local-keypair");
    assert.equal(report.policy.requiredPresets.includes("privy"), false);
  });
});
