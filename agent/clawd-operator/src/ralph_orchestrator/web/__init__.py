# ABOUTME: Web UI module for OpenClawd Operator monitoring and control
# ABOUTME: Provides real-time dashboard for agent execution and system metrics

"""Web UI module for OpenClawd Operator monitoring."""

import os
from pathlib import Path


def _load_local_env() -> None:
    """Load a local .env file before importing web modules with env-backed config."""
    env_path = Path.cwd() / ".env"
    if not env_path.exists():
        return

    for line in env_path.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        if not key or key in os.environ:
            continue
        os.environ[key] = value.strip().strip('"').strip("'")


_load_local_env()

from .server import WebMonitor

__all__ = ['WebMonitor']
