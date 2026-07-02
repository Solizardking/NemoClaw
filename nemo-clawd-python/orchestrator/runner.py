#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""
Nemo Clawd Blueprint Runner

Orchestrates Nemo Clawd sandbox lifecycle inside OpenShell.
Called by the thin TS plugin via subprocess.

Protocol:
  - stdout lines starting with PROGRESS:<0-100>:<label> are parsed as progress updates
  - stdout line RUN_ID:<id> reports the run identifier
  - exit code 0 = success, non-zero = failure
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import yaml


def log(msg: str) -> None:
    print(msg, flush=True)


def fail(msg: str) -> None:
    log(f"ERROR: {msg}")
    sys.exit(1)


def progress(pct: int, label: str) -> None:
    print(f"PROGRESS:{pct}:{label}", flush=True)


def emit_run_id() -> str:
    rid = f"nc-{datetime.now(UTC).strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"
    print(f"RUN_ID:{rid}", flush=True)
    return rid


def load_blueprint() -> dict[str, Any]:
    blueprint_path = Path(os.environ.get("NEMOCLAWD_BLUEPRINT_PATH", "."))
    bp_file = blueprint_path / "blueprint.yaml"
    if not bp_file.exists():
        fail(f"blueprint.yaml not found at {bp_file}")
    with bp_file.open() as f:
        blueprint = yaml.safe_load(f)
    if not isinstance(blueprint, dict):
        fail(f"blueprint.yaml at {bp_file} must contain a mapping")
    return blueprint


def load_plan(plan_path: str) -> dict[str, Any]:
    path = Path(plan_path)
    if not path.exists():
        fail(f"plan file not found at {path}")
    try:
        plan = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        fail(f"plan file is not valid JSON: {exc}")
    if not isinstance(plan, dict):
        fail("plan file must contain a JSON object")
    return plan


def resolve_runs_dir() -> Path:
    state_root = Path(os.environ.get("NEMOCLAWD_STATE_DIR", Path.home() / ".nemoclawd" / "state"))
    return state_root / "runs"


def mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        fail(f"{label} must be a mapping")
    return value


def resolve_inference_profiles(blueprint: dict[str, Any]) -> dict[str, Any]:
    components = mapping(blueprint.get("components", {}), "components")
    inference = mapping(components.get("inference", {}), "components.inference")
    return mapping(inference.get("profiles", {}), "components.inference.profiles")


def resolve_inference_config(
    profile: str,
    blueprint: dict[str, Any],
    endpoint_url: str | None,
) -> dict[str, Any]:
    inference_profiles = resolve_inference_profiles(blueprint)
    if profile not in inference_profiles:
        available = ", ".join(inference_profiles.keys())
        fail(f"Profile '{profile}' not found. Available: {available}")

    inference_cfg = mapping(inference_profiles[profile], f"inference profile '{profile}'")
    if endpoint_url:
        inference_cfg = {**inference_cfg, "endpoint": validate_endpoint_url(endpoint_url)}
    return inference_cfg


def validate_endpoint_url(endpoint_url: str) -> str:
    endpoint_url = endpoint_url.strip()
    parsed = urlparse(endpoint_url)
    if parsed.scheme not in {"http", "https"}:
        fail("--endpoint-url must use http:// or https://")
    if not parsed.hostname:
        fail("--endpoint-url must include a host")
    if parsed.username or parsed.password:
        fail("--endpoint-url must not include credentials")
    if parsed.fragment:
        fail("--endpoint-url must not include a URL fragment")
    return endpoint_url


def validate_sandbox_name(name: Any) -> str:
    if not isinstance(name, str) or not name.strip():
        fail("sandbox.name must be a non-empty string")
    if any(char.isspace() for char in name):
        fail(f"sandbox.name must not contain whitespace: {name!r}")
    return name


def validate_sandbox_image(image: Any) -> str:
    if not isinstance(image, str) or not image.strip():
        fail("sandbox.image must be a non-empty string")
    if any(char.isspace() for char in image):
        fail(f"sandbox.image must not contain whitespace: {image!r}")
    return image


