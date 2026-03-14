// SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: Apache-2.0

import { execSync } from "node:child_process";
import { CommandContext } from "../index.js";
import { loadState } from "../blueprint/state.js";

export async function connect(ctx: CommandContext): Promise<void> {
  const { api, flags } = ctx;
  const sandboxName = (flags["sandbox"] as string) ?? loadState().sandboxName ?? "openclaw";

  api.log("info", `Connecting to OpenClaw sandbox: ${sandboxName}`);
  api.log("info", "You will be inside the sandbox. Run 'openclaw' commands normally.");
  api.log("info", "Type 'exit' to return to your host shell.");
  api.log("info", "");

  try {
    execSync(`openshell sandbox connect ${sandboxName}`, {
      stdio: "inherit",
    });
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : String(err);
    if (msg.includes("not found")) {
      api.log("error", `Sandbox '${sandboxName}' not found.`);
      api.log("info", "Run 'openclaw openshell status' to check available sandboxes.");
    } else {
      api.log("error", `Connection failed: ${msg}`);
    }
  }
}
