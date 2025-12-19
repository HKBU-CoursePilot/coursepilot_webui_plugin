"""
CoursePilot API - Main FastAPI Application.

Central entry point for the REST API that serves the SvelteKit frontend.
"""

import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.getcwd()
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from managers.config_manager import ConfigManager
from utils.logger_util import Logger

from plugins.coursepilot_webui_plugin.api.routes import health, courses, chat

logger = Logger(name="CoursePilotAPI")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    logger.info("CoursePilot API starting up...")
    yield
    logger.info("CoursePilot API shutting down...")


# Create FastAPI app
app = FastAPI(
    title="CoursePilot API",
    description="Educational AI assistant API for HKBU courses",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS
cm = ConfigManager()
config = cm.config.coursepilot_webui_plugin
api_config = config.dict_get("api", {})
cors_origins = api_config.get("cors_origins", ["http://localhost:5173"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(courses.router, prefix="/api", tags=["courses"])
app.include_router(chat.router, prefix="/api", tags=["chat"])


# Serve static files in production
frontend_config = config.dict_get("frontend", {})
if frontend_config.get("mode") == "production":
    build_dir = Path(__file__).parent.parent / frontend_config.get("build_dir", "frontend/build")
    if build_dir.exists():
        app.mount("/", StaticFiles(directory=build_dir, html=True), name="static")
        logger.info(f"Serving static files from {build_dir}")


@app.get("/")
async def root():
    """Root endpoint - API info."""
    return {
        "name": "CoursePilot API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/api/health",
    }
