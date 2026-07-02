// SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: Apache-2.0

const { describe, it } = require("node:test");
const assert = require("node:assert/strict");
const { spawnSync } = require("node:child_process");
const path = require("node:path");
const { pathToFileURL } = require("node:url");

const TOOL = path.join(__dirname, "..", "tools", "e2e", "solana-keychain.mts");
const HELPER = path.join(__dirname, "..", "tools", "advisors", "solana-keychain.mts");
const PUBLIC_KEY = "So11111111111111111111111111111111111111112";

describe("Solana Keychain signing posture tools", () => {
  it("tracks the supported Keychain backend set without adding the all-backends meta package", async () => {
    const { KEYCHAIN_BACKENDS } = await import(pathToFileURL(HELPER).href);
    assert.deepEqual(
      KEYCHAIN_BACKENDS.map((backend) => backend.id),
      [
        "memory",
        "vault",
        "aws_kms",
        "gcp_kms",
        "privy",
        "turnkey",
        "fireblocks",
        "cdp",
        "crossmint",
        "dfns",
        "openfort",
        "para",
        "utila",
      ],
    );

    const pkg = require("../package.json");
    assert.equal(pkg.dependencies["@solana/keychain"], undefined);
    assert.ok(pkg.scripts["tools:solana:keychain"].includes("solana-keychain.mts"));
  });

  it("blocks memory signing in production and redacts local key paths", async () => {
    const { buildSolanaKeychainReport } = await import(pathToFileURL(HELPER).href);
    const report = buildSolanaKeychainReport({
      config: {
        backend: "memory",
        privateKeyPath: "/Users/example/.config/solana/id.json",
      },
      environment: "production",
      cluster: "mainnet",
      now: new Date("2026-07-02T00:00:00.000Z"),
    });

    assert.equal(report.status, "blocked");
    assert.equal(report.generatedAt, "2026-07-02T00:00:00.000Z");
    assert.ok(
      report.blockers.includes("memory signing is limited to development, test, or CI on non-mainnet clusters."),
    );
    assert.equal(report.guardrails.signerCreationEnabled, false);
    assert.equal(report.guardrails.transactionSubmissionEnabled, false);
    assert.equal(report.guardrails.privateKeyMaterialAllowed, false);
    assert.equal(report.config.redacted.privateKeyPath, "<redacted>");
    assert.equal(JSON.stringify(report).includes("/Users/example/.config/solana/id.json"), false);
  });

  it("blocks non-HTTPS Vault addresses and never serializes Vault tokens", async () => {
    const { buildSolanaKeychainConfigFromEnv, buildSolanaKeychainReport } = await import(pathToFileURL(HELPER).href);
    const config = buildSolanaKeychainConfigFromEnv({
      env: {
        SOLANA_KEYCHAIN_BACKEND: "vault",
        SOLANA_KEYCHAIN_VAULT_ADDR: "http://vault.example.com:8200",
        SOLANA_KEYCHAIN_VAULT_TOKEN: "hvs.super-secret",
        SOLANA_KEYCHAIN_KEY_NAME: "agent-fee-payer",
        SOLANA_KEYCHAIN_PUBLIC_KEY: PUBLIC_KEY,
      },
    });
    const report = buildSolanaKeychainReport({
      config,
      environment: "production",
      cluster: "mainnet",
    });

    assert.equal(report.status, "blocked");
    assert.ok(report.blockers.includes("vaultAddr must be an HTTPS URL for remote signing backends."));
    assert.equal(report.config.redacted.vaultToken, "<redacted>");
    assert.equal(JSON.stringify(report).includes("hvs.super-secret"), false);
  });

  it("accepts a production managed-wallet backend while redacting provider secrets", async () => {
    const { buildSolanaKeychainReport } = await import(pathToFileURL(HELPER).href);
    const report = buildSolanaKeychainReport({
      config: {
        backend: "privy",
        appId: "app_123",
        appSecret: "privy-secret",
        walletId: "wallet_123",
      },
      environment: "production",
      cluster: "devnet",
      role: "user-wallet",
    });

    assert.equal(report.status, "ready");
    assert.equal(report.signing.packageName, "@solana/keychain-privy");
    assert.equal(report.guardrails.availabilityCheckRequired, true);
    assert.equal(report.config.redacted.appSecret, "<redacted>");
    assert.ok(report.recommendations.preferredBackendsForRole.includes("privy"));
    assert.equal(JSON.stringify(report).includes("privy-secret"), false);
  });

  it("renders CLI JSON from env without leaking secret values", () => {
    const result = spawnSync(
      process.execPath,
      [
        "--experimental-strip-types",
        TOOL,
        "--backend",
        "vault",
        "--environment",
        "production",
        "--cluster",
        "devnet",
        "--role",
        "fee-payer",
        "--vault-addr",
        "https://vault.example.com:8200",
        "--key-name",
        "agent-fee-payer",
        "--public-key",
        PUBLIC_KEY,
        "--json",
      ],
      {
        encoding: "utf8",
        env: {
          ...process.env,
          SOLANA_KEYCHAIN_VAULT_TOKEN: "hvs.cli-secret",
        },
      },
    );

    assert.equal(result.status, 0, result.stderr);
    assert.equal(result.stdout.includes("hvs.cli-secret"), false);
    const report = JSON.parse(result.stdout);
    assert.equal(report.name, "nemoclawd-solana-keychain");
    assert.equal(report.status, "ready");
    assert.equal(report.config.redacted.vaultToken, "<redacted>");
    assert.equal(report.signing.address, PUBLIC_KEY);
  });

  it("requires explicit opt-in before creating a signer and passes config to the selected factory", async () => {
    const { createNemoSolanaSigner } = await import(pathToFileURL(HELPER).href);
    const config = {
      backend: "privy",
      appId: "app_123",
      appSecret: "privy-secret",
      walletId: "wallet_123",
    };
    await assert.rejects(
      createNemoSolanaSigner({
        config,
        environment: "production",
        cluster: "devnet",
      }),
      /allowSigning=true/,
    );

    let receivedConfig;
    const signer = await createNemoSolanaSigner({
      config,
      environment: "production",
      cluster: "devnet",
      allowSigning: true,
      verifyAvailability: true,
      factory: async (factoryConfig) => {
        receivedConfig = factoryConfig;
        return { address: PUBLIC_KEY, isAvailable: async () => true };
      },
    });

    assert.equal(signer.address, PUBLIC_KEY);
    assert.equal(receivedConfig.backend, undefined);
    assert.equal(receivedConfig.appSecret, "privy-secret");
  });
});
