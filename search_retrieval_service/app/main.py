import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.api_router import api_v1_router
from app.core.config import settings
from app.search.chroma_client import chroma_client
from app.search.elasticsearch_client import elasticsearch_client
from app.search.embeddings import embedding_service
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger('reg_iris_search')
SEED_CLAUSES = [{'chunkId': 'EMIR-DOC1-P001', 'documentId': 1, 'fileName': 'EMIR_Technical_Standards_v1.0.pdf', 'regulator': 'EMIR', 'jurisdiction': 'EU', 'category': 'TRANSACTION_REPORTING', 'version': 'v1.0', 'parentSectionId': 'Article 9 - Reporting Obligation', 'pageNumber': 14, 'effectiveDate': '2024-04-29', 'text': 'Counterparties and CCPs shall ensure that the details of any derivative contract they have concluded and of any modification or termination of the contract are reported to a trade repository registered in accordance with Article 55 or recognised in accordance with Article 77 no later than the working day following the conclusion, counterparties must be uniquely identified by an active 20-character ISO 17442 Legal Entity Identifier (LEI).'}, {'chunkId': 'MIFID-DOC3-P001', 'documentId': 3, 'fileName': 'MiFID_II_RTS_22_Reporting_Guide.pdf', 'regulator': 'MiFID II', 'jurisdiction': 'EU', 'category': 'TRADE_TRANSPARENCY', 'version': 'v1.2', 'parentSectionId': 'Article 15 - Transaction Price Fields', 'pageNumber': 22, 'effectiveDate': '2024-01-01', 'text': 'Investment firms reporting transactions under Article 26 of Regulation (EU) No 600/2014 shall state the price of the transaction in the currency in which the transaction was executed. Traded prices must be strictly positive numerical values. Where the transaction is executed on a trading venue, Field 36 (Venue) must contain the four-letter Market Identifier Code (MIC) under ISO 10383.'}, {'chunkId': 'CFTC-DOC4-P001', 'documentId': 4, 'fileName': 'Dodd_Frank_CFTC_Part_43_Guide.pdf', 'regulator': 'Dodd-Frank', 'jurisdiction': 'US', 'category': 'SWAP_DATA_RECORDKEEPING', 'version': 'v1.0', 'parentSectionId': 'Part 43 - Real-Time Public Reporting', 'pageNumber': 12, 'effectiveDate': '2024-06-30', 'text': 'CFTC Part 43 governs real-time public reporting of swap transaction and pricing data. Reporting entities must publicly disseminate swap transaction data as soon as technologically practicable following execution. The transaction quantity and notional volume must be strictly greater than zero.'}, {'chunkId': 'FCA-DOC5-P001', 'documentId': 5, 'fileName': 'FCA_SUP_17_Transaction_Reporting.pdf', 'regulator': 'FCA', 'jurisdiction': 'UK', 'category': 'MARKET_ABUSE', 'version': 'v1.1', 'parentSectionId': 'SUP 17 Annex 1 - Reporting Standards', 'pageNumber': 8, 'effectiveDate': '2024-03-31', 'text': 'FCA authorized investment firms must submit accurate transaction reports to the FCA Market Data Processor (MDP). Currency codes must be populated using valid 3-letter ISO 4217 alphabetic currency codes. Reports containing invalid currency codes or unregistered trading counterparties are automatically rejected.'}]

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info('Starting Search & Retrieval Microservice on port %d...', settings.PORT)
    try:
        elasticsearch_client.index_clauses(SEED_CLAUSES)
        c_ids = [c['chunkId'] for c in SEED_CLAUSES]
        c_texts = [c['text'] for c in SEED_CLAUSES]
        c_metas = [{'chunk_id': c['chunkId'], 'document_id': str(c['documentId']), 'file_name': c['fileName'], 'regulator': c['regulator'], 'page_number': str(c['pageNumber']), 'parent_section_id': c['parentSectionId']} for c in SEED_CLAUSES]
        vectors = embedding_service.embed_batch(c_texts)
        chroma_client.add_documents(ids=c_ids, embeddings=vectors, documents=c_texts, metadatas=c_metas)
        logger.info('Search indices initialized.')
    except Exception as e:
        logger.warning('Search indices startup notice: %s', e)
    yield
    logger.info('Shutting down Search & Retrieval Microservice.')
app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION, description='Dedicated microservice component for full-text BM25 search, semantic vector retrieval, hybrid RRF search, and RAG Q&A.', lifespan=lifespan, docs_url='/docs', redoc_url='/redoc')
app.add_middleware(CORSMiddleware, allow_origins=settings.CORS_ORIGINS, allow_credentials=True, allow_methods=['*'], allow_headers=['*'])
app.include_router(api_v1_router, prefix=settings.API_PREFIX)

@app.get('/', tags=['Health'])
def root():
    return {'service': settings.APP_NAME, 'port': settings.PORT, 'status': 'operational', 'endpoints': {'search': f'{settings.API_PREFIX}/search', 'rag': f'{settings.API_PREFIX}/rag/ask', 'internal_webhook': f'{settings.API_PREFIX}/internal/embed-chunks'}}

@app.get('/health', tags=['Health'])
def health():
    return JSONResponse(content={'status': 'healthy'})
if __name__ == '__main__':
    import uvicorn
    uvicorn.run('app.main:app', host='0.0.0.0', port=settings.PORT, reload=True)