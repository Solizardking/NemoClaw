// SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: Apache-2.0

import { isLikelySolanaAddress } from "./solana.mts";

export const SOLANA_PAYMENTS_TOOL = "tools/e2e/solana-payments.mts";
export const SOLANA_PAYMENTS_COMMAND =
  "node --experimental-strip-types tools/e2e/solana-payments.mts --network devnet --recipient \"$SOLANA_PAYMENT_RECIPIENT\" --tokens usdc,openusd,clawd --openusd-mint \"$OPENUSD_MINT\" --json";

export const CLAWD_MINT = "8cHzQHUS2s2h8TzCmfqPKYiM4dSt4roa3n7MyRLApump";
export const USDC_MAINNET_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v";
export const USDC_DEVNET_MINT = "4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU";
export const SOLANA_MAINNET_CAIP2 = "solana:5eykt4UsFv8P8NJdTREpY1vzqKqZKvdp";
export const SOLANA_DEVNET_CAIP2 = "solana:EtWTRABZaYq6iMfeYKouRu166VU2xqa1";

export type SolanaPaymentNetwork = "mainnet" | "devnet";
export type PaymentTokenSymbol = "usdc" | "openusd" | "clawd";

export type SolanaPaymentToken = {
  symbol: PaymentTokenSymbol;
  displayName: string;
  mint: string | null;
  decimals: number;
  amount: string;
  amountAtomicUnits: string;
  stablecoin: boolean;
  configured: boolean;
  role: "stablecoin" | "utility-token";
};

export type X402ExactPaymentRequirement = {
  scheme: "exact";
  network: string;
  payTo: string;
  maxAmountRequired: string;
  asset: string;
  resource: string;
  description: string;
  mimeType: string;
  maxTimeoutSeconds: number;
  extra: {
    token: string;
    tokenName: string;
    decimals: number;
    amount: string;
    amountInAtomicUnits: string;
  };
};

export type X402PaymentRequiredPayload = {
  x402Version: 2;
  error: "Payment required";
  accepts: X402ExactPaymentRequirement[];
};

export type SolanaPaymentsReport = {
  name: "nemoclawd-solana-payments";
  version: 1;
  mode: "dry-run-config";
  status: "ready" | "blocked";
  generatedAt: string;
  network: {
    name: SolanaPaymentNetwork;
    caip2: string;
    facilitatorUrl: string;
    koraRpcUrl: string | null;
  };
  recipient: {
    address: string | null;
    validAddress: boolean;
  };
  resource: {
    method: string;
    url: string;
    description: string;
    mimeType: string;
  };
  tokens: SolanaPaymentToken[];
  x402: {
    version: 2;
    scheme: "exact";
    requiredHeaders: string[];
    paymentRequired: X402PaymentRequiredPayload;
    paymentRequiredHeaderName: "PAYMENT-REQUIRED";
    encodedPaymentRequired: string;
    facilitatorVerifyEndpoint: string;
    facilitatorSettleEndpoint: string;
  };
  cloudflare: {
    requiredEnv: string[];
    snippet: string;
  };
  kora: {
    priceSource: string;
    initializeAtasCommand: string;
    startCommand: string;
    supportedMethods: string[];
    toml: string;
  };
  guardrails: {
    signingEnabled: false;
    transactionSubmissionEnabled: false;
    privateKeyMaterialAllowed: false;
    generatedArtifactsOnly: true;
  };
  blockers: string[];
  warnings: string[];
  nextCommands: string[];
};

export type BuildSolanaPaymentsReportInput = {
  network?: SolanaPaymentNetwork;
  recipient?: string;
  amount?: string;
  tokenSymbols?: PaymentTokenSymbol[];
  openUsdMint?: string;
  openUsdDecimals?: number;
  clawdMint?: string;
  clawdDecimals?: number;
  facilitatorUrl?: string;
  koraRpcUrl?: string;
  priceSource?: string;
  method?: string;
  resourceUrl?: string;
  description?: string;
  mimeType?: string;
  maxTimeoutSeconds?: number;
  now?: Date;
};

