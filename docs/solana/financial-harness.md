---
title:
  page: "Nemo Clawd Financial Harness - Dry-Run Solana Wallet and Signing Guardrails"
  nav: "Financial Harness"
description: "Use the dry-run financial harness to inspect Solana RPC, wallet metadata, network policy coverage, and signing guardrails before enabling wallet-aware services."
keywords: ["nemoclawd financial harness", "solana wallet guardrails", "blockchain ai safety preflight"]
topics: ["generative_ai", "ai_agents", "solana"]
tags: ["nemoclawd", "openshell", "solana", "wallets", "network_policy", "guardrails"]
content:
  type: how_to
  difficulty: intermediate
  audience: ["developer", "engineer", "security_engineer"]
status: published
---

<!--
  SPDX-FileCopyrightText: Copyright (c) 2025-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
  SPDX-License-Identifier: Apache-2.0
-->

# Nemo Clawd Financial Harness - Dry-Run Solana Wallet and Signing Guardrails

The financial harness is the first safe checkpoint for Solana-oriented Nemo Clawd development.
It reports the active RPC endpoint, inferred cluster, wallet metadata, applied policy presets, missing policy presets, and signing guardrails before wallet-aware runtime services start.

The harness is intentionally dry-run only.
It does not create wallets, store private keys, sign transactions, submit orders, or provide trading advice.

The repository installer seeds a matching runtime profile under `~/.nemoclawd/`.
When `solana-keygen` is available, it creates an unfunded local keypair in `~/.nemoclawd/wallets/` with file mode `600`, registers that wallet as `local-keypair`, writes `agent.json` for the lobster-themed Clawd deck, and writes `trading-box.json` with dry-run guardrails.
The private keypair remains on the host and is not copied into the sandbox.

Use it whenever you change RPC configuration, wallet configuration, policy presets, or service mode.
For new users, run the [Solana and Blockchain AI Onboarding](onboarding.md) path first.

## Run the Harness

Run it before creating a sandbox, after onboarding, or against a specific sandbox.

```console
$ nemoclawd financial-harness
$ nemoclawd financial-harness my-assistant
$ nemoclawd my-assistant financial-harness
```

Use JSON output for automation:

```console
$ nemoclawd financial-harness my-assistant --json
```

## What It Checks

The report covers the areas that determine whether a blockchain AI runtime is still in a safe onboarding posture:

| Area | What the harness reports |
|---|---|
| RPC | Redacted RPC URL and inferred network, such as `mainnet`, `devnet`, `testnet`, or `local-validator`. |
| Wallet | Whether a developer wallet is configured through Privy, an installer-created `local-keypair`, environment variables, or local config metadata. |
| Policy | Applied, required, and missing policy presets. Remote RPC use requires `solana-rpc`; Privy wallet use requires `privy`. |
| Guardrails | Signing disabled, transaction submission disabled, live-trading env gate, default spend limit, and private-key storage policy. |
| Mechanism | Observe, orient, propose, approve, execute, and settle stages for the future financial loop. |
| Blockers | Explicit reasons live execution must remain disabled. |

## How to Read the Report

Start with the cluster and RPC fields.
They tell you whether the agent is looking at mainnet, devnet, testnet, or a local validator.

Then check wallet posture.
For a first run, no wallet or a low-balance development wallet is acceptable.
For wallet-aware services, confirm that the reported wallet identity matches the one you intended to use.

Finally, review blockers and missing policy presets.
Do not start runtime services until each blocker is either resolved or intentionally accepted for your development stage.

## Dry-Run Mechanism

The harness describes the intended trading-control sequence without executing it:

1. Observe Solana RPC, wallet balance, and token/account state.
2. Orient around cluster, policy coverage, wallet readiness, and risk limits.
3. Propose a trade intent for operator review.
4. Require explicit approval before any signing path.
5. Keep execution disabled in the harness.
6. Verify chain state after any future confirmation path and write an audit record.

Live execution remains blocked because the harness itself does not implement signing or transaction submission.
Future live adapters must keep signing outside the sandbox filesystem and enforce wallet policy gates.

## Typical Onboarding Flow

1. Run `nemoclawd doctor` to check the host.
2. Run `nemoclawd onboard` or `nemoclawd launch` to create the OpenShell sandbox.
3. Run `nemoclawd wallet create` if you need a Privy-backed Solana wallet.
4. Apply missing network policy presets with `nemoclawd <sandbox> policy-add`.
5. Run `nemoclawd financial-harness <sandbox>` and resolve all reported blockers that apply to your development stage.
6. Start runtime services with `nemoclawd solana start <sandbox>` only after the harness output matches the intended operator posture.

## Related Pages

- [Solana and Blockchain AI Onboarding](onboarding.md) for the beginner path and core concepts.
- [Commands](../reference/commands.md) for CLI syntax.
- [How It Works](../about/how-it-works.md) for the financial runtime loop.
- [Network Policies](../reference/network-policies.md) for egress control.
