# ABOUTME: Entry point for running the OpenClawd Operator web monitoring server
# ABOUTME: Enables execution with `python -m ralph_orchestrator.web`

"""Entry point for the OpenClawd Operator web monitoring server."""

import argparse
import logging
import os
from pathlib import Path


def _load_local_env() -> None:
    """Load a local .env file before importing modules that read env vars at import time."""
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

logger = logging.getLogger(__name__)


def main():
    """Main entry point for the web monitoring server."""
    parser = argparse.ArgumentParser(
        description="OpenClawd Operator Web Monitoring Dashboard"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port to run the web server on (default: 8080)"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host to bind the server to (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--no-auth",
        action="store_true",
        help="Disable authentication (not recommended for production)"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set logging level (default: INFO)"
    )
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and run the web monitor
    monitor = WebMonitor(
        port=args.port,
        host=args.host,
        enable_auth=not args.no_auth
    )
    
    logger.info(f"Starting OpenClawd Operator Web Monitor on {args.host}:{args.port}")
    if args.no_auth:
        logger.warning("Authentication is disabled - not recommended for production")
    else:
        password_hint = os.getenv("RALPH_WEB_PASSWORD", "admin123")
        logger.info("Authentication enabled - username: admin, password from env/default: %s", password_hint)
    
    try:
        monitor.run()
    except KeyboardInterrupt:
        logger.info("Web monitor stopped by user")
    except Exception as e:
        logger.error(f"Web monitor error: {e}", exc_info=True)


if __name__ == "__main__":
    main()
