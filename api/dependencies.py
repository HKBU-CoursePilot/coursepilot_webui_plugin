"""
Dependency injection for FastAPI routes.

Provides manager instances and configuration to route handlers.
"""

import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.getcwd()
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from managers.config_manager import ConfigManager
from managers.llm_gateway_manager import LLMGatewayManager
from plugins.moodle_adapter_plugin import get_adapter
from plugins.moodle_adapter_plugin.moodle_port import IMoodlePort


@lru_cache
def get_config() -> ConfigManager:
    """Get the config manager singleton."""
    return ConfigManager()


@lru_cache
def get_llm_gateway() -> LLMGatewayManager:
    """Get the LLM gateway singleton."""
    return LLMGatewayManager()


def get_moodle_adapter() -> IMoodlePort:
    """Get the Moodle adapter based on config."""
    return get_adapter()


# Type aliases for dependency injection
ConfigDep = Annotated[ConfigManager, Depends(get_config)]
LLMDep = Annotated[LLMGatewayManager, Depends(get_llm_gateway)]
MoodleDep = Annotated[IMoodlePort, Depends(get_moodle_adapter)]
