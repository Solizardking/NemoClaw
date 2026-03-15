// SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: Apache-2.0

import { execFileSync } from "node:child_process";
import { existsSync, mkdirSync, cpSync, readdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import type { PluginLogger, NemoClawConfig } from "../index.js";
import { resolveBlueprint } from "../blueprint/resolve.js";
import { verifyBlueprintDigest } from "../blueprint/verify.js";
import { execBlueprint } from "../blueprint/exec.js";
import { loadState, saveState } from "../blueprint/state.js";

const HOME = process.env.HOME ?? "/tmp";

export interface HostOpenClawState {
  exists: boolean;
  configDir: string | null;
  workspaceDir: string | null;
  extensionsDir: string | null;
  skillsDir: string | null;
  hooksDir: string | null;
  configFile: string | null;
}

export function detectHostOpenClaw(): HostOpenClawState {
  const configDir = join(HOME, ".openclaw");
  const exists = existsSync(configDir);

  if (!exists) {
    return {
      exists: false,
      configDir: null,
      workspaceDir: null,
      extensionsDir: null,
      skillsDir: null,
      hooksDir: null,
      configFile: null,
    };
  }

  const configFile = existsSync(join(configDir, "openclaw.json"))
    ? join(configDir, "openclaw.json")
    : null;

  const workspaceDir = existsSync(join(configDir, "workspace"))
    ? join(configDir, "workspace")
    : null;

  const extensionsDir = existsSync(join(configDir, "extensions"))
    ? join(configDir, "extensions")
    : null;

  const skillsDir = existsSync(join(configDir, "skills")) ? join(configDir, "skills") : null;
  const hooksDir = existsSync(join(configDir, "hooks")) ? join(configDir, "hooks") : null;

  return {
    exists: true,
    configDir,
    workspaceDir,
    extensionsDir,
    skillsDir,
    hooksDir,
    configFile,
  };
}

export interface MigrateOptions {
  dryRun: boolean;
  profile: string;
  skipBackup: boolean;
  logger: PluginLogger;
  pluginConfig: NemoClawConfig;
}

export async function cliMigrate(opts: MigrateOptions): Promise<void> {
  const { dryRun, profile, skipBackup, logger, pluginConfig } = opts;

  logger.info("NemoClaw migrate: moving host OpenClaw into OpenShell sandbox");

  // Step 1: Detect host OpenClaw state
  logger.info("Detecting host OpenClaw installation...");
  const hostState = detectHostOpenClaw();

  if (!hostState.exists) {
    logger.error("No OpenClaw installation found at ~/.openclaw");
    logger.info("Use 'openclaw nemoclaw launch' for a fresh install.");
    return;
  }

  logger.info(`Found OpenClaw config at ${hostState.configDir ?? "~/.openclaw"}`);
  if (hostState.configFile) logger.info(`  Config: ${hostState.configFile}`);
  if (hostState.workspaceDir) logger.info(`  Workspace: ${hostState.workspaceDir}`);
  if (hostState.extensionsDir) logger.info(`  Extensions: ${hostState.extensionsDir}`);
  if (hostState.skillsDir) logger.info(`  Skills: ${hostState.skillsDir}`);
  if (hostState.hooksDir) logger.info(`  Hooks: ${hostState.hooksDir}`);

  // Step 2: Create snapshot backup
  let snapshotPath: string | null = null;
  if (!skipBackup) {
    logger.info("Creating host backup snapshot...");
    snapshotPath = createSnapshot(hostState, logger);
    if (!snapshotPath) {
      logger.error("Failed to create backup snapshot. Use --skip-backup to proceed anyway.");
      return;
    }
    logger.info(`Snapshot saved to ${snapshotPath}`);
  }

  if (dryRun) {
    logger.info("");
    logger.info("[Dry run] Would perform the following:");
    logger.info("  1. Resolve and verify blueprint");
    logger.info("  2. Create OpenShell sandbox");
    logger.info("  3. Copy ~/.openclaw (config, hooks, workspace, extensions, skills) into sandbox");
    logger.info("  4. Configure inference provider");
    logger.info("  5. Leave host ~/.openclaw snapshot available for rollback");
    return;
  }

  // Step 3: Resolve and verify blueprint
  logger.info("Resolving blueprint...");
  const blueprint = await resolveBlueprint(pluginConfig);

  logger.info("Verifying blueprint...");
  const verification = verifyBlueprintDigest(blueprint.localPath, blueprint.manifest);
  if (!verification.valid) {
    logger.error(`Blueprint verification failed: ${verification.errors.join(", ")}`);
    return;
  }

  // Step 4: Plan migration
  logger.info("Planning migration...");
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
    logger.error(`Migration plan failed: ${planResult.output}`);
    return;
  }

  // Step 5: Apply migration
  logger.info("Provisioning OpenShell sandbox...");
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
    logger.error(`Migration apply failed: ${applyResult.output}`);
    if (snapshotPath) {
      logger.info(`Restore from snapshot: ${snapshotPath}`);
    }
    return;
  }

  logger.info("Syncing host OpenClaw state into sandbox...");
  const synced = syncOpenClawStateIntoSandbox({
    configDir: hostState.configDir,
    sandboxName: pluginConfig.sandboxName,
    logger,
  });
  if (!synced) {
    logger.error("Sandbox sync failed. Host OpenClaw state was not copied into the sandbox.");
    logger.info("Your host installation is unchanged. Resolve the copy error and rerun migrate.");
    return;
  }

  // Step 6: Save state for eject
  saveState({
    ...loadState(),
    lastRunId: applyResult.runId,
    lastAction: "migrate",
    blueprintVersion: blueprint.version,
    sandboxName: pluginConfig.sandboxName,
    migrationSnapshot: snapshotPath,
    hostBackupPath: snapshotPath,
  });

  logger.info("");
  logger.info("Migration complete. OpenClaw is now running inside OpenShell.");
  logger.info(`Sandbox: ${pluginConfig.sandboxName}`);
  logger.info("");
  logger.info("Next steps:");
  logger.info("  openclaw nemoclaw connect    # Enter the sandbox");
  logger.info("  openclaw nemoclaw status     # Verify everything is healthy");
  logger.info("  openshell term               # Monitor sandbox activity");
  logger.info("");
  logger.info("To rollback to your host installation:");
  logger.info("  openclaw nemoclaw eject");
}

