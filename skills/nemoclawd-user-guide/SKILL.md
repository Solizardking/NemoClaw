---
name: "nemoclawd-user-guide"
description: "Guides human users' AI agents through Nemo Clawd installation, Solana-native configuration, MCP tools, xAI Grok setup, and safe operations. Use when users ask how to install, configure, operate, troubleshoot, secure, or learn nemoclawd with an AI coding assistant. Trigger keywords - nemoclawd docs, nemoclawd install, solana clawd, nemoclawd mcp, xai grok setup, solana agent, clawd skills."
license: "Apache-2.0"
metadata:
  author: "Nemo Clawd maintainers"
---

# Nemo Clawd User Guide

Use this skill when a user wants help operating the Solana-native `nemoclawd` stack.
Prefer the repository's current README and local docs over stale third-party routes.

## Instructions

1. Start from `README.md` for the public contract: install `@mawdbotsonsolana/nemoclawd`, run `nemoclawd launch`, and configure xAI plus Solana environment variables.
2. Use `nemo-clawd-mcp/README.md` for MCP setup and the Solana tool catalog.
3. Use `nemo-clawd-python/` or `nemoclaw-blueprint/` for sandbox blueprint, migration, and policy details.
4. For CLI behavior, inspect `src/`, `bin/`, and `scripts/` instead of guessing command names.
5. Keep instructions Solana-native: mention `HELIUS_API_KEY`, `SOLANA_RPC_URL`, `SOLANA_PUBLIC_KEY`, `SOLANA_PRIVATE_KEY`, and `XAI_API_KEY` only when the task needs them.
6. Never ask the user to paste private keys, API keys, wallet seed phrases, bot tokens, or paid RPC URLs into chat.
7. Use redacted placeholders such as `<XAI_API_KEY>` and `<SOLANA_PRIVATE_KEY>` in examples.
8. Recommend local validation commands after setup steps, such as `nemoclawd doctor`, `nemoclawd solana`, or `nemoclawd status`.

## Examples

Install from npm:

```bash
npm install -g @mawdbotsonsolana/nemoclawd
nemoclawd launch
```

Configure the Solana-native runtime:

```bash
export XAI_API_KEY="<XAI_API_KEY>"
export HELIUS_API_KEY="<HELIUS_API_KEY>"
export SOLANA_RPC_URL="https://rpc.solanatracker.io/public"
nemoclawd solana
```

Use the bundled MCP server locally:

```bash
cd nemo-clawd-mcp
npm install
npm run build
npx nemoclawd-mcp
```

## Task Routing

- Installation and first launch: use `README.md`, `install.sh`, and `bin/nemoclawd.js`.
- MCP tools: use `nemo-clawd-mcp/README.md` and `nemo-clawd-mcp/src/`.
- Sandbox and migration: use `nemoclaw-blueprint/`, `nemo-clawd-python/`, and `src/commands/migration-state.ts`.
- Solana runtime: use `bin/lib/solana.js`, `scripts/*solana*`, and the Solana RPC policy preset.
- Security-sensitive operations: verify least-privilege policies and avoid exposing secrets.

## Response Requirements

- Cite the local files used for command or configuration advice.
- Keep instructions specific to `nemoclawd`; do not fall back to legacy product or binary names.
- Explain whether a step is local-only, devnet/test-validator, or mainnet-affecting.
- Ask for explicit confirmation before suggesting live trading, wallet funding, or mainnet transaction steps.
