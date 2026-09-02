import os
import logging
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.config import settings
from app.database import engine, Base
from app.routers import (
    auth_routes,
    weather_routes,
    pfz_routes,
    sos_routes,
    chat_routes,
    gps_routes,
    admin_routes,
    researcher_routes,
    hazard_routes
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("JalDoot")

# Create database tables automatically
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Maritime safety, fish zone detection, disaster management, and multilingual assistant for traditional fishermen.",
    version="1.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers under /api
app.include_router(auth_routes.router, prefix="/api")
app.include_router(weather_routes.router, prefix="/api")
app.include_router(pfz_routes.router, prefix="/api")
app.include_router(sos_routes.router, prefix="/api")
app.include_router(chat_routes.router, prefix="/api")
app.include_router(gps_routes.router, prefix="/api")
app.include_router(admin_routes.router, prefix="/api")
app.include_router(researcher_routes.router, prefix="/api")
app.include_router(hazard_routes.router, prefix="/api")

# Static files for vessel image uploads
if not settings.UPLOAD_DIR.exists():
    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(settings.UPLOAD_DIR)), name="uploads")

# Mount frontend directory if present
if settings.STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(settings.STATIC_DIR)), name="static")

    @app.get("/")
    async def serve_index():
        index_path = settings.STATIC_DIR / "index.html"
        if index_path.exists():
            return FileResponse(str(index_path))
        return {"message": f"Welcome to {settings.PROJECT_NAME} API"}

@app.get("/api/health")
def health_check():
    return {
        "status": "online",
        "service": "JalDoot Backend",
        "database": str(engine.url),
        "gemini_api_configured": bool(settings.GEMINI_API_KEY)
    }
