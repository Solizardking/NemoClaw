// SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: Apache-2.0

/**
 * Nemo Clawd — Clawd Plugin for OpenShell
 *
 * Uses the real Clawd plugin API. Types defined locally are minimal stubs
 * that match the Clawd SDK interfaces available at runtime via
 * `clawd/plugin-sdk`. We define them here because the SDK package is only
 * available inside the Clawd host process and cannot be imported at build
 * time.
 */

import type { Command } from "commander";
import { registerCliCommands } from "./cli.js";
import { handleSlashCommand } from "./commands/slash.js";
import { loadOnboardConfig } from "./onboard/config.js";

// ---------------------------------------------------------------------------
// Clawd Plugin SDK compatible types (mirrors clawd/plugin-sdk)
// ---------------------------------------------------------------------------

/** Subset of ClawdConfig that we actually read. */
export interface ClawdConfig {
  [key: string]: unknown;
}

/** Logger provided by the plugin host. */
export interface PluginLogger {
  info(message: string): void;
  warn(message: string): void;
  error(message: string): void;
  debug(message: string): void;
}

/** Context passed to slash-command handlers. */
export interface PluginCommandContext {
  senderId?: string;
  channel: string;
  isAuthorizedSender: boolean;
  args?: string;
  commandBody: string;
  config: ClawdConfig;
  from?: string;
  to?: string;
  accountId?: string;
}

/** Return value from a slash-command handler. */
export interface PluginCommandResult {
  text?: string;
  mediaUrl?: string;
  mediaUrls?: string[];
}

/** Registration shape for a slash command. */
export interface PluginCommandDefinition {
  name: string;
  description: string;
  acceptsArgs?: boolean;
  requireAuth?: boolean;
  handler: (ctx: PluginCommandContext) => PluginCommandResult | Promise<PluginCommandResult>;
}

/** Context passed to the CLI registrar callback. */
export interface PluginCliContext {
  program: Command;
  config: ClawdConfig;
  workspaceDir?: string;
  logger: PluginLogger;
}

/** CLI registrar callback type. */
export type PluginCliRegistrar = (ctx: PluginCliContext) => void | Promise<void>;

/** Auth method for a provider plugin. */
export interface ProviderAuthMethod {
  type: string;
  envVar?: string;
  headerName?: string;
  label?: string;
}

/** Model entry in a provider's model catalog. */
export interface ModelProviderEntry {
  id: string;
  label: string;
  contextWindow?: number;
  maxOutput?: number;
}

/** Model catalog shape. */
export interface ModelProviderConfig {
  chat?: ModelProviderEntry[];
  completion?: ModelProviderEntry[];
}

/** Registration shape for a custom model provider. */
export interface ProviderPlugin {
  id: string;
  label: string;
  docsPath?: string;
  aliases?: string[];
  envVars?: string[];
  models?: ModelProviderConfig;
  auth: ProviderAuthMethod[];
}

/** Background service registration. */
export interface PluginService {
  id: string;
  start: (ctx: { config: ClawdConfig; logger: PluginLogger }) => void | Promise<void>;
  stop?: (ctx: { config: ClawdConfig; logger: PluginLogger }) => void | Promise<void>;
}

/**
 * The API object injected into the plugin's register function by the Clawd
 * host. Only the methods we actually call are listed here.
 */
export interface ClawdPluginApi {
  id: string;
  name: string;
  version?: string;
  config: ClawdConfig;
  pluginConfig?: Record<string, unknown>;
  logger: PluginLogger;
  registerCommand: (command: PluginCommandDefinition) => void;
  registerCli: (registrar: PluginCliRegistrar, opts?: { commands?: string[] }) => void;
  registerProvider: (provider: ProviderPlugin) => void;
  registerService: (service: PluginService) => void;
  resolvePath: (input: string) => string;
  on: (hookName: string, handler: (...args: unknown[]) => void) => void;
}

// ---------------------------------------------------------------------------
// Plugin-specific config (read from pluginConfig in clawd.plugin.json)
// ---------------------------------------------------------------------------

export interface NemoClawdConfig {
  blueprintVersion: string;
  blueprintRegistry: string;
  sandboxName: string;
  inferenceProvider: string;
}

