import datetime
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.api_router import api_v1_router
from app.core.config import settings
from app.db.models import DocumentMetadataRecord, RegulatoryAlertRecord
from app.db.session import SessionLocal, init_db
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger('reg_iris_rules')

def seed_rules_database():
    init_db()
    db = SessionLocal()
    try:
        count = db.query(DocumentMetadataRecord).count()
        if count == 0:
            docs = [DocumentMetadataRecord(document_id=1, file_name='EMIR_Technical_Standards_v1.0.pdf', regulator='EMIR', jurisdiction='EU', effective_date=datetime.date(2024, 4, 29), category='TRANSACTION_REPORTING', version='v1.0'), DocumentMetadataRecord(document_id=2, file_name='EMIR_Technical_Standards_v2.0.pdf', regulator='EMIR', jurisdiction='EU', effective_date=datetime.date(2026, 1, 15), category='TRANSACTION_REPORTING', version='v2.0', parent_doc_id=1), DocumentMetadataRecord(document_id=3, file_name='MiFID_II_RTS_22_Reporting_Guide.pdf', regulator='MiFID II', jurisdiction='EU', effective_date=datetime.date(2024, 1, 1), category='TRADE_TRANSPARENCY', version='v1.2')]
            db.add_all(docs)
            db.commit()
            alert = RegulatoryAlertRecord(document_id=2, regulator='EMIR', document_title='EMIR_Technical_Standards_v2.0.pdf', version='v2.0', effective_date=datetime.date(2026, 1, 15), diff_summary='EMIR Refit revision: Mandates Unique Product Identifier (UPI), dual-sided Unique Trade Identifier (UTI) matching, and GLEIF LEI pre-validation.', impact_level='HIGH', is_read=False)
            db.add(alert)
            db.commit()
            logger.info('Rules service database seeded.')
    except Exception as e:
        logger.warning('Rules database initialization warning: %s', e)
    finally:
        db.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info('Starting Rules Engine & Impact Scanner Microservice on port %d...', settings.PORT)
    seed_rules_database()
    yield
    logger.info('Shutting down Rules Engine Microservice.')
app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION, description="Dedicated microservice component for data-driven JSON rules execution, trade impact matrix analysis, What's New diff cards, and gap analysis.", lifespan=lifespan, docs_url='/docs', redoc_url='/redoc')
app.add_middleware(CORSMiddleware, allow_origins=settings.CORS_ORIGINS, allow_credentials=True, allow_methods=['*'], allow_headers=['*'])
app.include_router(api_v1_router, prefix=settings.API_PREFIX)

@app.get('/', tags=['Health'])
def root():
    return {'service': settings.APP_NAME, 'port': settings.PORT, 'status': 'operational', 'endpoints': {'rules': f'{settings.API_PREFIX}/rules', 'impact_matrix': f'{settings.API_PREFIX}/rules/impact-matrix', 'export_csv': f'{settings.API_PREFIX}/rules/impact-matrix/export-csv', 'alerts': f'{settings.API_PREFIX}/alerts', 'gap_analysis': f'{settings.API_PREFIX}/gap-analysis', 'checklist': f'{settings.API_PREFIX}/checklist'}}

@app.get('/health', tags=['Health'])
def health():
    return JSONResponse(content={'status': 'healthy'})
if __name__ == '__main__':
    import uvicorn
    uvicorn.run('app.main:app', host='0.0.0.0', port=settings.PORT, reload=True)