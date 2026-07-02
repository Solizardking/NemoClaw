// SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: Apache-2.0

const { describe, it } = require("node:test");
const assert = require("node:assert/strict");
const { execFileSync } = require("node:child_process");
const path = require("node:path");

const ROOT = path.join(__dirname, "..");
const CLI = path.join(ROOT, "bin", "nemoclawd.js");
const { verifyAiTraining } = require("../scripts/verify-ai-training");

describe("AI training integration", () => {
  it("verifies the bundled source lanes", () => {
    const report = verifyAiTraining(ROOT);
    assert.equal(report.ok, true);
    assert.equal(report.summary.present, report.summary.required);
    assert.equal(report.forbidden.length, 0);
    assert.equal(report.secretFindings.length, 0);
    assert.equal(report.oversizedFiles.length, 0);
  });

  it("is exposed through the standalone CLI", () => {
    const out = execFileSync("node", [CLI, "ai-training", "check", "--json"], {
      encoding: "utf-8",
      timeout: 10000,
      env: { ...process.env, HOME: "/tmp/nemoclawd-ai-training-test-" + Date.now() },
    });
    const report = JSON.parse(out);
    assert.equal(report.ok, true);
    assert.equal(report.summary.present, report.summary.required);
  });
});
