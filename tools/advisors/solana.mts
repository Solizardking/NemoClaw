// SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: Apache-2.0

export const DEFAULT_SOLANA_RPC_URL = "https://rpc.solanatracker.io/public";
export const SOLANA_READINESS_TOOL = "tools/e2e/solana-readiness.mts";
export const SOLANA_READINESS_COMMAND =
  "node --experimental-strip-types tools/e2e/solana-readiness.mts --no-network --json";

export type SolanaCluster =
  | "local-validator"
  | "devnet"
  | "testnet"
  | "mainnet"
  | "custom"
  | "unconfigured";

export type SolanaRpcCallResult<T = unknown> =
  | {
      ok: true;
      method: string;
      result: T;
      latencyMs: number;
    }
  | {
      ok: false;
      method: string;
      error: string;
      latencyMs: number;
    };

export type SolanaReadinessReport = {
  name: "nemoclawd-solana-readiness";
  version: 1;
  mode: "dry-run";
  status: "ready" | "blocked" | "skipped";
  generatedAt: string;
  rpc: {
    url: string | null;
    cluster: SolanaCluster;
    expectedCluster?: SolanaCluster;
    networkSkipped: boolean;
    health?: unknown;
    version?: unknown;
    epochInfo?: unknown;
    latestBlockhash?: unknown;
    latencyMs?: number;
    errors: string[];
  };
  wallet: {
    configured: boolean;
    address: string | null;
    validAddress: boolean;
    balanceLamports?: number | null;
  };
  policyHints: {
    requiredPresets: string[];
    optionalPresets: string[];
  };
  guardrails: {
    signingEnabled: false;
    transactionSubmissionEnabled: false;
    privateKeyMaterialAllowed: false;
  };
  blockers: string[];
  nextCommands: string[];
};

type FetchLike = (input: string, init: RequestInit) => Promise<Response>;

const REDACTED_QUERY_KEYS = new Set([
  "api-key",
  "apikey",
  "api_key",
  "key",
  "token",
  "access-token",
  "access_token",
  "auth",
  "password",
  "jwt",
]);

const BASE58_ADDRESS_PATTERN = /^[1-9A-HJ-NP-Za-km-z]{32,44}$/;

export function inferSolanaCluster(rpcUrl: string | undefined | null): SolanaCluster {
  if (!rpcUrl) return "unconfigured";
  const value = String(rpcUrl).toLowerCase();
  if (value.includes("localhost") || value.includes("127.0.0.1") || value.includes("[::1]")) {
    return "local-validator";
  }
  if (value.includes("devnet")) return "devnet";
  if (value.includes("testnet")) return "testnet";
  if (
    value.includes("mainnet") ||
    value.includes("solanatracker") ||
    value.includes("helius") ||
    value.includes("ankr.com/solana")
  ) {
    return "mainnet";
  }
  return "custom";
}

export function redactRpcUrl(rawUrl: string | undefined | null): string | null {
  if (!rawUrl) return null;
  try {
    const url = new URL(rawUrl);
    for (const key of [...url.searchParams.keys()]) {
      if (REDACTED_QUERY_KEYS.has(key.toLowerCase())) {
        url.searchParams.set(key, "redacted");
      }
    }
    return url.toString();
  } catch {
    return rawUrl.replace(
      /([?&](?:api[-_]?key|apikey|key|token|access[-_]?token|auth|password|jwt)=)[^&\s]+/gi,
      "$1redacted",
    );
  }
}

export function isLikelySolanaAddress(value: string | undefined | null): boolean {
  return Boolean(value && BASE58_ADDRESS_PATTERN.test(value));
}

export function policyHintsForSolana(input: {
  cluster: SolanaCluster;
  walletConfigured?: boolean;
  privyConfigured?: boolean;
  telegramConfigured?: boolean;
}): { requiredPresets: string[]; optionalPresets: string[] } {
  const required = new Set<string>();
  const optional = new Set(["telegram", "pumpfun"]);
  if (input.cluster !== "local-validator" && input.cluster !== "unconfigured") {
    required.add("solana-rpc");
  }
  if (input.privyConfigured) required.add("privy");
  if (input.telegramConfigured) required.add("telegram");
  if (input.walletConfigured && !input.privyConfigured) optional.add("privy");
  return {
    requiredPresets: [...required].sort(),
    optionalPresets: [...optional].filter((preset) => !required.has(preset)).sort(),
  };
}

