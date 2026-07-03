// SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: Apache-2.0

const { describe, it } = require("node:test");
const assert = require("node:assert/strict");
const { execSync } = require("child_process");
const path = require("path");
const fs = require("fs");

const CLI = path.join(__dirname, "..", "bin", "nemoclawd.js");

function run(args) {
  try {
    const out = execSync(`node "${CLI}" ${args}`, {
      encoding: "utf-8",
      timeout: 10000,
      env: { ...process.env, HOME: "/tmp/nemoclawd-cli-test-" + Date.now() },
    });
    return { code: 0, out };
  } catch (err) {
    return { code: err.status, out: (err.stdout || "") + (err.stderr || "") };
  }
}

describe("CLI dispatch", () => {
  it("help exits 0 and shows sections", () => {
    const r = run("help");
    assert.equal(r.code, 0);
    assert.ok(r.out.includes("Getting Started"), "missing Getting Started section");
    assert.ok(r.out.includes("Sandbox Management"), "missing Sandbox Management section");
    assert.ok(r.out.includes("Policy Presets"), "missing Policy Presets section");
    assert.ok(r.out.includes("doctor"), "missing doctor command");
    assert.ok(r.out.includes("launch"), "missing launch command");
    assert.ok(r.out.includes("financial-harness"), "missing financial harness command");
    assert.ok(r.out.includes("ai-training"), "missing ai-training command");
    assert.ok(r.out.includes("birth"), "missing birth command");
    assert.ok(r.out.includes("demo"), "missing demo command");
    assert.ok(r.out.includes("Lobster-themed"), "missing lobster theme");
    assert.ok(r.out.includes("solana-agent"), "missing Solana agent action");
    assert.ok(r.out.includes("solana-bridge"), "missing Solana bridge action");
    assert.ok(r.out.includes("solana start"), "missing Solana one-shot action");
    assert.ok(r.out.includes("telegram-bot"), "missing Telegram bot action");
    assert.ok(r.out.includes("payment-app"), "missing payment app action");
  });

  it("--help exits 0", () => {
    assert.equal(run("--help").code, 0);
  });

  it("-h exits 0", () => {
    assert.equal(run("-h").code, 0);
  });

  it("no args exits 0 (shows help)", () => {
    const r = run("");
    assert.equal(r.code, 0);
    assert.ok(r.out.includes("nemoclawd"));
  });

  it("unknown command exits 1", () => {
    const r = run("boguscmd");
    assert.equal(r.code, 1);
    assert.match(r.out, /unknown command/i);
  });

  it("list exits 0", () => {
    const r = run("list");
    assert.equal(r.code, 0);
    // With empty HOME, should say no sandboxes
    assert.ok(r.out.includes("No sandboxes"));
  });

  it("version exits 0 and shows package version", () => {
    const pkg = JSON.parse(fs.readFileSync(path.join(__dirname, "..", "package.json"), "utf-8"));
    const r = run("version");
    assert.equal(r.code, 0);
    assert.ok(r.out.includes(pkg.version), "missing CLI version");
  });

  it("financial-harness --json exits 0 and stays dry-run", () => {
    const r = run("financial-harness --json");
    assert.equal(r.code, 0);
    const report = JSON.parse(r.out);
    assert.equal(report.name, "nemoclawd-financial-harness");
    assert.equal(report.mode, "dry-run");
    assert.equal(report.guardrails.signingEnabled, false);
    assert.equal(report.guardrails.transactionSubmissionEnabled, false);
  });

  it("demo exits 0 and prints the dry-run walkthrough", () => {
    const r = run("demo");
    assert.equal(r.code, 0);
    assert.ok(r.out.includes("Nemo Clawd Demo Walkthrough"), "missing demo title");
    assert.ok(r.out.includes("nemoclawd financial-harness"), "missing harness step");
    assert.ok(r.out.includes("dry-run only"), "missing dry-run safety note");
  });

  it("birth --json lists localized Clawd agents", () => {
    const r = run("birth --json");
    assert.equal(r.code, 0);
    const deck = JSON.parse(r.out);
    assert.equal(deck.theme, "lobster");
    assert.equal(deck.symbol, "🦞");
    assert.ok(deck.count >= 42, "missing locale birth agents");
    assert.ok(
      deck.agents.some((agent) => agent.id === "clawd-onboarding-guide"),
      "missing clawd-onboarding-guide",
    );
    assert.ok(
      deck.agents.some((agent) => agent.id === "yield-dashboard-builder"),
      "missing yield-dashboard-builder",
    );
  });

  it("birth writes a lobster-themed agent record", () => {
    const r = run("birth clawd-onboarding-guide --locale fr-FR --json");
    assert.equal(r.code, 0);
    const record = JSON.parse(r.out);
    assert.equal(record.theme, "lobster");
    assert.equal(record.id, "clawd-onboarding-guide");
    assert.equal(record.locale, "fr-FR");
    assert.ok(record.path.endsWith("clawd-onboarding-guide.json"));
  });

  it("routes unknown legacy commands through the compiled dist runtime", () => {
    const r = run("gateway --help");
    assert.equal(r.code, 0);
    assert.ok(r.out.includes("Usage: clawdbot gateway"), "missing compiled gateway help");
    assert.ok(r.out.includes("Run the WebSocket Gateway"), "missing compiled gateway description");
  });

  it("supports explicit compiled dist runtime dispatch", () => {
    const r = run("dist status --help");
    assert.equal(r.code, 0);
    assert.ok(r.out.includes("Usage: clawdbot status"), "missing compiled status help");
    assert.ok(r.out.includes("Show channel health"), "missing compiled status description");
  });

  it("solana overview prefers active gateway last sandbox over first registry entry", () => {
    const home = "/tmp/nemoclawd-cli-test-" + Date.now();
    const sandboxDir = path.join(home, ".nemoclawd");
    const openshellDir = path.join(home, ".config", "openshell", "gateways", "nemoclawd");
    fs.mkdirSync(sandboxDir, { recursive: true });
    fs.mkdirSync(openshellDir, { recursive: true });
    fs.writeFileSync(
      path.join(sandboxDir, "sandboxes.json"),
      JSON.stringify({
        sandboxes: {
          "my-assistant": { name: "my-assistant", model: "old-model", provider: "ollama-local", gpuEnabled: true, policies: [] },
          "nemo": { name: "nemo", model: "8bit/DeepSolana", provider: "ollama-local", gpuEnabled: true, policies: [] },
        },
        defaultSandbox: "my-assistant",
      }),
    );
    fs.mkdirSync(path.join(home, ".config", "openshell"), { recursive: true });
    fs.writeFileSync(path.join(home, ".config", "openshell", "active_gateway"), "nemoclawd\n");
    fs.writeFileSync(path.join(openshellDir, "last_sandbox"), "nemo\n");

    const out = execSync(`node "${CLI}" solana`, {
      encoding: "utf-8",
      timeout: 10000,
      env: { ...process.env, HOME: home },
    });

    assert.ok(out.includes("Using sandbox: nemo"), out);
    assert.ok(!out.includes("Using sandbox: my-assistant"), out);
  });
});
