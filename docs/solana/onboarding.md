---
title:
  page: "Solana and Blockchain AI Onboarding with Nemo Clawd"
  nav: "Solana Onboarding"
description: "Learn the Solana, wallet, RPC, policy, and blockchain AI concepts needed to start Nemo Clawd safely."
keywords: ["solana onboarding", "blockchain ai onboarding", "nemoclawd solana guide"]
topics: ["generative_ai", "ai_agents", "solana"]
tags: ["nemoclawd", "solana", "blockchain_ai", "wallets", "network_policy", "guardrails"]
content:
  type: get_started
  difficulty: technical_beginner
  audience: ["developer", "engineer", "operator"]
status: published
---

<!--
  SPDX-FileCopyrightText: Copyright (c) 2025-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
  SPDX-License-Identifier: Apache-2.0
-->

# Solana and Blockchain AI Onboarding with Nemo Clawd

This page explains the Solana and blockchain AI concepts you need before you run Nemo Clawd with wallet-aware services.
It is written for users who are comfortable with a terminal but new to operating an AI agent around blockchain data, wallets, and policy-bounded automation.

:::{warning}
Do not treat an AI agent as a substitute for wallet custody, security review, or financial judgment.
Start with read-only data, dry-run reports, devnet, a local validator, or low-balance wallets.
:::

## Mental Model

Nemo Clawd gives a blockchain AI agent a controlled place to work.
The agent can read Solana data, call approved tools, use configured inference, and report what it sees.
The sandbox and policy layers decide which network endpoints, files, credentials, and runtime services are available.

| Concept | What it means in Nemo Clawd |
|---|---|
| Solana cluster | The chain environment the agent reads from, such as mainnet, devnet, testnet, or a local validator. |
| RPC endpoint | The URL used to read chain state and submit requests to a Solana node or RPC provider. |
| Wallet | The identity that can hold SOL and tokens, usually managed through Privy for Nemo Clawd. |
| Signing | The action that authorizes a transaction from a wallet. |
| Network policy | The allowlist that decides which hosts the sandbox can reach. |
| Financial harness | The dry-run checkpoint that reports RPC, wallet, policy, and signing guardrail state. |
| Vault | The append-only local trail of service sessions, heartbeat snapshots, and wallet activity records. |

## What Nemo Clawd Does

Nemo Clawd can help you run a sandboxed Solana operator loop.
The loop can inspect RPC configuration, check wallet metadata, monitor activity, narrate events, and start bundled services such as the Solana bridge, Telegram bot, and websocket relay.

Nemo Clawd does not make unrestricted financial decisions for you.
The default onboarding path keeps dangerous actions behind explicit setup, policy, and guardrail checks.
The financial harness remains dry-run only.

## First Run Journey

Use this sequence for a first-time setup:

| Stage | Command | Outcome |
|---|---|---|
| Install | `npm install -g @mawdbotsonsolana/nemoclawd` | Adds the `nemoclawd` CLI to your machine. |
| Diagnose | `nemoclawd doctor` | Checks Docker, OpenShell, Node.js, npm, RPC, wallet, Telegram, and Helius readiness. |
| Create sandbox | `nemoclawd launch` | Runs onboarding when needed and starts the best available local stack. |
| Inspect Solana | `nemoclawd solana` | Shows the active sandbox, RPC, wallet status, and next commands. |
| Dry-run safety | `nemoclawd financial-harness` | Reports RPC, wallet, policy, and signing guardrails without executing transactions. |
| Add wallet | `nemoclawd wallet create` | Creates a managed Solana wallet when you are ready for wallet-aware services. |
| Start services | `nemoclawd solana start <sandbox>` | Starts the Solana bridge, bot, relay, heartbeat, and vault logging for a sandbox. |

## Choose a Solana Network

Use the safest network that matches your learning goal.
Mainnet is appropriate only when you understand the wallet, funding, and policy posture.

| Network | Use it when | Risk posture |
|---|---|---|
| Local validator | You want to learn commands without public-chain state. | Lowest operational risk. |
| Devnet | You want public Solana behavior without mainnet funds. | Good for onboarding and tests. |
| Testnet | You need validator or protocol testing behavior. | Specialized testing path. |
| Mainnet | You need real market or wallet data. | Requires strict wallet and policy controls. |

## Configure RPC Carefully

The RPC endpoint controls what chain state the agent sees.
Use a provider and cluster that match your goal.

Keep RPC credentials out of documentation, screenshots, and chat transcripts.
The financial harness redacts common credential query parameters when it prints RPC URLs.

Run the harness after changing RPC configuration:

```console
$ nemoclawd financial-harness my-assistant
```

## Use Wallets Conservatively

Use `nemoclawd wallet create` when you need a Privy-backed wallet for the agent.
This keeps private keys out of the sandbox filesystem.

```console
$ nemoclawd wallet create
$ nemoclawd wallet status
```

For early onboarding, keep wallet balances small or use a non-mainnet network.
If a service needs a funded wallet, confirm that the minimum balance, stop balance, and operator approval expectations match your risk tolerance.

## Understand the Policy Boundary

The sandbox starts from a strict baseline policy.
Solana RPC, Privy, Telegram, Helius, market data, and trading-adjacent services must be explicitly allowed by policy presets or static policy entries.

Use the policy commands after the harness reports missing presets:

```console
$ nemoclawd my-assistant policy-list
$ nemoclawd my-assistant policy-add
```

Open the TUI to review blocked network requests:

```console
$ openshell term
```

Approve only the host, port, method, and path that match your intended service.

## Read the Agent Loop

The blockchain AI loop is easiest to understand as a series of checkpoints:

1. Observe chain, wallet, market, and service state.
2. Orient around cluster, policy, balance, and risk limits.
3. Propose an action or explanation.
4. Require approval before any signing path.
5. Execute only through configured wallet and policy controls.
6. Record heartbeat and activity in the vault.

The financial harness covers the first four checkpoints in dry-run form.
Runtime services add monitoring, narration, and audit records after you intentionally start them.

## Verify the Setup

Run these commands after onboarding:

```console
$ nemoclawd status
$ nemoclawd solana
$ nemoclawd financial-harness my-assistant
```

The setup is ready for the next stage when the harness shows the expected cluster, wallet posture, policy presets, and guardrails.
If the report shows blockers, resolve them before starting runtime services.

## Next Steps

- Follow the [Quickstart](../get-started/quickstart.md) for the install and first sandbox path.
- Run the [Financial Harness](financial-harness.md) before enabling Solana runtime services.
- Review [Network Policies](../reference/network-policies.md) before approving blockchain service endpoints.
- Use the [Command Reference](../reference/commands.md) for wallet, Solana, and sandbox commands.
