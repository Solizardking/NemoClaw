---
name: "nemoclawd-skills-guide"
description: "Start here. Introduces what Nemo Clawd is, what agent skills are available, and which skill to use for Solana-native Clawd tasks. Use when discovering Nemo Clawd capabilities, choosing the right skill, or orienting in the project. Trigger keywords - skills, capabilities, what can I do, help, guide, index, overview, start here, solana clawd, nemoclawd."
license: "Apache-2.0"
---

# Nemo Clawd Skills Guide

Nemo Clawd is a Solana-native agentic runtime packaged as
`@mawdbotsonsolana/nemoclawd`. It combines the `nemoclawd` CLI, OpenShell
sandboxing, xAI/NVIDIA inference routing, the bundled Nemo Clawd MCP server,
Solana wallet and RPC guardrails, and CLAWD-aware agent auth flows.

This guide lists the active source skills for Nemo Clawd and calls out legacy
compatibility skills that still exist for old maintainer workflows. Load the
specific skill you need after identifying it here.

## Skill Buckets

### `nemoclawd-user-*` (1 skill)

For end users operating a Nemo Clawd sandbox or asking a coding assistant for
setup help. Covers routing to local docs, public Markdown docs, Solana
onboarding, MCP setup, financial-harness guardrails, and agent-auth flows.

### Legacy internal workflow skills

The source tree still contains internal `nemoclaw-maintainer-*` and
`nemoclaw-contributor-*` directories. Treat those as compatibility-only workflow
helpers for old repository maintenance tasks, not user-facing Nemo Clawd skills.
Do not copy them into the published `skills/` catalog.

When working on public Nemo Clawd support, prefer `nemoclawd-user-guide`.

## Skill Catalog

### User Skills

<!-- user-skills-table:begin -->
| Skill | Summary |
|-------|---------|
| `nemoclawd-user-guide` | Route human users' AI agents to local docs, `llms.txt`, the Nemo Clawd docs MCP server, Solana onboarding pages, financial-harness guardrails, MCP setup, and agent-auth guidance for installation, configuration, operation, security, and troubleshooting. |
<!-- user-skills-table:end -->

## Getting Started

For user support, start with `nemoclawd-user-guide`.

Use it for:

- Installing `@mawdbotsonsolana/nemoclawd`.
- Launching or checking `nemoclawd` sandboxes.
- Setting Solana RPC, Helius, Privy, Telegram, or xAI configuration safely.
- Running `nemoclawd financial-harness` before live services.
- Configuring the bundled Nemo Clawd MCP server.
- Explaining SIWS, CAAP/1.0, CLAWD token gating, and Phala TEE attestation via `agent-auth`.
- Routing to local `docs/` pages or `https://docs.nvidia.com/nemoclawd/llms.txt`.

When the user asks about repository maintenance, CI triage, PR review, or old
NVIDIA workflow automation, inspect the relevant compatibility skill directly
and verify that its repository assumptions still match the current Nemo Clawd
checkout before acting.