const DEFAULT_AMOUNT = "0.01";
const DEFAULT_FACILITATOR_URL = "https://x402.org/facilitator";
const DEFAULT_KORA_RPC_URL = "http://127.0.0.1:8080";
const DEFAULT_RESOURCE_URL = "https://nemoclawd.local/api/paid";
const DEFAULT_DESCRIPTION = "Nemo Clawd Solana AI payment gate";
const DEFAULT_MIME_TYPE = "application/json";
const DEFAULT_MAX_TIMEOUT_SECONDS = 300;
const TOKEN_PROGRAM = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA";
const ASSOCIATED_TOKEN_PROGRAM = "ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL";
const SYSTEM_PROGRAM = "11111111111111111111111111111111";
const COMPUTE_BUDGET_PROGRAM = "ComputeBudget111111111111111111111111111111";
const ADDRESS_LOOKUP_TABLE_PROGRAM = "AddressLookupTab1e1111111111111111111111111";

export function parsePaymentTokenSymbols(value: string | undefined): PaymentTokenSymbol[] {
  const raw = value || "usdc,openusd,clawd";
  const symbols = raw
    .split(",")
    .map((item) => item.trim().toLowerCase())
    .filter(Boolean);
  const unique: PaymentTokenSymbol[] = [];
  for (const symbol of symbols) {
    if (symbol !== "usdc" && symbol !== "openusd" && symbol !== "clawd") {
      throw new Error(`Unsupported payment token "${symbol}". Use usdc, openusd, and/or clawd.`);
    }
    if (!unique.includes(symbol)) unique.push(symbol);
  }
  if (unique.length === 0) {
    throw new Error("At least one payment token is required.");
  }
  return unique;
}

