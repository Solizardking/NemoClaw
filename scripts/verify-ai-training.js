#!/usr/bin/env node
// SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: Apache-2.0

const fs = require("fs");
const path = require("path");

const DEFAULT_ROOT = path.resolve(__dirname, "..");
const MAX_SOURCE_FILE_BYTES = 25 * 1024 * 1024;

const REQUIRED_PATHS = [
  ["ai-training/README.md", "file"],
  ["ai-training/STRUCTURE.md", "file"],
  ["ai-training/Anchor.toml", "file"],
  ["ai-training/Cargo.toml", "file"],
  ["ai-training/Cargo.lock", "file"],
  ["ai-training/configs/core_ai_lora_config.yaml", "file"],
  ["ai-training/docs/model_card.md", "file"],
  ["ai-training/memory/honcho.py", "file"],
  ["ai-training/model-kit/bin/clawd-model-kit", "file"],
  ["ai-training/model-kit/clawd_model_kit.py", "file"],
  ["ai-training/model-kit/backend/main.py", "file"],
  ["ai-training/model-kit/frontend/index.html", "file"],
  ["ai-training/model-kit/scripts/verify-static-site.mjs", "file"],
  ["ai-training/nvidia/README.md", "file"],
  ["ai-training/nvidia/blueprints/signal-discovery/README.md", "file"],
  ["ai-training/nvidia/blueprints/signal-discovery/agent.py", "file"],
  ["ai-training/nvidia/blueprints/signal-discovery/quantitative_signal_agent.py", "file"],
  ["ai-training/nvidia/blueprints/signal-discovery/perps_signal_agent.py", "file"],
  ["ai-training/nvidia/blueprints/signal-discovery/frontend/index.html", "file"],
  ["ai-training/nvidia/integration/clawd_nim_bridge.py", "file"],
  ["ai-training/nvidia/integration/nemo_clawd.py", "file"],
  ["ai-training/nvidia/scripts/verify_nvidia.py", "file"],
  ["ai-training/perps/schema.py", "file"],
  ["ai-training/programs/clawd-core/src/lib.rs", "file"],
  ["ai-training/programs/clawd-registry/src/lib.rs", "file"],
  ["ai-training/programs/clawd-treasury/src/lib.rs", "file"],
  ["ai-training/schemas/ai_training_layout.schema.json", "file"],
  ["ai-training/scripts/run_local_clawd_stack.py", "file"],
  ["ai-training/studio/index.html", "file"],
  ["ai-training/trading_factory/README.md", "file"],
  ["ai-training/trading_factory/solana_factory/factory.py", "file"],
];

const FORBIDDEN_PATHS = [
  "ai-training/.claude",
  "ai-training/.git",
  "ai-training/.hf",
  "ai-training/.venv",
  "ai-training/data",
  "ai-training/outputs",
  "ai-training/target",
  "ai-training/wandb",
  "ai-training/ollama/build",
  "ai-training/nvidia/outputs",
  "ai-training/trainingday.jsonl",
  "ai-training/solana1_yourgpt.jsonl",
  "ai-training/trading_factory/clawd-autoresearch-wiki/.env",
  "ai-training/trading_factory/clawd-autoresearch-wiki/.clawvault",
  "ai-training/trading_factory/clawd-autoresearch-wiki/nanochat-master",
  "ai-training/trading_factory/clawd-autoresearch-wiki/solana-chat",
];

const SKIP_DIR_NAMES = new Set([
  ".git",
  ".hf",
  ".venv",
  ".uv-cache",
  "__pycache__",
  "data",
  "node_modules",
  "outputs",
  "target",
  "wandb",
]);

const SECRET_FILE_PATTERNS = [
  /(^|\/)\.env(\.|$)/,
  /(^|\/)credentials\.json$/,
  /(^|\/)secrets\.(json|ya?ml)$/,
  /(^|\/).*keypair.*\.json$/,
  /(^|\/).*(?:wallet|token|secret)\.json$/,
  /\.(pem|key|p12|pfx|keystore|jks|asc|gpg)$/i,
];

const SECRET_CONTENT_PATTERNS = [
  ["private_key", /-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----/],
  ["nvidia_api_key", /\bnvapi-[A-Za-z0-9_-]{20,}\b/],
  ["openai_api_key", /\bsk-[A-Za-z0-9]{20,}\b/],
  ["github_pat", /\bghp_[A-Za-z0-9]{30,}\b/],
  ["aws_access_key", /\bAKIA[A-Z0-9]{16}\b/],
  ["telegram_bot_token", /\bbot[0-9]{8,}:[A-Za-z0-9_-]{30,}\b/],
  ["huggingface_token", /\bhf_[A-Za-z0-9]{30,}\b/],
];

