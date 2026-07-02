---
title:
  page: "Approve or Deny Nemo Clawd Solana Network Requests"
  nav: "Approve Network Requests"
description: "Review and approve blocked Solana, wallet, inference, and messaging network requests in the OpenShell TUI."
keywords: ["nemoclawd approve network requests", "sandbox egress approval tui", "solana rpc policy approval"]
topics: ["generative_ai", "ai_agents", "solana"]
tags: ["nemoclawd", "openshell", "network_policy", "security", "solana"]
content:
  type: how_to
  difficulty: technical_beginner
  audience: ["developer", "engineer", "security_engineer"]
status: published
---

<!--
  SPDX-FileCopyrightText: Copyright (c) 2025-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
  SPDX-License-Identifier: Apache-2.0
-->

# Approve or Deny Nemo Clawd Solana Network Requests

Review and act on network requests that the agent makes to endpoints not listed in the sandbox policy.
OpenShell intercepts these requests and presents them in the TUI for operator approval.
For Solana onboarding, most approvals involve RPC providers, wallet APIs, Telegram, market data, or inference endpoints.

## Prerequisites

- A running Nemo Clawd sandbox.
- The OpenShell CLI on your `PATH`.
- A known Solana cluster, RPC endpoint, and wallet posture.
- A recent `nemoclawd financial-harness <sandbox>` report when approving wallet-aware service traffic.

## Open the TUI

Start the OpenShell terminal UI to monitor sandbox activity:

```console
$ openshell term
```

For a remote sandbox, pass the instance name:

```console
$ ssh my-gpu-box 'cd /home/ubuntu/nemoclawd && . .env && openshell term'
```

The TUI displays the sandbox state, active inference provider, and a live feed of network activity.

## Review Solana Context First

Before approving blockchain service traffic, inspect the current Solana state:

```console
$ nemoclawd solana
$ nemoclawd financial-harness my-assistant
```

The report shows the inferred cluster, redacted RPC URL, wallet posture, applied policy presets, missing policy presets, and signing guardrails.
Use that context to decide whether the blocked host belongs to the setup you intended.

## Trigger a Blocked Request

When the agent attempts to reach an endpoint that is not in the baseline policy, OpenShell blocks the connection and displays the request in the TUI.
The blocked request includes the following details:

- **Host and port** of the destination.
- **Binary** that initiated the request.
- **HTTP method** and path, if available.

For Solana services, compare the request to the endpoint category:

| Endpoint type | Expected examples | Approval posture |
|---|---|---|
| Solana RPC | Your configured RPC host, such as a provider URL or `api.mainnet-beta.solana.com`. | Approve only the exact host and port for the cluster you selected. |
| Wallet API | Privy auth, wallet, or RPC endpoints. | Approve only after wallet setup is intentional and the harness reports the `privy` preset requirement. |
| Telegram | `api.telegram.org`. | Approve only when `TELEGRAM_BOT_TOKEN` is configured and the bridge is expected to run. |
| Market data | Helius, BirdEye, CoinGecko, Jupiter, Pump.fun, or other configured data hosts. | Approve only the service you selected and avoid broad host patterns. |

## Approve or Deny the Request

The TUI presents an approval prompt for each blocked request.

- **Approve** the request to add the endpoint to the running policy for the current session.
- **Deny** the request to keep the endpoint blocked.

Approved endpoints remain in the running policy until the sandbox stops.
They are not persisted to the baseline policy file.

Use `nemoclawd <sandbox> policy-add` for known presets such as `solana-rpc`, `privy`, `telegram`, and `pumpfun` when you want persistent setup behavior.
Use one-off TUI approval only for endpoints you can explain and verify.

## Run the Walkthrough

To observe the approval flow in a guided session, run the walkthrough script:

```console
$ ./scripts/walkthrough.sh
```

This script opens a split tmux session with the TUI on the left and the agent on the right.
The walkthrough requires tmux and the `NVIDIA_API_KEY` environment variable.

## Related Topics

- [Customize the Sandbox Network Policy](customize-network-policy.md) to add endpoints permanently.
- [Network Policies](../reference/network-policies.md) for the full baseline policy reference.
- [Monitor Sandbox Activity](../monitoring/monitor-sandbox-activity.md) for general sandbox monitoring.
- [Financial Harness](../solana/financial-harness.md) for dry-run policy and wallet checks.
