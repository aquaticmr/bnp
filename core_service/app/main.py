import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.v1.api_router import api_v1_router
from app.core.config import settings
from app.db.seed import seed_database_and_indices

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("reg_iris")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Reg IRIS Core Intelligence Platform...")
    try:
        seed_database_and_indices()
        logger.info("Core indices and relational stores verified.")
    except Exception as e:
        logger.error("Startup initialization warning: %s", e)
    yield
    logger.info("Shutting down Reg IRIS Core Intelligence Platform.")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Microservices-based regulatory intelligence hub. "
        "Provides hybrid search, data-driven rule evaluation, Impact Matrix generation, "
        "and grounded Q&A across global regulatory frameworks (MiFID II, EMIR, Dodd-Frank, FCA)."
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers
app.include_router(api_v1_router, prefix=settings.API_PREFIX)


@app.get("/", tags=["Health"])
def root_info():
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "operational",
        "docs_url": "/docs",
        "endpoints": {
            "search": f"{settings.API_PREFIX}/search",
            "rules": f"{settings.API_PREFIX}/rules",
            "impact_matrix": f"{settings.API_PREFIX}/rules/impact-matrix",
            "rag": f"{settings.API_PREFIX}/rag/ask",
            "alerts": f"{settings.API_PREFIX}/alerts",
            "gap_analysis": f"{settings.API_PREFIX}/gap-analysis",
            "checklist": f"{settings.API_PREFIX}/checklist",
            "internal_webhook": f"{settings.API_PREFIX}/internal/embed-chunks",
        },
    }


@app.get("/health", tags=["Health"])
def health_check():
    return JSONResponse(content={"status": "healthy"})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.PORT, reload=True)
