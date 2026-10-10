from fastapi import APIRouter
from app.api.v1.alerts_router import router as alerts_router
from app.api.v1.gap_analysis_router import router as gap_analysis_router
from app.api.v1.internal_router import router as internal_router
from app.api.v1.rag_router import router as rag_router
from app.api.v1.rules_router import router as rules_router
from app.api.v1.search_router import router as search_router

api_v1_router = APIRouter()

api_v1_router.include_router(search_router)
api_v1_router.include_router(rules_router)
api_v1_router.include_router(rag_router)
api_v1_router.include_router(alerts_router)
api_v1_router.include_router(gap_analysis_router)
api_v1_router.include_router(internal_router)