def validate_forward_ports(ports: Any) -> list[int]:
    if ports is None:
        return [18789]
    if not isinstance(ports, list):
        fail("sandbox.forward_ports must be a list")
    validated: list[int] = []
    for port in ports:
        if not isinstance(port, int) or port < 1024 or port > 65535:
            fail(f"sandbox.forward_ports entries must be integers between 1024 and 65535: {port!r}")
        validated.append(port)
    return validated


def run_cmd(
    args: list[str],
    *,
    check: bool = True,
    capture: bool = False,
) -> subprocess.CompletedProcess[str]:
    """Run a command as an argv list (never shell=True)."""
    return subprocess.run(
        args,
        check=check,
        capture_output=capture,
        text=True,
    )


def openshell_available() -> bool:
    """Check if openshell CLI is available."""
    return shutil.which("openshell") is not None


# ---------------------------------------------------------------------------
# Actions
# ---------------------------------------------------------------------------


def action_plan(
    profile: str,
    blueprint: dict[str, Any],
    *,
    dry_run: bool = False,
    endpoint_url: str | None = None,
) -> dict[str, Any]:
    """Plan the deployment: validate inputs, resolve profile, check prerequisites."""
    rid = emit_run_id()
    progress(10, "Validating blueprint")

    inference_cfg = resolve_inference_config(profile, blueprint, endpoint_url)

    progress(20, "Checking prerequisites")
    if not openshell_available():
        log("  See: https://github.com/NVIDIA/OpenShell")
        fail("openshell CLI not found. Install OpenShell first.")

    components = mapping(blueprint.get("components", {}), "components")
    sandbox_cfg = mapping(components.get("sandbox", {}), "components.sandbox")
    sandbox_image = validate_sandbox_image(sandbox_cfg.get("image", "nemoclawd"))
    sandbox_name = validate_sandbox_name(sandbox_cfg.get("name", "nemoclawd"))
    forward_ports = validate_forward_ports(sandbox_cfg.get("forward_ports", [18789]))

    plan: dict[str, Any] = {
        "run_id": rid,
        "profile": profile,
        "sandbox": {
            "image": sandbox_image,
            "name": sandbox_name,
            "forward_ports": forward_ports,
        },
        "inference": {
            "provider_type": inference_cfg.get("provider_type"),
            "provider_name": inference_cfg.get("provider_name"),
            "endpoint": inference_cfg.get("endpoint"),
            "model": inference_cfg.get("model"),
            "credential_env": inference_cfg.get("credential_env"),
        },
        "policy_additions": (
            blueprint.get("components", {}).get("policy", {}).get("additions", {})
        ),
        "dry_run": dry_run,
    }

    progress(100, "Plan complete")
    log(json.dumps(plan, indent=2))
    return plan


