"""FastAPI application entry point for SentinelVision."""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.core.config import settings
from app.core.logging import logger
from app.infrastructure.database.models import Base
from app.infrastructure.database.session import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle manager for the FastAPI application.
    Handles startup and shutdown events such as DB schema creation 
    and connection management.
    """
    logger.info("Starting up SentinelVision API...")
    
    # Ensure upload directory exists on startup
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    # Create database tables automatically on startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("Database tables verified/created.")
    
    yield
    
    logger.info("Shutting down SentinelVision API...")
    # Safely close async database connections
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    lifespan=lifespan,
    version="0.1.0",
    description="Intelligent Security Video Analytics API",
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for video uploads
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Include API Routes
app.include_router(router) 


@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint to monitor application status."""
    return {
        "status": "ok",
        "environment": settings.ENVIRONMENT,
        "version": "0.1.0",
    }