function existsWithKind(absolutePath, kind) {
  try {
    const stat = fs.statSync(absolutePath);
    return kind === "directory" ? stat.isDirectory() : stat.isFile();
  } catch {
    return false;
  }
}

function listFiles(rootDir, relativeDir = "") {
  const absoluteDir = path.join(rootDir, relativeDir);
  let entries;
  try {
    entries = fs.readdirSync(absoluteDir, { withFileTypes: true });
  } catch {
    return [];
  }

  const files = [];
  for (const entry of entries) {
    const relativePath = path.join(relativeDir, entry.name);
    const normalized = relativePath.split(path.sep).join("/");
    if (entry.isDirectory()) {
      if (SKIP_DIR_NAMES.has(entry.name)) {
        continue;
      }
      files.push(...listFiles(rootDir, relativePath));
      continue;
    }
    if (entry.isFile()) {
      files.push(normalized);
    }
  }
  return files;
}

function scanSecrets(rootDir, files) {
  const findings = [];
  for (const file of files) {
    if (SECRET_FILE_PATTERNS.some((pattern) => pattern.test(file))) {
      findings.push({ path: file, reason: "secret-like filename" });
      continue;
    }

    const absolutePath = path.join(rootDir, file);
    const stat = fs.statSync(absolutePath);
    if (stat.size > MAX_SOURCE_FILE_BYTES) {
      continue;
    }

    const text = fs.readFileSync(absolutePath, "utf8");
    for (const [name, pattern] of SECRET_CONTENT_PATTERNS) {
      if (pattern.test(text)) {
        findings.push({ path: file, reason: name });
      }
    }
  }
  return findings;
}

function verifyAiTraining(rootDir = DEFAULT_ROOT) {
  const required = REQUIRED_PATHS.map(([relativePath, kind]) => ({
    path: relativePath,
    kind,
    ok: existsWithKind(path.join(rootDir, relativePath), kind),
  }));

  const forbidden = FORBIDDEN_PATHS
    .filter((relativePath) => fs.existsSync(path.join(rootDir, relativePath)))
    .map((relativePath) => ({ path: relativePath, reason: "forbidden generated, local, or secret lane" }));

  const files = listFiles(rootDir, "ai-training");
  const oversizedFiles = files
    .map((file) => {
      const size = fs.statSync(path.join(rootDir, file)).size;
      return { path: file, size };
    })
    .filter((item) => item.size > MAX_SOURCE_FILE_BYTES);

  const secretFindings = scanSecrets(rootDir, files);
  const ok =
    required.every((item) => item.ok) &&
    forbidden.length === 0 &&
    oversizedFiles.length === 0 &&
    secretFindings.length === 0;

  return {
    ok,
    root: rootDir,
    required,
    forbidden,
    oversizedFiles,
    secretFindings,
    summary: {
      required: required.length,
      present: required.filter((item) => item.ok).length,
      filesScanned: files.length,
    },
  };
}

function printReport(report) {
  console.log(`[ai-training] ${report.ok ? "ok" : "failed"}`);
  console.log(`required paths: ${report.summary.present}/${report.summary.required}`);
  console.log(`source files scanned: ${report.summary.filesScanned}`);

  const missing = report.required.filter((item) => !item.ok);
  if (missing.length > 0) {
    console.log("");
    console.log("missing required paths:");
    missing.forEach((item) => console.log(`  - ${item.path}`));
  }

  if (report.forbidden.length > 0) {
    console.log("");
    console.log("forbidden paths present:");
    report.forbidden.forEach((item) => console.log(`  - ${item.path}`));
  }

  if (report.oversizedFiles.length > 0) {
    console.log("");
    console.log("oversized source files:");
    report.oversizedFiles.forEach((item) => console.log(`  - ${item.path} (${item.size} bytes)`));
  }

  if (report.secretFindings.length > 0) {
    console.log("");
    console.log("secret-like findings:");
    report.secretFindings.forEach((item) => console.log(`  - ${item.path}: ${item.reason}`));
  }
}

function main(argv = process.argv.slice(2)) {
  const json = argv.includes("--json");
  const report = verifyAiTraining();

  if (json) {
    console.log(JSON.stringify(report, null, 2));
  } else {
    printReport(report);
  }

  if (!report.ok) {
    process.exit(1);
  }
}

if (require.main === module) {
  main();
}

module.exports = {
  REQUIRED_PATHS,
  FORBIDDEN_PATHS,
  verifyAiTraining,
};
