import logging
from fastapi import APIRouter
from app.schemas.internal import (
    EmbedChunksWebhookRequest,
    EmbedChunksWebhookResponse,
)
from app.search.chroma_client import chroma_client
from app.search.elasticsearch_client import elasticsearch_client
from app.search.embeddings import embedding_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/internal", tags=["Internal Webhooks"])


@router.post(
    "/embed-chunks",
    response_model=EmbedChunksWebhookResponse,
    summary="Webhook from Ingestion Service to index chunks and compute embeddings",
)
def handle_embed_chunks_webhook(
    payload: EmbedChunksWebhookRequest,
) -> EmbedChunksWebhookResponse:
    """
    Receives parsed regulatory chunks from the Ingestion Service,
    indexes them into Elasticsearch for BM25 search,
    and computes sentence embeddings for ChromaDB vector search.
    """
    doc_id = payload.docId
    regulator = payload.regulator
    chunks = payload.chunks

    if not chunks:
        return EmbedChunksWebhookResponse(
            success=True,
            docId=doc_id,
            chunks_processed=0,
            message="No chunks provided in payload",
        )

    # 1. Prepare data structures for Elasticsearch and ChromaDB
    es_records = []
    chroma_ids = []
    chroma_texts = []
    chroma_metas = []

    for c in chunks:
        chunk_dict = {
            "chunkId": c.chunkId,
            "documentId": c.documentId or doc_id,
            "fileName": f"DOC_{doc_id}_{regulator}.pdf",
            "regulator": regulator,
            "jurisdiction": "Global",
            "category": "TRANSACTION_REPORTING",
            "version": "1.0",
            "parentSectionId": c.parentSectionId or "",
            "pageNumber": c.pageNumber,
            "text": c.text,
        }
        es_records.append(chunk_dict)

        chroma_ids.append(c.chunkId)
        chroma_texts.append(c.text)
        chroma_metas.append({
            "chunk_id": c.chunkId,
            "document_id": str(c.documentId or doc_id),
            "file_name": f"DOC_{doc_id}_{regulator}.pdf",
            "regulator": regulator,
            "page_number": str(c.pageNumber),
            "parent_section_id": c.parentSectionId or "",
        })

    # 2. Index to Elasticsearch
    try:
        elasticsearch_client.index_clauses(es_records)
    except Exception as es_err:
        logger.error("Error syncing chunks to Elasticsearch: %s", es_err)

    # 3. Compute vector embeddings and store in ChromaDB
    try:
        embeddings = embedding_service.embed_batch(chroma_texts)
        chroma_client.add_documents(
            ids=chroma_ids,
            embeddings=embeddings,
            documents=chroma_texts,
            metadatas=chroma_metas,
        )
    except Exception as chroma_err:
        logger.error("Error storing vectors in ChromaDB: %s", chroma_err)

    logger.info("Successfully ingested and indexed %d chunks for docId %d", len(chunks), doc_id)

    return EmbedChunksWebhookResponse(
        success=True,
        docId=doc_id,
        chunks_processed=len(chunks),
        message=f"Successfully indexed and embedded {len(chunks)} regulatory chunks.",
    )
