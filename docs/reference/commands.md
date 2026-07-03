---
title:
  page: "Nemo Clawd CLI Commands Reference"
  nav: "Commands"
description: "Full CLI reference for plugin and standalone Nemo Clawd commands, including Solana onboarding, wallet checks, policy presets, and runtime services."
keywords: ["nemoclawd cli commands", "nemoclawd command reference", "solana onboarding cli", "privy wallet"]
topics: ["generative_ai", "ai_agents", "solana"]
tags: ["nemoclawd", "openshell", "nemoclawd", "cli", "solana", "pump-fun", "privy"]
content:
  type: reference
  difficulty: technical_beginner
  audience: ["developer", "engineer"]
status: published
---

<!--
  SPDX-FileCopyrightText: Copyright (c) 2025-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
  SPDX-License-Identifier: Apache-2.0
-->

# Commands

Nemo Clawd provides two command interfaces.
The plugin commands run under the `nemoclawd` namespace inside the Nemo Clawd CLI.
The standalone `nemoclawd` binary handles host-side setup, deployment, Solana integration, and service management.
Both interfaces are installed when you run `npm install -g @mawdbotsonsolana/nemoclawd`.
If npm returns `E404` for the scoped package, run `./install.sh` from a source checkout to build and link the local CLI.

New users should start with the [Quickstart](../get-started/quickstart.md) and [Solana and Blockchain AI Onboarding](../solana/onboarding.md) pages before using this reference.

## Command Dispatch

The standalone binary checks host commands and registered sandbox names before it hands a command to the compiled runtime.
If the command is not a built-in host command and does not match a sandbox, `nemoclawd` delegates to `dist/entry.js` when the packaged runtime is present.
The local plugin build output lives under `dist/nemoclawd-plugin`, which keeps the imported runtime available after `npm run build`.

Use `nemoclawd dist <command>` to run the compiled runtime directly.
This is useful when a runtime command has the same name as a host command.

```console
$ nemoclawd dist status --help
$ nemoclawd gateway --help
```

## Quick Start

Use this order for a first Solana-oriented onboarding run:

```console
$ nemoclawd doctor
$ nemoclawd launch
$ nemoclawd solana
$ nemoclawd financial-harness
$ nemoclawd demo
$ nemoclawd ai-training
```

Create a wallet and start runtime services only after the dry-run report matches your intended posture:

```console
$ nemoclawd wallet create
$ nemoclawd solana start my-assistant
```

### `nemoclawd launch`

Run the fastest host-side path after installation.

```console
$ nemoclawd launch
```

This command:

- runs `nemoclawd doctor`
- runs onboarding automatically if no sandbox exists
- starts the best available Solana stack for the current machine
- falls back to relay-only mode when `TELEGRAM_BOT_TOKEN` is not configured yet

### `nemoclawd solana`

One-shot command that shows your Solana configuration status and lists all available actions.
If no sandbox exists, it runs the full onboard wizard automatically.

```console
$ nemoclawd solana
```

### `nemoclawd financial-harness`

Dry-run preflight for the Solana financial path.
The command reports the active RPC, inferred cluster, wallet metadata, applied and missing policy presets, and the guardrails that keep signing and transaction submission disabled.

```console
$ nemoclawd financial-harness
$ nemoclawd financial-harness my-assistant --json
```

Use this before `nemoclawd solana start` when validating wallet, policy, and operator-review posture.

### `nemoclawd demo`

Print the local dry-run walkthrough without starting services.
Use this command to review the first-run sequence and the interactive OpenShell demo prerequisites.

```console
$ nemoclawd demo
$ nemoclawd demo --run
```

The `--run` option starts the interactive walkthrough from `scripts/walkthrough.sh`.
It opens the OpenShell TUI and a sandboxed agent session so you can observe and approve network requests.

### `nemoclawd doctor`

Run a host-side diagnostic pass before onboarding or going live.

```console
$ nemoclawd doctor
```

This checks:

- Node.js and npm versions
- Docker CLI and daemon availability
- OpenShell installation state
- sandbox registry state
- Solana RPC, Privy wallet, Telegram token, and Helius configuration

### `nemoclawd ai-training`

Inspect the bundled AI training source lanes and print the commands for deeper model-kit and local-stack checks.

```console
$ nemoclawd ai-training
$ nemoclawd ai-training --json
```

Run the build gate explicitly when changing imported training assets.

```console
$ nemoclawd ai-training check
$ npm run ai-training:check
```

The command verifies source files under `ai-training/` and rejects generated training data, model outputs, local virtual environments, caches, and secret-like files.
See [AI Training Integration](ai-training.md) for the lane map and generated-data policy.

### `nemoclawd onboard`

Run the 9-step interactive setup wizard.
The wizard creates an OpenShell gateway, registers inference providers, builds the sandbox image, configures Solana RPC, sets up a Privy agentic wallet, and optionally starts a local test-validator.

```console
$ nemoclawd onboard
```

Onboard steps:

