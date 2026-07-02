// SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: Apache-2.0

import { execFileSync } from "node:child_process";
import type { NemoclawdConfig, PluginLogger } from "../index.js";

const OPENROUTER_ENDPOINT = "https://openrouter.ai/api/v1";
const NVIDIA_ENDPOINT = "https://integrate.api.nvidia.com/v1";
const XAI_ENDPOINT = "https://api.x.ai/v1";

export type MagicRouterIntent =
  | "solana-trading"
  | "solana-research"
  | "code"
  | "vision"
  | "long-context"
  | "fast-chat"
  | "general";

export type MagicRouterBudget = "low" | "balanced" | "premium";

export interface MagicRouterOptions {
  goal?: string;
  budget?: string;
  useOpenRouter?: boolean;
  offline?: boolean;
  apply?: boolean;
  json?: boolean;
  logger: PluginLogger;
  pluginConfig: NemoclawdConfig;
  env?: NodeJS.ProcessEnv;
  fetchImpl?: typeof fetch;
  execFileSyncImpl?: typeof execFileSync;
}

export interface ToolSetRecommendation {
  id: string;
  label: string;
  tools: string[];
  requiredEnv: string[];
  policyPresets: string[];
  reason: string;
}

export interface CandidateModel {
  provider: "xai-grok" | "nvidia-nim" | "openrouter";
  model: string;
  label: string;
  endpoint: string;
  credentialEnv: string;
  contextWindow: number | null;
  maxOutput: number | null;
  supportsTools: boolean;
  supportsVision: boolean;
  supportsReasoning: boolean;
  inputCostPerMillion: number | null;
  outputCostPerMillion: number | null;
  source: "bundled" | "openrouter";
}

export interface ScoredCandidate extends CandidateModel {
  score: number;
  reasons: string[];
}

export interface MagicRouterRecommendation {
  goal: string;
  intent: MagicRouterIntent;
  budget: MagicRouterBudget;
  provider: string;
  model: string;
  endpoint: string;
  credentialEnv: string;
  score: number;
  reasons: string[];
  tools: ToolSetRecommendation[];
  applyCommands: string[];
  openRouter: {
    used: boolean;
    modelCount: number;
    error: string | null;
  };
  warnings: string[];
}

interface OpenRouterModel {
  id?: unknown;
  name?: unknown;
  context_length?: unknown;
  supported_parameters?: unknown;
  pricing?: unknown;
  architecture?: unknown;
  top_provider?: unknown;
}

interface OpenRouterModelsResponse {
  data?: OpenRouterModel[];
}

interface Pricing {
  prompt?: unknown;
  completion?: unknown;
}

interface Architecture {
  modality?: unknown;
}

interface TopProvider {
  max_completion_tokens?: unknown;
}

const SOLANA_MARKET_TOOLS = [
  "solana_price",
  "solana_trending",
  "solana_token_info",
  "solana_wallet_pnl",
  "solana_search",
  "solana_top_traders",
  "solana_wallet_tokens",
  "sol_price",
];

const HELIUS_TOOLS = [
  "helius_account_info",
  "helius_balance",
  "helius_transactions",
  "helius_priority_fee",
  "helius_das_asset",
  "helius_webhook_create",
];

const PUMP_TOOLS = [
  "pump_token_scan",
  "pump_buy_quote",
  "pump_sell_quote",
  "pump_graduation",
  "pump_market_cap",
  "pump_top_tokens",
  "pump_new_tokens",
];

const RESEARCH_TOOLS = [
  "grok_chat",
  "grok_x_search",
  "grok_web_search",
  "grok_deep_research",
  "memory_recall",
  "memory_write",
];

function normalizeBudget(raw: string | undefined): MagicRouterBudget {
  if (raw === "low" || raw === "balanced" || raw === "premium") return raw;
  return "balanced";
}

