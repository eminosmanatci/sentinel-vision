from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.core.config import settings
from app.core.logging import logger
from app.infrastructure.database.session import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up SentinelVision API...")
    yield
    logger.info("Shutting down...")
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    lifespan=lifespan,
    version="0.1.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
import os
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# API Routes
app.include_router(router)

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "environment": settings.ENVIRONMENT,
        "version": "0.1.0",
    }