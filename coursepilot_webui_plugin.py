"""
CoursePilot WebUI Plugin - Main Entry Point.

Provides functions to start the API server and development environment.
"""

import os
import sys
import asyncio
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.getcwd()
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from managers.config_manager import ConfigManager
from utils.logger_util import Logger

if TYPE_CHECKING:
    from fastapi import FastAPI

logger = Logger(name="CoursePilotWebUI")

FRONTEND_DIR = Path(__file__).parent / "frontend"


def get_app() -> "FastAPI":
    """
    Get the FastAPI application instance.

    Returns:
        The configured FastAPI app
    """
    from plugins.coursepilot_webui_plugin.api.main import app

    return app


def start_api(host: str | None = None, port: int | None = None) -> None:
    """
    Start the FastAPI server.

    Args:
        host: Override host from config
        port: Override port from config
    """
    import uvicorn

    cm = ConfigManager()
    config = cm.config.coursepilot_webui_plugin

    api_config = config.api
    final_host = host or api_config.host
    final_port = port or api_config.port

    logger.info(f"Starting CoursePilot API at http://{final_host}:{final_port}")

    uvicorn.run(
        "plugins.coursepilot_webui_plugin.api.main:app",
        host=final_host,
        port=final_port,
        reload=True,
        log_level="info",
    )


def start_frontend() -> subprocess.Popen | None:
    """
    Start the SvelteKit development server.

    Returns:
        The subprocess handle, or None if frontend not available
    """
    if not FRONTEND_DIR.exists():
        logger.warning("Frontend directory not found. Skipping frontend start.")
        return None

    if not (FRONTEND_DIR / "node_modules").exists():
        logger.warning("Frontend dependencies not installed. Run 'adhd_framework.py refresh'.")
        return None

    cm = ConfigManager()
    config = cm.config.coursepilot_webui_plugin
    frontend_config = config.dict_get("frontend", {})
    dev_port = frontend_config.get("dev_port", 5173)

    logger.info(f"Starting SvelteKit dev server at http://localhost:{dev_port}")

    process = subprocess.Popen(
        ["npm", "run", "dev", "--", "--port", str(dev_port)],
        cwd=FRONTEND_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    return process


def start_dev() -> None:
    """
    Start both the API server and frontend development server.

    This is the main entry point for development.
    """
    import signal
    import threading

    frontend_process = start_frontend()

    def cleanup(signum, frame):
        """Clean up frontend process on exit."""
        if frontend_process:
            logger.info("Shutting down frontend server...")
            frontend_process.terminate()
            frontend_process.wait()
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    # Start API (blocking)
    start_api()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="CoursePilot WebUI Plugin")
    parser.add_argument(
        "--api-only",
        action="store_true",
        help="Start only the API server (no frontend)",
    )
    parser.add_argument("--host", help="API host override")
    parser.add_argument("--port", type=int, help="API port override")

    args = parser.parse_args()

    if args.api_only:
        start_api(host=args.host, port=args.port)
    else:
        start_dev()
