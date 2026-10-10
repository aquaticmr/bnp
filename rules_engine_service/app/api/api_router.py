from fastapi import APIRouter
from app.api.alerts_router import router as alerts_router
from app.api.gap_analysis_router import router as gap_analysis_router
from app.api.rules_router import router as rules_router
api_v1_router = APIRouter()
api_v1_router.include_router(rules_router)
api_v1_router.include_router(alerts_router)
api_v1_router.include_router(gap_analysis_router)