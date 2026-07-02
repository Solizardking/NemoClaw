<!-- SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved. -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Agent Instructions

## Project Overview

Nemo Clawd is a Solana-native agentic runtime distributed as
`@mawdbotsonsolana/nemoclawd`. It provides the `nemoclawd` CLI, OpenShell
sandbox orchestration, a Nemo Clawd MCP server, Solana wallet/RPC guardrails,
CLAWD-aware agent auth flows, and service helpers for Telegram, bridges,
payments, swarm bots, and websocket relays.

Status: Active development. Interfaces may change without notice.

## Agent Skills

This repo ships source-side agent skills under `.agents/skills/`.
Use `nemoclawd-user-guide` for end-user documentation routing, Solana setup,
MCP setup, financial-harness safety checks, and CAAP/SIWS agent-auth guidance.
Load `nemoclawd-skills-guide` for the source skill catalog.

The `.claude/skills` path is a symlink to `.agents/skills`.
The repo still contains legacy internal `nemoclaw-maintainer-*` and
`nemoclaw-contributor-*` skill directories. Treat them as compatibility-only
workflow helpers for old repository maintenance tasks unless a user explicitly
asks for those workflows.

## Architecture

| Path | Language | Purpose |
|------|----------|---------|
| `bin/` | JavaScript (CJS) | CLI launcher (`nemoclawd.js`), legacy shim (`nemoclaw.js`), and runtime helpers |
| `src/` | TypeScript | Plugin/runtime source for blueprint, commands, and onboarding |
| `nemo-clawd-mcp/` | TypeScript | Bundled Nemo Clawd MCP server and Solana tool catalog |
| `nemo-clawd-python/` | Python/YAML | Current blueprint artifact, migrations, orchestrator, and policy presets |
| `nemoclaw-blueprint/` | Python/YAML | Compatibility blueprint path retained for existing package and docs references |
| `agents/` and `agent/` | JSON/Python | Clawd agent catalog, locales, schemas, and Solana agent implementations |
| `extensions/` | JSON | Clawd extension manifests, including Solana and messaging integrations |
| `scripts/` | Bash/JS/Python | Install, setup, Solana stack, payment, bridge, Telegram, and audit helpers |
| `docs/` | Markdown | User-facing Nemo Clawd documentation, including Solana onboarding and financial harness |
| `skills/` | Markdown/JSON | Published NVSkills catalog copy; currently `skills/nemoclawd-user-guide/` |
| `.agents/skills/` | Markdown/TS/Shell | Source-side skills used by local agents |
| `test/` | JavaScript | Node test suite for package behavior |

## Quick Reference

| Task | Command |
|------|---------|
| Install root deps | `npm install` |
| Install MCP deps | `npm --prefix nemo-clawd-mcp install` |
| Build plugin and MCP server | `npm run build` |
| Build plugin only | `npm run build:plugin` |
| Build MCP server only | `npm run build:mcp` |
| Run tests | `npm test` |
| Run Solana readiness check | `npm run tools:solana:readiness` |
| Run devnet payment harness | `npm run tools:solana:payments` |
| Run public release audit | `npm run public:audit` |
| Dry-run npm package | `npm run pack:check` |
| Run release check | `npm run release:check` |
| Inspect CLI help | `node bin/nemoclawd.js --help` |

There is no `npm run dev:doctor` script in this checkout. Use the targeted
scripts above for verification.

## Key Architecture Decisions

### Dual Runtime Stack

- **CLI and plugin**: TypeScript source plus CommonJS launchers in `bin/`.
- **MCP server**: `nemo-clawd-mcp/` builds separately and is included in the
  root `npm run build` flow.
- **Blueprint**: Python/YAML artifacts live in `nemo-clawd-python/`, with
  `nemoclaw-blueprint/` retained as a compatibility path.
- **Docs**: Markdown pages under `docs/`; generated HTML under `docs/_build/`
  is not the source of truth.
- **Solana runtime**: Scripts and agents under `scripts/`, `agent/`, `agents/`,
  and `extensions/` wire RPC, wallets, trading tools, Telegram, and MCP.

### Testing Strategy

The root `npm test` script runs `node --test test/*.test.js`.
Use focused tests for changed behavior and reserve `npm run release:check` for
broader release validation. Do not call live Solana mainnet, paid x402, or real
trading flows from unit tests.

When changing Solana-facing behavior:

- Prefer local validator, devnet, dry-run, or no-network checks first.
- Mock external RPC, Telegram, wallet, and paid attestation calls.
- Add coverage for wallet-safety, network-policy, and secret-redaction paths.

### Security Model

Nemo Clawd runs agents inside OpenShell sandboxes with:

- Network policies controlling egress to Solana RPC, xAI/NVIDIA inference, and
  approved integration endpoints.
- Credential and wallet-secret handling that keeps private keys, seed phrases,
  API keys, bot tokens, and paid RPC URLs out of chat and logs.
