---
title:
  page: "Nemo Clawd Architecture — Plugin, Blueprint, and Sandbox Structure"
  nav: "Architecture"
description: "Plugin structure, blueprint lifecycle, sandbox environment, and inference routing."
keywords: ["nemoclawd architecture", "nemoclawd plugin blueprint structure"]
topics: ["generative_ai", "ai_agents"]
tags: ["nemoclawd", "openshell", "sandboxing", "blueprints", "inference_routing"]
content:
  type: reference
  difficulty: intermediate
  audience: ["developer", "engineer"]
status: published
---

<!--
  SPDX-FileCopyrightText: Copyright (c) 2025-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
  SPDX-License-Identifier: Apache-2.0
-->

# Architecture

Nemo Clawd has three main components: a TypeScript plugin that integrates with the Nemo Clawd CLI, a Hermes-derived agent image with bundled MCP tooling, and a Python blueprint that orchestrates OpenShell resources.

## Nemo Clawd Plugin

The plugin is a thin TypeScript package that registers commands under `nemoclawd`.
It runs in-process with the Nemo Clawd gateway and handles user-facing CLI interactions.
Root `npm run build` writes local plugin artifacts under `dist/nemoclawd-plugin` so the imported `dist` runtime remains available for `nemoclawd dist ...` and fallback commands.

```text
nemoclawd/
├── src/
│   ├── index.ts                    Plugin entry — registers all commands
│   ├── cli.ts                      Commander.js subcommand wiring
│   ├── commands/
│   │   ├── launch.ts               Fresh install into OpenShell
│   │   ├── connect.ts              Interactive shell into sandbox
│   │   ├── status.ts               Blueprint run state + sandbox health
│   │   ├── logs.ts                 Stream blueprint and sandbox logs
│   │   └── slash.ts                /nemoclawd chat command handler
│   └── blueprint/
│       ├── resolve.ts              Version resolution, cache management
│       ├── fetch.ts                Download blueprint from OCI registry
│       ├── verify.ts               Digest verification, compatibility checks
│       ├── exec.ts                 Subprocess execution of blueprint runner
│       └── state.ts                Persistent state (run IDs)
├── nemoclawd.plugin.json            Plugin manifest
└── package.json                    Published CLI package metadata
```

## Nemo Clawd Agent Image

The first-class `nemo-clawd` agent image derives from the Hermes sandbox image.
It keeps the Hermes runtime contract while layering the Nemo Clawd MCP server, the Python blueprint, and the agent manifest used by OpenShell.

```text
agents/nemo-clawd/
├── Dockerfile                    Hermes-derived image definition
├── manifest.yaml                 Agent contract, ports, MCP server, state paths
├── policy-additions.yaml         MCP-specific egress additions
└── start-mcp.sh                  Stdio MCP launcher

nemo-clawd-mcp/
├── src/index.ts                  Stdio MCP server and 31 tool definitions
└── src/http.ts                   Separate Streamable HTTP transport entry point
```

The sandbox contract starts the bundled MCP server through `/usr/local/bin/nemo-clawd-mcp` over stdio.
Remote HTTP MCP deployments use the package HTTP entry point separately.
The image also bundles `/agents/clawd-operator` at `/opt/clawd-operator`.
It exposes `/usr/local/bin/clawd-operator`, which starts `ralph_orchestrator` with `/opt/clawd-operator/ralph.yml` or `/opt/clawd-operator/ralph.codex-acp.yml`.
Operator skills live in `/opt/clawd-operator/skills`, and the clawd agent files live in `/opt/clawd-operator/clawd-agent`.
The Docker build and npm package include `.env.example` files for configuration shape and intentionally exclude real `.env` and `.env.local` files.

## Nemo Clawd Blueprint

The blueprint is a versioned Python artifact with its own release stream.
The plugin resolves, verifies, and executes the blueprint as a subprocess.
The blueprint drives all interactions with the OpenShell CLI.

```text
nemo-clawd-python/
├── blueprint.yaml                  Manifest — version, profiles, compatibility
├── orchestrator/
│   └── runner.py                   CLI runner — plan / apply / status
├── policies/
│   └── nemoclawd-sandbox.yaml       Strict baseline network + filesystem policy
```

### Blueprint Lifecycle

```{mermaid}
flowchart LR
    A[resolve] --> B[verify digest]
    B --> C[plan]
    C --> D[apply]
    D --> E[status]
```

1. Resolve. The plugin locates the blueprint artifact and checks the version against `min_openshell_version` and `min_nemoclawd_version` constraints in `blueprint.yaml`.
2. Verify. The plugin checks the artifact digest against the expected value.
3. Plan. The runner determines what OpenShell resources to create or update, such as the gateway, providers, sandbox, inference route, and policy.
4. Apply. The runner executes the plan by calling `openshell` CLI commands.
5. Status. The runner reports current state.

## Sandbox Environment

The sandbox runs the `ghcr.io/nvidia/nemoclaw/nemo-clawd:latest` container image.
The blueprint creates the sandbox with the Docker-safe name `nemoclawd` and forwards ports `18789` and `8642`.

Inside the sandbox:

- Hermes runs at `/usr/local/bin/hermes`.
- The bundled Nemo Clawd MCP server runs at `/usr/local/bin/nemo-clawd-mcp`.
- The bundled clawd operator runs at `/usr/local/bin/clawd-operator`.
- The Python blueprint is available under `/opt/nemo-clawd-python`.
- The clawd operator bundle is available under `/opt/clawd-operator`, including its configs, skills, and agent files.
- Inference calls are routed through OpenShell to the configured provider.
- Network egress is restricted by the baseline policy in `nemoclawd-sandbox.yaml`.
- Filesystem access is confined to `/sandbox` and `/tmp` for read-write access, with system paths read-only.

## Inference Routing

Inference requests from the agent never leave the sandbox directly.
OpenShell intercepts them and routes to the configured provider:

```text
Agent (sandbox)  ──▶  OpenShell gateway  ──▶  NVIDIA cloud (build.nvidia.com)
```

Refer to [Inference Profiles](../reference/inference-profiles.md) for provider configuration details.