export function inferMagicRouterIntent(goal: string): MagicRouterIntent {
  const text = goal.toLowerCase();
  if (/(trade|swap|pump|token|wallet|pnl|jupiter|solana|defi|market|price|launch)/.test(text)) {
    return /(research|scan|analy[sz]e|watch|monitor|trend)/.test(text)
      ? "solana-research"
      : "solana-trading";
  }
  if (/(code|test|debug|patch|refactor|repo|typescript|python|shell)/.test(text)) return "code";
  if (/(image|vision|screenshot|chart|visual|picture)/.test(text)) return "vision";
  if (/(long|docs|document|large context|book|transcript|audit)/.test(text)) return "long-context";
  if (/(fast|latency|quick|realtime|real-time)/.test(text)) return "fast-chat";
  return "general";
}

export function recommendMagicRouterTools(intent: MagicRouterIntent): ToolSetRecommendation[] {
  if (intent === "solana-trading") {
    return [
      {
        id: "solana-market",
        label: "Solana market data",
        tools: SOLANA_MARKET_TOOLS,
        requiredEnv: ["HELIUS_API_KEY"],
        policyPresets: ["solana-rpc"],
        reason: "Observe price, trend, wallet, and token state before any action.",
      },
      {
        id: "pumpfun-guarded",
        label: "Pump.fun guarded execution",
        tools: PUMP_TOOLS,
        requiredEnv: ["HELIUS_API_KEY"],
        policyPresets: ["pumpfun", "solana-rpc"],
        reason: "Quote and inspect token launches while keeping execution behind operator approval.",
      },
      {
        id: "wallet-guardrails",
        label: "Wallet and signing guardrails",
        tools: ["helius_balance", "helius_priority_fee", "memory_write"],
        requiredEnv: ["SOLANA_RPC_URL"],
        policyPresets: ["solana-rpc", "privy"],
        reason: "Check balance, fees, and audit state before wallet-aware services run.",
      },
    ];
  }

  if (intent === "solana-research") {
    return [
      {
        id: "solana-research",
        label: "Solana research",
        tools: [...SOLANA_MARKET_TOOLS, ...HELIUS_TOOLS],
        requiredEnv: ["HELIUS_API_KEY"],
        policyPresets: ["solana-rpc"],
        reason: "Combine market data and on-chain state for read-only research.",
      },
      {
        id: "grok-research",
        label: "Grok web and X research",
        tools: RESEARCH_TOOLS,
        requiredEnv: ["XAI_API_KEY"],
        policyPresets: [],
        reason: "Add web, X, memory, and deep research tools for external context.",
      },
    ];
  }

  if (intent === "code") {
    return [
      {
        id: "operator-code",
        label: "Operator coding tools",
        tools: ["agent_spawn", "agent_list", "memory_recall", "memory_write"],
        requiredEnv: [],
        policyPresets: ["github", "npm"],
        reason: "Use agent fleet and memory with repository, package, and test commands.",
      },
    ];
  }

  if (intent === "vision") {
    return [
      {
        id: "grok-vision",
        label: "Vision and image tools",
        tools: ["grok_vision", "grok_image", "memory_write"],
        requiredEnv: ["XAI_API_KEY"],
        policyPresets: [],
        reason: "Route visual analysis and image generation to the bundled Grok tools.",
      },
    ];
  }

  return [
    {
      id: "general-research",
      label: "General research and memory",
      tools: RESEARCH_TOOLS,
      requiredEnv: ["XAI_API_KEY"],
      policyPresets: [],
      reason: "Use chat, web/X search, deep research, and memory for open-ended tasks.",
    },
  ];
}

