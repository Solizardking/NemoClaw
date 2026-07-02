// SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: Apache-2.0

/**
 * CLI registrar for `nemoclawd <subcommand>`.
 *
 * Wires commander.js subcommands to the existing blueprint infrastructure.
 */

import type { NemoclawdPluginApi, PluginCliContext } from "./index.js";
import { getPluginConfig } from "./index.js";
import { cliStatus } from "./commands/status.js";
import { cliMigrate } from "./commands/migrate.js";
import { cliLaunch } from "./commands/launch.js";
import { cliConnect } from "./commands/connect.js";
import { cliEject } from "./commands/eject.js";
import { cliLogs } from "./commands/logs.js";
import { cliOnboard } from "./commands/onboard.js";
import { cliMagicRouter } from "./commands/magic-router.js";

export function registerCliCommands(ctx: PluginCliContext, api: NemoclawdPluginApi): void {
  const { program, logger } = ctx;
  const pluginConfig = getPluginConfig(api);

  const nemoclawd = program.command("nemoclawd").description("🦞 Nemo Clawd lobster command deck");

  // nemoclawd status
  nemoclawd
    .command("status")
    .description("Show sandbox, blueprint, and inference state")
    .option("--json", "Output as JSON", false)
    .action(async (opts: { json: boolean }) => {
      await cliStatus({ json: opts.json, logger, pluginConfig });
    });

  // nemoclawd migrate
  nemoclawd
    .command("migrate")
    .description("Migrate host Nemo Clawd installation into an OpenShell sandbox")
    .option("--dry-run", "Show what would be migrated without making changes", false)
    .option("--profile <profile>", "Blueprint profile to use", "default")
    .option("--skip-backup", "Skip creating a host backup snapshot", false)
    .action(async (opts: { dryRun: boolean; profile: string; skipBackup: boolean }) => {
      await cliMigrate({
        dryRun: opts.dryRun,
        profile: opts.profile,
        skipBackup: opts.skipBackup,
        logger,
        pluginConfig,
      });
    });

  // nemoclawd launch
  nemoclawd
    .command("launch")
    .description("Fresh setup: bootstrap Nemo Clawd inside OpenShell")
    .option("--force", "Skip ergonomics warning and force plugin-driven bootstrap", false)
    .option("--profile <profile>", "Blueprint profile to use", "default")
    .action(async (opts: { force: boolean; profile: string }) => {
      await cliLaunch({
        force: opts.force,
        profile: opts.profile,
        logger,
        pluginConfig,
      });
    });

  // nemoclawd connect
  nemoclawd
    .command("connect")
    .description("Open an interactive shell inside the Nemo Clawd sandbox")
    .option("--sandbox <name>", "Sandbox name to connect to", pluginConfig.sandboxName)
    .action(async (opts: { sandbox: string }) => {
      await cliConnect({ sandbox: opts.sandbox, logger });
    });

  // nemoclawd logs
  nemoclawd
    .command("logs")
    .description("Stream blueprint execution and sandbox logs")
    .option("-f, --follow", "Follow log output", false)
    .option("-n, --lines <count>", "Number of lines to show", "50")
    .option("--run-id <id>", "Show logs for a specific blueprint run")
    .action(async (opts: { follow: boolean; lines: string; runId?: string }) => {
      await cliLogs({
        follow: opts.follow,
        lines: parseInt(opts.lines, 10),
        runId: opts.runId,
        logger,
        pluginConfig,
      });
    });

  // nemoclawd eject
  nemoclawd
    .command("eject")
    .description("Rollback from OpenShell and restore host installation")
    .option("--run-id <id>", "Specific blueprint run ID to rollback from")
    .option("--confirm", "Skip confirmation prompt", false)
    .action(async (opts: { runId?: string; confirm: boolean }) => {
      await cliEject({
        runId: opts.runId,
        confirm: opts.confirm,
        logger,
        pluginConfig,
      });
    });

  // nemoclawd onboard
  nemoclawd
    .command("onboard")
    .description("Interactive setup: configure inference endpoint, credential, and model")
    .option("--api-key <key>", "API key for endpoints that require one (skips prompt)")
    .option("--endpoint <type>", "Endpoint type: build, ncp, nim-local, vllm, ollama, custom (local options are experimental)")
    .option("--ncp-partner <name>", "NCP partner name (when endpoint is ncp)")
    .option("--endpoint-url <url>", "Endpoint URL (for ncp, nim-local, ollama, or custom)")
    .option("--model <model>", "Model ID to use")
    .action(
      async (opts: {
        apiKey?: string;
        endpoint?: string;
        ncpPartner?: string;
        endpointUrl?: string;
        model?: string;
      }) => {
        await cliOnboard({
          apiKey: opts.apiKey,
          endpoint: opts.endpoint,
          ncpPartner: opts.ncpPartner,
          endpointUrl: opts.endpointUrl,
          model: opts.model,
          logger,
          pluginConfig,
        });
      },
    );

  // nemoclawd magic-router
  nemoclawd
    .command("magic-router [goal...]")
    .description("Recommend the best inference provider, model, and Nemo Clawd tool set")
    .option("--goal <text>", "Task or operator goal to optimize for")
    .option("--budget <level>", "Routing budget: low, balanced, premium", "balanced")
    .option("--use-openrouter", "Fetch OpenRouter model metadata when routing", false)
    .option("--offline", "Use only bundled routing rules", false)
    .option("--apply", "Apply the recommendation with OpenShell", false)
    .option("--json", "Output as JSON", false)
    .action(
      async (
        goalParts: string[] | string | undefined,
        opts: {
          goal?: string;
          budget?: string;
          useOpenrouter?: boolean;
          useOpenRouter?: boolean;
          offline?: boolean;
          apply?: boolean;
          json?: boolean;
        },
      ) => {
        const goalFromArgs = Array.isArray(goalParts) ? goalParts.join(" ") : goalParts;
        await cliMagicRouter({
          goal: opts.goal ?? goalFromArgs,
          budget: opts.budget,
          useOpenRouter: opts.useOpenRouter ?? opts.useOpenrouter,
          offline: opts.offline,
          apply: opts.apply,
          json: opts.json,
          logger,
          pluginConfig,
        });
      },
    );
}
