#!/usr/bin/env sh
# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

set -eu

OPERATOR_HOME="${OPENCLAWD_OPERATOR_HOME:-/opt/clawd-operator}"
OPERATOR_WORKDIR="${CLAWD_OPERATOR_WORKDIR:-/sandbox}"

if [ -n "${PYTHONPATH:-}" ]; then
  export PYTHONPATH="${OPERATOR_HOME}/src:${PYTHONPATH}"
else
  export PYTHONPATH="${OPERATOR_HOME}/src"
fi

export OPENCLAWD_OPERATOR_HOME="${OPERATOR_HOME}"
export PYTHONUNBUFFERED="${PYTHONUNBUFFERED:-1}"

if [ -x "${OPERATOR_HOME}/.venv/bin/python" ]; then
  PYTHON="${OPERATOR_HOME}/.venv/bin/python"
else
  PYTHON="${PYTHON:-python3}"
fi

cd "${OPERATOR_WORKDIR}"
exec "${PYTHON}" -m ralph_orchestrator "$@"
