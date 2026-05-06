// SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: Apache-2.0

import { Config as OclifConfig } from "@oclif/core";
import { describe, expect, it } from "vitest";

import commands from "../../../dist/lib/commands/index.js";

const expectedIds = Object.keys(commands).sort();

describe("oclif pattern command discovery", () => {
  it("discovers every command id from the compatibility command index", async () => {
    const config = await OclifConfig.load(process.cwd());
    const discoveredIds = config.commands.map((command) => command.id).sort();

    expect(discoveredIds).toEqual(expect.arrayContaining(expectedIds));
  });
});