function syncOpenClawStateIntoSandbox(params: {
  configDir: string | null;
  sandboxName: string;
  logger: PluginLogger;
}): boolean {
  const { configDir, sandboxName, logger } = params;
  if (!configDir) {
    logger.error("Cannot sync host state: ~/.openclaw was not found.");
    return false;
  }

  try {
    // Copy directory contents so hooks/extensions/skills land directly under
    // /sandbox/.openclaw instead of creating a nested ".openclaw" directory.
    execFileSync(
      "openshell",
      ["sandbox", "cp", join(configDir, "."), `${sandboxName}:/sandbox/.openclaw`],
      {
        encoding: "utf-8",
        stdio: ["ignore", "pipe", "pipe"],
      },
    );
    logger.info("Sandbox state synchronized to /sandbox/.openclaw.");
    return true;
  } catch (err: unknown) {
    const stderr =
      err &&
      typeof err === "object" &&
      "stderr" in err &&
      typeof (err as { stderr?: unknown }).stderr === "string"
        ? (err as { stderr: string }).stderr.trim()
        : "";
    logger.error(`Failed to copy ~/.openclaw into sandbox: ${stderr || String(err)}`);
    return false;
  }
}

function createSnapshot(hostState: HostOpenClawState, logger: PluginLogger): string | null {
  if (!hostState.configDir) return null;

  const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
  const snapshotDir = join(HOME, ".nemoclaw", "snapshots", timestamp);

  try {
    mkdirSync(snapshotDir, { recursive: true });
    cpSync(hostState.configDir, join(snapshotDir, "openclaw"), {
      recursive: true,
    });

    // Record what was captured
    const manifest = {
      timestamp,
      source: hostState.configDir,
      contents: readdirSync(join(snapshotDir, "openclaw")),
    };
    writeFileSync(join(snapshotDir, "snapshot.json"), JSON.stringify(manifest, null, 2));

    return snapshotDir;
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : String(err);
    logger.error(`Snapshot failed: ${msg}`);
    return null;
  }
}
