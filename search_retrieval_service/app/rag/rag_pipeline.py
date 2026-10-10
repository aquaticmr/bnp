import logging
from typing import List
from app.rag.llm_provider import llm_provider
from app.rag.prompt_templates import REGULATORY_SYSTEM_PROMPT, REGULATORY_USER_TEMPLATE
from app.schemas.rag import RagQueryRequest, RagQueryResponse
from app.schemas.search import SearchCitation, SearchFilterParams, SearchMode, SearchQueryRequest
from app.search.search_service import search_service
logger = logging.getLogger(__name__)

class RegulatoryRagPipeline:

    def __init__(self):
        self.search_service = search_service
        self.llm_provider = llm_provider

    async def answer_query(self, request: RagQueryRequest) -> RagQueryResponse:
        filters = SearchFilterParams(regulator=request.regulator_filter) if request.regulator_filter else None
        search_req = SearchQueryRequest(query=request.query, mode=SearchMode.HYBRID, top_k=request.top_k, filters=filters)
        search_resp = self.search_service.search(search_req)
        retrieved_chunks = search_resp.results
        if not retrieved_chunks:
            return RagQueryResponse(query=request.query, answer='No relevant regulatory text or citations were found matching your inquiry.', citations=[], grounded=False, retrieved_chunks_count=0)
        context_blocks: List[str] = []
        citations: List[SearchCitation] = []
        for chunk in retrieved_chunks:
            citations.append(chunk.citation)
            block = f"[Document: {chunk.file_name} | Page: {chunk.page_number} | Clause: {chunk.id}]\nSection: {chunk.citation.parent_section_id or 'General'}\n{chunk.text}\n"
            context_blocks.append(block)
        formatted_context = '\n---\n'.join(context_blocks)
        user_prompt = REGULATORY_USER_TEMPLATE.format(context=formatted_context, query=request.query)
        answer = await self.llm_provider.generate_response(system_prompt=REGULATORY_SYSTEM_PROMPT, user_prompt=user_prompt, chunks=retrieved_chunks)
        return RagQueryResponse(query=request.query, answer=answer, citations=citations, grounded=True, retrieved_chunks_count=len(retrieved_chunks))
rag_pipeline = RegulatoryRagPipeline()