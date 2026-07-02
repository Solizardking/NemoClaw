---
title:
  page: "Set Up the Nemo Clawd Telegram Bridge for Solana Wallet Narration"
  nav: "Set Up Telegram Bridge"
description: "Forward remote chat and Solana wallet activity narration between Telegram and the sandboxed Nemo Clawd agent."
keywords: ["nemoclawd telegram bridge", "telegram bot nemoclawd agent", "solana wallet telegram narration"]
topics: ["generative_ai", "ai_agents", "solana"]
tags: ["nemoclawd", "openshell", "telegram", "deployment", "solana", "wallets"]
content:
  type: how_to
  difficulty: intermediate
  audience: ["developer", "engineer"]
status: published
---

<!--
  SPDX-FileCopyrightText: Copyright (c) 2025-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
  SPDX-License-Identifier: Apache-2.0
-->

# Set Up the Nemo Clawd Telegram Bridge for Solana Wallet Narration

Forward messages and Solana wallet activity narration between a Telegram bot and the Nemo Clawd agent running inside the sandbox.
The generic chat bridge is managed by `nemoclawd start`.
The Solana wallet narration bridge runs through `nemoclawd solana start <sandbox>` or `nemoclawd <name> solana-bridge`.

:::{warning}
Do not send API keys, bot tokens, wallet secrets, seed phrases, private keys, or private RPC URLs through Telegram.
Run `nemoclawd financial-harness` before starting wallet-aware bridge services.
:::

## Prerequisites

- A running Nemo Clawd sandbox, either local or remote.
- A Telegram bot token from [BotFather](https://t.me/BotFather).
- A completed `nemoclawd solana` check when you plan to use wallet activity narration.
- An acceptable `nemoclawd financial-harness <sandbox>` report before starting wallet-aware services.

## Create a Telegram Bot

Open Telegram and send `/newbot` to [@BotFather](https://t.me/BotFather).
Follow the prompts to create a bot and receive a bot token.

## Set the Environment Variable

Export the bot token as an environment variable:

```console
$ export TELEGRAM_BOT_TOKEN=<your-bot-token>
```

## Start the Generic Chat Bridge

Start the generic Telegram bridge and other auxiliary services:

```console
$ nemoclawd start
```

The `start` command launches the following services:

- The Telegram bridge forwards messages between Telegram and the agent.
- The cloudflared tunnel provides external access to the sandbox.

The Telegram bridge starts only when the `TELEGRAM_BOT_TOKEN` environment variable is set.

## Start Solana Wallet Narration

Use the Solana startup flow when you want wallet activity, relay, heartbeat, and vault records:

```console
$ nemoclawd financial-harness my-assistant
$ nemoclawd solana start my-assistant
```

To run only the bridge inside an existing sandbox, use the sandbox-scoped command:

```console
$ nemoclawd my-assistant solana-bridge
```

The Solana bridge pushes narrated wallet activity to `TELEGRAM_NOTIFY_CHAT_IDS`, records heartbeat snapshots and wallet activity to the Nemo Clawd vault, and respects the wallet and policy posture reported by the harness.

Set notification chat IDs for broadcast narration:

```console
$ export TELEGRAM_NOTIFY_CHAT_IDS="123456789,987654321"
```

## Verify the Services

Check that the Telegram bridge is running:

```console
$ nemoclawd status
```

The output shows the status of all auxiliary services.

## Send a Message

Open Telegram, find your bot, and send a message.
The bridge forwards the message to the Nemo Clawd agent inside the sandbox and returns the agent response.

## Restrict Interactive Chat by Chat ID

To restrict which Telegram chats can interact with the legacy chat bridge, set the `ALLOWED_CHAT_IDS` environment variable to a comma-separated list of Telegram chat IDs:

```console
$ export ALLOWED_CHAT_IDS="123456789,987654321"
$ nemoclawd start
```

## Stop the Services

To stop the Telegram bridge and all other auxiliary services:

```console
$ nemoclawd stop
```

## Related Topics

- [Deploy Nemo Clawd to a Remote GPU Instance](deploy-to-remote-gpu.md) for remote deployment with Telegram support.
- [Solana and Blockchain AI Onboarding](../solana/onboarding.md) for wallet and policy concepts.
- [Financial Harness](../solana/financial-harness.md) before enabling wallet-aware services.
- [Commands](../reference/commands.md) for the full `start` and `stop` command reference.