function bundledCandidates(): CandidateModel[] {
  return [
    {
      provider: "xai-grok",
      model: "grok-4.20-reasoning",
      label: "Grok 4.20 Reasoning",
      endpoint: XAI_ENDPOINT,
      credentialEnv: "XAI_API_KEY",
      contextWindow: 131072,
      maxOutput: 8192,
      supportsTools: true,
      supportsVision: true,
      supportsReasoning: true,
      inputCostPerMillion: null,
      outputCostPerMillion: null,
      source: "bundled",
    },
    {
      provider: "xai-grok",
      model: "grok-4-1-fast",
      label: "Grok 4.1 Fast",
      endpoint: XAI_ENDPOINT,
      credentialEnv: "XAI_API_KEY",
      contextWindow: 131072,
      maxOutput: 4096,
      supportsTools: true,
      supportsVision: false,
      supportsReasoning: false,
      inputCostPerMillion: null,
      outputCostPerMillion: null,
      source: "bundled",
    },
    {
      provider: "nvidia-nim",
      model: "nvidia/nemotron-3-super-120b-a12b",
      label: "Nemotron 3 Super 120B",
      endpoint: NVIDIA_ENDPOINT,
      credentialEnv: "NVIDIA_API_KEY",
      contextWindow: 131072,
      maxOutput: 8192,
      supportsTools: true,
      supportsVision: false,
      supportsReasoning: true,
      inputCostPerMillion: null,
      outputCostPerMillion: null,
      source: "bundled",
    },
    {
      provider: "nvidia-nim",
      model: "nvidia/nemotron-3-nano-30b-a3b",
      label: "Nemotron 3 Nano 30B",
      endpoint: NVIDIA_ENDPOINT,
      credentialEnv: "NVIDIA_API_KEY",
      contextWindow: 131072,
      maxOutput: 4096,
      supportsTools: true,
      supportsVision: false,
      supportsReasoning: false,
      inputCostPerMillion: null,
      outputCostPerMillion: null,
      source: "bundled",
    },
  ];
}

function readNumber(value: unknown): number | null {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value === "string" && value.trim() !== "") {
    const parsed = Number(value);
    if (Number.isFinite(parsed)) return parsed;
  }
  return null;
}

function parsePricing(value: unknown): { input: number | null; output: number | null } {
  if (!value || typeof value !== "object") return { input: null, output: null };
  const pricing = value as Pricing;
  const prompt = readNumber(pricing.prompt);
  const completion = readNumber(pricing.completion);
  return {
    input: prompt === null ? null : prompt * 1_000_000,
    output: completion === null ? null : completion * 1_000_000,
  };
}

function parseOpenRouterModel(raw: OpenRouterModel): CandidateModel | null {
  if (typeof raw.id !== "string" || raw.id.trim() === "") return null;
  const supportedParameters = Array.isArray(raw.supported_parameters)
    ? raw.supported_parameters.filter((item): item is string => typeof item === "string")
    : [];
  const architecture = raw.architecture && typeof raw.architecture === "object"
    ? (raw.architecture as Architecture)
    : {};
  const topProvider = raw.top_provider && typeof raw.top_provider === "object"
    ? (raw.top_provider as TopProvider)
    : {};
  const modality = typeof architecture.modality === "string" ? architecture.modality : "";
  const pricing = parsePricing(raw.pricing);
  const id = raw.id;
  const label = typeof raw.name === "string" && raw.name.trim() !== "" ? raw.name : id;
  const text = `${id} ${label}`.toLowerCase();

  return {
    provider: "openrouter",
    model: id,
    label,
    endpoint: OPENROUTER_ENDPOINT,
    credentialEnv: "OPENROUTER_API_KEY",
    contextWindow: readNumber(raw.context_length),
    maxOutput: readNumber(topProvider.max_completion_tokens),
    supportsTools:
      supportedParameters.includes("tools") ||
      supportedParameters.includes("tool_choice") ||
      supportedParameters.includes("function_call"),
    supportsVision: modality.includes("image") || /vision|image|multimodal/.test(text),
    supportsReasoning: /reason|thinking|grok|claude|sonnet|gemini|deepseek|nemotron|qwen/.test(text),
    inputCostPerMillion: pricing.input,
    outputCostPerMillion: pricing.output,
    source: "openrouter",
  };
}

async function fetchOpenRouterCandidates(
  fetchImpl: typeof fetch,
  env: NodeJS.ProcessEnv,
): Promise<CandidateModel[]> {
  const headers: Record<string, string> = {
    "HTTP-Referer": "https://nemo-clawd.ai",
    "X-OpenRouter-Title": "Nemo Clawd Magic Router",
  };
  if (env.OPENROUTER_API_KEY) {
    headers.Authorization = `Bearer ${env.OPENROUTER_API_KEY}`;
  }

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 5000);
  try {
    const response = await fetchImpl(`${OPENROUTER_ENDPOINT}/models`, {
      headers,
      signal: controller.signal,
    });
    if (!response.ok) {
      throw new Error(`OpenRouter models request failed with HTTP ${response.status}`);
    }
    const body = (await response.json()) as OpenRouterModelsResponse;
    return (body.data ?? []).map(parseOpenRouterModel).filter((item): item is CandidateModel => item !== null);
  } finally {
    clearTimeout(timeout);
  }
}

