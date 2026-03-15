---
title:
  page: NVIDIA NemoClaw Developer Guide
  nav: Get Started
  card: NVIDIA NemoClaw
description: NemoClaw is the OpenClaw plugin for OpenShell. Run OpenClaw inside sandboxed environments with NVIDIA inference routing, strict network policies, and one-command setup.
topics:
- Generative AI
- AI Agents
tags:
- OpenClaw
- OpenShell
- Sandboxing
- Inference Routing
- NemoClaw
content:
  type: index
---

<!--
  SPDX-FileCopyrightText: Copyright (c) 2025-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
  SPDX-License-Identifier: Apache-2.0
-->

# NVIDIA NemoClaw

[![GitHub](https://img.shields.io/badge/github-repo-green?logo=github)](https://github.com/NVIDIA/openshell-openclaw-plugin)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue)](https://github.com/NVIDIA/openshell-openclaw-plugin/blob/main/LICENSE)

NemoClaw is the OpenClaw plugin for [NVIDIA OpenShell](https://github.com/NVIDIA/OpenShell).
It runs OpenClaw inside a sandboxed environment with NVIDIA inference
(Nemotron 3 Super 120B via [build.nvidia.com](https://build.nvidia.com), or local vLLM),
strict network policies, and operator-controlled egress approval.

## Get Started

Install the CLI and launch a sandboxed OpenClaw instance in a few commands.

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
    <div><span class="nc-ps">$ </span>npm install -g nemoclaw</div>
    <div><span class="nc-ps">$ </span>nemoclaw setup</div>
    <div><span class="nc-ps">$ </span>nemoclaw connect<span class="nc-cursor"></span></div>
  </div>
</div>
```

Run `nemoclaw --help` in your terminal to see the full CLI reference. You can also clone the [NemoClaw repository](https://github.com/NVIDIA/openshell-openclaw-plugin) to explore the plugin source and blueprint.

Proceed to the [Quickstart](get-started/quickstart.md) for step-by-step instructions.

---

## Explore

::::{grid} 2 2 3 3
:gutter: 3

:::{grid-item-card} About NemoClaw
:link: about/overview
:link-type: doc

Learn what NemoClaw does and how it integrates OpenClaw with OpenShell.

+++
{bdg-secondary}`Concept`
:::

:::{grid-item-card} Quickstart
:link: get-started/quickstart
:link-type: doc

Install the CLI, configure inference, and launch your first sandboxed agent.

+++
{bdg-secondary}`Tutorial`
:::

:::{grid-item-card} Commands
:link: reference/commands
:link-type: doc

CLI commands for launching, connecting, monitoring, and managing sandboxes.

+++
{bdg-secondary}`Reference`
:::

:::{grid-item-card} Inference Profiles
:link: reference/inference-profiles
:link-type: doc

Switch between NVIDIA cloud, local NIM, and vLLM inference backends.

+++
{bdg-secondary}`Reference`
:::

:::{grid-item-card} Architecture
:link: about/architecture
:link-type: doc

Plugin structure, blueprint system, and sandbox lifecycle.

+++
{bdg-secondary}`Concept`
:::

:::{grid-item-card} Network Policies
:link: reference/network-policies
:link-type: doc

Egress control, operator approval flow, and policy configuration.

+++
{bdg-secondary}`Reference`
:::

::::

```{toctree}
:hidden:

Home <self>
```

```{toctree}
:caption: About NemoClaw
:hidden:

Overview <about/overview>
Architecture <about/architecture>
Release Notes <about/release-notes>
```

```{toctree}
:caption: Get Started
:hidden:

Quickstart <get-started/quickstart>
```

```{toctree}
:caption: Reference
:hidden:

Commands <reference/commands>
Inference Profiles <reference/inference-profiles>
Network Policies <reference/network-policies>
```

```{toctree}
:caption: Resources
:hidden:

resources/license
```
