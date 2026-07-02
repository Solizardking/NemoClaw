// SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: Apache-2.0

import { execSync } from "node:child_process";
import type { PluginLogger, NemoclawdConfig } from "../index.js";
import { resolveBlueprint } from "../blueprint/resolve.js";
import { verifyBlueprintDigest, checkCompatibility } from "../blueprint/verify.js";
import { execBlueprint } from "../blueprint/exec.js";
import { loadState, saveState } from "../blueprint/state.js";
import { detectHostNemoclawd } from "./migrate.js";

export interface LaunchOptions {
  force: boolean;
  profile: string;
  logger: PluginLogger;
  pluginConfig: NemoclawdConfig;
}

export async function cliLaunch(opts: LaunchOptions): Promise<void> {
  const { force, profile, logger, pluginConfig } = opts;

  logger.info("Nemo Clawd launch: setting up Nemo Clawd inside OpenShell");

  // Check if there's an existing host Nemo Clawd installation
  const hostState = detectHostNemoclawd();

  if (!hostState.exists && !force) {
    logger.info("");
    logger.info("No existing Nemo Clawd installation detected on this host.");
    logger.info("");
    logger.info("For net-new users, the recommended path is OpenShell-native setup:");
    logger.info("");
    logger.info("  openshell sandbox create --from nemoclawd:latest --name nemoclawd");
    logger.info("  openshell sandbox connect nemoclawd");
    logger.info("");
    logger.info(
      "This avoids installing Nemo Clawd on the host only to redeploy it inside OpenShell.",
    );
    logger.info("");
    logger.info("To proceed with Nemo Clawd-driven bootstrap anyway, use --force.");
    return;
  }

  if (hostState.exists && !force) {
    logger.info(
      "Existing Nemo Clawd installation detected. Consider using 'nemoclawd migrate' instead.",
    );
    logger.info(
      "Use --force to proceed with a fresh launch (existing config will not be migrated).",
    );
    return;
  }

  // Resolve and verify blueprint
  logger.info("Resolving blueprint...");
  const blueprint = await resolveBlueprint(pluginConfig);

  logger.info("Verifying blueprint integrity...");
  const verification = verifyBlueprintDigest(blueprint.localPath, blueprint.manifest);
  if (!verification.valid) {
    logger.error(`Blueprint verification failed: ${verification.errors.join(", ")}`);
    return;
  }

  // Check version compatibility
  const openshellVersion = getOpenshellVersion();
  const nemoclawdVersion = getNemoclawdVersion();
  const compat = checkCompatibility(blueprint.manifest, openshellVersion, nemoclawdVersion);
  if (compat.length > 0) {
    logger.error(`Compatibility check failed:\n  ${compat.join("\n  ")}`);
    return;
  }

  // Plan
  logger.info("Planning deployment...");
  const planResult = await execBlueprint(
    {
      blueprintPath: blueprint.localPath,
      action: "plan",
      profile,
      jsonOutput: true,
    },
    logger,
  );

  if (!planResult.success) {
    logger.error(`Blueprint plan failed: ${planResult.output}`);
    return;
  }

  // Apply
  logger.info("Deploying Nemo Clawd sandbox...");
  const applyResult = await execBlueprint(
    {
      blueprintPath: blueprint.localPath,
      action: "apply",
      profile,
      planPath: planResult.runId,
      jsonOutput: true,
    },
    logger,
  );

  if (!applyResult.success) {
    logger.error(`Blueprint apply failed: ${applyResult.output}`);
    return;
  }

  // Save state
  saveState({
    ...loadState(),
    lastRunId: applyResult.runId,
    lastAction: "launch",
    blueprintVersion: blueprint.version,
    sandboxName: pluginConfig.sandboxName,
  });

  logger.info("");
  logger.info("Nemo Clawd is now running inside OpenShell.");
  logger.info(`Sandbox: ${pluginConfig.sandboxName}`);
  logger.info("");
  logger.info("Next steps:");
  logger.info("  nemoclawd connect    # Enter the sandbox");
  logger.info("  nemoclawd status     # Check health");
  logger.info("  openshell term               # Monitor network egress");
}

function getOpenshellVersion(): string {
  try {
    return execSync("openshell --version", { encoding: "utf-8" }).trim();
  } catch {
    return "0.0.0";
  }
}

function getNemoclawdVersion(): string {
  try {
    return execSync("nemoclawd --version", { encoding: "utf-8" }).trim();
  } catch {
    return "0.0.0";
  }
}
