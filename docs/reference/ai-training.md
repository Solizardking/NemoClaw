---
title:
  page: "Nemo Clawd AI Training Integration"
  nav: "AI Training"
description: "Reference for the bundled AI training source lane, model kit, NVIDIA blueprint adapters, onchain programs, and build verification commands."
keywords: ["nemoclawd ai training", "solana ai model kit", "nvidia blueprint training", "clawd model kit"]
topics: ["generative_ai", "ai_agents", "solana"]
tags: ["nemoclawd", "ai-training", "model-kit", "nvidia", "solana"]
content:
  type: reference
  difficulty: technical_intermediate
  audience: ["developer", "engineer"]
status: published
---

<!--
  SPDX-FileCopyrightText: Copyright (c) 2025-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
  SPDX-License-Identifier: Apache-2.0
-->

# AI Training Integration

Nemo Clawd includes an `ai-training/` source lane for model-kit workflows, NVIDIA blueprint adapters, onchain registration programs, perps tooling, memory helpers, studio assets, and trading-factory code.
The package build verifies that these source lanes are present without bundling generated datasets, local model weights, caches, or private operator state.

## Verify the Source Lane

Run the package-level check before publishing or after changing imported training assets.

```console
$ npm run ai-training:check
```

The standalone CLI exposes the same report.

```console
$ nemoclawd ai-training
$ nemoclawd ai-training check --json
```

The check validates required source paths under `ai-training/`, rejects generated lanes such as `data/`, `outputs/`, `target/`, `.hf/`, `.venv/`, and `ollama/build/`, and scans for secret-like filenames or credential patterns.

## Included Lanes

The build packages source and configuration lanes that can reproduce or operate the training workflow.

| Path | Purpose |
|---|---|
| `ai-training/programs/` | Anchor programs for Clawd core, registry, and treasury contracts. |
| `ai-training/model-kit/` | Terminal model-kit CLI, static frontend, backend handoff, onboarding docs, and static-site verifier. |
| `ai-training/nvidia/` | NVIDIA blueprint adapters, NIM bridge, transaction-foundation model scaffolding, RAG and signal-discovery blueprints, and config validation scripts. |
| `ai-training/memory/` | Local memory integration helper code. |
| `ai-training/docs/` | Model, dataset, onchain, and design notes for the training workspace. |
| `ai-training/perps/` | Model-facing perps tool schemas, prompt helpers, and NVIDIA perps handoff generator. |
| `ai-training/schemas/` | JSON schema contracts for layout and generated artifacts. |
| `ai-training/studio/` | Static local studio entrypoint. |
| `ai-training/trading_factory/` | Trading-factory strategy code, cuFOLIO adapters, and Solana factory integrations. |
| `ai-training/configs/` | LoRA, realtime research, Core AI, and trading-factory training configs. |
| `ai-training/scripts/` | Dataset, release, evaluation, local-stack, and training orchestration scripts. |

## Generated Data Policy

Generated and local-only paths are intentionally excluded from the build.
Create them on the operator machine when running training jobs.

```console
$ ai-training/model-kit/bin/clawd-model-kit init
$ python3 ai-training/scripts/run_local_clawd_stack.py --best-effort
```

Keep raw credentials, wallet files, API keys, model weights, processed datasets, and run logs outside git.
The ignore rules cover `ai-training/data/`, `ai-training/outputs/`, `ai-training/target/`, `ai-training/wandb/`, `ai-training/.hf/`, virtual environments, Python caches, and `ai-training/ollama/build/`.

## Model Kit Static Build

Use the model-kit static verifier when changing frontend files under `ai-training/model-kit/frontend/`.

```console
$ npm run ai-training:model-kit:build
```

This command runs the model-kit package build in place and checks the static frontend contract.

## Full Training Workspace Checks

The imported training workspace also contains deeper Python verifiers.
Those checks expect hydrated local data lanes and optional provider credentials, so they are not part of the default package build.

Run them only after creating the local training data and installing the training requirements.

```console
$ python3 ai-training/scripts/organize_ai_training.py --check
$ python3 ai-training/nvidia/scripts/verify_nvidia.py --strict
```

## Next Steps

Read the [Commands](commands.md) reference for the host CLI syntax.
Use the imported `ai-training/README.md` and `ai-training/STRUCTURE.md` files when working directly inside the training workspace.