export async function callSolanaRpc<T = unknown>(input: {
  rpcUrl: string;
  method: string;
  params?: unknown[];
  fetchImpl?: FetchLike;
  timeoutMs?: number;
}): Promise<SolanaRpcCallResult<T>> {
  const startedAt = Date.now();
  const fetchImpl = input.fetchImpl || fetch;
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), input.timeoutMs || 10000);
  try {
    const response = await fetchImpl(input.rpcUrl, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        jsonrpc: "2.0",
        id: input.method,
        method: input.method,
        params: input.params || [],
      }),
      signal: controller.signal,
    });
    const text = await response.text();
    if (!response.ok) {
      return rpcError(input.method, `HTTP ${response.status}: ${text.slice(0, 240)}`, startedAt);
    }
    let payload: unknown;
    try {
      payload = JSON.parse(text);
    } catch {
      return rpcError(input.method, `non-JSON response: ${text.slice(0, 240)}`, startedAt);
    }
    if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
      return rpcError(input.method, "JSON-RPC response was not an object", startedAt);
    }
    const object = payload as Record<string, unknown>;
    if (object.error) {
      return rpcError(input.method, JSON.stringify(object.error), startedAt);
    }
    return {
      ok: true,
      method: input.method,
      result: object.result as T,
      latencyMs: Date.now() - startedAt,
    };
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : String(error);
    return rpcError(input.method, message, startedAt);
  } finally {
    clearTimeout(timeout);
  }
}

export async function buildSolanaReadinessReport(input: {
  rpcUrl?: string;
  expectedCluster?: SolanaCluster;
  walletAddress?: string;
  privyConfigured?: boolean;
  telegramConfigured?: boolean;
  noNetwork?: boolean;
  fetchImpl?: FetchLike;
  timeoutMs?: number;
  now?: Date;
}): Promise<SolanaReadinessReport> {
  const rpcUrl = input.rpcUrl || DEFAULT_SOLANA_RPC_URL;
  const cluster = inferSolanaCluster(rpcUrl);
  const walletAddress = input.walletAddress || null;
  const validAddress = isLikelySolanaAddress(walletAddress);
  const blockers: string[] = [];
  const errors: string[] = [];
  const nextCommands = [
    "nemoclawd solana",
    "nemoclawd financial-harness <sandbox>",
    "nemoclawd <sandbox> policy-list",
  ];

  if (input.expectedCluster && input.expectedCluster !== cluster) {
    blockers.push(`expected ${input.expectedCluster} RPC but inferred ${cluster}`);
  }
  if (walletAddress && !validAddress) {
    blockers.push("wallet address is not a valid Solana base58 address shape");
  }

  let health: unknown;
  let version: unknown;
  let epochInfo: unknown;
  let latestBlockhash: unknown;
  let balanceLamports: number | null | undefined;
  let latencyMs: number | undefined;

  if (!input.noNetwork) {
    const probes = [
      await callSolanaRpc({ ...input, rpcUrl, method: "getHealth" }),
      await callSolanaRpc({ ...input, rpcUrl, method: "getVersion" }),
      await callSolanaRpc({ ...input, rpcUrl, method: "getEpochInfo" }),
      await callSolanaRpc({ ...input, rpcUrl, method: "getLatestBlockhash" }),
    ];
    if (walletAddress && validAddress) {
      probes.push(await callSolanaRpc({ ...input, rpcUrl, method: "getBalance", params: [walletAddress] }));
    }
    latencyMs = probes.reduce((total, probe) => total + probe.latencyMs, 0);
    for (const probe of probes) {
      if (!probe.ok) {
        errors.push(`${probe.method}: ${probe.error}`);
        continue;
      }
      if (probe.method === "getHealth") health = probe.result;
      if (probe.method === "getVersion") version = probe.result;
      if (probe.method === "getEpochInfo") epochInfo = probe.result;
      if (probe.method === "getLatestBlockhash") latestBlockhash = probe.result;
      if (probe.method === "getBalance") {
        balanceLamports = extractLamports(probe.result);
      }
    }
    if (errors.length > 0) {
      blockers.push(`Solana RPC probe failed: ${errors.slice(0, 2).join("; ")}`);
    }
  }

  const policyHints = policyHintsForSolana({
    cluster,
    walletConfigured: Boolean(walletAddress),
    privyConfigured: input.privyConfigured,
    telegramConfigured: input.telegramConfigured,
  });

  const status = blockers.length > 0 ? "blocked" : input.noNetwork ? "skipped" : "ready";
  return {
    name: "nemoclawd-solana-readiness",
    version: 1,
    mode: "dry-run",
    status,
    generatedAt: (input.now || new Date()).toISOString(),
    rpc: {
      url: redactRpcUrl(rpcUrl),
      cluster,
      expectedCluster: input.expectedCluster,
      networkSkipped: Boolean(input.noNetwork),
      health,
      version,
      epochInfo,
      latestBlockhash,
      latencyMs,
      errors,
    },
    wallet: {
      configured: Boolean(walletAddress),
      address: walletAddress,
      validAddress,
      balanceLamports,
    },
    policyHints,
    guardrails: {
      signingEnabled: false,
      transactionSubmissionEnabled: false,
      privateKeyMaterialAllowed: false,
    },
    blockers,
    nextCommands,
  };
}

