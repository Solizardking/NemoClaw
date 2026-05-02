// SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: Apache-2.0

/* v8 ignore start -- thin oclif adapter covered through CLI integration tests. */

import { Args, Command, Flags } from "@oclif/core";

type RuntimeBridge = {
  deploy: (instanceName?: string) => Promise<void>;
};

function getRuntimeBridge(): RuntimeBridge {
  return require("../nemoclaw") as RuntimeBridge;
}

export default class DeployCliCommand extends Command {
  static id = "deploy";
  static strict = true;
  static summary = "Deprecated Brev-specific bootstrap path";
  static description = "Deprecated compatibility command for Brev-specific deployment.";
  static usage = ["deploy [instance-name]"];
  static args = {
    instanceName: Args.string({
      name: "instance-name",
      description: "Brev instance name",
      required: false,
    }),
  };
  static flags = {
    help: Flags.help({ char: "h" }),
  };

  public async run(): Promise<void> {
    const { args } = await this.parse(DeployCliCommand);
    await getRuntimeBridge().deploy(args.instanceName);
  }
}
