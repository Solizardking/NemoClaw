# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Backward-compatible console module for adapter imports."""

from . import DiffFormatter, DiffStats, RICH_AVAILABLE, RalphConsole

__all__ = ["DiffFormatter", "DiffStats", "RICH_AVAILABLE", "RalphConsole"]
