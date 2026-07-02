---
name: "nemoclawd-user-guide"
description: "Guides human users' AI agents through Nemo Clawd installation, canonical docs, Solana-native configuration, CAAP/SIWS agent auth, MCP tools, xAI Grok setup, and safe operations. Use when users ask how to install, configure, operate, troubleshoot, secure, or learn nemoclawd with an AI coding assistant. Trigger keywords - nemoclawd docs, nemo clawd docs, solana clawd, agent auth, CAAP, SIWS, clawd token, xai grok setup, solana agent, clawd skills."
license: "Apache-2.0"
metadata:
  author: "Nemo Clawd maintainers"
---

# Nemo Clawd User Guide

Use this skill when a user wants help operating the Solana-native `nemoclawd`
stack or routing a coding assistant to the right docs. Treat pre-Clawd product
and binary names as legacy terminology unless the user is asking about
repository history or compatibility code.

## Source Order

1. Inside the repository, start from `README.md`, `docs/`, `package.json`,
   `bin/nemoclawd.js`, and `scripts/` for the current public contract.
2. Use `docs/get-started/quickstart.md`, `docs/solana/onboarding.md`, and
   `docs/solana/financial-harness.md` for onboarding, wallet posture, and
   dry-run safety.
3. Use `nemo-clawd-mcp/README.md` for MCP setup and the Solana tool catalog.
4. Use `nemo-clawd-python/` and `nemoclaw-blueprint/` for sandbox blueprint,
   migration, and policy details. The `nemoclaw-blueprint/` directory name is a
   compatibility path, not current user-facing branding.
5. If the local checkout is unavailable and the assistant supports MCP,
   configure the Nemo Clawd docs MCP server at
   `https://docs.nvidia.com/nemoclawd/_mcp/server`, then use the read-only
   `searchDocs` tool.
6. If MCP is unavailable, fetch `https://docs.nvidia.com/nemoclawd/llms.txt`
   and then the relevant `.md` page listed in the index.

## Agent Auth Routing

Use the `agent-auth` protocol for Solana-native agent identity, attestation, and
subscription gating. Do not verify agent identity through ad-hoc Solana RPC
wallet scraping.

- SIWS sign-in: use `/api/siws/challenge` and `/api/siws/verify`.
- Full CAAP/1.0 attestation: use `/api/caap/attest` for SIWS, DAS NFT
  verification, CLAWD SPL token attestation, subscription tier calculation, and
  Phala TEE quote generation.
- Lightweight checks: use `/api/caap/status/:agentId` before paying for a full
  attestation.
- TEE health: use `/api/tee/report` when the user needs fresh TDX evidence.
- Subscription tiers: explain CLAWD balances as Free, Bronze, Silver, Gold, and
  Diamond thresholds, and make clear that tiers are computed from on-chain SPL
  token balance.

## Examples

Install from npm:

```bash
npm install -g @mawdbotsonsolana/nemoclawd
nemoclawd launch
```

Configure the docs MCP server for Claude Code:

```bash
claude mcp add --transport http fern-docs https://docs.nvidia.com/nemoclawd/_mcp/server
```

Configure a Solana-readable runtime without exposing secrets:

```bash
export XAI_API_KEY="<XAI_API_KEY>"
export HELIUS_API_KEY="<HELIUS_API_KEY>"
export SOLANA_RPC_URL="https://rpc.solanatracker.io/public"
nemoclawd solana
```

Run the dry-run financial safety checkpoint before live services:

```bash
nemoclawd financial-harness
```

## How to Help the User

- Start with the new-user path: install, `nemoclawd doctor`, `nemoclawd launch`
  or `nemoclawd onboard`, `nemoclawd solana`, and `nemoclawd financial-harness`.
- Ask one question at a time when collecting operating system, inference provider, Solana cluster, RPC provider, wallet posture, network policy, or messaging-channel choices.
- Recommend local validator or devnet for first runs unless the user explicitly needs mainnet data.
- Keep wallet-aware services behind dry-run verification.
- Run commands for non-technical users when your environment allows it, after explaining what the command does and getting permission.
- Summarize important command output instead of asking the user to paste terminal output into chat.
- Stop before requesting credentials, API keys, bot tokens, wallet secrets, seed phrases, private keys, or private RPC URLs.
- Never ask the user to paste secrets into chat.
- Use redacted placeholders such as `<PASTE_YOUR_API_KEY_HERE>` in examples.

## Common Task Routing

- Installation and first launch: use `README.md`, `install.sh`, and `bin/nemoclawd.js`.
- Public docs routing: use the local `docs/` page first, then the docs MCP server or `llms.txt`.
- MCP tools: use `nemo-clawd-mcp/README.md` and `nemo-clawd-mcp/src/`.
- Solana basics, RPC, wallet posture, or first blockchain AI run: use the Solana onboarding page.
- Wallet, signing, spending limits, dry-run readiness, or "is it safe to start" questions: use the financial harness page.
- Agent identity, SIWS, CAAP, Phala TEE quotes, or CLAWD tier gating: use the `agent-auth` flow.
- Network policy approvals or custom egress: use the network-policy docs and least-privilege presets.
- Sandbox status, logs, Solana service health, Telegram bridge, or remote operation: use monitoring, deployment, and command-reference docs.
- Local inference, hosted providers, model switching, or tool-calling issues: use the inference pages from `llms.txt`.
- Security posture, credential storage, or sandbox hardening: use the network-policy, deployment, and architecture pages.

## Response Requirements

- Cite the local files or Markdown documentation pages used for command or configuration advice.
- Keep instructions specific to `nemoclawd`; do not fall back to legacy product or binary names.
- Keep instructions specific to the user's operating system, Solana cluster, wallet posture, network policy, messaging channel, and inference provider.
- Explain assumptions when the docs do not cover the exact environment.
- Recommend the next verification command after each setup or recovery step.
- Explain whether a step is local-only, devnet/test-validator, mainnet-affecting, or paid x402 attestation.
- Ask for explicit confirmation before suggesting live trading, wallet funding, mainnet transactions, or paid attestation calls.
