// SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: Apache-2.0

import { spawn } from "node:child_process";
import { join } from "node:path";
import { PluginAPI } from "../index.js";

export type BlueprintAction = "plan" | "apply" | "status" | "rollback";

export interface BlueprintRunOptions {
  blueprintPath: string;
  action: BlueprintAction;
  profile: string;
  planPath?: string;
  runId?: string;
  jsonOutput?: boolean;
  dryRun?: boolean;
}

export interface BlueprintRunResult {
  success: boolean;
  runId: string;
  action: BlueprintAction;
  output: string;
  exitCode: number;
}

export async function execBlueprint(
  options: BlueprintRunOptions,
  api: PluginAPI
): Promise<BlueprintRunResult> {
  const runnerPath = join(options.blueprintPath, "orchestrator", "runner.py");

  const args: string[] = [
    runnerPath,
    options.action,
    "--profile",
    options.profile,
  ];

  if (options.jsonOutput) args.push("--json");
  if (options.planPath) args.push("--plan", options.planPath);
  if (options.runId) args.push("--run-id", options.runId);
  if (options.dryRun) args.push("--dry-run");

  api.log("info", `Running blueprint: ${options.action} (profile: ${options.profile})`);

  return new Promise((resolve) => {
    const chunks: string[] = [];
    const proc = spawn("python3", args, {
      cwd: options.blueprintPath,
      env: {
        ...process.env,
        OPENSHELL_PLUGIN_BLUEPRINT_PATH: options.blueprintPath,
        OPENSHELL_PLUGIN_ACTION: options.action,
      },
      stdio: ["pipe", "pipe", "pipe"],
    });

    proc.stdout.on("data", (data: Buffer) => {
      const line = data.toString();
      chunks.push(line);
      // Parse progress lines from blueprint runner
      const progressMatch = line.match(/^PROGRESS:(\d+):(.+)$/m);
      if (progressMatch) {
        api.progress(progressMatch[2], parseInt(progressMatch[1], 10));
      }
    });

    proc.stderr.on("data", (data: Buffer) => {
      const line = data.toString().trim();
      if (line) api.log("warn", line);
    });

    proc.on("close", (code) => {
      const output = chunks.join("");
      const runIdMatch = output.match(/^RUN_ID:(.+)$/m);
      resolve({
        success: code === 0,
        runId: runIdMatch?.[1] ?? "unknown",
        action: options.action,
        output,
        exitCode: code ?? 1,
      });
    });

    proc.on("error", (err) => {
      resolve({
        success: false,
        runId: "error",
        action: options.action,
        output: err.message,
        exitCode: 1,
      });
    });
  });
}
