<!-- SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved. -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Compact Extensions

This directory is intentionally manifest-only. The previous drop contained copied plugin source trees, tests, lockfiles, generated output, and local credential artifacts. Those were replaced with a compact registry that records extension identity, capability boundaries, configuration namespaces, and sensitive environment variables without vendoring implementation code.

- `registry.json` is the source of truth.
- `registry.schema.json` describes registry entries.
- `extension-pointer.schema.json` describes the tiny per-extension pointer files.
- Each extension directory contains only `clawd.extension.json`, which points back to the matching registry entry.

Perpetual futures support is explicit through `trading.perps` capabilities and the `perps` metadata on `aster-dex`, `hyperliquid-dex`, and the aggregate `perps` router.

Do not commit `.env`, private keys, provider key JSON files, lockfiles, `nohup.out`, `node_modules`, generated `dist/`, or copied upstream SDK trees here.
