#!/usr/bin/env node
// SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: Apache-2.0

import fs from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";

import { parseArgs, writeJson } from "../advisors/io.mts";
import {
  type SolanaPaymentNetwork,
  buildSolanaPaymentsReport,
  parsePaymentTokenSymbols,
  renderSolanaPaymentsMarkdown,
} from "../advisors/solana-payments.mts";

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((error: unknown) => {
    console.error(error instanceof Error ? error.message : String(error));
    process.exit(1);
  });
}

function usage(): string {
  return [
    "Usage: node --experimental-strip-types tools/e2e/solana-payments.mts [options]",
    "",
    "Generate dry-run Solana x402, Cloudflare, Kora, USDC, OpenUSD, and CLAWD payment artifacts.",
    "",
    "Options:",
    "  --network NAME                Solana network: devnet or mainnet. Defaults to devnet.",
    "  --recipient ADDRESS           Recipient wallet. Defaults to SOLANA_PAYMENT_RECIPIENT.",
    "  --amount VALUE                Display amount per token. Defaults to 0.01.",
    "  --tokens LIST                 Comma list: usdc,openusd,clawd. Defaults to all three.",
    "  --openusd-mint ADDRESS        OpenUSD SPL mint. Defaults to OPENUSD_MINT or SOLANA_OPENUSD_MINT.",
    "  --openusd-decimals N          OpenUSD decimals. Defaults to 6.",
    "  --clawd-mint ADDRESS          CLAWD SPL mint. Defaults to CLAWD_MINT or the Nemo Clawd mint.",
    "  --clawd-decimals N            CLAWD decimals. Defaults to 6.",
    "  --facilitator-url URL         x402 facilitator URL. Defaults to X402_FACILITATOR_URL or x402.org.",
    "  --kora-rpc URL                Kora RPC URL. Defaults to KORA_RPC_URL or http://127.0.0.1:8080.",
    "  --price-source NAME           Kora price source. Defaults to KORA_PRICE_SOURCE or Mock.",
    "  --resource-url URL            Absolute protected resource URL.",
    "  --origin URL                  Worker origin used with --path when --resource-url is not provided.",
    "  --path PATH                   Protected resource path. Defaults to /api/paid.",
    "  --method METHOD               Protected method. Defaults to GET.",
    "  --description TEXT            x402 payment description.",
    "  --mime-type TYPE              x402 resource mime type. Defaults to application/json.",
    "  --json                        Print JSON instead of Markdown.",
    "  --out PATH                    Write JSON report to PATH.",
    "  --markdown PATH               Write Markdown report to PATH.",
    "  --kora-toml-out PATH          Write generated Kora TOML fragment to PATH.",
    "  --cloudflare-snippet-out PATH Write generated Cloudflare Worker snippet to PATH.",
    "  --payment-required-out PATH   Write base64 PAYMENT-REQUIRED header value to PATH.",
    "  --help                        Show this message.",
  ].join("\n");
}

async function main(): Promise<void> {
  const args = parseArgs(process.argv.slice(2));
  if (Object.hasOwn(args, "help") || Object.hasOwn(args, "h")) {
    console.log(usage());
    return;
  }

  const report = buildSolanaPaymentsReport({
    network: parseNetwork(args.network),
    recipient: args.recipient || process.env.SOLANA_PAYMENT_RECIPIENT,
    amount: args.amount,
    tokenSymbols: parsePaymentTokenSymbols(args.tokens),
    openUsdMint: args.openusdMint || process.env.OPENUSD_MINT || process.env.SOLANA_OPENUSD_MINT,
    openUsdDecimals: parseOptionalInt(args.openusdDecimals),
    clawdMint: args.clawdMint || process.env.CLAWD_MINT,
    clawdDecimals: parseOptionalInt(args.clawdDecimals),
    facilitatorUrl: args.facilitatorUrl || process.env.X402_FACILITATOR_URL,
    koraRpcUrl: args.koraRpc || process.env.KORA_RPC_URL,
    priceSource: args.priceSource || process.env.KORA_PRICE_SOURCE,
    method: args.method,
    resourceUrl: buildResourceUrl(args.resourceUrl, args.origin, args.path),
    description: args.description,
    mimeType: args.mimeType,
  });

  const markdown = renderSolanaPaymentsMarkdown(report);
  if (args.out) {
    ensureParentDir(args.out);
    writeJson(args.out, report);
  }
  if (args.markdown) {
    ensureParentDir(args.markdown);
    fs.writeFileSync(args.markdown, markdown);
  }
  if (args.koraTomlOut) {
    ensureParentDir(args.koraTomlOut);
    fs.writeFileSync(args.koraTomlOut, report.kora.toml);
  }
  if (args.cloudflareSnippetOut) {
    ensureParentDir(args.cloudflareSnippetOut);
    fs.writeFileSync(args.cloudflareSnippetOut, report.cloudflare.snippet);
  }
  if (args.paymentRequiredOut) {
    ensureParentDir(args.paymentRequiredOut);
    fs.writeFileSync(args.paymentRequiredOut, `${report.x402.encodedPaymentRequired}\n`);
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

function parseNetwork(value: string | undefined): SolanaPaymentNetwork | undefined {
  if (!value) return undefined;
  if (value === "devnet" || value === "mainnet") return value;
  throw new Error(`Unsupported --network value: ${value}`);
}

function parseOptionalInt(value: string | undefined): number | undefined {
  if (!value) return undefined;
  const parsed = Number.parseInt(value, 10);
  if (!Number.isInteger(parsed) || parsed < 0) {
    throw new Error(`Expected a non-negative integer, got: ${value}`);
  }
  return parsed;
}

function buildResourceUrl(
  resourceUrl: string | undefined,
  origin: string | undefined,
  resourcePath: string | undefined,
): string | undefined {
  if (resourceUrl) return resourceUrl;
  const resolvedOrigin = origin || process.env.CLOUDFLARE_WORKER_URL || process.env.WORKER_URL;
  if (!resolvedOrigin) return undefined;
  return new URL(resourcePath || "/api/paid", resolvedOrigin).toString();
}

function ensureParentDir(filePath: string): void {
  fs.mkdirSync(path.dirname(path.resolve(process.cwd(), filePath)), { recursive: true });
}
