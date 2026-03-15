// SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: Apache-2.0
//
// Policy preset management — list, load, merge, and apply presets.

const fs = require("fs");
const path = require("path");
const os = require("os");
const { ROOT, run, runCapture } = require("./runner");
const registry = require("./registry");

const PRESETS_DIR = path.join(ROOT, "nemoclaw-blueprint", "policies", "presets");

function listPresets() {
  if (!fs.existsSync(PRESETS_DIR)) return [];
  return fs
    .readdirSync(PRESETS_DIR)
    .filter((f) => f.endsWith(".yaml"))
    .map((f) => {
      const content = fs.readFileSync(path.join(PRESETS_DIR, f), "utf-8");
      const nameMatch = content.match(/^\s*name:\s*(.+)$/m);
      const descMatch = content.match(/^\s*description:\s*"?([^"]*)"?$/m);
      return {
        file: f,
        name: nameMatch ? nameMatch[1].trim() : f.replace(".yaml", ""),
        description: descMatch ? descMatch[1].trim() : "",
      };
    });
}

function loadPreset(name) {
  const file = path.join(PRESETS_DIR, `${name}.yaml`);
  if (!fs.existsSync(file)) {
    console.error(`  Preset not found: ${name}`);
    return null;
  }
  return fs.readFileSync(file, "utf-8");
}

function getPresetEndpoints(content) {
  const hosts = [];
  const regex = /host:\s*([^\s,}]+)/g;
  let match;
  while ((match = regex.exec(content)) !== null) {
    hosts.push(match[1]);
  }
  return hosts;
}

function applyPreset(sandboxName, presetName) {
  const presetContent = loadPreset(presetName);
  if (!presetContent) {
    console.error(`  Cannot load preset: ${presetName}`);
    return false;
  }

  // Get current policy
  let currentPolicy = "";
  try {
    currentPolicy = runCapture(
      `openshell policy get --sandbox ${sandboxName} 2>/dev/null`,
      { ignoreError: true }
    );
  } catch {}

  // Extract network_policies section from preset (skip the preset: header)
  const npMatch = presetContent.match(/^network_policies:[\s\S]*$/m);
  if (!npMatch) {
    console.error(`  Preset ${presetName} has no network_policies section.`);
    return false;
  }
  const presetNetworkPolicies = npMatch[0];

  // Merge: append preset network_policies into current policy
  let merged;
  if (currentPolicy && currentPolicy.includes("network_policies:")) {
    // Insert the preset's policies under the existing network_policies block
    const presetEntries = presetNetworkPolicies
      .replace(/^network_policies:\s*\n/, "")
      .trim();
    merged = currentPolicy.replace(
      /^(network_policies:.*$)/m,
      `$1\n${presetEntries}`
    );
  } else if (currentPolicy) {
    merged = currentPolicy + "\n" + presetNetworkPolicies;
  } else {
    merged = presetNetworkPolicies;
  }

  // Write temp file and apply
  const tmpFile = path.join(os.tmpdir(), `nemoclaw-policy-${Date.now()}.yaml`);
  fs.writeFileSync(tmpFile, merged, "utf-8");

  try {
    run(`openshell policy set --sandbox ${sandboxName} --policy "${tmpFile}" --wait`);
    console.log(`  Applied preset: ${presetName}`);
  } finally {
    fs.unlinkSync(tmpFile);
  }

  // Update registry
  const sandbox = registry.getSandbox(sandboxName);
  if (sandbox) {
    const policies = sandbox.policies || [];
    if (!policies.includes(presetName)) {
      policies.push(presetName);
    }
    registry.updateSandbox(sandboxName, { policies });
  }

  return true;
}

function getAppliedPresets(sandboxName) {
  const sandbox = registry.getSandbox(sandboxName);
  return sandbox ? sandbox.policies || [] : [];
}

module.exports = {
  PRESETS_DIR,
  listPresets,
  loadPreset,
  getPresetEndpoints,
  applyPreset,
  getAppliedPresets,
};
