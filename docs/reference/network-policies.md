---
title:
  page: "Nemo Clawd Network Policies — Baseline Rules and Operator Approval"
  nav: "Network Policies"
description: "Baseline network policy, filesystem rules, and operator approval flow."
keywords: ["nemoclawd network policy", "sandbox egress control operator approval"]
topics: ["generative_ai", "ai_agents"]
tags: ["nemoclawd", "openshell", "sandboxing", "network_policy", "security"]
content:
  type: reference
  difficulty: intermediate
  audience: ["developer", "engineer", "security_engineer"]
status: published
---

<!--
  SPDX-FileCopyrightText: Copyright (c) 2025-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
  SPDX-License-Identifier: Apache-2.0
-->

# Network Policies

Nemo Clawd runs with a strict-by-default network policy.
The sandbox can only reach endpoints that are explicitly allowed.
Any request to an unlisted destination is intercepted by OpenShell, and the operator is prompted to approve or deny it in real time through the TUI.

## Baseline Policy

The baseline policy is defined in `nemo-clawd-python/policies/nemoclawd-sandbox.yaml`.

### Filesystem

| Path | Access |
|---|---|
| `/sandbox`, `/tmp`, `/dev/null` | Read-write |
| `/usr`, `/lib`, `/proc`, `/dev/urandom`, `/app`, `/etc`, `/var/log` | Read-only |

The sandbox process runs as a dedicated `sandbox` user and group.
Landlock LSM enforcement applies on a best-effort basis.

### Network Policies

The following endpoint groups are allowed by default:

:::{list-table}
:header-rows: 1
:widths: 20 30 20 30

* - Policy
  - Endpoints
  - Binaries
  - Rules

* - `claude_code`
  - `api.anthropic.com:443`, `statsig.anthropic.com:443`, `sentry.io:443`
  - `/usr/local/bin/claude`
  - All methods

* - `nvidia`
  - `integrate.api.nvidia.com:443`, `inference-api.nvidia.com:443`
  - `/usr/local/bin/claude`, `/usr/local/bin/nemoclawd`, `/usr/local/bin/nemo-clawd-mcp`
  - All methods

* - `github`
  - `github.com:443`, `api.github.com:443`
  - `/usr/bin/gh`, `/usr/bin/git`
  - All methods, all paths

* - `clawdhub`
  - `clawdhub.com:443`
  - `/usr/local/bin/nemoclawd`
  - GET, POST

* - `nemoclawd_api`
  - `nemo-clawd.ai:443`
  - `/usr/local/bin/nemoclawd`
  - GET, POST

* - `nemoclawd_docs`
  - `docs.nemo-clawd.ai:443`
  - `/usr/local/bin/nemoclawd`
  - GET only

* - `npm_registry`
  - `registry.npmjs.org:443`
  - `/usr/local/bin/nemoclawd`, `/usr/local/bin/npm`
  - Registry access

* - `xai_grok`
  - `api.x.ai:443`
  - `/usr/local/bin/nemo-clawd-mcp`, `/usr/bin/node`
  - POST on `/v1/chat/completions` and `/v1/images/generations`

* - `helius_rpc`
  - `mainnet.helius-rpc.com:443`
  - `/usr/local/bin/nemo-clawd-mcp`, `/usr/bin/node`
  - GET, POST

* - `birdeye_market_data`
  - `api.birdeye.so:443`
  - `/usr/local/bin/nemo-clawd-mcp`, `/usr/bin/node`
  - GET only

* - `coingecko_market_data`
  - `api.coingecko.com:443`
  - `/usr/local/bin/nemo-clawd-mcp`, `/usr/bin/node`
  - GET only

* - `telegram`
  - `api.telegram.org:443`
  - Any binary
  - GET, POST on `/bot*/**`

* - `ollama`
  - `host.openshell.internal:11434`
  - `/usr/local/bin/nemoclawd`, `/usr/local/bin/nemo-clawd-mcp`, `/usr/bin/curl`
  - All methods

:::

Port `443` endpoints use TLS termination.
Local inference egress uses the explicit host alias and port listed in the policy.

### Inference

The active model route lives in OpenShell inference configuration.
The baseline policy limits direct sandbox egress by executable path so bundled MCP tools can reach only the listed xAI, Helius, BirdEye, CoinGecko, and Telegram endpoints.

## Operator Approval Flow

When the agent attempts to reach an endpoint not listed in the policy, OpenShell intercepts the request and presents it in the TUI for operator review:

1. The agent makes a network request to an unlisted host.
2. OpenShell blocks the connection and logs the attempt.
3. The TUI command `openshell term` displays the blocked request with host, port, and requesting binary.
4. The operator approves or denies the request.
5. If approved, the endpoint is added to the running policy for the session.

To try this, run the walkthrough:

```console
$ ./scripts/walkthrough.sh
```

This opens a split tmux session with the TUI on the left and the agent on the right.

## Modifying the Policy

### Static Changes

Edit `nemo-clawd-python/policies/nemoclawd-sandbox.yaml` and re-run the setup path that creates or migrates the sandbox:

```console
$ nemoclawd migrate
```

### Dynamic Changes

Apply policy updates to a running sandbox without restarting:

```console
$ openshell policy set --policy <policy-file> --wait <sandbox-name>
```
