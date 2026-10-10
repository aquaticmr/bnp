import asyncio
import pytest
from app.rag.rag_pipeline import rag_pipeline
from app.schemas.rag import RagQueryRequest


def test_rag_pipeline_grounding_and_citations():
    query_req = RagQueryRequest(
        query="What are the counterparty LEI requirements under EMIR?",
        top_k=3,
    )
    resp = asyncio.run(rag_pipeline.answer_query(query_req))

    assert resp.grounded is True
    assert resp.retrieved_chunks_count > 0
    assert len(resp.citations) > 0
    assert len(resp.answer) > 50

    # Ensure citation format is preserved
    first_citation = resp.citations[0]
    assert first_citation.document_name.endswith(".pdf")
    assert first_citation.page_number > 0
    assert first_citation.chunk_id != ""


def test_rag_pipeline_out_of_domain_query():
    query_req = RagQueryRequest(
        query="xyz_quantum_non_existent_topic_12345",
        top_k=2,
    )
    resp = asyncio.run(rag_pipeline.answer_query(query_req))
    assert resp.answer is not None
