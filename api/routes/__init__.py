"""
CoursePilot API Routes Package.
"""

import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.getcwd()
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from plugins.coursepilot_webui_plugin.api.routes import health, courses, chat

__all__ = ["health", "courses", "chat"]