- Dry-run financial harness checks before live Solana runtime services.
- Agent identity and subscription gating through SIWS, CAAP/1.0, CLAWD SPL token
  balance, and TEE evidence when `agent-auth` is used.

Security-sensitive code paths require extra test coverage.

## Code Style and Conventions

### Commit Messages

Conventional Commits are required:

```text
<type>(<scope>): <description>
```

Types: `feat`, `fix`, `docs`, `chore`, `refactor`, `test`, `ci`, `perf`,
`merge`.

### SPDX Headers

Every source file must include an SPDX license header. The hooks may auto-insert
headers, but add them manually for new files when practical.

```javascript
// SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: Apache-2.0
```

For shell scripts use `#` comments. For Markdown use HTML comments.

### JavaScript and TypeScript

- `bin/` launcher files and small helpers use CommonJS where needed for CLI
  compatibility.
- TypeScript builds through `tsconfig.nemoclawd.json` and the MCP server's own
  `tsconfig.json`.
- Keep function complexity low and prefer existing local helpers over new
  abstractions.
- Prefix intentionally unused variables with `_`.

### Shell Scripts

- Shell scripts must have shebangs and be executable.
- Prefer existing scripts under `scripts/` for Solana stack operations instead
  of duplicating setup logic.

### No External Project Links

Do not add links to third-party code repositories, community collections, or
unofficial resources. Links to official tool documentation are acceptable.

## Working with This Repo

### Before Making Changes

1. Read `CONTRIBUTING.md` for the contributor guide.
2. Run targeted tests or checks for the area you plan to change.
3. Use `npm run tools:solana:readiness` for Solana safety checks when relevant.

### Git and GitHub Access Failures

Follow `.agents/skills/_shared/git-github-hard-stop.md`: if SSH, `gh`,
authentication, authorization, remote access, or push permission fails, stop and
ask the user instead of working around access. Do not stop for ordinary merge
conflicts or dirty-worktree state; resolve mechanical conflicts in the relevant
workflow and ask only when resolution would change behavior or contributor
intent.

### Pull Request Follow-Up

Follow `.agents/skills/_shared/pr-follow-up.md`: after opening or pushing to a
PR, monitor required CI and automated review comments, address valid automated
review findings, and consult the user when feedback is ambiguous or
design-changing.

### Common Patterns

**Adding a CLI command:**

- Entry point: `bin/nemoclawd.js`.
- Add implementation under `src/`, `bin/lib/`, or the relevant runtime module
  according to the existing pattern.
- Add focused tests under `test/`.

**Adding an MCP tool:**

- Source: `nemo-clawd-mcp/src/`.
- Update `nemo-clawd-mcp/README.md` when user-facing tool behavior changes.
- Build with `npm run build:mcp`.

**Adding Solana runtime behavior:**

- Keep wallet-aware operations behind explicit dry-run or user confirmation.
- Add or update policy presets in `nemo-clawd-python/policies/` or
  `nemoclaw-blueprint/policies/` as needed.
- Prefer devnet/test-validator verification before any mainnet guidance.

**Updating the user skill:**

- Source: `.agents/skills/nemoclawd-user-guide/`.
- Published copy: `skills/nemoclawd-user-guide/`.
- Keep both copies in sync and update evals when the routing behavior changes.

### Gotchas

- `nemoclaw-blueprint/` and some `nemoclaw*` filenames are compatibility paths.
  Do not rename runtime paths unless the package manifest, imports, docs, and
  tests are updated together.
- The root package publishes `skills/nemoclawd-user-guide/**`; keep catalog
  docs aligned with that path.
- `.venv/`, `.mypy_cache/`, `.logs/`, `dist/`, and `docs/_build/` are generated
  or environment-specific artifacts. Do not treat them as source docs.

## Documentation

- Treat `docs/` as the source of truth for user-facing documentation and follow
  `docs/CONTRIBUTING.md` for docs changes.
- After completing development changes, run a documentation review before final
  handoff. Give the reviewer the changed files, behavior summary, and test
  evidence so it can update docs or report that no doc changes are needed.
- Update `.agents/skills/nemoclawd-user-guide/SKILL.md` only when AI-agent docs
  routing guidance changes, and update `skills/nemoclawd-user-guide/` with it.

## PR Requirements

- Create feature branches from `main`.
- Let normal commit and push hooks provide verification before submitting.
- Contributor-owned PRs must self-serve the DCO declaration and GitHub commit
  verification before opening a PR.
- Every contributor-owned PR description must include a valid `Signed-off-by:`
  declaration for the contributor, and every commit in the PR must appear as
  `Verified` in GitHub.
- Stop before `gh pr create` if the PR body will not include the DCO declaration
  or any commit is missing GitHub verification.
- Run targeted tests for changed behavior, and run docs checks for docs changes.
- No secrets, API keys, wallet private keys, seed phrases, or credentials may be
  committed.
