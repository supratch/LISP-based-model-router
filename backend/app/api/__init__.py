#!/usr/bin/env python3
"""
API Module for AI Workload Routing System
Provides REST endpoints and monitoring services.
"""

from .routes import router
from .monitoring import MonitoringService

__all__ = ["router", "MonitoringService"]