export function buildSolanaPaymentsReport(input: BuildSolanaPaymentsReportInput): SolanaPaymentsReport {
  const network = input.network || "devnet";
  const recipient = cleanOptional(input.recipient);
  const amount = input.amount || DEFAULT_AMOUNT;
  const tokenSymbols = input.tokenSymbols || ["usdc", "openusd", "clawd"];
  const openUsdMint = cleanOptional(input.openUsdMint);
  const clawdMint = cleanOptional(input.clawdMint) || CLAWD_MINT;
  const facilitatorUrl = stripTrailingSlash(input.facilitatorUrl || DEFAULT_FACILITATOR_URL);
  const koraRpcUrl = cleanOptional(input.koraRpcUrl) || DEFAULT_KORA_RPC_URL;
  const method = (input.method || "GET").toUpperCase();
  const resourceUrl = input.resourceUrl || DEFAULT_RESOURCE_URL;
  const description = input.description || DEFAULT_DESCRIPTION;
  const mimeType = input.mimeType || DEFAULT_MIME_TYPE;
  const maxTimeoutSeconds = input.maxTimeoutSeconds || DEFAULT_MAX_TIMEOUT_SECONDS;
  const blockers: string[] = [];
  const warnings: string[] = [];

  if (!recipient) {
    blockers.push("SOLANA_PAYMENT_RECIPIENT or --recipient is required.");
  } else if (!isLikelySolanaAddress(recipient)) {
    blockers.push("payment recipient is not a valid Solana base58 address shape.");
  }

  if (!isHttpUrl(resourceUrl)) {
    blockers.push("--resource-url must be an absolute http(s) URL for x402 resource binding.");
  }

  const tokens = tokenSymbols.map((symbol) =>
    buildToken({
      symbol,
      network,
      amount,
      openUsdMint,
      openUsdDecimals: input.openUsdDecimals,
      clawdMint,
      clawdDecimals: input.clawdDecimals,
    }),
  );

  for (const token of tokens) {
    if (!token.configured) {
      blockers.push(`${token.displayName} mint is not configured.`);
    }
    if (token.mint && !isLikelySolanaAddress(token.mint)) {
      blockers.push(`${token.displayName} mint is not a valid Solana base58 address shape.`);
    }
  }

  const configuredTokens = tokens.filter((token) => token.configured && token.mint);
  const paymentRequired: X402PaymentRequiredPayload = {
    x402Version: 2,
    error: "Payment required",
    accepts: configuredTokens.map((token) => ({
      scheme: "exact",
      network: caip2ForNetwork(network),
      payTo: recipient || "",
      maxAmountRequired: token.amountAtomicUnits,
      asset: token.mint || "",
      resource: resourceUrl,
      description: `${description} (${token.displayName})`,
      mimeType,
      maxTimeoutSeconds,
      extra: {
        token: token.symbol,
        tokenName: token.displayName,
        decimals: token.decimals,
        amount: token.amount,
        amountInAtomicUnits: token.amountAtomicUnits,
      },
    })),
  };

  if (paymentRequired.accepts.length === 0) {
    blockers.push("no configured payment tokens are available for the x402 accepts list.");
  }

  if (tokens.some((token) => token.symbol === "openusd" && !token.configured)) {
    warnings.push("OpenUSD support is enabled only after OPENUSD_MINT or --openusd-mint is set.");
  }
  if (input.priceSource?.toLowerCase() === "jupiter") {
    warnings.push("Kora price_source=Jupiter requires JUPITER_API_KEY in the Kora runtime environment.");
  }

  const encodedPaymentRequired = encodePaymentRequired(paymentRequired);
  const report: SolanaPaymentsReport = {
    name: "nemoclawd-solana-payments",
    version: 1,
    mode: "dry-run-config",
    status: blockers.length > 0 ? "blocked" : "ready",
    generatedAt: (input.now || new Date()).toISOString(),
    network: {
      name: network,
      caip2: caip2ForNetwork(network),
      facilitatorUrl,
      koraRpcUrl,
    },
    recipient: {
      address: recipient,
      validAddress: Boolean(recipient && isLikelySolanaAddress(recipient)),
    },
    resource: {
      method,
      url: resourceUrl,
      description,
      mimeType,
    },
    tokens,
    x402: {
      version: 2,
      scheme: "exact",
      requiredHeaders: ["PAYMENT-REQUIRED", "PAYMENT-SIGNATURE", "PAYMENT-RESPONSE"],
      paymentRequired,
      paymentRequiredHeaderName: "PAYMENT-REQUIRED",
      encodedPaymentRequired,
      facilitatorVerifyEndpoint: `${facilitatorUrl}/verify`,
      facilitatorSettleEndpoint: `${facilitatorUrl}/settle`,
    },
    cloudflare: {
      requiredEnv: [
        "SOLANA_PAYMENT_RECIPIENT",
        "X402_FACILITATOR_URL",
        "SOLANA_RPC_URL",
        "KORA_RPC_URL",
        "OPENUSD_MINT",
        "CLAWD_MINT",
      ],
      snippet: renderCloudflareWorkerSnippet({
        method,
        resourceUrl,
        paymentRequired,
        facilitatorUrl,
      }),
    },
    kora: {
      priceSource: input.priceSource || "Mock",
      initializeAtasCommand: "kora rpc initialize-atas --signers-config signers.toml",
      startCommand: "kora rpc start --signers-config signers.toml",
      supportedMethods: [
        "estimateTransactionFee",
        "getPayerSigner",
        "getSupportedTokens",
        "getPaymentInstruction",
        "signTransaction",
        "transferTransaction",
        "signAndSendTransaction",
      ],
      toml: renderKoraToml({
        tokens: configuredTokens,
        priceSource: input.priceSource || "Mock",
        maxAllowedLamports: 1000000,
      }),
    },
    guardrails: {
      signingEnabled: false,
      transactionSubmissionEnabled: false,
      privateKeyMaterialAllowed: false,
      generatedArtifactsOnly: true,
    },
    blockers,
    warnings,
    nextCommands: [
      SOLANA_PAYMENTS_COMMAND,
      "wrangler secret put SOLANA_PAYMENT_RECIPIENT",
      "wrangler secret put X402_FACILITATOR_URL",
      "kora rpc initialize-atas --signers-config signers.toml",
      "kora rpc start --signers-config signers.toml",
    ],
  };

  return report;
}

export function encodePaymentRequired(payload: X402PaymentRequiredPayload): string {
  return Buffer.from(JSON.stringify(payload)).toString("base64");
}

export function decodePaymentRequiredHeader(value: string): X402PaymentRequiredPayload {
  return JSON.parse(Buffer.from(value, "base64").toString("utf8")) as X402PaymentRequiredPayload;
}

