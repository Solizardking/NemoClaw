---
title:
  page: "NVIDIA Nemo Clawd Developer Guide"
  nav: "Nemo Clawd"
description: "Onboard new users to Solana-aware blockchain AI with Nemo Clawd, OpenShell sandboxes, routed inference, wallets, and network policies."
keywords: ["nemoclawd sandboxed ai agent", "solana blockchain ai onboarding", "nemo clawd openshell plugin"]
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

# NVIDIA Nemo Clawd Developer Guide

```{include} ../README.md
:start-after: <!-- start-badges -->
:end-before: <!-- end-badges -->
```

Nemo Clawd is a Solana-aware blockchain AI runtime for [NVIDIA OpenShell](https://github.com/NVIDIA/OpenShell).
It runs the Nemo Clawd agent stack inside a sandboxed environment with routed inference, the Nemo Clawd MCP server, clawd operator services, Solana tooling, wallet-aware dry-run checks, and strict network policies.
The docs start with new-user onboarding and then move into reference material for operators who need deeper control.

## Get Started

Install the CLI, create a sandboxed agent, inspect the Solana configuration, and run the financial harness before wallet-aware services start.

```{raw} html
<style>
.nc-term {
  background: #1a1a2e;
  border-radius: 8px;
  overflow: hidden;
  margin: 1.5em 0;
  box-shadow: 0 4px 16px rgba(0,0,0,0.25);
  font-family: 'SFMono-Regular', Menlo, Monaco, Consolas, 'Liberation Mono', monospace;
  font-size: 0.875em;
  line-height: 1.8;
}
.nc-term-bar {
  background: #252545;
  padding: 10px 14px;
  display: flex;
  gap: 7px;
  align-items: center;
}
.nc-term-dot { width: 12px; height: 12px; border-radius: 50%; }
.nc-term-dot-r { background: #ff5f56; }
.nc-term-dot-y { background: #ffbd2e; }
.nc-term-dot-g { background: #27c93f; }
.nc-term-body { padding: 16px 20px; color: #d4d4d8; }
.nc-term-body .nc-ps { color: #76b900; user-select: none; }
.nc-hl { color: #76b900; font-weight: 600; }
.nc-cursor {
  display: inline-block;
  width: 2px;
  height: 1.1em;
  background: #d4d4d8;
  vertical-align: text-bottom;
  margin-left: 1px;
  animation: nc-blink 1s step-end infinite;
}
@keyframes nc-blink { 50% { opacity: 0; } }
</style>
<div class="nc-term">
  <div class="nc-term-bar">
    <span class="nc-term-dot nc-term-dot-r"></span>
    <span class="nc-term-dot nc-term-dot-y"></span>
    <span class="nc-term-dot nc-term-dot-g"></span>
  </div>
  <div class="nc-term-body">
    <div><span class="nc-ps">$ </span>npm install -g @mawdbotsonsolana/nemoclawd</div>
    <div><span class="nc-ps">$ </span>nemoclawd doctor</div>
    <div><span class="nc-ps">$ </span>nemoclawd launch</div>
    <div><span class="nc-ps">$ </span>nemoclawd financial-harness</div>
  </div>
</div>
```

Run `nemoclawd doctor` to validate your machine, or `nemoclawd --help` to view the full CLI reference.
Use `nemoclawd launch`, `nemoclawd solana`, and `nemoclawd financial-harness` as the first blockchain AI onboarding checkpoints.

Proceed to the [Quickstart](get-started/quickstart.md) for step-by-step setup, or read [Solana and Blockchain AI Onboarding](solana/onboarding.md) first if you are new to Solana wallets, RPC, clusters, and policy controls.

---

## Explore

::::{grid} 2 2 3 3
:gutter: 3

:::{grid-item-card} About Nemo Clawd
:link: about/overview
:link-type: doc

Learn what Nemo Clawd does and how it integrates Nemo Clawd with OpenShell.

+++
{bdg-secondary}`Concept`
:::

:::{grid-item-card} Quickstart
:link: get-started/quickstart
:link-type: doc

Install the CLI, launch your first sandboxed agent, and run Solana safety checks.

+++
{bdg-secondary}`Tutorial`
:::

:::{grid-item-card} Solana Onboarding
:link: solana/onboarding
:link-type: doc

Learn the wallet, RPC, network policy, and blockchain AI concepts needed for a safe first run.

+++
{bdg-secondary}`Get Started`
:::

:::{grid-item-card} Commands
:link: reference/commands
:link-type: doc

CLI commands for launching, connecting, monitoring, wallet setup, and Solana services.

+++
{bdg-secondary}`Reference`
:::

:::{grid-item-card} AI Training
:link: reference/ai-training
:link-type: doc

Source lanes, build checks, model-kit commands, NVIDIA adapters, and generated-data policy.

+++
{bdg-secondary}`Reference`
:::

:::{grid-item-card} Inference Profiles
:link: reference/inference-profiles
:link-type: doc

NVIDIA cloud inference configuration and available models.

+++
{bdg-secondary}`Reference`
:::

:::{grid-item-card} How It Works
:link: about/how-it-works
:link-type: doc

High-level overview of the plugin, blueprint, sandbox, and inference routing.

+++
{bdg-secondary}`Concept`
:::

:::{grid-item-card} Architecture
:link: reference/architecture
:link-type: doc

Plugin structure, blueprint system, and sandbox lifecycle.

+++
{bdg-secondary}`Reference`
:::

:::{grid-item-card} Network Policies
:link: reference/network-policies
:link-type: doc

Egress control, operator approval flow, and policy configuration.

+++
{bdg-secondary}`Reference`
:::

:::{grid-item-card} How-To Guides
:link: inference/switch-inference-providers
:link-type: doc

Task-oriented guides for inference, deployment, and policy management.

+++
{bdg-secondary}`How-To`
:::

:::{grid-item-card} Financial Harness
:link: solana/financial-harness
:link-type: doc

Dry-run Solana wallet, RPC, policy, and signing guardrail preflight.

+++
{bdg-secondary}`How-To`
:::

::::

```{toctree}
:hidden:

Home <self>
```

```{toctree}
:caption: About Nemo Clawd
:hidden:

Overview <about/overview>
How It Works <about/how-it-works>
Release Notes <about/release-notes>
```

```{toctree}
:caption: Get Started
:hidden:

Quickstart <get-started/quickstart>
```

```{toctree}
:caption: Inference
:hidden:

Switch Inference Providers <inference/switch-inference-providers>
```

```{toctree}
:caption: Network Policy
:hidden:

Approve or Deny Network Requests <network-policy/approve-network-requests>
Customize the Network Policy <network-policy/customize-network-policy>
```

```{toctree}
:caption: Solana
:hidden:

Solana and Blockchain AI Onboarding <solana/onboarding>
Financial Harness <solana/financial-harness>
```

```{toctree}
:caption: Deployment
:hidden:

Deploy to a Remote GPU Instance <deployment/deploy-to-remote-gpu>
Set Up the Telegram Bridge <deployment/set-up-telegram-bridge>
```

```{toctree}
:caption: Monitoring
:hidden:

Monitor Sandbox Activity <monitoring/monitor-sandbox-activity>
```

```{toctree}
:caption: Reference
:hidden:

Architecture <reference/architecture>
AI Training <reference/ai-training>
Commands <reference/commands>
Inference Profiles <reference/inference-profiles>
Network Policies <reference/network-policies>
```

```{toctree}
:caption: Resources
:hidden:

resources/license
```
