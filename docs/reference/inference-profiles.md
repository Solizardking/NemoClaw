---
title:
  page: "Nemo Clawd Inference Profiles"
  nav: "Inference Profiles"
description: "Configuration reference for Nemo Clawd blueprint inference profiles."
keywords: ["nemoclawd inference profiles", "nemoclawd ncp profile", "nemoclawd vllm profile", "nemoclawd nvidia cloud provider"]
topics: ["generative_ai", "ai_agents"]
tags: ["nemoclawd", "openshell", "inference_routing", "llms", "ncp", "vllm"]
content:
  type: reference
  difficulty: intermediate
  audience: ["developer", "engineer"]
status: published
---

<!--
  SPDX-FileCopyrightText: Copyright (c) 2025-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
  SPDX-License-Identifier: Apache-2.0
-->

# Inference Profiles

Nemo Clawd ships with inference profiles defined in `nemo-clawd-python/blueprint.yaml`.
The selected profile configures an OpenShell inference provider and model route during `nemoclawd launch --profile <profile>` or `nemoclawd migrate --profile <profile>`.
The agent inside the sandbox uses whichever model is active.
Inference requests are routed transparently through the OpenShell gateway.

The `nemoclawd onboard` command records the endpoint type, endpoint URL, model, credential environment variable, and resolved profile in `~/.nemoclawd/config.json`.

## Profile Summary

The Python blueprint accepts the following profile names.
Unknown profile names fail during blueprint planning.

| Profile | Provider Name | Provider Type | Endpoint | Credential |
|---|---|---|---|---|
| `default` | `nvidia-inference` | `nvidia` | `https://integrate.api.nvidia.com/v1` | None in the profile |
| `ncp` | `nvidia-ncp` | `nvidia` | Supplied by NCP onboarding or endpoint override | `NVIDIA_API_KEY` |
| `nim-local` | `nim-local` | `openai` | `http://nim-service.local:8000/v1` | `NIM_API_KEY` |
| `vllm` | `vllm-local` | `openai` | `http://localhost:8000/v1` | `OPENAI_API_KEY`, default `dummy` |

The host onboarding command maps endpoint choices onto these profile names.
The `build` endpoint maps to `default`, `ncp` and `custom` map to `ncp`, `nim-local` maps to `nim-local`, and `vllm` maps to `vllm`.
Local and custom endpoint options are experimental.

Endpoint URL overrides must use `http://` or `https://`, include a host, and omit credentials and URL fragments.

## Available NVIDIA Cloud Models

Nemo Clawd registers the following NVIDIA cloud model IDs for the provider exposed by onboarding:

| Model ID | Label | Context Window | Max Output |
|---|---|---|---|
| `nvidia/nemotron-3-super-120b-a12b` | Nemotron 3 Super 120B | 131,072 | 8,192 |
| `nvidia/llama-3.1-nemotron-ultra-253b-v1` | Nemotron Ultra 253B | 131,072 | 4,096 |
| `nvidia/llama-3.3-nemotron-super-49b-v1.5` | Nemotron Super 49B v1.5 | 131,072 | 4,096 |
| `nvidia/nemotron-3-nano-30b-a3b` | Nemotron 3 Nano 30B | 131,072 | 4,096 |

## Switching Models at Runtime

After the sandbox is running, switch models with the OpenShell CLI.
Use the provider name shown by `nemoclawd status`.

```console
# Switch to NVIDIA Cloud
$ openshell inference set --provider nvidia-nim --model nvidia/nemotron-3-super-120b-a12b
```

The change takes effect immediately.
No sandbox restart is needed.

## `default`

The `default` profile uses NVIDIA cloud inference at `https://integrate.api.nvidia.com/v1` with `nvidia/nemotron-3-super-120b-a12b`.
Use this profile for the standard build.nvidia.com path.

Get an API key from [build.nvidia.com](https://build.nvidia.com).
The `nemoclawd onboard` command prompts for this key and stores the selected endpoint, model, credential environment variable, and profile in `~/.nemoclawd/config.json`.

## `ncp`

The `ncp` profile uses NVIDIA Cloud Partner capacity.
It requires an endpoint URL and `NVIDIA_API_KEY`.

## `nim-local`

The `nim-local` profile targets an OpenAI-compatible NIM service at `http://nim-service.local:8000/v1`.
It requires `NIM_API_KEY` when the service enforces authentication.
The blueprint includes a `nim_service` policy addition for `nim-service.local:8000`.

## `vllm`

The `vllm` profile targets an OpenAI-compatible vLLM endpoint at `http://localhost:8000/v1`.
It uses `OPENAI_API_KEY` and defaults to `dummy` for local development endpoints that do not require authentication.
