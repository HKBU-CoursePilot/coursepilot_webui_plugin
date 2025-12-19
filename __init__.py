"""
CoursePilot WebUI Plugin.

Provides a FastAPI backend and SvelteKit frontend for the CoursePilot
educational assistant.

Usage:
    from plugins.coursepilot_webui_plugin import start_api, start_dev

    # Start API server only
    start_api()

    # Start both API and frontend dev servers
    start_dev()
"""

import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.getcwd()
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from plugins.coursepilot_webui_plugin.coursepilot_webui_plugin import (
    start_api,
    start_dev,
    get_app,
)

__all__ = ["start_api", "start_dev", "get_app"]