1. Preflight checks (Docker, OpenShell, GPU detection)
2. Start OpenShell gateway
3. Create sandbox (builds Docker image with Solana CLI + Pump-Fun SDK)
4. Configure inference (NIM / NVIDIA Cloud / Ollama / vLLM)
5. Set up inference provider
6. Set up Nemo Clawd inside sandbox
7. Solana and wallet configuration, including RPC URL, Privy agentic wallet, and Pump-Fun token
8. Solana test-validator, optional local validator with cloned Pump programs
9. Policy presets (auto-detects solana-rpc, pumpfun, privy, telegram)

## Plugin Commands

### `nemoclawd launch`

Bootstrap Nemo Clawd inside an OpenShell sandbox.
If Nemo Clawd detects an existing host installation, `launch` stops unless you pass `--force`.

```console
$ nemoclawd launch [--force] [--profile <profile>]
```

`--force`
: Skip the ergonomics warning and force plugin-driven bootstrap. Without this flag,
  Nemo Clawd recommends using `openshell sandbox create` directly for new installs.

`--profile <profile>`
: Blueprint profile to use. Default: `default`.

### `nemoclawd status`

Display sandbox health, blueprint run state, and inference configuration.

```console
$ nemoclawd status [--json]
```

### `nemoclawd logs`

Stream blueprint execution and sandbox logs.

```console
$ nemoclawd logs [-f] [-n <count>] [--run-id <id>]
```

### `/nemoclawd` Slash Command

| Subcommand | Description |
|---|---|
| `/nemoclawd status` | Show sandbox and inference state |

## Standalone Host Commands

### Solana Quick Start

#### `nemoclawd solana`

Show the Solana quick-start overview for the default sandbox.

```console
$ nemoclawd solana
```

This prints the active RPC, wallet, and the recommended Solana runtime commands.

#### `nemoclawd financial-harness [sandbox] [--json]`

Show the dry-run financial harness for the default or named sandbox.

```console
$ nemoclawd financial-harness my-assistant
$ nemoclawd financial-harness my-assistant --json
```

The harness does not create wallets, sign transactions, submit orders, or provide trading advice.
It is an auditable readiness report for RPC, wallet, policy, and future trading-control guardrails.

#### `nemoclawd solana start [sandbox]`

Run the one-shot Solana startup flow.

```console
$ nemoclawd solana start my-assistant
```

This launches the bundled Solana operator stack inside the sandbox:

- Pump-Fun Telegram bot + API
- natural-language Solana wallet bridge
- realtime websocket relay
- wallet heartbeat and vault logging

If no sandbox exists yet, Nemo Clawd runs `onboard` first and then starts the stack.

#### `nemoclawd wallet [create|list|status]`

Manage the Privy-backed Solana wallet used by the agent.

```console
$ nemoclawd wallet create
$ nemoclawd wallet list
$ nemoclawd wallet status
```

`create` provisions a Privy-managed Solana wallet and can optionally create a default
spending policy. `list` shows locally known wallet records, and `status` prints the
current Privy, wallet, and RPC configuration.

### Sandbox Management

#### `nemoclawd <name> connect`

Open an interactive shell inside the sandbox. The sandbox includes Solana CLI tools,
Pump-Fun SDK, `helius`, and the Privy agentic wallet skill.

```console
$ nemoclawd my-assistant connect
```

#### `nemoclawd <name> financial-harness [--json]`

Show the same dry-run financial harness scoped to a registered sandbox.

```console
$ nemoclawd my-assistant financial-harness
$ nemoclawd my-assistant financial-harness --json
```

Use the sandbox-scoped form when you want the report to include policy presets recorded for that sandbox.

#### `nemoclawd <name> status`

Show sandbox status, health, inference config, Solana RPC, and wallet info.

```console
$ nemoclawd my-assistant status
```

#### `nemoclawd <name> logs`

View sandbox logs. Use `--follow` to stream output in real time.

```console
$ nemoclawd my-assistant logs [--follow]
```

#### `nemoclawd <name> destroy`

Stop the NIM container and delete the sandbox.

```console
$ nemoclawd my-assistant destroy
```

### Solana Agent Commands

#### `nemoclawd <name> solana-stack`

Start the Solana operator stack inside the sandbox.

```console
$ nemoclawd my-assistant solana-stack
```

This is the sandbox-scoped equivalent of `nemoclawd solana start`.
The stack writes service and runtime records to `~/.nemoclawd/vault/`.

#### `nemoclawd <name> solana-agent`

Run the Pump-Fun Solana tracker bot inside the sandbox.
Monitors agent payments, creator fee claims, and token buybacks on-chain,
sending real-time Telegram notifications.

```console
$ nemoclawd my-assistant solana-agent
```

**Required env:** `AGENT_TOKEN_MINT_ADDRESS`, `DEVELOPER_WALLET`, `TELEGRAM_BOT_TOKEN`
**Optional env:** `SOLANA_RPC_URL`, `SOLANA_WS_URL`, `HELIUS_API_KEY`, `CURRENCY_MINT`, `PRICE_AMOUNT`, `PRIVY_APP_ID`, `PRIVY_APP_SECRET`

