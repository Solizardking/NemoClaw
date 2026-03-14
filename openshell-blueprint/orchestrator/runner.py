#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""
OpenShell Plugin Blueprint Runner

Orchestrates OpenClaw sandbox lifecycle inside OpenShell.
Called by the thin TS plugin via subprocess.

Protocol:
  - stdout lines starting with PROGRESS:<0-100>:<label> are parsed as progress updates
  - stdout line RUN_ID:<id> reports the run identifier
  - exit code 0 = success, non-zero = failure
"""

import argparse
import json
import os
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

import yaml


def log(msg: str) -> None:
    print(msg, flush=True)


def progress(pct: int, label: str) -> None:
    print(f"PROGRESS:{pct}:{label}", flush=True)


def run_id() -> str:
    rid = f"nc-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"
    print(f"RUN_ID:{rid}", flush=True)
    return rid


def load_blueprint() -> dict:
    blueprint_path = Path(os.environ.get("OPENSHELL_PLUGIN_BLUEPRINT_PATH", "."))
    bp_file = blueprint_path / "blueprint.yaml"
    if not bp_file.exists():
        log(f"ERROR: blueprint.yaml not found at {bp_file}")
        sys.exit(1)
    with open(bp_file) as f:
        return yaml.safe_load(f)


def shell(cmd: str, check: bool = True, capture: bool = False) -> subprocess.CompletedProcess:
    """Run a shell command, optionally capturing output."""
    return subprocess.run(
        cmd,
        shell=True,
        check=check,
        capture_output=capture,
        text=True,
    )


def openshell_available() -> bool:
    """Check if openshell CLI is available."""
    result = shell("which openshell", check=False, capture=True)
    return result.returncode == 0


# ---------------------------------------------------------------------------
# Actions
# ---------------------------------------------------------------------------


def action_plan(profile: str, blueprint: dict, dry_run: bool = False) -> dict:
    """Plan the deployment: validate inputs, resolve profile, check prerequisites."""
    rid = run_id()
    progress(10, "Validating blueprint")

    inference_profiles = blueprint.get("components", {}).get("inference", {}).get("profiles", {})
    if profile not in inference_profiles:
        available = ", ".join(inference_profiles.keys())
        log(f"ERROR: Profile '{profile}' not found. Available: {available}")
        sys.exit(1)

    progress(20, "Checking prerequisites")
    if not openshell_available():
        log("ERROR: openshell CLI not found. Install OpenShell first.")
        log("  See: https://github.com/NVIDIA/OpenShell")
        sys.exit(1)

    sandbox_cfg = blueprint.get("components", {}).get("sandbox", {})
    inference_cfg = inference_profiles[profile]

    plan = {
        "run_id": rid,
        "profile": profile,
        "sandbox": {
            "image": sandbox_cfg.get("image", "openclaw"),
            "name": sandbox_cfg.get("name", "openclaw"),
            "forward_ports": sandbox_cfg.get("forward_ports", [18789]),
        },
        "inference": {
            "provider_type": inference_cfg.get("provider_type"),
            "provider_name": inference_cfg.get("provider_name"),
            "endpoint": inference_cfg.get("endpoint"),
            "model": inference_cfg.get("model"),
            "credential_env": inference_cfg.get("credential_env"),
        },
        "policy_additions": blueprint.get("components", {}).get("policy", {}).get("additions", {}),
        "dry_run": dry_run,
    }

    progress(100, "Plan complete")
    log(json.dumps(plan, indent=2))
    return plan


def action_apply(profile: str, blueprint: dict, plan_path: str | None = None) -> None:
    """Apply the plan: create sandbox, configure provider, set inference route."""
    rid = run_id()

    # Load plan if provided, otherwise generate one
    if plan_path:
        # In a real implementation, load the saved plan
        pass

    inference_profiles = blueprint.get("components", {}).get("inference", {}).get("profiles", {})
    inference_cfg = inference_profiles.get(profile, {})
    sandbox_cfg = blueprint.get("components", {}).get("sandbox", {})

    sandbox_name = sandbox_cfg.get("name", "openclaw")
    sandbox_image = sandbox_cfg.get("image", "openclaw")
    forward_ports = sandbox_cfg.get("forward_ports", [18789])

    # Step 1: Create sandbox
    progress(20, "Creating OpenClaw sandbox")
    port_flags = " ".join(f"--forward {p}" for p in forward_ports)
    result = shell(
        f"openshell sandbox create --from {sandbox_image} --name {sandbox_name} {port_flags}",
        check=False,
        capture=True,
    )
    if result.returncode != 0:
        if "already exists" in (result.stderr or ""):
            log(f"Sandbox '{sandbox_name}' already exists, reusing.")
        else:
            log(f"ERROR: Failed to create sandbox: {result.stderr}")
            sys.exit(1)

    # Step 2: Configure inference provider
    progress(50, "Configuring inference provider")
    provider_name = inference_cfg.get("provider_name", "default")
    provider_type = inference_cfg.get("provider_type", "openai")
    endpoint = inference_cfg.get("endpoint", "")
    model = inference_cfg.get("model", "")

    # Resolve credential
    credential_env = inference_cfg.get("credential_env")
    credential_default = inference_cfg.get("credential_default", "")
    credential = ""
    if credential_env:
        credential = os.environ.get(credential_env, credential_default)

    credential_flag = ""
    if credential:
        credential_flag = f"--credential OPENAI_API_KEY={credential}"

    config_flag = ""
    if endpoint:
        config_flag = f"--config OPENAI_BASE_URL={endpoint}"

    shell(
        f"openshell provider create --name {provider_name} --type {provider_type} "
        f"{credential_flag} {config_flag}",
        check=False,
        capture=True,
    )

    # Step 3: Set inference route
    progress(70, "Setting inference route")
    shell(
        f"openshell inference set --provider {provider_name} --model {model}",
        check=False,
        capture=True,
    )

    # Step 4: Save run state
    progress(85, "Saving run state")
    state_dir = Path.home() / ".openshell-plugin" / "state" / "runs" / rid
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "plan.json").write_text(json.dumps({
        "run_id": rid,
        "profile": profile,
        "sandbox_name": sandbox_name,
        "inference": inference_cfg,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }, indent=2))

    progress(100, "Apply complete")
    log(f"Sandbox '{sandbox_name}' is ready.")
    log(f"Inference: {provider_name} -> {model} @ {endpoint}")


def action_status(rid: str | None = None) -> None:
    """Report current state of the most recent (or specified) run."""
    run_id()
    state_dir = Path.home() / ".openshell-plugin" / "state" / "runs"

    if rid:
        run_dir = state_dir / rid
    else:
        # Find most recent run
        if not state_dir.exists():
            log("No runs found.")
            sys.exit(0)
        runs = sorted(state_dir.iterdir(), reverse=True)
        if not runs:
            log("No runs found.")
            sys.exit(0)
        run_dir = runs[0]

    plan_file = run_dir / "plan.json"
    if plan_file.exists():
        log(plan_file.read_text())
    else:
        log(json.dumps({"run_id": run_dir.name, "status": "unknown"}))


def action_rollback(rid: str) -> None:
    """Rollback a specific run: stop sandbox, remove provider config."""
    run_id()

    state_dir = Path.home() / ".openshell-plugin" / "state" / "runs" / rid
    if not state_dir.exists():
        log(f"ERROR: Run {rid} not found.")
        sys.exit(1)

    plan_file = state_dir / "plan.json"
    if plan_file.exists():
        plan = json.loads(plan_file.read_text())
        sandbox_name = plan.get("sandbox_name", "openclaw")

        progress(30, f"Stopping sandbox {sandbox_name}")
        shell(f"openshell sandbox stop {sandbox_name}", check=False, capture=True)

        progress(60, f"Removing sandbox {sandbox_name}")
        shell(f"openshell sandbox remove {sandbox_name}", check=False, capture=True)

    progress(90, "Cleaning up run state")
    # Mark run as rolled back
    (state_dir / "rolled_back").write_text(datetime.now(timezone.utc).isoformat())

    progress(100, "Rollback complete")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="OpenShell Plugin Blueprint Runner")
    parser.add_argument("action", choices=["plan", "apply", "status", "rollback"])
    parser.add_argument("--profile", default="default")
    parser.add_argument("--plan", dest="plan_path")
    parser.add_argument("--run-id", dest="run_id")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--dry-run", action="store_true")

    args = parser.parse_args()
    blueprint = load_blueprint()

    if args.action == "plan":
        action_plan(args.profile, blueprint, dry_run=args.dry_run)
    elif args.action == "apply":
        action_apply(args.profile, blueprint, plan_path=args.plan_path)
    elif args.action == "status":
        action_status(rid=args.run_id)
    elif args.action == "rollback":
        if not args.run_id:
            log("ERROR: --run-id is required for rollback")
            sys.exit(1)
        action_rollback(args.run_id)


if __name__ == "__main__":
    main()
