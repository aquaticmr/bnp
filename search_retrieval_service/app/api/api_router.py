from fastapi import APIRouter
from app.api.internal_router import router as internal_router
from app.api.rag_router import router as rag_router
from app.api.search_router import router as search_router
api_v1_router = APIRouter()
api_v1_router.include_router(search_router)
api_v1_router.include_router(rag_router)
api_v1_router.include_router(internal_router)