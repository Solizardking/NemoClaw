---
title:
  page: "Deploy Nemo Clawd to a Remote GPU Instance for Solana AI"
  nav: "Deploy to Remote GPU"
description: "Provision a remote GPU VM with Nemo Clawd, then verify Solana RPC, wallet posture, and network policy before starting wallet-aware services."
keywords: ["deploy nemoclawd remote gpu", "nemoclawd brev cloud deployment", "solana ai remote agent"]
topics: ["generative_ai", "ai_agents", "solana"]
tags: ["nemoclawd", "openshell", "deployment", "gpu", "solana", "wallets"]
content:
  type: how_to
  difficulty: intermediate
  audience: ["developer", "engineer"]
status: published
---

<!--
  SPDX-FileCopyrightText: Copyright (c) 2025-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
  SPDX-License-Identifier: Apache-2.0
-->

# Deploy Nemo Clawd to a Remote GPU Instance for Solana AI

Run Nemo Clawd on a remote GPU instance through [Brev](https://brev.nvidia.com).
The deploy command provisions the VM, installs dependencies, and connects you to a running sandbox.
Use the same Solana onboarding sequence on the remote instance that you use locally: diagnose, inspect Solana configuration, run the financial harness, then start wallet-aware services only when the report matches your intended posture.

## Prerequisites

- The [Brev CLI](https://brev.nvidia.com) installed and authenticated.
- An NVIDIA API key from [build.nvidia.com](https://build.nvidia.com).
- Nemo Clawd installed locally. Install with `npm install -g @mawdbotsonsolana/nemoclawd`, or run `./install.sh` from a source checkout if npm returns `E404`.

## Deploy the Instance

Create a Brev instance and run the Nemo Clawd setup:

```console
$ nemoclawd deploy <instance-name>
```

Replace `<instance-name>` with a name for your remote instance, for example `my-gpu-box`.

The deploy script performs the following steps on the VM:

1. Installs Docker and the NVIDIA Container Toolkit if a GPU is present.
2. Installs the OpenShell CLI.
3. Runs the nemoclawd setup to create the gateway, register providers, and launch the sandbox.
4. Starts auxiliary services, such as the Telegram bridge and cloudflared tunnel.

## Verify Solana Readiness

After the VM is available, run the Solana checks on the remote host before enabling runtime services:

```console
$ ssh <instance-name> 'cd /home/ubuntu/nemoclawd && set -a && . .env && set +a && nemoclawd doctor && nemoclawd solana && nemoclawd financial-harness'
```

The financial harness should show the expected cluster, RPC endpoint, wallet posture, required policy presets, and signing guardrails.
Resolve blockers before you start `nemoclawd solana start <sandbox>`.

For first remote deployments, prefer a local validator, devnet, or low-balance mainnet wallet until you have reviewed the policy and vault output.

## Connect to the Remote Sandbox

After deployment finishes, the deploy command opens an interactive shell inside the remote sandbox.
To reconnect after closing the session, run the deploy command again:

```console
$ nemoclawd deploy <instance-name>
```

## Monitor the Remote Sandbox

SSH to the instance and run the OpenShell TUI to monitor activity and approve network requests:

```console
$ ssh <instance-name> 'cd /home/ubuntu/nemoclawd && set -a && . .env && set +a && openshell term'
```

## Verify Inference

Run a test agent prompt inside the remote sandbox:

```console
$ nemoclawd agent --agent main --local -m "Hello from the remote sandbox" --session-id test
```

## Start Solana Runtime Services

Start wallet-aware services only after the financial harness output is acceptable:

```console
$ ssh <instance-name> 'cd /home/ubuntu/nemoclawd && set -a && . .env && set +a && nemoclawd solana start <sandbox-name>'
```

The startup flow can launch the Solana bridge, Telegram bot, websocket relay, wallet heartbeat, and vault logging.
If Telegram is not configured, Nemo Clawd can run relay-only services.

## GPU Configuration

The deploy script uses the `NEMOCLAW_GPU` environment variable to select the GPU type.
The default value is `a2-highgpu-1g:nvidia-tesla-a100:1`.
Set this variable before running `nemoclawd deploy` to use a different GPU configuration:

```console
$ export NEMOCLAW_GPU="a2-highgpu-1g:nvidia-tesla-a100:2"
$ nemoclawd deploy <instance-name>
```

## Related Topics

- [Set Up the Telegram Bridge](set-up-telegram-bridge.md) to interact with the remote agent through Telegram.
- [Solana and Blockchain AI Onboarding](../solana/onboarding.md) for cluster, RPC, wallet, and policy concepts.
- [Financial Harness](../solana/financial-harness.md) for dry-run wallet and signing guardrail checks.
- [Monitor Sandbox Activity](../monitoring/monitor-sandbox-activity.md) for sandbox monitoring tools.
- [Commands](../reference/commands.md) for the full `deploy` command reference.
