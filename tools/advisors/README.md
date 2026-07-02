<!-- SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved. -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Advisor shared utilities

Shared implementation helpers for Nemo Clawd advisor workflows.

The advisor entrypoints stay domain-specific under `tools/e2e-advisor/` and
`tools/pr-review-advisor/`, while this directory owns common infrastructure:

- read-only Pi SDK session execution, including deterministic synthetic tool-result preloading for known advisor context;
- Git diff and metadata helpers;
- JSON extraction and sanitization helpers;
- Solana RPC, wallet-address, policy-hint, and dry-run readiness helpers;
- artifact path and file I/O helpers;
- GitHub API and sticky-comment helpers.

GitHub workflows must continue to execute advisor entrypoints from the trusted
`ADVISOR_DIR` checkout. PR workspaces remain inert analysis data only.

## Solana helper

`tools/advisors/solana.mts` is shared by advisor scripts and E2E tooling.
It provides deterministic helpers for:

- inferring Solana cluster from RPC URLs;
- redacting credential-bearing RPC query parameters;
- validating Solana wallet address shape;
- deriving network-policy preset hints;
- running dry-run JSON-RPC readiness probes without signing or transaction submission;
- classifying Solana-related changed files for advisor recommendations.

Use the runnable wrapper for local checks:

```bash
node --experimental-strip-types tools/e2e/solana-readiness.mts --no-network --json
```

## Solana payment helper

`tools/advisors/solana-payments.mts` builds deterministic payment artifacts for
Solana x402 onboarding:

- USDC devnet/mainnet SPL mint selection;
- configurable OpenUSD mint support;
- CLAWD SPL mint support;
- base64 `PAYMENT-REQUIRED` header generation for x402 V2;
- Cloudflare Worker verification snippet generation;
- Kora TOML `allowed_tokens` and `allowed_spl_paid_tokens` generation.

The runnable wrapper is:

```bash
node --experimental-strip-types tools/e2e/solana-payments.mts \
  --recipient "$SOLANA_PAYMENT_RECIPIENT" \
  --tokens usdc,openusd,clawd \
  --openusd-mint "$OPENUSD_MINT" \
  --json
```