export function decimalToAtomicUnits(value: string, decimals: number): string {
  if (!Number.isInteger(decimals) || decimals < 0 || decimals > 18) {
    throw new Error(`Unsupported decimals value: ${decimals}`);
  }
  const trimmed = value.trim();
  if (!/^\d+(\.\d+)?$/.test(trimmed)) {
    throw new Error(`Invalid token amount: ${value}`);
  }
  const [wholePart, fractionalPart = ""] = trimmed.split(".");
  if (fractionalPart.length > decimals) {
    throw new Error(`Amount ${value} has more than ${decimals} decimal places.`);
  }
  const multiplier = 10n ** BigInt(decimals);
  const whole = BigInt(wholePart || "0") * multiplier;
  const fractional = BigInt((fractionalPart || "").padEnd(decimals, "0") || "0");
  const atomic = whole + fractional;
  if (atomic <= 0n) {
    throw new Error("Payment amount must be greater than zero.");
  }
  return atomic.toString();
}

export function renderSolanaPaymentsMarkdown(report: SolanaPaymentsReport): string {
  const lines: string[] = [];
  lines.push("# Nemo Clawd Solana Payments");
  lines.push("");
  lines.push(`Status: **${report.status}**`);
  lines.push(`Network: \`${report.network.name}\` (${report.network.caip2})`);
  lines.push(`Recipient: \`${report.recipient.address || "unconfigured"}\``);
  lines.push(`Resource: \`${report.resource.method} ${report.resource.url}\``);
  lines.push("");
  lines.push("## Tokens");
  for (const token of report.tokens) {
    const mint = token.mint || "unconfigured";
    lines.push(
      `- ${token.displayName}: \`${mint}\`, amount \`${token.amountAtomicUnits}\` atomic units, configured \`${String(token.configured)}\``,
    );
  }
  lines.push("");
  lines.push("## x402");
  lines.push(`- Header: \`${report.x402.paymentRequiredHeaderName}: ${report.x402.encodedPaymentRequired}\``);
  lines.push(`- Verify endpoint: \`${report.x402.facilitatorVerifyEndpoint}\``);
  lines.push(`- Settle endpoint: \`${report.x402.facilitatorSettleEndpoint}\``);
  lines.push("");
  lines.push("## Cloudflare");
  lines.push(`- Required env: ${formatInlineList(report.cloudflare.requiredEnv)}`);
  lines.push("");
  lines.push("## Kora");
  lines.push(`- Price source: \`${report.kora.priceSource}\``);
  lines.push(`- Initialize ATAs: \`${report.kora.initializeAtasCommand}\``);
  lines.push(`- Start RPC: \`${report.kora.startCommand}\``);
  lines.push("");
  lines.push("## Guardrails");
  lines.push("- Signing enabled: `false`");
  lines.push("- Transaction submission enabled: `false`");
  lines.push("- Private key material allowed: `false`");
  lines.push("");
  lines.push("## Blockers");
  if (report.blockers.length === 0) {
    lines.push("- _None._");
  } else {
    for (const blocker of report.blockers) lines.push(`- ${blocker}`);
  }
  lines.push("");
  lines.push("## Warnings");
  if (report.warnings.length === 0) {
    lines.push("- _None._");
  } else {
    for (const warning of report.warnings) lines.push(`- ${warning}`);
  }
  return `${lines.join("\n")}\n`;
}

function buildToken(input: {
  symbol: PaymentTokenSymbol;
  network: SolanaPaymentNetwork;
  amount: string;
  openUsdMint?: string;
  openUsdDecimals?: number;
  clawdMint: string;
  clawdDecimals?: number;
}): SolanaPaymentToken {
  const decimals =
    input.symbol === "clawd" ? input.clawdDecimals ?? 6 : input.symbol === "openusd" ? input.openUsdDecimals ?? 6 : 6;
  const mint = mintForToken(input.symbol, input.network, input.openUsdMint, input.clawdMint);
  return {
    symbol: input.symbol,
    displayName: displayNameForToken(input.symbol),
    mint,
    decimals,
    amount: input.amount,
    amountAtomicUnits: decimalToAtomicUnits(input.amount, decimals),
    stablecoin: input.symbol === "usdc" || input.symbol === "openusd",
    configured: Boolean(mint),
    role: input.symbol === "clawd" ? "utility-token" : "stablecoin",
  };
}

function mintForToken(
  symbol: PaymentTokenSymbol,
  network: SolanaPaymentNetwork,
  openUsdMint: string | undefined,
  clawdMint: string,
): string | null {
  if (symbol === "usdc") return network === "mainnet" ? USDC_MAINNET_MINT : USDC_DEVNET_MINT;
  if (symbol === "openusd") return openUsdMint || null;
  return clawdMint;
}