function scoreCandidate(
  candidate: CandidateModel,
  intent: MagicRouterIntent,
  budget: MagicRouterBudget,
): ScoredCandidate {
  let score = 0;
  const reasons: string[] = [];
  const text = `${candidate.model} ${candidate.label}`.toLowerCase();

  if (candidate.supportsTools) {
    score += 18;
    reasons.push("supports tool calling");
  }
  if (candidate.supportsReasoning) {
    score += intent === "fast-chat" ? 4 : 18;
    reasons.push("strong reasoning fit");
  }
  if (candidate.supportsVision && intent === "vision") {
    score += 22;
    reasons.push("vision-capable");
  }
  if ((candidate.contextWindow ?? 0) >= 128000) {
    score += intent === "long-context" ? 18 : 8;
    reasons.push("large context window");
  }

  if (intent.startsWith("solana")) {
    if (/grok|x-ai|xai/.test(text)) {
      score += 20;
      reasons.push("matches README Grok-first Solana runtime");
    }
    if (/nemotron|nvidia/.test(text)) {
      score += 12;
      reasons.push("NVIDIA runtime compatibility");
    }
    if (/claude|sonnet|gemini|deepseek|qwen/.test(text)) {
      score += 10;
      reasons.push("strong multi-step analysis candidate");
    }
  }

  if (intent === "code" && /claude|sonnet|coder|qwen|deepseek|gpt/.test(text)) {
    score += 18;
    reasons.push("coding model fit");
  }

  if (intent === "fast-chat" || budget === "low") {
    if (/fast|flash|mini|nano|haiku|lite/.test(text)) {
      score += 16;
      reasons.push("latency/cost oriented");
    }
  }

  if (candidate.provider === "openrouter") {
    score += 8;
    reasons.push("OpenRouter catalog candidate");
  }

  const blendedCost = (candidate.inputCostPerMillion ?? 0) + (candidate.outputCostPerMillion ?? 0);
  if (blendedCost > 0) {
    if (budget === "low" && blendedCost <= 2) {
      score += 14;
      reasons.push("low OpenRouter listed price");
    } else if (budget === "balanced" && blendedCost <= 10) {
      score += 8;
      reasons.push("balanced OpenRouter listed price");
    } else if (budget === "premium") {
      score += 4;
      reasons.push("price allowed by premium budget");
    }
  }

  return { ...candidate, score, reasons };
}

function applyCommandsFor(candidate: CandidateModel): string[] {
  return [
    `openshell provider create --name ${candidate.provider} --type openai --credential "${candidate.credentialEnv}=$${candidate.credentialEnv}" --config "OPENAI_BASE_URL=${candidate.endpoint}"`,
    `openshell inference set --provider ${candidate.provider} --model ${candidate.model}`,
  ];
}

function applyRecommendation(
  candidate: CandidateModel,
  execFileSyncImpl: typeof execFileSync,
  env: NodeJS.ProcessEnv,
): void {
  const credential = `${candidate.credentialEnv}=${env[candidate.credentialEnv] ?? ""}`;
  const config = `OPENAI_BASE_URL=${candidate.endpoint}`;
  try {
    execFileSyncImpl("openshell", [
      "provider",
      "create",
      "--name",
      candidate.provider,
      "--type",
      "openai",
      "--credential",
      credential,
      "--config",
      config,
    ], { stdio: "pipe" });
  } catch {
    execFileSyncImpl("openshell", [
      "provider",
      "update",
      candidate.provider,
      "--credential",
      credential,
      "--config",
      config,
    ], { stdio: "pipe" });
  }

  execFileSyncImpl("openshell", [
    "inference",
    "set",
    "--provider",
    candidate.provider,
    "--model",
    candidate.model,
  ], { stdio: "pipe" });
}

