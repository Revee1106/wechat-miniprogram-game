from fastapi import APIRouter

from app.api.core_loop import router as core_loop_router


api_router = APIRouter(prefix="/api")
api_router.include_router(core_loop_router)
