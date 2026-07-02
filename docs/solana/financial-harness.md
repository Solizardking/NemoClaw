---
title:
  page: "Nemo Clawd Financial Harness — Dry-Run Solana Wallet and Trading Guardrails"
  nav: "Financial Harness"
description: "Use the dry-run financial harness to inspect Solana RPC, wallet metadata, network policy coverage, and trading guardrails before enabling live signing work."
keywords: ["nemoclawd financial harness", "solana wallet guardrails", "openshell trading preflight"]
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

# Financial Harness

The financial harness is the first safe checkpoint for Solana-oriented Nemo Clawd development.
It reports the active RPC endpoint, inferred cluster, wallet metadata, applied policy presets, missing policy presets, and the trading mechanism guardrails that must be satisfied before any future live signing adapter is considered.

The harness is intentionally dry-run only.
It does not create wallets, store private keys, sign transactions, submit orders, or provide trading advice.

## Run the Harness

Run it before creating a sandbox, after onboarding, or against a specific sandbox:

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

The report covers:

| Area | What the harness reports |
|---|---|
| RPC | Redacted RPC URL and inferred network, such as `mainnet`, `devnet`, `testnet`, or `local-validator`. |
| Wallet | Whether a developer wallet is configured through Privy, environment variables, or local config metadata. |
| Policy | Applied, required, and missing policy presets. Remote RPC use requires `solana-rpc`; Privy wallet use requires `privy`. |
| Guardrails | Signing disabled, transaction submission disabled, live-trading env gate, default spend limit, and private-key storage policy. |
| Mechanism | Observe, orient, propose, approve, execute, and settle stages for the future financial loop. |
| Blockers | Explicit reasons live execution must remain disabled. |

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

- [Commands](../reference/commands.md) for CLI syntax.
- [How It Works](../about/how-it-works.md) for the financial runtime loop.
- [Network Policies](../reference/network-policies.md) for egress control.
