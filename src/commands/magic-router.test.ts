// SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: Apache-2.0

import { describe, expect, it, vi } from "vitest";
import type { NemoclawdConfig, PluginLogger } from "../index.js";
import {
  inferMagicRouterIntent,
  recommendMagicRoute,
  recommendMagicRouterTools,
} from "./magic-router.js";

const defaultConfig: NemoclawdConfig = {
  blueprintVersion: "latest",
  blueprintRegistry: "ghcr.io/nvidia/nemoclawd-blueprint",
  sandboxName: "nemoclawd",
  inferenceProvider: "nvidia",
};

const logger: PluginLogger = {
  info: () => {},
  warn: () => {},
  error: () => {},
  debug: () => {},
};

function mockFetch(models: unknown[]): typeof fetch {
  return vi.fn(async () => ({
    ok: true,
    status: 200,
    json: async () => ({ data: models }),
  })) as unknown as typeof fetch;
}

describe("inferMagicRouterIntent", () => {
  it("detects Solana trading goals", () => {
    expect(inferMagicRouterIntent("watch Solana Pump.fun launches and quote trades")).toBe(
      "solana-research",
    );
  });

  it("detects coding goals", () => {
    expect(inferMagicRouterIntent("debug TypeScript tests in this repo")).toBe("code");
  });
});

describe("recommendMagicRouterTools", () => {
  it("includes Solana market and guardrail tools for trading", () => {
    const tools = recommendMagicRouterTools("solana-trading");
    const toolNames = tools.flatMap((toolSet) => toolSet.tools);

    expect(toolNames).toContain("solana_price");
    expect(toolNames).toContain("pump_buy_quote");
    expect(toolNames).toContain("helius_priority_fee");
    expect(tools.flatMap((toolSet) => toolSet.policyPresets)).toContain("solana-rpc");
  });
});

describe("recommendMagicRoute", () => {
  it("uses bundled Grok-first routing when offline", async () => {
    const recommendation = await recommendMagicRoute({
      goal: "run a Solana trading agent with wallet guardrails",
      offline: true,
      logger,
      pluginConfig: defaultConfig,
      env: {},
    });

    expect(recommendation.provider).toBe("xai-grok");
    expect(recommendation.model).toBe("grok-4.20-reasoning");
    expect(recommendation.tools[0].id).toBe("solana-market");
    expect(recommendation.openRouter.used).toBe(false);
  });

  it("can select an OpenRouter model from the live catalog shape", async () => {
    const fetchImpl = mockFetch([
      {
        id: "openrouter/cheap-fast",
        name: "Cheap Fast",
        context_length: 8192,
        supported_parameters: [],
        pricing: { prompt: "0.0000001", completion: "0.0000002" },
      },
      {
        id: "x-ai/grok-4",
        name: "Grok 4",
        context_length: 256000,
        supported_parameters: ["tools", "tool_choice"],
        pricing: { prompt: "0.000003", completion: "0.000015" },
        architecture: { modality: "text+image->text" },
        top_provider: { max_completion_tokens: 8192 },
      },
    ]);

    const recommendation = await recommendMagicRoute({
      goal: "research a Solana token launch and explain wallet risk",
      budget: "premium",
      useOpenRouter: true,
      logger,
      pluginConfig: defaultConfig,
      fetchImpl,
      env: { OPENROUTER_API_KEY: "test-key" },
    });

    expect(recommendation.openRouter.used).toBe(true);
    expect(recommendation.openRouter.modelCount).toBe(2);
    expect(recommendation.provider).toBe("openrouter");
    expect(recommendation.model).toBe("x-ai/grok-4");
    expect(recommendation.credentialEnv).toBe("OPENROUTER_API_KEY");
  });

  it("falls back to bundled candidates when OpenRouter is unavailable", async () => {
    const fetchImpl = vi.fn(async () => {
      throw new Error("network unavailable");
    }) as unknown as typeof fetch;

    const recommendation = await recommendMagicRoute({
      goal: "fast Solana market check",
      useOpenRouter: true,
      logger,
      pluginConfig: defaultConfig,
      fetchImpl,
      env: {},
    });

    expect(recommendation.provider).toBe("xai-grok");
    expect(recommendation.openRouter.error).toContain("network unavailable");
    expect(recommendation.warnings[0]).toContain("OpenRouter catalog unavailable");
  });
});
