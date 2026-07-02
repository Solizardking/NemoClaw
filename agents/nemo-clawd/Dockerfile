# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Nemo Clawd sandbox image.
#
# This is a thin derivative of the Hermes sandbox image. Build orchestration
# must pass a resolved Hermes final-image reference through BASE_IMAGE; this
# file only layers the clawd MCP server and Python blueprint/orchestrator.

ARG BASE_IMAGE

# hadolint ignore=DL3006
FROM ${BASE_IMAGE}

RUN set -eu; \
    hermes_path="$(command -v hermes 2>/dev/null || true)"; \
    if [ "$hermes_path" != "/usr/local/bin/hermes" ]; then \
        echo "ERROR: expected hermes at /usr/local/bin/hermes, got ${hermes_path:-missing}" >&2; \
        exit 1; \
    fi; \
    test -x /usr/local/bin/hermes; \
    /usr/local/bin/hermes --version; \
    node --version; \
    npm --version; \
    python3 --version

COPY nemo-clawd-mcp/package.json nemo-clawd-mcp/package-lock.json /opt/nemo-clawd-mcp/
COPY nemo-clawd-mcp/tsconfig.json /opt/nemo-clawd-mcp/tsconfig.json
COPY nemo-clawd-mcp/src/ /opt/nemo-clawd-mcp/src/
WORKDIR /opt/nemo-clawd-mcp
RUN npm ci --ignore-scripts --no-audit --no-fund \
    && npm run build \
    && npm prune --omit=dev --ignore-scripts --no-audit --no-fund

COPY nemo-clawd-mcp/README.md /opt/nemo-clawd-mcp/README.md
COPY nemo-clawd-python/ /opt/nemo-clawd-python/
COPY agents/nemo-clawd/manifest.yaml /opt/nemoclaw-agents/nemo-clawd/manifest.yaml
COPY agents/nemo-clawd/policy-additions.yaml /opt/nemoclaw-agents/nemo-clawd/policy-additions.yaml
COPY agents/nemo-clawd/start-mcp.sh /usr/local/bin/nemo-clawd-mcp

RUN set -eu; \
    chmod 755 /usr/local/bin/nemo-clawd-mcp; \
    chmod -R a+rX /opt/nemo-clawd-mcp /opt/nemo-clawd-python /opt/nemoclaw-agents/nemo-clawd; \
    python3 -m py_compile \
        /opt/nemo-clawd-python/orchestrator/runner.py \
        /opt/nemo-clawd-python/migrations/snapshot.py; \
    node -e "import('/opt/nemo-clawd-mcp/dist/index.js').then((m) => { if (!Array.isArray(m.TOOLS) || m.TOOLS.length !== 31) throw new Error('expected 31 MCP tools'); })"

ENV NEMOCLAW_AGENT=nemo-clawd \
    NEMOCLAW_BLUEPRINT_PATH=/opt/nemo-clawd-python \
    NEMO_CLAWD_MCP_SERVER=/usr/local/bin/nemo-clawd-mcp \
    NEMO_CLAWD_MCP_PACKAGE_DIR=/opt/nemo-clawd-mcp

WORKDIR /sandbox
