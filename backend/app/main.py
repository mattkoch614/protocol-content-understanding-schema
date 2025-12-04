"""
FastAPI application entry point for the Content Understanding POC.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.config import settings
from app.middleware import LoggingMiddleware

# Configure logging to show INFO level and above in console
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    # Startup
    logger.info("🚀 Starting Content Understanding API...")
    logger.info(f"Environment: {settings.PROJECT_NAME}")
    logger.info(f"CORS Origins: {settings.ALLOWED_ORIGINS}")

    yield

    # Shutdown
    logger.info("👋 Shutting down Content Understanding API...")


app = FastAPI(
    title="Content Understanding API",
    description="API for extracting structured data from clinical trial protocol documents",
    version="0.1.0",
    lifespan=lifespan,
)

# Add logging middleware (first, to log all requests)
app.add_middleware(LoggingMiddleware)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Content Understanding API",
        "version": "0.1.0",
        "docs": "/docs",
    }
