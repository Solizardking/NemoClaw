// SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: Apache-2.0

import { launch } from "./commands/launch.js";
import { migrate } from "./commands/migrate.js";
import { connect } from "./commands/connect.js";
import { status } from "./commands/status.js";
import { logs } from "./commands/logs.js";
import { eject } from "./commands/eject.js";

export interface OpenShellPluginConfig {
  blueprintVersion: string;
  blueprintRegistry: string;
  sandboxName: string;
  inferenceProvider: string;
}

/**
 * Draft interface — pending alignment with OpenClaw's actual plugin API.
 *
 * This mirrors what we *expect* the OpenClaw plugin host to provide based on
 * public docs and the extension model described in the OpenClaw RFC. Once the
 * real SDK ships, this interface should be replaced with the canonical type
 * from `@openclaw/plugin-sdk` (or similar).
 */
export interface PluginAPI {
  registerCommand(spec: CommandSpec): void;
  getConfig(): OpenShellPluginConfig;
  log(level: "info" | "warn" | "error", message: string): void;
  progress(label: string, percent: number): void;
}

export interface CommandSpec {
  name: string;
  description: string;
  args?: ArgSpec[];
  flags?: FlagSpec[];
  run(ctx: CommandContext): Promise<void>;
}

export interface ArgSpec {
  name: string;
  description: string;
  required?: boolean;
}

export interface FlagSpec {
  name: string;
  description: string;
  type: "string" | "boolean" | "number";
  default?: string | boolean | number;
}

export interface CommandContext {
  args: Record<string, string>;
  flags: Record<string, string | boolean | number>;
  config: OpenShellPluginConfig;
  api: PluginAPI;
}

export default function openshellPlugin(api: PluginAPI): void {
  api.registerCommand({
    name: "openshell launch",
    description:
      "Fresh install: bootstrap OpenClaw inside OpenShell (prefers OpenShell-native flow for net-new users)",
    flags: [
      {
        name: "force",
        description: "Skip ergonomics warning and force plugin-driven bootstrap",
        type: "boolean",
        default: false,
      },
      {
        name: "profile",
        description: "Blueprint profile to use (e.g., 'default', 'nim-local', 'ollama')",
        type: "string",
        default: "default",
      },
    ],
    run: launch,
  });

  api.registerCommand({
    name: "openshell migrate",
    description:
      "Migrate existing host OpenClaw installation into an OpenShell sandbox with snapshot/restore/cutover",
    flags: [
      {
        name: "dry-run",
        description: "Show what would be migrated without making changes",
        type: "boolean",
        default: false,
      },
      {
        name: "profile",
        description: "Blueprint profile to use",
        type: "string",
        default: "default",
      },
      {
        name: "skip-backup",
        description: "Skip creating a host backup snapshot (not recommended)",
        type: "boolean",
        default: false,
      },
    ],
    run: migrate,
  });

  api.registerCommand({
    name: "openshell connect",
    description: "Open an interactive shell inside the OpenClaw sandbox",
    flags: [
      {
        name: "sandbox",
        description: "Sandbox name to connect to",
        type: "string",
        default: "openclaw",
      },
    ],
    run: connect,
  });

  api.registerCommand({
    name: "openshell status",
    description: "Show blueprint run state, sandbox health, and backend status",
    flags: [
      {
        name: "json",
        description: "Output as JSON",
        type: "boolean",
        default: false,
      },
    ],
    run: status,
  });

  api.registerCommand({
    name: "openshell logs",
    description: "Stream logs from the blueprint runner and sandbox",
    flags: [
      {
        name: "follow",
        description: "Follow log output",
        type: "boolean",
        default: false,
      },
      {
        name: "component",
        description: "Filter logs by component (blueprint, sandbox, inference)",
        type: "string",
      },
    ],
    run: logs,
  });

  api.registerCommand({
    name: "openshell eject",
    description: "Rollback from OpenShell and restore host OpenClaw installation from snapshot",
    flags: [
      {
        name: "run-id",
        description: "Specific blueprint run ID to rollback from",
        type: "string",
      },
      {
        name: "confirm",
        description: "Skip confirmation prompt",
        type: "boolean",
        default: false,
      },
    ],
    run: eject,
  });
}
