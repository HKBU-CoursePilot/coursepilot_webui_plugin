"""
Lifecycle hooks for coursepilot_webui_plugin.

Called by: ./adhd_framework.py refresh

Manages:
- Node.js dependency checking
- npm install for frontend
- Production builds
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.getcwd()
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils.logger_util import Logger

FRONTEND_DIR = Path(__file__).parent / "frontend"
MIN_NODE_VERSION = 18

logger = Logger(name="coursepilot_webui_plugin.refresh")


def refresh() -> None:
    """Called during adhd_framework.py refresh."""
    logger.info("Refreshing coursepilot_webui_plugin...")

    # Check if frontend directory exists
    if not FRONTEND_DIR.exists():
        logger.warning(
            f"Frontend directory not found at {FRONTEND_DIR}. "
            "Run 'npm create svelte@latest frontend' in the plugin directory."
        )
        return

    # 1. Check Node.js is available
    if not _check_node_installed():
        logger.warning(
            "Node.js not found or version < 18. "
            "Frontend features will not be available."
        )
        return

    # 2. Install npm dependencies if needed
    if not (FRONTEND_DIR / "node_modules").exists():
        logger.info("Installing frontend dependencies...")
        _npm_install()
    else:
        logger.debug("Frontend dependencies already installed.")


def _check_node_installed() -> bool:
    """Verify Node.js >= 18 is available."""
    node_path = shutil.which("node")
    if not node_path:
        return False

    try:
        result = subprocess.run(
            ["node", "--version"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            return False

        # Parse version (e.g., "v20.10.0" -> 20)
        version_str = result.stdout.strip().lstrip("v")
        major_version = int(version_str.split(".")[0])

        if major_version < MIN_NODE_VERSION:
            logger.warning(
                f"Node.js version {version_str} is below minimum {MIN_NODE_VERSION}"
            )
            return False

        logger.debug(f"Node.js version: {version_str}")
        return True

    except (subprocess.SubprocessError, ValueError) as e:
        logger.error(f"Error checking Node.js version: {e}")
        return False


def _npm_install() -> bool:
    """Install frontend dependencies."""
    try:
        subprocess.run(
            ["npm", "install"],
            cwd=FRONTEND_DIR,
            check=True,
            capture_output=True,
        )
        logger.info("Frontend dependencies installed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"npm install failed: {e.stderr.decode() if e.stderr else e}")
        return False


def _npm_build() -> bool:
    """Build SvelteKit for production."""
    try:
        subprocess.run(
            ["npm", "run", "build"],
            cwd=FRONTEND_DIR,
            check=True,
            capture_output=True,
        )
        logger.info("Frontend build completed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"npm build failed: {e.stderr.decode() if e.stderr else e}")
        return False


if __name__ == "__main__":
    refresh()
