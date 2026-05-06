// SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: Apache-2.0

import { spawnSync } from "node:child_process";
import path from "node:path";
import { describe, expect, it } from "vitest";

const CLI = path.join(import.meta.dirname, "..", "bin", "nemoclaw.js");

describe("internal oclif namespace", () => {
  it("passes internal subcommands directly to oclif space-separated routing", () => {
    const result = spawnSync(process.execPath, [CLI, "internal", "dns", "fix-coredns", "--help"], {
      encoding: "utf-8",
    });

    expect(result.status).toBe(0);
    expect(result.stdout).toContain("Internal: patch CoreDNS");
    expect(result.stdout).toContain("nemoclaw internal dns fix-coredns [gateway-name]");
  });

  it("exposes setup-proxy as an oclif-routed internal subcommand", () => {
    const result = spawnSync(process.execPath, [CLI, "internal", "dns", "setup-proxy", "--help"], {
      encoding: "utf-8",
    });

    expect(result.status).toBe(0);
    expect(result.stdout).toContain("Internal: configure sandbox DNS proxy");
    expect(result.stdout).toContain("nemoclaw internal dns setup-proxy <gateway-name> <sandbox-name>");
  });
});