export async function recommendMagicRoute(opts: MagicRouterOptions): Promise<MagicRouterRecommendation> {
  const env = opts.env ?? process.env;
  const goal = opts.goal?.trim() || "Run a Solana-native Nemo Clawd agent safely.";
  const budget = normalizeBudget(opts.budget);
  const intent = inferMagicRouterIntent(goal);
  const warnings: string[] = [];
  const candidates = bundledCandidates();
  let openRouterUsed = false;
  let openRouterModelCount = 0;
  let openRouterError: string | null = null;

  const shouldUseOpenRouter =
    !opts.offline && (opts.useOpenRouter === true || Boolean(env.OPENROUTER_API_KEY));
  if (shouldUseOpenRouter) {
    const fetchImpl = opts.fetchImpl ?? globalThis.fetch;
    if (!fetchImpl) {
      openRouterError = "fetch is not available in this Node.js runtime";
      warnings.push(openRouterError);
    } else {
      try {
        const openRouterCandidates = await fetchOpenRouterCandidates(fetchImpl, env);
        openRouterUsed = true;
        openRouterModelCount = openRouterCandidates.length;
        candidates.push(...openRouterCandidates);
      } catch (error) {
        openRouterError = error instanceof Error ? error.message : String(error);
        warnings.push(`OpenRouter catalog unavailable: ${openRouterError}`);
      }
    }
  }

  const scored = candidates
    .map((candidate) => scoreCandidate(candidate, intent, budget))
    .sort((left, right) => {
      if (right.score !== left.score) return right.score - left.score;
      return left.model.localeCompare(right.model);
    });
  const selected = scored[0];
  const tools = recommendMagicRouterTools(intent);

  const recommendation: MagicRouterRecommendation = {
    goal,
    intent,
    budget,
    provider: selected.provider,
    model: selected.model,
    endpoint: selected.endpoint,
    credentialEnv: selected.credentialEnv,
    score: selected.score,
    reasons: selected.reasons,
    tools,
    applyCommands: applyCommandsFor(selected),
    openRouter: {
      used: openRouterUsed,
      modelCount: openRouterModelCount,
      error: openRouterError,
    },
    warnings,
  };

  if (opts.apply) {
    if (!env[selected.credentialEnv]) {
      throw new Error(`Cannot apply Magic Router result without ${selected.credentialEnv}`);
    }
    applyRecommendation(selected, opts.execFileSyncImpl ?? execFileSync, env);
  }

  return recommendation;
}

function renderRecommendation(result: MagicRouterRecommendation, applied: boolean, logger: PluginLogger): void {
  logger.info("Nemo Clawd Magic Router");
  logger.info("-----------------------");
  logger.info(`Goal:       ${result.goal}`);
  logger.info(`Intent:     ${result.intent}`);
  logger.info(`Budget:     ${result.budget}`);
  logger.info(`Provider:   ${result.provider}`);
  logger.info(`Model:      ${result.model}`);
  logger.info(`Endpoint:   ${result.endpoint}`);
  logger.info(`Credential: $${result.credentialEnv}`);
  logger.info(`Score:      ${result.score}`);
  logger.info("");
  logger.info("Why:");
  for (const reason of result.reasons) {
    logger.info(`  - ${reason}`);
  }
  logger.info("");
  logger.info("Tool Sets:");
  for (const toolSet of result.tools) {
    logger.info(`  - ${toolSet.label}: ${toolSet.tools.join(", ")}`);
    logger.info(`    ${toolSet.reason}`);
  }
  logger.info("");
  logger.info("Apply:");
  if (applied) {
    logger.info("  Applied to OpenShell inference.");
  } else {
    for (const command of result.applyCommands) {
      logger.info(`  ${command}`);
    }
    logger.info("  Re-run with --apply to execute these commands.");
  }
  if (result.warnings.length > 0) {
    logger.info("");
    logger.info("Warnings:");
    for (const warning of result.warnings) {
      logger.info(`  - ${warning}`);
    }
  }
}

export async function cliMagicRouter(opts: MagicRouterOptions): Promise<void> {
  const result = await recommendMagicRoute(opts);
  if (opts.json) {
    opts.logger.info(JSON.stringify(result, null, 2));
    return;
  }
  renderRecommendation(result, Boolean(opts.apply), opts.logger);
}
