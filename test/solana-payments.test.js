// SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: Apache-2.0

const { describe, it } = require("node:test");
const assert = require("node:assert/strict");
const { execFileSync, spawnSync } = require("node:child_process");
const path = require("node:path");
const { pathToFileURL } = require("node:url");

const TOOL = path.join(__dirname, "..", "tools", "e2e", "solana-payments.mts");
const HELPER = path.join(__dirname, "..", "tools", "advisors", "solana-payments.mts");
const RECIPIENT = "So11111111111111111111111111111111111111112";
const OPENUSD_MINT = "4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU";
const CLAWD_MINT = "8cHzQHUS2s2h8TzCmfqPKYiM4dSt4roa3n7MyRLApump";

describe("Solana payment tools", () => {
  it("builds x402 exact payment requirements for USDC and CLAWD without enabling signing", async () => {
    const { buildSolanaPaymentsReport, decodePaymentRequiredHeader } = await import(pathToFileURL(HELPER).href);
    const report = buildSolanaPaymentsReport({
      recipient: RECIPIENT,
      amount: "1.25",
      tokenSymbols: ["usdc", "clawd"],
      resourceUrl: "https://worker.example/api/paid",
      now: new Date("2026-07-02T00:00:00.000Z"),
    });

    assert.equal(report.status, "ready");
    assert.equal(report.generatedAt, "2026-07-02T00:00:00.000Z");
    assert.equal(report.guardrails.signingEnabled, false);
    assert.equal(report.guardrails.transactionSubmissionEnabled, false);
    assert.equal(report.guardrails.privateKeyMaterialAllowed, false);
    assert.equal(report.x402.paymentRequired.accepts.length, 2);
    assert.deepEqual(report.x402.requiredHeaders, [
      "PAYMENT-REQUIRED",
      "PAYMENT-SIGNATURE",
      "PAYMENT-RESPONSE",
    ]);

    const decoded = decodePaymentRequiredHeader(report.x402.encodedPaymentRequired);
    assert.equal(decoded.x402Version, 2);
    assert.equal(decoded.accepts[0].scheme, "exact");
    assert.equal(decoded.accepts[0].network, "solana:EtWTRABZaYq6iMfeYKouRu166VU2xqa1");
    assert.equal(decoded.accepts.find((item) => item.extra.token === "clawd").asset, CLAWD_MINT);
  });

  it("keeps OpenUSD blocked until the mint is configured", async () => {
    const { buildSolanaPaymentsReport } = await import(pathToFileURL(HELPER).href);
    const report = buildSolanaPaymentsReport({
      recipient: RECIPIENT,
      tokenSymbols: ["openusd"],
      resourceUrl: "https://worker.example/api/paid",
    });

    assert.equal(report.status, "blocked");
    assert.ok(report.blockers.includes("OpenUSD mint is not configured."));
    assert.equal(report.x402.paymentRequired.accepts.length, 0);
  });

  it("includes configured OpenUSD, USDC, and CLAWD in Kora allowlists", async () => {
    const { buildSolanaPaymentsReport } = await import(pathToFileURL(HELPER).href);
    const report = buildSolanaPaymentsReport({
      network: "mainnet",
      recipient: RECIPIENT,
      tokenSymbols: ["usdc", "openusd", "clawd"],
      openUsdMint: OPENUSD_MINT,
      resourceUrl: "https://worker.example/api/paid",
    });

    assert.equal(report.status, "ready");
    assert.ok(report.tokens.find((token) => token.symbol === "openusd").stablecoin);
    assert.ok(report.kora.toml.includes("allowed_spl_paid_tokens"));
    assert.ok(report.kora.toml.includes("EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"));
    assert.ok(report.kora.toml.includes(OPENUSD_MINT));
    assert.ok(report.kora.toml.includes(CLAWD_MINT));
  });

  it("renders deterministic CLI JSON for configured tokens", () => {
    const output = execFileSync(
      process.execPath,
      [
        "--experimental-strip-types",
        TOOL,
        "--recipient",
        RECIPIENT,
        "--tokens",
        "usdc,clawd",
        "--resource-url",
        "https://worker.example/api/paid",
        "--json",
      ],
      { encoding: "utf8" },
    );
    const report = JSON.parse(output);
    assert.equal(report.name, "nemoclawd-solana-payments");
    assert.equal(report.status, "ready");
    assert.equal(report.tokens.length, 2);
    assert.ok(report.cloudflare.snippet.includes("PAYMENT-SIGNATURE"));
    assert.ok(report.kora.toml.includes("Kora RPC"));
  });

  it("exits non-zero when the recipient is missing", () => {
    const result = spawnSync(
      process.execPath,
      ["--experimental-strip-types", TOOL, "--tokens", "usdc", "--json"],
      { encoding: "utf8", env: { ...process.env, SOLANA_PAYMENT_RECIPIENT: "" } },
    );
    assert.equal(result.status, 1);
    const report = JSON.parse(result.stdout);
    assert.equal(report.status, "blocked");
    assert.ok(report.blockers.includes("SOLANA_PAYMENT_RECIPIENT or --recipient is required."));
  });
});
