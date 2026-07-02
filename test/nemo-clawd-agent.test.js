// SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: Apache-2.0

const { describe, it } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const repoRoot = path.resolve(__dirname, "..");

function readRepoFile(relativePath) {
  return fs.readFileSync(path.join(repoRoot, relativePath), "utf8");
}

describe("nemo-clawd agent packaging", () => {
  it("declares a Hermes-derived agent and bundled MCP server contract", () => {
    const manifest = readRepoFile("agents/nemo-clawd/manifest.yaml");

    assert.match(manifest, /^name: nemo-clawd$/m);
    assert.match(manifest, /^base_agent: hermes$/m);
    assert.match(manifest, /command: \/usr\/local\/bin\/nemo-clawd-mcp/);
    assert.match(manifest, /tool_count: 31/);
    assert.match(manifest, /name: clawd-operator/);
    assert.match(manifest, /binary_path: \/usr\/local\/bin\/clawd-operator/);
    assert.match(manifest, /clawd_agent_dir: \/opt\/clawd-operator\/clawd-agent/);
  });

  it("uses Docker-safe image and executable names in the Python blueprint", () => {
    const blueprint = readRepoFile("nemo-clawd-python/blueprint.yaml");

    assert.match(blueprint, /image: "ghcr\.io\/nvidia\/nemoclaw\/nemo-clawd:latest"/);
    assert.match(blueprint, /name: "nemo-clawd"/);
    assert.match(blueprint, /command: "\/usr\/local\/bin\/nemo-clawd-mcp"/);
    assert.match(blueprint, /name: "clawd-operator"/);
    assert.match(blueprint, /command: "\/usr\/local\/bin\/clawd-operator"/);
    assert.doesNotMatch(blueprint, /nemo clawd/);
  });

  it("restricts clawd network policies to executable paths without spaces", () => {
    const policy = readRepoFile("nemo-clawd-python/policies/nemoclawd-sandbox.yaml");

    assert.doesNotMatch(policy, /\/usr\/local\/bin\/nemo clawd/);
    assert.match(policy, /\/usr\/local\/bin\/nemoclawd/);
    assert.match(policy, /\/usr\/local\/bin\/nemo-clawd-mcp/);
    assert.match(policy, /\/usr\/local\/bin\/clawd-operator/);
    assert.match(policy, /host: api\.x\.ai/);
    assert.match(policy, /host: mainnet\.helius-rpc\.com/);
    assert.match(policy, /host: api\.jup\.ag/);
    assert.match(policy, /host: public-api\.birdeye\.so/);
  });

  it("installs clawd-operator without copying secret env files into the image contract", () => {
    const dockerfile = readRepoFile("agents/nemo-clawd/Dockerfile");
    const dockerignore = readRepoFile(".dockerignore");
    const packageJson = JSON.parse(readRepoFile("package.json"));

    assert.match(dockerfile, /COPY agents\/clawd-operator\/ \/opt\/clawd-operator\//);
    assert.match(dockerfile, /COPY agents\/nemo-clawd\/start-operator\.sh \/usr\/local\/bin\/clawd-operator/);
    assert.match(dockerfile, /secret env files must not be copied into clawd-operator image layers/);
    assert.match(dockerignore, /^\.env$/m);
    assert.match(dockerignore, /^\.env\.\*$/m);
    assert.match(dockerignore, /^!agents\/clawd-operator\/\.env\.example$/m);
    assert.ok(packageJson.files.includes("agents/clawd-operator/.env.example"));
    assert.ok(!packageJson.files.includes("agents/clawd-operator/.env"));
    assert.ok(!packageJson.files.includes("agents/clawd-operator/clawd-agent/.env.local"));
  });

  it("packages the Hermes base contract and imported dist runtime without local artifacts", () => {
    const packageJson = JSON.parse(readRepoFile("package.json"));
    const nemoClawdDockerfile = readRepoFile("agents/nemo-clawd/Dockerfile");
    const files = packageJson.files;

    assert.equal(packageJson.scripts["build:plugin"], "tsc -p tsconfig.nemoclawd.json");
    assert.ok(files.includes("dist/**"));
    assert.ok(files.includes("dist/acp/**"));
    assert.ok(files.includes("dist/agents/**"));
    assert.ok(files.includes("dist/gateway/**"));
    assert.ok(files.includes("dist/plugin-sdk/**"));
    assert.ok(files.includes("dist/*.js"));
    assert.ok(files.includes("dist/*.d.ts"));
    assert.ok(files.includes("dist/*.map"));

    assert.ok(files.includes("agents/hermes/Dockerfile"));
    assert.ok(files.includes("agents/hermes/Dockerfile.base"));
    assert.ok(files.includes("agents/hermes/generate-config.ts"));
    assert.ok(files.includes("agents/hermes/hermes-wrapper.py"));
    assert.ok(files.includes("agents/hermes/manifest.yaml"));
    assert.ok(files.includes("agents/hermes/policy-additions.yaml"));
    assert.ok(files.includes("agents/hermes/policy-permissive.yaml"));
    assert.ok(files.includes("agents/hermes/runtime-config-guard.py"));
    assert.ok(files.includes("agents/hermes/seed-dashboard-config.py"));
    assert.ok(files.includes("agents/hermes/start.sh"));
    assert.ok(files.includes("agents/hermes/validate-env-secret-boundary.py"));
    assert.ok(files.includes("agents/hermes/config/**"));
    assert.ok(files.includes("agents/hermes/host/**"));
    assert.ok(files.includes("agents/hermes/plugin/**"));

    assert.ok(!files.includes("agents/hermes/**"));
    assert.ok(!files.includes("agents/hermes/.DS_Store"));
    assert.ok(!files.includes("agents/hermes/.env"));
    assert.ok(!files.includes("agents/hermes/.env.local"));
    assert.match(nemoClawdDockerfile, /FROM \$\{BASE_IMAGE\}/);
    assert.match(nemoClawdDockerfile, /command -v hermes/);
  });
});

describe("nemo-clawd MCP transports", () => {
  it("starts stdio only when index.ts is invoked directly", () => {
    const indexTs = readRepoFile("nemo-clawd-mcp/src/index.ts");
    const httpTs = readRepoFile("nemo-clawd-mcp/src/http.ts");

    assert.match(indexTs, /function isDirectRun\(\): boolean/);
    assert.match(indexTs, /export async function startStdioServer/);
    assert.match(indexTs, /if \(isDirectRun\(\)\)/);
    assert.match(httpTs, /import \{ server \} from "\.\/index\.js";/);
    assert.doesNotMatch(httpTs, /startStdioServer/);
  });
});