const DEFAULT_PLUGIN_CONFIG: NemoClawdConfig = {
  blueprintVersion: "latest",
  blueprintRegistry: "ghcr.io/nvidia/nemoclawd-blueprint",
  sandboxName: "nemoclawd",
  inferenceProvider: "nvidia",
};

export function getPluginConfig(api: ClawdPluginApi): NemoClawdConfig {
  const raw = api.pluginConfig ?? {};
  return {
    blueprintVersion:
      typeof raw["blueprintVersion"] === "string"
        ? raw["blueprintVersion"]
        : DEFAULT_PLUGIN_CONFIG.blueprintVersion,
    blueprintRegistry:
      typeof raw["blueprintRegistry"] === "string"
        ? raw["blueprintRegistry"]
        : DEFAULT_PLUGIN_CONFIG.blueprintRegistry,
    sandboxName:
      typeof raw["sandboxName"] === "string"
        ? raw["sandboxName"]
        : DEFAULT_PLUGIN_CONFIG.sandboxName,
    inferenceProvider:
      typeof raw["inferenceProvider"] === "string"
        ? raw["inferenceProvider"]
        : DEFAULT_PLUGIN_CONFIG.inferenceProvider,
  };
}

// ---------------------------------------------------------------------------
// Plugin entry point
// ---------------------------------------------------------------------------

export default function register(api: ClawdPluginApi): void {
  // 1. Register /nemoclawd slash command (chat interface)
  api.registerCommand({
    name: "nemoclawd",
    description: "Nemo Clawd sandbox management (status, eject).",
    acceptsArgs: true,
    handler: (ctx) => handleSlashCommand(ctx, api),
  });

  // 2. Register `clawd nemoclawd` CLI subcommands (commander.js)
  api.registerCli(
    (cliCtx) => {
      registerCliCommands(cliCtx, api);
    },
    { commands: ["nemoclawd"] },
  );

  // 3. Register nvidia-nim provider — use onboard config if available
  const onboardCfg = loadOnboardConfig();
  const providerCredentialEnv = onboardCfg?.credentialEnv ?? "NVIDIA_API_KEY";
  const providerLabel = onboardCfg
    ? `NVIDIA NIM (${onboardCfg.endpointType}${onboardCfg.ncpPartner ? ` - ${onboardCfg.ncpPartner}` : ""})`
    : "NVIDIA NIM (build.nvidia.com)";

  api.registerProvider({
    id: "nvidia-nim",
    label: providerLabel,
    docsPath: "https://build.nvidia.com/docs",
    aliases: ["nvidia", "nim"],
    envVars: [providerCredentialEnv],
    models: {
      chat: [
        {
          id: "nvidia/nemotron-3-super-120b-a12b",
          label: "Nemotron 3 Super 120B (March 2026)",
          contextWindow: 131072,
          maxOutput: 8192,
        },
        {
          id: "nvidia/llama-3.1-nemotron-ultra-253b-v1",
          label: "Nemotron Ultra 253B",
          contextWindow: 131072,
          maxOutput: 4096,
        },
        {
          id: "nvidia/llama-3.3-nemotron-super-49b-v1.5",
          label: "Nemotron Super 49B v1.5",
          contextWindow: 131072,
          maxOutput: 4096,
        },
        {
          id: "nvidia/nemotron-3-nano-30b-a3b",
          label: "Nemotron 3 Nano 30B",
          contextWindow: 131072,
          maxOutput: 4096,
        },
      ],
    },
    auth: [
      {
        type: "bearer",
        envVar: providerCredentialEnv,
        headerName: "Authorization",
        label: `NVIDIA API Key (${providerCredentialEnv})`,
      },
    ],
  });

  const bannerEndpoint = onboardCfg?.endpointType ?? "build.nvidia.com";
  const bannerModel = onboardCfg?.model ?? "nvidia/nemotron-3-super-120b-a12b";

  api.logger.info("");
  api.logger.info("  ┌─────────────────────────────────────────────────────┐");
  api.logger.info("  │  Nemo Clawd registered                              │");
  api.logger.info("  │                                                     │");
  api.logger.info(`  │  Endpoint:  ${bannerEndpoint.padEnd(40)}│`);
  api.logger.info(`  │  Model:     ${bannerModel.padEnd(40)}│`);
  api.logger.info("  │  Commands:  clawd nemoclawd <command>              │");
  api.logger.info("  └─────────────────────────────────────────────────────┘");
  api.logger.info("");
}
