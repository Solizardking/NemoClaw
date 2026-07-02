---
title:
  page: "Nemo Clawd Overview — What It Does and How It Fits Together"
  nav: "Overview"
description: "Nemo Clawd sandboxes Nemo Clawd with NVIDIA inference and declarative policy."
keywords: ["nemoclawd overview", "nemo clawd openshell sandbox plugin"]
topics: ["generative_ai", "ai_agents"]
tags: ["nemoclawd", "openshell", "sandboxing", "inference_routing", "blueprints"]
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

# Overview

Nemo Clawd is the [Nemo Clawd](https://nemo-clawd.ai) plugin for [NVIDIA OpenShell](https://github.com/NVIDIA/OpenShell).
It moves Nemo Clawd into a sandboxed environment where every network request, file access, and inference call is governed by declarative policy.

| Capability              | Description                                                                                                                                          |
|-------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------|
| Sandbox Nemo Clawd        | Creates an OpenShell sandbox pre-configured for Nemo Clawd, with strict filesystem and network policies applied from the first boot.                   |
| Route inference         | Configures OpenShell inference routing so agent traffic flows through cloud-hosted Nemotron 3 Super 120B via [build.nvidia.com](https://build.nvidia.com). |
| Manage the lifecycle    | Handles blueprint versioning, digest verification, and sandbox setup.                                                                                |

## Challenge

Autonomous AI agents like Nemo Clawd can make arbitrary network requests, access the host filesystem, and call any inference endpoint. Without guardrails, this creates security, cost, and compliance risks that grow as agents run unattended.

## Benefits

Nemo Clawd provides the following benefits.

| Benefit                    | Description                                                                                                            |
|----------------------------|------------------------------------------------------------------------------------------------------------------------|
| Sandboxed execution        | Every agent runs inside an OpenShell sandbox with Landlock, seccomp, and network namespace isolation. No access is granted by default. |
| NVIDIA cloud inference     | Agent traffic routes through cloud-hosted Nemotron 3 Super 120B via [build.nvidia.com](https://build.nvidia.com), transparent to the agent.          |
| Declarative network policy | Egress rules are defined in YAML. Unknown hosts are blocked and surfaced to the operator for approval.                 |
| Single CLI                 | The `nemoclawd` command orchestrates the full stack: gateway, sandbox, inference provider, and network policy.           |
| Blueprint lifecycle        | Versioned blueprints handle sandbox creation, digest verification, and reproducible setup.                             |

## Use Cases

You can use Nemo Clawd for various use cases including the following.

| Use Case                  | Description                                                                                  |
|---------------------------|----------------------------------------------------------------------------------------------|
| Always-on assistant       | Run an Nemo Clawd assistant with controlled network access and operator-approved egress.        |
| Sandboxed testing         | Test agent behavior in a locked-down environment before granting broader permissions.         |
| Remote GPU deployment     | Deploy a sandboxed agent to a remote GPU instance for persistent operation.                   |

## Next Steps

Explore the following pages to learn more about Nemo Clawd.

- [How It Works](../about/how-it-works.md) to understand the key concepts behind Nemo Clawd.
- [Quickstart](../get-started/quickstart.md) to install Nemo Clawd and run your first agent.
- [Switch Inference Providers](../inference/switch-inference-providers.md) to configure the inference provider.
- [Approve or Deny Network Requests](../network-policy/approve-network-requests.md) to manage egress approvals.
- [Deploy to a Remote GPU Instance](../deployment/deploy-to-remote-gpu.md) for persistent operation.
- [Monitor Sandbox Activity](../monitoring/monitor-sandbox-activity.md) to observe agent behavior.