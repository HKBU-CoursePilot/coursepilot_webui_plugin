"""
Health check endpoint.

Simple endpoint for liveness/readiness probes and API status.
"""

import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.getcwd()
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from datetime import datetime, timezone

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Health check endpoint.

    Returns:
        Health status with timestamp
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "coursepilot-api",
        "version": "0.1.0",
    }


@router.get("/health/ready")
async def readiness_check():
    """
    Readiness check - verifies dependencies are available.

    Returns:
        Readiness status with dependency checks
    """
    checks = {
        "llm_gateway": False,
        "moodle_adapter": False,
    }

    # Check LLM Gateway
    try:
        from managers.llm_gateway_manager import LLMGatewayManager

        gateway = LLMGatewayManager()
        checks["llm_gateway"] = True
    except Exception:
        pass

    # Check Moodle Adapter
    try:
        from plugins.moodle_adapter_plugin import get_adapter

        adapter = get_adapter()
        checks["moodle_adapter"] = True
    except Exception:
        pass

    all_ready = all(checks.values())

    return {
        "status": "ready" if all_ready else "degraded",
        "checks": checks,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
