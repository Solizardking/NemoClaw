<!-- SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved. -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Nemo Clawd Tools

This directory contains trusted repository tools used by CI advisors and local operator checks.

## Solana Readiness

Run the dry-run Solana readiness tool without external network calls:

```bash
npm run tools:solana:readiness
```

Run it against a real RPC endpoint:

```bash
node --experimental-strip-types tools/e2e/solana-readiness.mts \
  --rpc "$SOLANA_RPC_URL" \
  --wallet "$DEVELOPER_WALLET" \
  --expect-cluster devnet \
  --json
```

The tool probes Solana JSON-RPC health, version, epoch, latest blockhash, and optional wallet balance.
It never signs transactions, submits transactions, or accepts private key material.
