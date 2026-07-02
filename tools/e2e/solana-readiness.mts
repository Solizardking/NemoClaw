#!/usr/bin/env node
// SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: Apache-2.0

import fs from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";

import { parseArgs, parsePositiveInt, writeJson } from "../advisors/io.mts";
import {
  type SolanaCluster,
  buildSolanaReadinessReport,
  renderSolanaReadinessMarkdown,
} from "../advisors/solana.mts";

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((error: unknown) => {
    console.error(error instanceof Error ? error.message : String(error));
    process.exit(1);
  });
}

function usage(): string {
  return [
    "Usage: node --experimental-strip-types tools/e2e/solana-readiness.mts [options]",
    "",
    "Dry-run Solana JSON-RPC, wallet, policy, and signing guardrail readiness checks.",
    "",
    "Options:",
    "  --rpc URL              Solana RPC URL. Defaults to SOLANA_RPC_URL or the public Nemo Clawd fallback.",
    "  --wallet ADDRESS       Wallet address to validate and balance-check.",
    "  --expect-cluster NAME  Expected cluster: local-validator, devnet, testnet, mainnet, custom.",
    "  --privy                Include the Privy policy preset as required.",
    "  --telegram             Include the Telegram policy preset as required.",
    "  --timeout-ms N         Per-RPC timeout. Defaults to 10000.",
    "  --no-network           Skip network calls and only render deterministic dry-run posture.",
    "  --json                 Print JSON instead of Markdown.",
    "  --out PATH             Write JSON report to PATH.",
    "  --markdown PATH        Write Markdown report to PATH.",
    "  --help                 Show this message.",
  ].join("\n");
}

async function main(): Promise<void> {
  const args = parseArgs(process.argv.slice(2));
  if (Object.hasOwn(args, "help") || Object.hasOwn(args, "h")) {
    console.log(usage());
    return;
  }

  const expectedCluster = parseCluster(args.expectCluster);
  const report = await buildSolanaReadinessReport({
    rpcUrl: args.rpc || process.env.SOLANA_RPC_URL,
    expectedCluster,
    walletAddress: args.wallet || process.env.DEVELOPER_WALLET,
    privyConfigured: Object.hasOwn(args, "privy") || Boolean(process.env.PRIVY_APP_ID),
    telegramConfigured: Object.hasOwn(args, "telegram") || Boolean(process.env.TELEGRAM_BOT_TOKEN),
    noNetwork: Object.hasOwn(args, "noNetwork"),
    timeoutMs: parsePositiveInt(args.timeoutMs, 10000),
  });

  if (args.out) {
    ensureParentDir(args.out);
    writeJson(args.out, report);
  }
  const markdown = renderSolanaReadinessMarkdown(report);
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

function parseCluster(value: string | undefined): SolanaCluster | undefined {
  if (!value) return undefined;
  if (
    value === "local-validator" ||
    value === "devnet" ||
    value === "testnet" ||
    value === "mainnet" ||
    value === "custom" ||
    value === "unconfigured"
  ) {
    return value;
  }
  throw new Error(`Unsupported --expect-cluster value: ${value}`);
}

function ensureParentDir(filePath: string): void {
  fs.mkdirSync(path.dirname(path.resolve(process.cwd(), filePath)), { recursive: true });
}
