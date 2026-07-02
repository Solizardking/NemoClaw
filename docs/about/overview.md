---
title:
  page: "Nemo Clawd Overview - Solana Blockchain AI in a Sandbox"
  nav: "Overview"
description: "Nemo Clawd runs Solana-aware blockchain AI agents inside OpenShell sandboxes with inference routing and declarative policy."
keywords: ["nemoclawd overview", "solana blockchain ai agent", "nemo clawd openshell sandbox plugin"]
topics: ["generative_ai", "ai_agents", "solana"]
tags: ["nemoclawd", "openshell", "sandboxing", "inference_routing", "blueprints", "solana", "wallets"]
content:
  type: concept
  difficulty: technical_beginner
  audience: ["developer", "engineer"]
status: published
---

<!--
  SPDX-FileCopyrightText: Copyright (c) 2025-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
  SPDX-License-Identifier: Apache-2.0
-->

# Nemo Clawd Overview - Solana Blockchain AI in a Sandbox

Nemo Clawd is a Solana-oriented blockchain AI runtime for running Nemo Clawd inside [NVIDIA OpenShell](https://github.com/NVIDIA/OpenShell) sandboxes.
It gives new users a path from host setup to Solana RPC checks, wallet posture checks, dry-run guardrails, and policy-bounded runtime services.

The goal is controlled agent operation, not unchecked autonomy.
Every network request, filesystem path, inference call, wallet-aware service, and runtime integration is constrained by the sandbox and its declarative policy.

| Capability              | Description                                                                                                                                          |
|-------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------|
| Sandbox Nemo Clawd      | Creates an OpenShell sandbox pre-configured for Nemo Clawd, with strict filesystem and network policies applied from the first boot.                  |
| Onboard Solana users    | Guides users through host diagnostics, Solana RPC checks, wallet setup, policy presets, and dry-run financial guardrails.                            |
| Route inference         | Configures OpenShell inference routing so agent traffic flows through the selected provider instead of direct sandbox egress.                         |
| Run operator services   | Starts optional Solana bridge, Telegram bot, websocket relay, heartbeat, and vault logging services when the operator is ready.                       |
| Manage the lifecycle    | Handles blueprint versioning, digest verification, sandbox setup, status checks, and service commands.                                               |

## Challenge

Blockchain AI agents can read live market data, interact with wallets, call inference providers, and reach external APIs.
Without guardrails, this creates security, cost, wallet, and compliance risks that grow as agents run unattended.

New Solana users also need a clear path through unfamiliar concepts such as RPC endpoints, clusters, wallet custody, signing, network policy, and audit trails.
Nemo Clawd makes those checkpoints explicit before runtime services start.

## Benefits

Nemo Clawd provides the following benefits:

| Benefit                    | Description                                                                                                            |
|----------------------------|------------------------------------------------------------------------------------------------------------------------|
| Sandboxed execution        | Every agent runs inside an OpenShell sandbox with Landlock, seccomp, and network namespace isolation. No access is granted by default. |
| Solana onboarding path     | The CLI walks users from `doctor` to `launch`, `solana`, `financial-harness`, wallet setup, and optional runtime services. |
| Dry-run financial checks   | The financial harness reports RPC, wallet, policy, and signing guardrails without creating wallets or submitting transactions. |
| Routed inference           | Agent traffic routes through the configured OpenShell inference provider, transparent to the agent.                    |
| Declarative network policy | Egress rules are defined in YAML. Unknown hosts are blocked and surfaced to the operator for approval.                 |
| Single CLI                 | The `nemoclawd` command orchestrates the full stack: gateway, sandbox, inference provider, and network policy.           |
| Blueprint lifecycle        | Versioned blueprints handle sandbox creation, digest verification, and reproducible setup.                             |

## Use Cases

You can use Nemo Clawd for various use cases including the following.

| Use Case                  | Description                                                                                  |
|---------------------------|----------------------------------------------------------------------------------------------|
| Solana learning path      | Learn RPC, wallets, clusters, policy presets, and dry-run guardrails with a guided CLI flow. |
| Blockchain AI operator    | Run a Nemo Clawd assistant with controlled network access, wallet-aware services, and operator-approved egress. |
| Sandboxed testing         | Test agent behavior in a locked-down environment before granting broader permissions.        |
| Remote GPU deployment     | Deploy a sandboxed agent to a remote GPU instance for persistent operation.                  |

## Next Steps

Explore the following pages to learn more about Nemo Clawd.

- [Solana and Blockchain AI Onboarding](../solana/onboarding.md) to learn the concepts and first-run path.
- [How It Works](../about/how-it-works.md) to understand the key concepts behind Nemo Clawd.
- [Quickstart](../get-started/quickstart.md) to install Nemo Clawd and run your first agent.
- [Financial Harness](../solana/financial-harness.md) to verify RPC, wallet, policy, and guardrail state.
- [Switch Inference Providers](../inference/switch-inference-providers.md) to configure the inference provider.
- [Approve or Deny Network Requests](../network-policy/approve-network-requests.md) to manage egress approvals.
- [Deploy to a Remote GPU Instance](../deployment/deploy-to-remote-gpu.md) for persistent operation.
- [Monitor Sandbox Activity](../monitoring/monitor-sandbox-activity.md) to observe agent behavior.