function displayNameForToken(symbol: PaymentTokenSymbol): string {
  if (symbol === "usdc") return "USDC";
  if (symbol === "openusd") return "OpenUSD";
  return "CLAWD";
}

function caip2ForNetwork(network: SolanaPaymentNetwork): string {
  return network === "mainnet" ? SOLANA_MAINNET_CAIP2 : SOLANA_DEVNET_CAIP2;
}

function renderKoraToml(input: {
  tokens: SolanaPaymentToken[];
  priceSource: string;
  maxAllowedLamports: number;
}): string {
  const mints = [
    ...new Set(input.tokens.map((token) => token.mint).filter((mint): mint is string => Boolean(mint))),
  ];
  const quotedMints = mints.map((mint) => `  "${mint}",`).join("\n");
  return [
    "# Nemo Clawd Solana payment policy for Kora RPC.",
    "# Keep signers.toml out of source control and initialize ATAs before starting the service.",
    `price_source = "${escapeToml(input.priceSource)}"`,
    `max_allowed_lamports = ${input.maxAllowedLamports}`,
    "max_signatures = 10",
    "",
    "allowed_tokens = [",
    quotedMints,
    "]",
    "",
    "allowed_spl_paid_tokens = [",
    quotedMints,
    "]",
    "",
    "allowed_programs = [",
    `  "${SYSTEM_PROGRAM}",`,
    `  "${TOKEN_PROGRAM}",`,
    `  "${ASSOCIATED_TOKEN_PROGRAM}",`,
    `  "${COMPUTE_BUDGET_PROGRAM}",`,
    `  "${ADDRESS_LOOKUP_TABLE_PROGRAM}",`,
    "]",
    "",
  ].join("\n");
}

function renderCloudflareWorkerSnippet(input: {
  method: string;
  resourceUrl: string;
  paymentRequired: X402PaymentRequiredPayload;
  facilitatorUrl: string;
}): string {
  const path = pathFromResourceUrl(input.resourceUrl);
  const paymentRequiredJson = JSON.stringify(input.paymentRequired, null, 2);
  return [
    "const paymentRequired = " + paymentRequiredJson + ";",
    "",
    "export default {",
    "  async fetch(request, env) {",
    "    const url = new URL(request.url);",
    `    if (request.method === "${input.method}" && url.pathname === "${path}") {`,
    "      const paymentSignature = request.headers.get(\"PAYMENT-SIGNATURE\");",
    "      if (!paymentSignature) {",
    "        return new Response(JSON.stringify(paymentRequired), {",
    "          status: 402,",
    "          headers: {",
    "            \"content-type\": \"application/json\",",
    "            \"PAYMENT-REQUIRED\": btoa(JSON.stringify(paymentRequired)),",
    "          },",
    "        });",
    "      }",
    `      const verify = await fetch((env.X402_FACILITATOR_URL || "${input.facilitatorUrl}") + "/verify", {`,
    "        method: \"POST\",",
    "        headers: { \"content-type\": \"application/json\" },",
    "        body: JSON.stringify({ payment: paymentSignature, paymentRequirements: paymentRequired.accepts }),",
    "      });",
    "      if (!verify.ok) return new Response(await verify.text(), { status: 402 });",
    "      return Response.json({ ok: true, paid: true });",
    "    }",
    "    return new Response(\"not found\", { status: 404 });",
    "  },",
    "};",
    "",
  ].join("\n");
}

function pathFromResourceUrl(value: string): string {
  try {
    return new URL(value).pathname;
  } catch {
    return "/api/paid";
  }
}

function cleanOptional(value: string | undefined | null): string | null {
  const cleaned = value?.trim();
  return cleaned ? cleaned : null;
}

function stripTrailingSlash(value: string): string {
  return value.replace(/\/+$/, "");
}

function isHttpUrl(value: string): boolean {
  try {
    const url = new URL(value);
    return url.protocol === "http:" || url.protocol === "https:";
  } catch {
    return false;
  }
}

function escapeToml(value: string): string {
  return value.replace(/\\/g, "\\\\").replace(/"/g, '\\"');
}

function formatInlineList(values: string[]): string {
  return values.length === 0 ? "_None._" : values.map((value) => `\`${value}\``).join(", ");
}
