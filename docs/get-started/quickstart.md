---
title:
  page: "Nemo Clawd Quickstart - Solana and Blockchain AI Onboarding"
  nav: "Quickstart"
description: "Install Nemo Clawd, validate your machine, launch a sandboxed blockchain AI agent, and run the first Solana safety checks."
keywords: ["nemoclawd quickstart", "solana ai agent onboarding", "blockchain ai sandbox"]
topics: ["generative_ai", "ai_agents", "solana"]
tags: ["nemoclawd", "openshell", "sandboxing", "inference_routing", "solana", "wallets"]
content:
  type: get_started
  difficulty: technical_beginner
  audience: ["developer", "engineer"]
status: published
---

<!--
  SPDX-FileCopyrightText: Copyright (c) 2025-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
  SPDX-License-Identifier: Apache-2.0
-->

# Nemo Clawd Quickstart - Solana and Blockchain AI Onboarding

Use this page to install Nemo Clawd, create a sandboxed agent runtime, and run the first Solana readiness checks.
The flow is written for new blockchain AI users who want a controlled setup before connecting wallets, RPC providers, market data, or Telegram services.

:::{warning}
Start with dry-run checks and low-risk development settings.
The financial harness does not sign transactions, submit orders, or provide trading advice.
:::

## What You Set Up

The quickstart creates a host-side `nemoclawd` CLI, an OpenShell sandbox, a Nemo Clawd agent image, and a policy-bounded Solana operator stack.
The sandbox includes the Nemo Clawd MCP server, clawd operator, Solana tooling, inference routing, and network policies for approved blockchain endpoints.

| Layer | Purpose |
|---|---|
| `nemoclawd` CLI | Runs setup, diagnostics, sandbox lifecycle commands, wallet commands, and Solana service commands. |
| OpenShell sandbox | Isolates the agent from the host filesystem and blocks network destinations that are not policy-approved. |
| Nemo Clawd agent | Runs the bundled runtime, MCP tools, and blockchain AI operator services. |
| Solana path | Checks RPC, wallet metadata, network policy, and transaction guardrails before live services start. |

## Prerequisites

Install the following tools before you start:

- Node.js 22 or newer.
- npm.
- Docker Desktop, Colima, or another working Docker daemon.
- OpenShell, or permission for `nemoclawd onboard` to install or configure it.

You also need provider credentials for the services you choose during onboarding.
Do not paste API keys, bot tokens, wallet secrets, or private URLs into chat tools.
Use local shell environment variables or the interactive prompts.

## Install the CLI

Install the published package globally:

```console
$ npm install -g @mawdbotsonsolana/nemoclawd
```

If npm returns `E404` for the scoped package, the package is not published or your npm account cannot access it.
From a source checkout, install the local CLI instead:

```console
$ ./install.sh
```

Verify that the binary is available:

```console
$ nemoclawd --help
```

When you run the repository `install.sh`, it also seeds local runtime files under `~/.nemoclawd/`.
Those include `solana.json` with the `8bit/DeepSolana` own-model profile, `agent.json` for the lobster-themed Clawd command deck, and `trading-box.json` for dry-run trading guardrails.
If `solana-keygen` is available, the installer creates an unfunded local Solana keypair under `~/.nemoclawd/wallets/` with file mode `600`.
The installer does not enable live signing or transaction submission.

## Check the Host

Run the doctor before onboarding.
This command checks Node.js, npm, Docker, OpenShell, sandbox registry state, Solana RPC configuration, Privy wallet configuration, Telegram token configuration, and Helius configuration.

```console
$ nemoclawd doctor
```

Resolve blocking errors before continuing.
Warnings for optional services are acceptable when you are only testing the local sandbox path.

## Launch the First Sandbox

Use `launch` for the fastest path.
It runs diagnostics, starts onboarding when needed, and starts the best available Solana stack for the current machine.

```console
$ nemoclawd launch
```

Use `onboard` when you want to walk through each setup decision.
The wizard asks about the sandbox, inference provider, Solana RPC, wallet configuration, local validator option, and network policy presets.

```console
$ nemoclawd onboard
```

## Inspect the Solana Setup

After the sandbox exists, print the Solana status page:

```console
$ nemoclawd solana
```

The output shows the active sandbox, RPC status, wallet status, and recommended next commands.
If no sandbox exists, this command starts the onboard flow.

## Run the Financial Harness

Run the dry-run harness before starting Solana runtime services.
It checks RPC, inferred cluster, wallet metadata, policy coverage, and guardrails while keeping signing and transaction submission disabled.

```console
$ nemoclawd financial-harness
```

Run it against a named sandbox when you have more than one sandbox:

```console
$ nemoclawd financial-harness my-assistant
```

Use JSON output for automation:

```console
$ nemoclawd financial-harness my-assistant --json
```

## Create or Attach a Wallet

Use a Privy-backed wallet when you want the agent to have a managed Solana identity.
Private keys should not be stored in the sandbox filesystem.

```console
$ nemoclawd wallet create
$ nemoclawd wallet status
```

Keep the first wallet in a development posture until you understand the policy and audit trail.
Use devnet, a local validator, or a low-balance mainnet wallet for early testing.

## Start Solana Runtime Services

Start the Solana stack only after the financial harness output matches your intended operator posture.

```console
$ nemoclawd solana start my-assistant
```

The one-shot startup flow can start the Telegram bot, Solana bridge, websocket relay, wallet heartbeat, and vault logging.
If Telegram is not configured, Nemo Clawd can fall back to relay-only behavior.

## Monitor the Agent

Open the OpenShell TUI when you want to review sandbox activity and approve or deny blocked network requests:

```console
$ openshell term
```

Use the Nemo Clawd status command for the host-side view:

```console
$ nemoclawd status
```

## New User Path

Follow this order for your first run:

1. Install with `npm install -g @mawdbotsonsolana/nemoclawd`, or run `./install.sh` from a source checkout if npm returns `E404`.
2. Run `nemoclawd doctor`.
3. Run `nemoclawd launch` or `nemoclawd onboard`.
4. Run `nemoclawd solana`.
5. Run `nemoclawd financial-harness`.
6. Create or attach a wallet only after you understand the dry-run report.
7. Start `nemoclawd solana start <sandbox>` only when network policy, wallet posture, and service configuration are ready.

### Next Steps

- [Solana and Blockchain AI Onboarding](../solana/onboarding.md) explains Solana concepts, wallet posture, RPC choices, and the Nemo Clawd operator loop for new users.
- [Switch inference providers](../inference/switch-inference-providers.md) to use a different model or endpoint.
- [Run the financial harness](../solana/financial-harness.md) to inspect Solana RPC, wallet metadata, policy presets, and dry-run signing guardrails.
- [Approve or deny network requests](../network-policy/approve-network-requests.md) when the agent tries to reach external hosts.
- [Customize the network policy](../network-policy/customize-network-policy.md) to pre-approve trusted domains.
- [Deploy to a remote GPU instance](../deployment/deploy-to-remote-gpu.md) for always-on operation.
- [Monitor sandbox activity](../monitoring/monitor-sandbox-activity.md) through the OpenShell TUI.
