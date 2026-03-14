#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""
Migration snapshot/restore logic for moving host OpenClaw into OpenShell sandbox.

Handles:
  - Snapshot: capture ~/.openclaw config, workspace, extensions, skills
  - Restore: push snapshot contents into sandbox filesystem
  - Cutover: rename host config to archived, point OpenClaw at sandbox
  - Rollback: restore host config from snapshot
"""

import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path


HOME = Path.home()
OPENCLAW_DIR = HOME / ".openclaw"
OPENSHELL_PLUGIN_DIR = HOME / ".openshell-plugin"
SNAPSHOTS_DIR = OPENSHELL_PLUGIN_DIR / "snapshots"


def create_snapshot() -> Path | None:
    """Snapshot the current host OpenClaw configuration."""
    if not OPENCLAW_DIR.exists():
        return None

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    snapshot_dir = SNAPSHOTS_DIR / timestamp
    snapshot_dir.mkdir(parents=True, exist_ok=True)

    # Copy the entire ~/.openclaw directory
    dest = snapshot_dir / "openclaw"
    shutil.copytree(OPENCLAW_DIR, dest, dirs_exist_ok=True)

    # Write manifest
    contents = [str(p.relative_to(dest)) for p in dest.rglob("*") if p.is_file()]
    manifest = {
        "timestamp": timestamp,
        "source": str(OPENCLAW_DIR),
        "file_count": len(contents),
        "contents": contents,
    }
    (snapshot_dir / "snapshot.json").write_text(json.dumps(manifest, indent=2))

    return snapshot_dir


def restore_into_sandbox(snapshot_dir: Path, sandbox_name: str = "openclaw") -> bool:
    """Push snapshot contents into a running OpenShell sandbox."""
    source = snapshot_dir / "openclaw"
    if not source.exists():
        return False

    # Use openshell sandbox cp to push files
    # Target path inside sandbox: /sandbox/.openclaw
    result = subprocess.run(
        ["openshell", "sandbox", "cp", str(source), f"{sandbox_name}:/sandbox/.openclaw"],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def cutover_host(snapshot_dir: Path) -> bool:
    """Archive host ~/.openclaw and mark migration as complete."""
    if not OPENCLAW_DIR.exists():
        return True  # Nothing to archive

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    archive_path = OPENCLAW_DIR.parent / f".openclaw.pre-openshell-plugin.{timestamp}"

    try:
        shutil.move(str(OPENCLAW_DIR), str(archive_path))
        return True
    except OSError:
        return False


def rollback_from_snapshot(snapshot_dir: Path) -> bool:
    """Restore host ~/.openclaw from a snapshot."""
    source = snapshot_dir / "openclaw"
    if not source.exists():
        return False

    # Remove current config if it exists
    if OPENCLAW_DIR.exists():
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        archive_path = OPENCLAW_DIR.parent / f".openclaw.openshell-plugin-archived.{timestamp}"
        shutil.move(str(OPENCLAW_DIR), str(archive_path))

    # Restore from snapshot
    shutil.copytree(source, OPENCLAW_DIR)
    return True


def list_snapshots() -> list[dict]:
    """List all available snapshots."""
    if not SNAPSHOTS_DIR.exists():
        return []

    snapshots = []
    for snap_dir in sorted(SNAPSHOTS_DIR.iterdir(), reverse=True):
        manifest_file = snap_dir / "snapshot.json"
        if manifest_file.exists():
            manifest = json.loads(manifest_file.read_text())
            manifest["path"] = str(snap_dir)
            snapshots.append(manifest)

    return snapshots
