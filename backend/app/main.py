#!/usr/bin/env python3
"""
AI Workload Routing System - Main Application
Provides LISP and DNS-based routing for AI workloads with enterprise features.
"""

import logging
import structlog
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn

from app.api.routes import router as api_router
from app.routing.lisp_router import LISPRouter
from app.routing.dns_router import DNSRouter
from app.models.llm_router import LLMRouter
from app.api.monitoring import MonitoringService

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Global services
lisp_router = None
dns_router = None
llm_router = None
monitoring_service = None
security = HTTPBearer()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup/shutdown events."""
    global lisp_router, dns_router, llm_router, monitoring_service
    
    # Startup
    logger.info("Starting AI Workload Routing System")
    
    try:
        # Initialize routing components
        lisp_router = LISPRouter()
        dns_router = DNSRouter()
        llm_router = LLMRouter()
        monitoring_service = MonitoringService()
        
        await lisp_router.initialize()
        await dns_router.initialize()
        await llm_router.initialize()
        
        logger.info("All routing services initialized successfully")
        
        yield
        
    except Exception as e:
        logger.error("Failed to initialize services", error=str(e))
        raise
    finally:
        # Shutdown
        logger.info("Shutting down AI Workload Routing System")
        
        if lisp_router:
            await lisp_router.cleanup()
        if dns_router:
            await dns_router.cleanup()
        if llm_router:
            await llm_router.cleanup()


# Create FastAPI application
app = FastAPI(
    title="AI Workload Routing System",
    description="Enterprise LISP and DNS-based routing for AI workloads",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS for enterprise environment
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://your-domain.com"],  # Configure for your environment
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # Added OPTIONS for preflight
    allow_headers=["*"],
)


async def verify_token(request: Request):
    """Verify JWT token for API authentication.

    Skip authentication for OPTIONS requests (CORS preflight).
    """
    # Allow OPTIONS requests without authentication (CORS preflight)
    if request.method == "OPTIONS":
        return None

    # Check for Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract token
    token = auth_header.replace("Bearer ", "")

    # In production, implement proper JWT verification
    # For now, accept any bearer token
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return token


# Include API routes
app.include_router(api_router, prefix="/api/v1", dependencies=[Depends(verify_token)])


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main application page."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>AI Workload Routing System</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
    </head>
    <body>
        <h1>AI Workload Routing System</h1>
        <p>Enterprise LISP and DNS-based routing for AI workloads</p>
        <p><a href="/docs">API Documentation</a></p>
        <p><a href="/api/v1/health">Health Check</a> (requires authentication)</p>
    </body>
    </html>
    """


@app.get("/health")
async def health_check():
    """Public health check endpoint."""
    return {
        "status": "healthy",
        "service": "AI Workload Routing System",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )