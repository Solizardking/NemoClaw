// SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: Apache-2.0

const { describe, it } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const repoRoot = path.resolve(__dirname, "..");
const extensionsDir = path.join(repoRoot, "extensions");

function readJson(relativePath) {
  return JSON.parse(fs.readFileSync(path.join(repoRoot, relativePath), "utf8"));
}

function listFiles(dir) {
  return fs.readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) return listFiles(fullPath);
    return [path.relative(repoRoot, fullPath)];
  });
}

describe("compact extension registry", () => {
  it("keeps extension directories as registry pointers only", () => {
    const registry = readJson("extensions/registry.json");
    const byId = new Map(registry.extensions.map((extension) => [extension.id, extension]));

    assert.equal(byId.size, registry.extensions.length);
    assert.ok(byId.has("perps"));
    assert.equal(byId.get("solana-agent-copy").aliasOf, "solana-agent");

    for (const extension of registry.extensions) {
      const dir = path.join(extensionsDir, extension.path);
      const pointerPath = path.join(dir, "clawd.extension.json");
      const files = listFiles(dir).map((file) => path.relative(`extensions/${extension.path}`, file));

      assert.deepEqual(files, ["clawd.extension.json"]);
      const pointer = JSON.parse(fs.readFileSync(pointerPath, "utf8"));
      assert.equal(pointer.id, extension.id);
      assert.equal(pointer.registry, "../registry.json");
      assert.equal(pointer.status, extension.status);
      if (extension.aliasOf) assert.equal(pointer.aliasOf, extension.aliasOf);
    }
  });

  it("does not reintroduce source-heavy or credential-bearing extension artifacts", () => {
    const files = listFiles(extensionsDir);
    const forbidden = [
      /\.env(?:\.|$)/,
      /cdp_api_key\.json$/,
      /nohup\.out$/,
      /package-lock\.json$/,
      /pnpm-lock\.yaml$/,
      /node_modules\//,
      /\/dist\//,
      /\/src\//,
      /\/test\//,
      /\/skills\//,
      /\/node-main\//,
    ];

    for (const file of files) {
      assert.equal(
        forbidden.some((pattern) => pattern.test(file)),
        false,
        `unexpected bulky or sensitive extension artifact: ${file}`,
      );
    }
  });

  it("declares perpetual futures support explicitly", () => {
    const registry = readJson("extensions/registry.json");
    const byId = new Map(registry.extensions.map((extension) => [extension.id, extension]));

    for (const id of ["aster-dex", "hyperliquid-dex", "perps"]) {
      const extension = byId.get(id);
      assert.ok(extension, `${id} is missing`);
      assert.ok(extension.capabilities.includes("trading.perps"));
      assert.equal(extension.perps.supported, true);
    }

    assert.deepEqual(byId.get("perps").perps.providers, ["aster-dex", "hyperliquid-dex"]);
    assert.ok(byId.get("perps").perps.riskControls.includes("require-confirmation"));
  });
});
