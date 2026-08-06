 from fastapi import APIRouter

from app.api.routes.assets import router as assets_router
from app.api.routes.investigations import router as investigations_router
from app.api.routes.memories import router as memories_router


api_router = APIRouter()

api_router.include_router(investigations_router)
api_router.include_router(assets_router)
api_router.include_router(memories_router)