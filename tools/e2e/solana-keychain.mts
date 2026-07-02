#!/usr/bin/env node
// SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: Apache-2.0

import fs from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";

import { parseArgs, writeJson } from "../advisors/io.mts";
import {
  type SolanaKeychainCluster,
  type SolanaKeychainEnvironment,
  type SolanaSignerRole,
  buildSolanaKeychainConfigFromEnv,
  buildSolanaKeychainReport,
  renderSolanaKeychainMarkdown,
} from "../advisors/solana-keychain.mts";

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((error: unknown) => {
    console.error(error instanceof Error ? error.message : String(error));
    process.exit(1);
  });
}

function usage(): string {
  return [
    "Usage: node --experimental-strip-types tools/e2e/solana-keychain.mts [options]",
    "",
    "Dry-run Solana Keychain signer configuration with redacted secrets and production guardrails.",
    "",
    "Options:",
    "  --backend NAME           Keychain backend. Defaults to SOLANA_KEYCHAIN_BACKEND or memory.",
    "  --environment NAME       development, test, ci, staging, or production.",
    "  --cluster NAME           local-validator, devnet, testnet, mainnet, mainnet-beta, or custom.",
    "  --role NAME              operational, fee-payer, treasury, or user-wallet.",
    "  --public-key ADDRESS     Public signer address for backends that require it.",
    "  --address ADDRESS        Address alias for managed wallet backends.",
    "  --key-name NAME          Backend key name alias for Vault or GCP KMS.",
    "  --key-id NAME            Backend key ID alias for AWS KMS.",
    "  --wallet-id ID           Managed wallet ID.",
    "  --private-key-path PATH  Memory backend keypair path for local development only.",
    "  --vault-addr URL         HashiCorp Vault HTTPS address.",
    "  --json                   Print JSON instead of Markdown.",
    "  --out PATH               Write JSON report to PATH.",
    "  --markdown PATH          Write Markdown report to PATH.",
    "  --help                   Show this message.",
  ].join("\n");
}

async function main(): Promise<void> {
  const args = parseArgs(process.argv.slice(2));
  if (Object.hasOwn(args, "help") || Object.hasOwn(args, "h")) {
    console.log(usage());
    return;
  }

  const config = buildSolanaKeychainConfigFromEnv({
    backend: args.backend,
    overrides: configOverridesFromArgs(args),
  });
  const report = buildSolanaKeychainReport({
    config,
    environment: parseEnvironment(args.environment),
    cluster: parseCluster(args.cluster),
    role: parseRole(args.role),
  });
  const markdown = renderSolanaKeychainMarkdown(report);

  if (args.out) {
    ensureParentDir(args.out);
    writeJson(args.out, report);
  }
  if (args.markdown) {
    ensureParentDir(args.markdown);
    fs.writeFileSync(args.markdown, markdown);
  }

  if (Object.hasOwn(args, "json")) {
    process.stdout.write(`${JSON.stringify(report, null, 2)}\n`);
  } else {
    process.stdout.write(markdown);
  }
  if (report.status === "blocked") {
    process.exitCode = 1;
  }
}

function configOverridesFromArgs(args: Record<string, string | undefined>): Record<string, unknown> {
  return {
    publicKey: args.publicKey,
    address: args.address,
    keyName: args.keyName,
    keyId: args.keyId,
    walletId: args.walletId,
    privateKeyPath: args.privateKeyPath,
    vaultAddr: args.vaultAddr,
  };
}

function parseEnvironment(value: string | undefined): SolanaKeychainEnvironment | undefined {
  if (!value) return undefined;
  if (value === "development" || value === "test" || value === "ci" || value === "staging" || value === "production") {
    return value;
  }
  throw new Error(`Unsupported --environment value: ${value}`);
}

function parseCluster(value: string | undefined): SolanaKeychainCluster | undefined {
  if (!value) return undefined;
  if (
    value === "local-validator" ||
    value === "devnet" ||
    value === "testnet" ||
    value === "mainnet" ||
    value === "mainnet-beta" ||
    value === "custom"
  ) {
    return value;
  }
  throw new Error(`Unsupported --cluster value: ${value}`);
}

function parseRole(value: string | undefined): SolanaSignerRole | undefined {
  if (!value) return undefined;
  if (value === "operational" || value === "fee-payer" || value === "treasury" || value === "user-wallet") {
    return value;
  }
  throw new Error(`Unsupported --role value: ${value}`);
}

function ensureParentDir(filePath: string): void {
  fs.mkdirSync(path.dirname(path.resolve(process.cwd(), filePath)), { recursive: true });
}