export function renderSolanaReadinessMarkdown(report: SolanaReadinessReport): string {
  const lines: string[] = [];
  lines.push("# Nemo Clawd Solana Readiness");
  lines.push("");
  lines.push(`Status: **${report.status}**`);
  lines.push(`RPC: \`${report.rpc.url || "unconfigured"}\``);
  lines.push(`Cluster: \`${report.rpc.cluster}\``);
  if (report.rpc.expectedCluster) lines.push(`Expected cluster: \`${report.rpc.expectedCluster}\``);
  lines.push(`Network skipped: \`${String(report.rpc.networkSkipped)}\``);
  if (report.wallet.configured) {
    lines.push(`Wallet: \`${report.wallet.address}\``);
    if (report.wallet.balanceLamports !== undefined) {
      lines.push(`Balance: \`${report.wallet.balanceLamports} lamports\``);
    }
  } else {
    lines.push("Wallet: `not configured`");
  }
  lines.push("");
  lines.push("## Policy Hints");
  lines.push(`- Required presets: ${formatInlineList(report.policyHints.requiredPresets)}`);
  lines.push(`- Optional presets: ${formatInlineList(report.policyHints.optionalPresets)}`);
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
  lines.push("## Next Commands");
  for (const command of report.nextCommands) lines.push(`- \`${command}\``);
  return `${lines.join("\n")}\n`;
}

export function classifySolanaChangedFiles(changedFiles: readonly string[]): {
  matchedFiles: string[];
  runtimeFiles: string[];
  policyFiles: string[];
  docsOnly: boolean;
} {
  const matchedFiles = changedFiles.filter(isSolanaRelatedFile);
  const runtimeFiles = matchedFiles.filter(isSolanaRuntimeFile);
  const policyFiles = matchedFiles.filter(isSolanaPolicyFile);
  return {
    matchedFiles,
    runtimeFiles,
    policyFiles,
    docsOnly: matchedFiles.length > 0 && matchedFiles.every(isDocsOnlyFile),
  };
}

export function isSolanaRelatedFile(file: string): boolean {
  return (
    /(^|\/)(solana|wallet|privy|helius|pumpfun|pump-fun|jupiter|birdeye|telegram|x402|kora|openusd|usdc|clawd|payment|payments)/i.test(
      file,
    ) ||
    /^docs\/solana\//.test(file) ||
    /^tools\/(?:advisors|e2e|e2e-advisor|pr-review-advisor)\/.*solana/i.test(file)
  );
}

export function isSolanaRuntimeFile(file: string): boolean {
  return (
    /^bin\/lib\/(?:solana|financial-harness)\.js$/.test(file) ||
    /^scripts\/nemoclawd-(?:solana|telegram|payment|swarm|websocket)/.test(file) ||
    /^tools\/(?:advisors|e2e|e2e-advisor|pr-review-advisor)\/.*solana/i.test(file) ||
    /^agents\/clawd-operator\/.*(?:solana|wallet|privy|helius|pump|telegram|x402|kora|openusd|usdc|payment)/i.test(
      file,
    ) ||
    /^nemo-clawd-mcp\/src\/.*(?:solana|wallet|privy|helius|pump|telegram|x402|kora|openusd|usdc|payment)/i.test(
      file,
    )
  );
}

export function isSolanaPolicyFile(file: string): boolean {
  return (
    /^nemo-clawd-python\/policies\/.*(?:solana|privy|pumpfun|telegram).*\.ya?ml$/i.test(file) ||
    /^nemoclaw-blueprint\/policies\/.*(?:solana|privy|pumpfun|telegram).*\.ya?ml$/i.test(file)
  );
}

function rpcError(method: string, error: string, startedAt: number): SolanaRpcCallResult {
  return {
    ok: false,
    method,
    error,
    latencyMs: Date.now() - startedAt,
  };
}

function extractLamports(result: unknown): number | null {
  if (!result || typeof result !== "object" || Array.isArray(result)) return null;
  const value = (result as Record<string, unknown>).value;
  return typeof value === "number" ? value : null;
}

function formatInlineList(values: string[]): string {
  return values.length === 0 ? "_None._" : values.map((value) => `\`${value}\``).join(", ");
}

function isDocsOnlyFile(file: string): boolean {
  return /\.(md|mdx|txt|json)$/.test(file) || file.startsWith("docs/");
}
