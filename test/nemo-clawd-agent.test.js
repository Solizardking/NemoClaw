// SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: Apache-2.0

const { describe, it } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const repoRoot = path.resolve(__dirname, "..");
const requiredBirthAgents = [
  "airdrop-hunter",
  "alpha-leak-detector",
  "apy-vs-apr-educator",
  "bridge-security-analyst",
  "clawd-bridge-assistant",
  "clawd-governance-guide",
  "clawd-liquidity-strategist",
  "clawd-onboarding-guide",
  "clawd-portfolio-tracker",
  "clawd-risk-monitor",
  "clawd-yield-aggregator",
  "crypto-news-analyst",
  "crypto-tax-strategist",
  "defi-insurance-advisor",
  "defi-onboarding-mentor",
  "defi-protocol-comparator",
  "defi-risk-scoring-engine",
  "defi-yield-farmer",
  "dex-aggregator-optimizer",
  "gas-optimization-expert",
  "governance-proposal-analyst",
  "impermanent-loss-calculator",
  "layer2-comparison-guide",
  "liquidation-risk-manager",
  "liquidity-pool-analyzer",
  "mev-protection-advisor",
  "narrative-trend-analyst",
  "nft-liquidity-advisor",
  "portfolio-rebalancing-advisor",
  "protocol-revenue-analyst",
  "protocol-treasury-analyst",
  "pump-fun-sdk-expert",
  "smart-contract-auditor",
  "spa-tokenomics-analyst",
  "stablecoin-comparator",
  "staking-rewards-calculator",
  "token-unlock-tracker",
  "usds-stablecoin-expert",
  "vespa-optimizer",
  "wallet-security-advisor",
  "whale-watcher",
  "yield-dashboard-builder",
  "yield-sustainability-analyst",
];

function readRepoFile(relativePath) {
  return fs.readFileSync(path.join(repoRoot, relativePath), "utf8");
}

function repoFileExists(relativePath) {
  return fs.existsSync(path.join(repoRoot, relativePath));
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

  it("packages localized birth agents and the Nemo Clawd user-guide skill", () => {
    const packageJson = JSON.parse(readRepoFile("package.json"));
    const rootPlugin = JSON.parse(readRepoFile("nemoclawd.plugin.json"));
    const nestedPlugin = JSON.parse(readRepoFile("nemoclaw/clawd.plugin.json"));
    const files = packageJson.files;

    assert.ok(files.includes("agents/agents-catalog.json"));
    assert.ok(files.includes("agents/agents-manifest.json"));
    assert.ok(files.includes("agents/locales/**"));
    assert.ok(files.includes("agents/src/*.json"));
    assert.ok(files.includes("skills/README.md"));
    assert.ok(files.includes("skills/nemoclawd-user-guide/**"));
    assert.ok(files.includes("nemoclaw/clawd.plugin.json"));
    assert.ok(files.includes("nemoclaw/package.json"));
    assert.ok(files.includes("nemoclaw/package-lock.json"));
    assert.ok(files.includes("nemoclaw/tsconfig.json"));
    assert.ok(files.includes("nemoclaw/vitest.config.ts"));
    assert.ok(files.includes("nemoclaw/.prettierrc"));
    assert.ok(files.includes("nemoclaw/eslint.config.mjs"));
    assert.ok(files.includes("nemoclaw/src/**"));
    assert.ok(files.includes("nemoclaw/dist/**"));
    assert.ok(files.includes("nemoclaw-blueprint/Makefile"));
    assert.ok(files.includes("nemoclaw-blueprint/blueprint.yaml"));
    assert.ok(files.includes("nemoclaw-blueprint/pyproject.toml"));
    assert.ok(files.includes("nemoclaw-blueprint/migrations/*.py"));
    assert.ok(files.includes("nemoclaw-blueprint/orchestrator/*.py"));
    assert.ok(files.includes("nemoclaw-blueprint/policies/**/*.yaml"));
    assert.ok(files.includes("nemoclaw-mcp/README.md"));
    assert.ok(files.includes("nemoclaw-mcp/package.json"));
    assert.ok(files.includes("nemoclaw-mcp/package-lock.json"));
    assert.ok(files.includes("nemoclaw-mcp/tsconfig.json"));
    assert.ok(files.includes("nemoclaw-mcp/src/**"));
    assert.ok(files.includes("nemoclaw-mcp/dist/**"));
    assert.ok(files.includes("schemas/*.json"));
    assert.ok(!files.includes("agents/**"));
    assert.ok(!files.includes("node_modules"));
    assert.ok(!files.includes("nemoclaw/node_modules/**"));
    assert.ok(!files.includes("nemoclaw-mcp/node_modules/**"));
    assert.ok(!files.includes("nemoclaw-blueprint/**"));
    assert.ok(!files.includes("nemoclaw/openclaw.plugin.json"));

    assert.ok(repoFileExists("skills/nemoclawd-user-guide/SKILL.md"));
    assert.ok(repoFileExists("skills/nemoclawd-user-guide/BENCHMARK.md"));
    assert.ok(repoFileExists("skills/nemoclawd-user-guide/skill-card.md"));
    assert.ok(repoFileExists("skills/nemoclawd-user-guide/skill.oms.sig"));
    assert.ok(repoFileExists("skills/nemoclawd-user-guide/evals/evals.json"));
    assert.ok(repoFileExists("nemoclaw/clawd.plugin.json"));
    assert.ok(repoFileExists("schemas/clawd-plugin.schema.json"));
    assert.ok(repoFileExists("schemas/openclaw-plugin.schema.json"));
    assert.ok(repoFileExists("nemoclaw-blueprint/blueprint.yaml"));
    assert.ok(repoFileExists("nemoclaw-mcp/src/index.ts"));
    assert.equal(rootPlugin.name, "Nemo Clawd");
    assert.equal(rootPlugin.activation.onStartup, true);
    assert.equal(rootPlugin.commandAliases[0].name, "nemoclawd");
    assert.equal(nestedPlugin.name, "Nemo Clawd");
    assert.equal(nestedPlugin.configSchema.properties.sandboxName.default, "nemoclawd");

    for (const agentId of requiredBirthAgents) {
      assert.ok(repoFileExists(`agents/locales/${agentId}/index.json`), `missing locale ${agentId}`);
      assert.ok(repoFileExists(`agents/src/${agentId}.json`), `missing source ${agentId}`);
    }
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