The bot also supports sub-modes inside the sandbox:

```console
$ nemoclawd-solana-agent bot              # Default: start tracker bot
$ nemoclawd-solana-agent test-validator   # Start local validator with Pump programs
$ nemoclawd-solana-agent status           # Show Solana + wallet status
```

#### `nemoclawd <name> solana-bridge`

Real-time Solana-Telegram bridge that monitors wallet activity and narrates it in natural language.
Detects incoming/outgoing transfers, buys, sells, token balance changes, and program interactions.

```console
$ nemoclawd my-assistant solana-bridge
```

**Required env:** `TELEGRAM_BOT_TOKEN`
**Optional env:** `SOLANA_RPC_URL`, `SOLANA_WS_URL`, `HELIUS_API_KEY`, `DEVELOPER_WALLET`, `AGENT_TOKEN_MINT_ADDRESS`, `TELEGRAM_NOTIFY_CHAT_IDS`, `PRIVY_APP_ID`, `NEMOCLAW_VAULT_DIR`, `HEARTBEAT_SECONDS`, `MIN_WALLET_SOL`, `STOP_BALANCE_SOL`

The bridge is broadcast-oriented and is designed to coexist with the main Pump-Fun Telegram bot without polling conflicts. It pushes narrated wallet activity to `TELEGRAM_NOTIFY_CHAT_IDS`, records heartbeat snapshots and wallet activity to the Nemo Clawd vault, and marks funded or protection state from wallet balance thresholds while the primary bot continues handling interactive commands.

#### `nemoclawd <name> telegram-bot`

Run the Pump-Fun Telegram monitor bot with full API and event filtering.

```console
$ nemoclawd my-assistant telegram-bot
```

#### `nemoclawd <name> payment-app`

Run the payment-gated Pump-Fun agent app (Next.js).

```console
$ nemoclawd my-assistant payment-app
```

#### `nemoclawd <name> swarm-bot`

Run the Pump-Fun swarm dashboard.

```console
$ nemoclawd my-assistant swarm-bot
```

#### `nemoclawd <name> websocket-server`

Run the Pump-Fun WebSocket relay server.

```console
$ nemoclawd my-assistant websocket-server
```

### Policy Presets

#### `nemoclawd <name> policy-add`

Add a policy preset to a sandbox.

```console
$ nemoclawd my-assistant policy-add
```

Available presets include:

| Preset | Description |
|---|---|
| `solana-rpc` | Solana RPC providers (mainnet, devnet, testnet, Helius, Alchemy, QuikNode) |
| `pumpfun` | Pump.fun APIs, Jupiter aggregator, DexScreener |
| `privy` | Privy agentic wallet APIs (auth, policies, transaction signing) |
| `telegram` | Telegram Bot API |
| `pypi` | Python package index |
| `npm` | npm registry |

#### `nemoclawd <name> policy-list`

List available presets and show which are applied.

```console
$ nemoclawd my-assistant policy-list
```

### Deploy

#### `nemoclawd deploy <instance>`

Deploy to a remote Brev GPU instance.

```console
$ nemoclawd deploy my-gpu-box
```

### Services

#### `nemoclawd start`

Start auxiliary services (Telegram bridge, cloudflared tunnel).

```console
$ nemoclawd start
```

#### `nemoclawd stop`

Stop all auxiliary services.

```console
$ nemoclawd stop
```

#### `nemoclawd status`

Show sandbox list and service status.

```console
$ nemoclawd status
```

### Infrastructure

#### `nemoclawd setup-spark`

Set up Nemo Clawd on DGX Spark (cgroup v2 + Docker fixes for Ubuntu 24.04).

```console
$ sudo nemoclawd setup-spark
```

## Sandbox Solana Tooling

When connected to a sandbox (`nemoclawd <name> connect`), the following tools are available:

### Solana CLI

```console
$ solana config set --url <rpc>          # Set RPC endpoint
$ solana balance                          # Check SOL balance
$ solana transfer <to> <amount>           # Send SOL
$ solana-keygen new                       # Generate a new keypair
$ solana deploy <program.so>              # Deploy a program
$ solana-test-validator                    # Run local test-validator
```

### SPL Token

```console
$ spl-token create-token                  # Create a new SPL token
$ spl-token create-account <mint>         # Create a token account
$ spl-token mint <mint> <amount>          # Mint tokens
$ spl-token transfer <mint> <amount> <to> # Transfer tokens
```

### Helius CLI

```console
$ helius                                  # Helius RPC CLI tools
```

### Privy Agentic Wallet

The Privy skill is available to the Nemo Clawd agent inside the sandbox.
Ask the agent to:

- "Create a Solana wallet for me using Privy"
- "Check my wallet balance"
- "Create a spending policy that limits to 0.1 SOL per transaction"
- "Send 0.01 SOL to `<address>`"

Private keys are managed by Privy.
They never leave Privy's infrastructure and are never stored in the sandbox.
