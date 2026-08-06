from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings
from app.database.init_db import init_db

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    """
    Initialize Relay resources when the application starts.
    """

    await init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Collaborative operational memory for AI agents built on DataHub.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
      allow_origins=[
        "https://relay-7b8e.onrender.com",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    api_router,
    prefix=settings.api_prefix,
)


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "name": settings.app_name,
        "status": "running",
        "message": "Relay API is online.",
    }


@app.get(f"{settings.api_prefix}/health")
async def health() -> dict[str, str | bool]:
    return {
        "status": "ok",
        "database": "connected",
        "datahub": settings.datahub_mode,
        "llm": "configured" if settings.llm_api_key else "not_configured",
        "demo_mode": settings.datahub_mode == "mock",
    }
