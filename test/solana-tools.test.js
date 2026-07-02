// SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: Apache-2.0

const { describe, it } = require("node:test");
const assert = require("node:assert/strict");
const { execFileSync, spawnSync } = require("node:child_process");
const path = require("node:path");
const { pathToFileURL } = require("node:url");

const TOOL = path.join(__dirname, "..", "tools", "e2e", "solana-readiness.mts");
const SOLANA_HELPER = path.join(__dirname, "..", "tools", "advisors", "solana.mts");

describe("Solana readiness tools", () => {
  it("renders deterministic no-network dry-run JSON with disabled signing guardrails", () => {
    const output = execFileSync(
      process.execPath,
      ["--experimental-strip-types", TOOL, "--no-network", "--json", "--privy"],
      { encoding: "utf8" },
    );
    const report = JSON.parse(output);
    assert.equal(report.name, "nemoclawd-solana-readiness");
    assert.equal(report.mode, "dry-run");
    assert.equal(report.status, "skipped");
    assert.equal(report.rpc.networkSkipped, true);
    assert.equal(report.guardrails.signingEnabled, false);
    assert.equal(report.guardrails.transactionSubmissionEnabled, false);
    assert.ok(report.policyHints.requiredPresets.includes("privy"));
  });

  it("probes Solana JSON-RPC through injected fetch and redacts RPC credentials", async () => {
    const { buildSolanaReadinessReport } = await import(pathToFileURL(SOLANA_HELPER).href);
    const requests = [];
    const address = "So11111111111111111111111111111111111111112";
    const report = await buildSolanaReadinessReport({
      rpcUrl: "http://127.0.0.1:8899/?api-key=secret",
      walletAddress: address,
      expectedCluster: "local-validator",
      now: new Date("2026-07-02T00:00:00.000Z"),
      fetchImpl: async (_url, init) => {
        const payload = JSON.parse(init.body);
        requests.push(payload.method);
        return new Response(JSON.stringify(jsonRpcResponse(payload.id, payload.method)), {
          status: 200,
          headers: { "content-type": "application/json" },
        });
      },
    });
    assert.equal(report.status, "ready");
    assert.equal(report.generatedAt, "2026-07-02T00:00:00.000Z");
    assert.equal(report.rpc.url, "http://127.0.0.1:8899/?api-key=redacted");
    assert.equal(report.rpc.cluster, "local-validator");
    assert.equal(report.rpc.health, "ok");
    assert.equal(report.wallet.address, address);
    assert.equal(report.wallet.balanceLamports, 123456789);
    assert.deepEqual(report.rpc.errors, []);
    assert.deepEqual(requests, [
      "getHealth",
      "getVersion",
      "getEpochInfo",
      "getLatestBlockhash",
      "getBalance",
    ]);
  });

  it("blocks when expected cluster does not match inferred RPC cluster", () => {
    const result = spawnSync(
      process.execPath,
      [
        "--experimental-strip-types",
        TOOL,
        "--no-network",
        "--rpc",
        "https://api.devnet.solana.com",
        "--expect-cluster",
        "mainnet",
        "--json",
      ],
      { encoding: "utf8" },
    );
    assert.equal(result.status, 1);
    const report = JSON.parse(result.stdout);
    assert.equal(report.status, "blocked");
    assert.ok(report.blockers.includes("expected mainnet RPC but inferred devnet"));
  });
});

function jsonRpcResponse(id, method) {
  const results = {
    getHealth: "ok",
    getVersion: { "solana-core": "1.18.26" },
    getEpochInfo: { epoch: 99, absoluteSlot: 12345 },
    getLatestBlockhash: {
      context: { slot: 12345 },
      value: {
        blockhash: "11111111111111111111111111111111",
        lastValidBlockHeight: 999999,
      },
    },
    getBalance: { context: { slot: 12345 }, value: 123456789 },
  };
  if (Object.hasOwn(results, method)) {
    return { jsonrpc: "2.0", id, result: results[method] };
  }
  return {
    jsonrpc: "2.0",
    id,
    error: { code: -32601, message: `unsupported method ${method}` },
  };
}
