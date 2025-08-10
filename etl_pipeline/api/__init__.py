"""
FastAPI module for Strategic Narrative Intelligence ETL Pipeline

This module provides REST API endpoints for pipeline management,
monitoring, and data access.
"""

from .main import app, create_app

__all__ = ["app", "create_app"]
