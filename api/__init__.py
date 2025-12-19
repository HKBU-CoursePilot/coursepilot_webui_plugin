"""
CoursePilot API Package.

FastAPI backend for the CoursePilot educational assistant.
"""

import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.getcwd()
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from plugins.coursepilot_webui_plugin.api.main import app

__all__ = ["app"]
