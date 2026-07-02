---
title:
  page: "Customize the Nemo Clawd Solana Network Policy"
  nav: "Customize Network Policy"
description: "Add, remove, or modify allowed Solana, wallet, messaging, inference, and package endpoints in the sandbox policy."
keywords: ["customize nemoclawd network policy", "sandbox egress policy configuration", "solana rpc policy preset"]
topics: ["generative_ai", "ai_agents", "solana"]
tags: ["nemoclawd", "openshell", "network_policy", "security", "solana"]
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

# Customize the Nemo Clawd Solana Network Policy

Add, remove, or modify the endpoints that the sandbox is allowed to reach.
Nemo Clawd supports both static policy changes that persist across restarts and dynamic updates to a running sandbox.
For Solana onboarding, start with named policy presets and add custom endpoints only when a provider is not covered.

## Prerequisites

- A running Nemo Clawd sandbox for dynamic changes, or the Nemo Clawd source repository for static changes.
- The OpenShell CLI on your `PATH`.
- The Solana cluster, RPC provider, wallet provider, and messaging services you intend to use.

## Use Solana Presets First

List the available presets and apply the ones that match your onboarding choices:

```console
$ nemoclawd my-assistant policy-list
$ nemoclawd my-assistant policy-add
```

Common Solana onboarding presets include:

| Preset | Use it for |
|---|---|
| `solana-rpc` | Solana mainnet, devnet, testnet, Helius, Alchemy, and QuikNode RPC hosts. |
| `privy` | Privy auth, wallet, policy, and transaction-signing APIs. |
| `telegram` | Telegram Bot API access for chat or wallet narration. |
| `pumpfun` | Pump.fun, Jupiter, DexScreener, and related market-data endpoints. |

After applying presets, run the dry-run harness:

```console
$ nemoclawd financial-harness my-assistant
```

The report identifies missing presets and keeps signing and transaction submission disabled while you inspect policy coverage.

## Static Changes

Static changes modify the baseline policy file and take effect after the next sandbox creation or migration.

### Edit the Policy File

Open `nemo-clawd-python/policies/nemoclawd-sandbox.yaml` and add or modify endpoint entries.

Each entry in the `network_policies` section defines an endpoint group with the following fields:

`endpoints`
: Host and port pairs that the sandbox can reach.

`binaries`
: Executables allowed to use this endpoint.

`rules`
: HTTP methods and paths that are permitted.

Prefer exact Solana RPC, wallet, and market-data hosts over broad domains.
Keep API keys in local environment variables and do not encode credentials into policy files.

### Re-Run Setup

Apply the updated policy by re-running the setup path that creates or migrates the sandbox:

```console
$ nemoclawd migrate
```

For a fresh sandbox, re-run the launch flow that created it.
The setup flow picks up the modified policy file and applies it to the sandbox.

### Verify the Policy

Check that the sandbox is running with the updated policy:

```console
$ nemoclawd status
```

## Dynamic Changes

Dynamic changes apply a policy update to a running sandbox without restarting it.

### Create a Policy File

Create a YAML file with the endpoints to add.
Follow the same format as the baseline policy in `nemo-clawd-python/policies/nemoclawd-sandbox.yaml`.

### Apply the Policy

Use the OpenShell CLI to apply the policy update:

```console
$ openshell policy set --policy <policy-file> --wait <sandbox-name>
```

The change takes effect immediately.

### Scope of Dynamic Changes

Dynamic changes apply only to the current session.
When the sandbox stops, the running policy resets to the baseline defined in the policy file.
To make changes permanent, update the static policy file and re-run setup.

## Related Topics

- [Approve or Deny Agent Network Requests](approve-network-requests.md) for real-time operator approval.
- [Network Policies](../reference/network-policies.md) for the full baseline policy reference.
- [Solana and Blockchain AI Onboarding](../solana/onboarding.md) for the first-run policy path.
- [Financial Harness](../solana/financial-harness.md) for dry-run policy and wallet checks.
