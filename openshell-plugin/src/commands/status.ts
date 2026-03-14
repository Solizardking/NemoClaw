// SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: Apache-2.0

import { execSync } from "node:child_process";
import { CommandContext } from "../index.js";
import { loadState } from "../blueprint/state.js";

export async function status(ctx: CommandContext): Promise<void> {
  const { api, flags } = ctx;
  const jsonOutput = flags["json"] as boolean;
  const state = loadState();

  const statusData = {
    openshellPlugin: {
      lastAction: state.lastAction,
      lastRunId: state.lastRunId,
      blueprintVersion: state.blueprintVersion,
      sandboxName: state.sandboxName,
      migrationSnapshot: state.migrationSnapshot,
      updatedAt: state.updatedAt,
    },
    sandbox: await getSandboxStatus(state.sandboxName ?? "openclaw"),
    inference: await getInferenceStatus(),
  };

  if (jsonOutput) {
    api.log("info", JSON.stringify(statusData, null, 2));
    return;
  }

  // Human-readable output
  api.log("info", "OpenShell Plugin Status");
  api.log("info", "======================");
  api.log("info", "");

  // Plugin state
  api.log("info", "Plugin State:");
  if (state.lastAction) {
    api.log("info", `  Last action:      ${state.lastAction}`);
    api.log("info", `  Blueprint:        ${state.blueprintVersion ?? "unknown"}`);
    api.log("info", `  Run ID:           ${state.lastRunId ?? "none"}`);
    api.log("info", `  Updated:          ${state.updatedAt}`);
  } else {
    api.log("info", "  No operations have been performed yet.");
  }
  api.log("info", "");

  // Sandbox state
  api.log("info", "Sandbox:");
  const sandbox = statusData.sandbox;
  if (sandbox.running) {
    api.log("info", `  Name:    ${sandbox.name}`);
    api.log("info", `  Status:  running`);
    api.log("info", `  Uptime:  ${sandbox.uptime ?? "unknown"}`);
  } else {
    api.log("info", `  Status:  not running`);
  }
  api.log("info", "");

  // Inference state
  api.log("info", "Inference:");
  const inference = statusData.inference;
  if (inference.configured) {
    api.log("info", `  Provider:  ${inference.provider ?? "unknown"}`);
    api.log("info", `  Model:     ${inference.model ?? "unknown"}`);
    api.log("info", `  Endpoint:  ${inference.endpoint ?? "unknown"}`);
  } else {
    api.log("info", "  Not configured");
  }

  // Snapshot info
  if (state.migrationSnapshot) {
    api.log("info", "");
    api.log("info", "Rollback:");
    api.log("info", `  Snapshot:  ${state.migrationSnapshot}`);
    api.log("info", "  Run 'openclaw openshell eject' to restore host installation.");
  }
}

interface SandboxStatus {
  name: string;
  running: boolean;
  uptime: string | null;
}

async function getSandboxStatus(sandboxName: string): Promise<SandboxStatus> {
  try {
    const output = execSync(`openshell sandbox status ${sandboxName} --json`, {
      encoding: "utf-8",
      timeout: 5000,
    });
    const parsed = JSON.parse(output);
    return {
      name: sandboxName,
      running: parsed.state === "running",
      uptime: parsed.uptime ?? null,
    };
  } catch {
    return { name: sandboxName, running: false, uptime: null };
  }
}

interface InferenceStatus {
  configured: boolean;
  provider: string | null;
  model: string | null;
  endpoint: string | null;
}

async function getInferenceStatus(): Promise<InferenceStatus> {
  try {
    const output = execSync("openshell inference get --json", {
      encoding: "utf-8",
      timeout: 5000,
    });
    const parsed = JSON.parse(output);
    return {
      configured: true,
      provider: parsed.provider ?? null,
      model: parsed.model ?? null,
      endpoint: parsed.endpoint ?? null,
    };
  } catch {
    return { configured: false, provider: null, model: null, endpoint: null };
  }
}
