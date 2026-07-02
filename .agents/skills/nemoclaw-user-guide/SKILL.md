---
name: "nemoclaw-user-guide"
description: "Guides human users' AI agents to the Nemo Clawd docs MCP server and canonical Markdown documentation for Solana-aware blockchain AI onboarding. Use when users ask how to install, configure, operate, troubleshoot, secure, or learn Nemo Clawd with an AI coding assistant. Trigger keywords - nemoclawd docs, nemo clawd docs, solana onboarding, blockchain ai onboarding, financial harness, wallet setup, network policy, llms.txt, agent skills."
license: "Apache-2.0"
---

# Nemo Clawd Docs for AI Agents

Use the canonical Nemo Clawd documentation as your source of truth.
Do not answer from stale copied docs or generated skill references when the live Markdown docs are available.
Treat older `NemoClaw` spelling as legacy shorthand for `Nemo Clawd` unless the user is specifically asking about repository history.

## Retrieval Order

1. If the assistant supports MCP, configure the Nemo Clawd docs MCP server at `https://docs.nvidia.com/nemoclawd/_mcp/server`.
2. Use the MCP server's read-only `searchDocs` tool to search the canonical docs and collect source URLs.
3. If MCP is not available, fetch the AI documentation index first: `https://docs.nvidia.com/nemoclawd/llms.txt`.
4. Fetch the specific `.md` page listed in the index or returned by docs search for the user's task.
5. If you only find an HTML documentation URL, replace the `.html` suffix with `.md`, or append `.md` to the route when the URL has no suffix.
6. If you are working inside the source repository, prefer the local `docs/` Markdown page that matches the public route.
7. Prefer Solana onboarding, financial harness, wallet, network policy, and command-reference pages over inferred behavior when the user asks about blockchain AI setup.

## Configure the MCP Server

For Claude Code, run:

```bash
claude mcp add --transport http fern-docs https://docs.nvidia.com/nemoclawd/_mcp/server
```

For Cursor, add `https://docs.nvidia.com/nemoclawd/_mcp/server` to the MCP server configuration.
For other MCP clients, configure a streamable HTTP MCP server at that URL.

## Starting Pages

Use these pages first for common onboarding flows:

- Home: `https://docs.nvidia.com/nemoclawd/latest/index.md`.
- Quickstart: `https://docs.nvidia.com/nemoclawd/latest/get-started/quickstart.md`.
- Solana and blockchain AI onboarding: `https://docs.nvidia.com/nemoclawd/latest/solana/onboarding.md`.
- Financial harness: `https://docs.nvidia.com/nemoclawd/latest/solana/financial-harness.md`.
- Commands: `https://docs.nvidia.com/nemoclawd/latest/reference/commands.md`.
- Network policies: `https://docs.nvidia.com/nemoclawd/latest/reference/network-policies.md`.

## How to Help the User

- Start with the new-user path: install, `nemoclawd doctor`, `nemoclawd launch` or `nemoclawd onboard`, `nemoclawd solana`, and `nemoclawd financial-harness`.
- Ask one question at a time when collecting operating system, inference provider, Solana cluster, RPC provider, wallet posture, network policy, or messaging-channel choices.
- Recommend local validator or devnet for first runs unless the user explicitly needs mainnet data.
- Keep wallet-aware services behind dry-run verification.
- Run commands for non-technical users when your environment allows it, after explaining what the command does and getting permission.
- Summarize important command output instead of asking the user to paste terminal output into chat.
- Stop before requesting credentials, API keys, bot tokens, wallet secrets, seed phrases, private keys, or private RPC URLs.
- Never ask the user to paste secrets into chat.
- Use redacted placeholders such as `<PASTE_YOUR_API_KEY_HERE>` in examples.

## Common Task Routing

- Installation and first sandbox: fetch the quickstart page.
- Solana basics, cluster choice, RPC, wallet posture, or first blockchain AI run: fetch the Solana onboarding page.
- Wallet, signing, spending limits, dry-run readiness, or "is it safe to start" questions: fetch the financial harness page.
- Network policy approvals or custom egress: fetch the network-policy how-to pages and the network policies reference.
- Sandbox status, logs, Solana service health, Telegram bridge, or remote operation: fetch the monitoring, deployment, and command reference pages.
- Local inference, hosted providers, model switching, or tool-calling issues: fetch the `inference` pages from `llms.txt`.
- Security posture, credential storage, or sandbox hardening: fetch the network-policy, deployment, and architecture pages.
- CLI flags and command syntax: fetch the command reference page.
- Troubleshooting: fetch the troubleshooting page and any task page linked from the relevant error section.

## Response Requirements

- Cite the Markdown documentation pages you used.
- Keep instructions specific to the user's operating system, Solana cluster, wallet posture, network policy, messaging channel, and inference provider.
- Explain assumptions when the docs do not cover the exact environment.
- Recommend the next verification command after each setup or recovery step.