def action_apply(
    profile: str,
    blueprint: dict[str, Any],
    plan_path: str | None = None,
    endpoint_url: str | None = None,
) -> None:
    """Apply the plan: create sandbox, configure provider, set inference route."""
    rid = emit_run_id()

    plan = load_plan(plan_path) if plan_path else None
    inference_cfg = resolve_inference_config(profile, blueprint, endpoint_url)
    components = mapping(blueprint.get("components", {}), "components")
    sandbox_cfg = mapping(components.get("sandbox", {}), "components.sandbox")

    if plan:
        planned_sandbox = mapping(plan.get("sandbox", {}), "plan.sandbox")
        planned_inference = mapping(plan.get("inference", {}), "plan.inference")
        sandbox_name = validate_sandbox_name(planned_sandbox.get("name", "nemoclawd"))
        sandbox_image = validate_sandbox_image(planned_sandbox.get("image", "nemoclawd"))
        forward_ports = validate_forward_ports(planned_sandbox.get("forward_ports", [18789]))
        inference_cfg = planned_inference or inference_cfg
    else:
        sandbox_name = validate_sandbox_name(sandbox_cfg.get("name", "nemoclawd"))
        sandbox_image = validate_sandbox_image(sandbox_cfg.get("image", "nemoclawd"))
        forward_ports = validate_forward_ports(sandbox_cfg.get("forward_ports", [18789]))

    # Step 1: Create sandbox
    progress(20, "Creating Nemo Clawd sandbox")
    create_args = [
        "openshell",
        "sandbox",
        "create",
        "--from",
        sandbox_image,
        "--name",
        sandbox_name,
    ]
    for port in forward_ports:
        create_args.extend(["--forward", str(port)])

    result = run_cmd(create_args, check=False, capture=True)
    if result.returncode != 0:
        if "already exists" in (result.stderr or ""):
            log(f"Sandbox '{sandbox_name}' already exists, reusing.")
        else:
            log(f"ERROR: Failed to create sandbox: {result.stderr}")
            sys.exit(1)

    # Step 2: Configure inference provider
    progress(50, "Configuring inference provider")
    provider_name: str = inference_cfg.get("provider_name", "default")
    provider_type: str = inference_cfg.get("provider_type", "openai")
    endpoint: str = inference_cfg.get("endpoint", "")
    model: str = inference_cfg.get("model", "")

    # Resolve credential from environment
    credential_env = inference_cfg.get("credential_env")
    credential_default: str = inference_cfg.get("credential_default", "")
    credential = ""
    if credential_env:
        credential = os.environ.get(credential_env, credential_default)

    provider_args = [
        "openshell",
        "provider",
        "create",
        "--name",
        provider_name,
        "--type",
        provider_type,
    ]
    if credential:
        provider_args.extend(["--credential", f"OPENAI_API_KEY={credential}"])
    if endpoint:
        provider_args.extend(["--config", f"OPENAI_BASE_URL={endpoint}"])

    run_cmd(provider_args, check=False, capture=True)

    # Step 3: Set inference route
    progress(70, "Setting inference route")
    run_cmd(
        ["openshell", "inference", "set", "--provider", provider_name, "--model", model],
        check=False,
        capture=True,
    )

    # Step 4: Save run state
    progress(85, "Saving run state")
    state_dir = resolve_runs_dir() / rid
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "plan.json").write_text(
        json.dumps(
            {
                "run_id": rid,
                "profile": profile,
                "sandbox_name": sandbox_name,
                "inference": inference_cfg,
                "timestamp": datetime.now(UTC).isoformat(),
            },
            indent=2,
        )
    )

    progress(100, "Apply complete")
    log(f"Sandbox '{sandbox_name}' is ready.")
    log(f"Inference: {provider_name} -> {model} @ {endpoint}")


def action_status(rid: str | None = None) -> None:
    """Report current state of the most recent (or specified) run."""
    emit_run_id()
    state_dir = resolve_runs_dir()

    if rid:
        run_dir = state_dir / rid
    else:
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
    emit_run_id()

    state_dir = resolve_runs_dir() / rid
    if not state_dir.exists():
        fail(f"Run {rid} not found.")

    plan_file = state_dir / "plan.json"
    if plan_file.exists():
        plan = json.loads(plan_file.read_text())
        sandbox_name = plan.get("sandbox_name", "nemoclawd")

        progress(30, f"Stopping sandbox {sandbox_name}")
        run_cmd(
            ["openshell", "sandbox", "stop", sandbox_name],
            check=False,
            capture=True,
        )

        progress(60, f"Removing sandbox {sandbox_name}")
        run_cmd(
            ["openshell", "sandbox", "remove", sandbox_name],
            check=False,
            capture=True,
        )

    progress(90, "Cleaning up run state")
    (state_dir / "rolled_back").write_text(datetime.now(UTC).isoformat())

    progress(100, "Rollback complete")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="Nemo Clawd Blueprint Runner")
    parser.add_argument("action", choices=["plan", "apply", "status", "rollback"])
    parser.add_argument("--profile", default="default")
    parser.add_argument("--plan", dest="plan_path")
    parser.add_argument("--run-id", dest="run_id")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--endpoint-url",
        dest="endpoint_url",
        default=None,
        help="Override endpoint URL for the selected profile",
    )

    args = parser.parse_args()
    blueprint = load_blueprint()

    if args.action == "plan":
        action_plan(args.profile, blueprint, dry_run=args.dry_run, endpoint_url=args.endpoint_url)
    elif args.action == "apply":
        action_apply(
            args.profile, blueprint, plan_path=args.plan_path, endpoint_url=args.endpoint_url
        )
    elif args.action == "status":
        action_status(rid=args.run_id)
    elif args.action == "rollback":
        if not args.run_id:
            fail("--run-id is required for rollback")
        action_rollback(args.run_id)


if __name__ == "__main__":
    main()
