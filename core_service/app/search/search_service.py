import logging
from typing import Dict, List, Optional
from app.schemas.search import (
    SearchFilterParams,
    SearchMode,
    SearchQueryRequest,
    SearchResponse,
    SearchResultItem,
)
from app.search.chroma_client import chroma_client
from app.search.elasticsearch_client import elasticsearch_client
from app.search.embeddings import embedding_service

logger = logging.getLogger(__name__)


class SearchOrchestratorService:
    def __init__(self):
        self.es_client = elasticsearch_client
        self.chroma_client = chroma_client
        self.embedding_service = embedding_service

    def search(self, request: SearchQueryRequest) -> SearchResponse:
        query_text = request.query.strip()
        mode = request.mode
        top_k = request.top_k
        filters = request.filters

        if mode == SearchMode.KEYWORD:
            results = self.es_client.search_keyword(query_text, top_k=top_k, filters=filters)
        elif mode == SearchMode.SEMANTIC:
            query_vector = self.embedding_service.embed_text(query_text)
            results = self.chroma_client.search_semantic(query_vector, top_k=top_k, filters=filters)
        else:
            # Hybrid search using Reciprocal Rank Fusion (RRF)
            results = self._hybrid_rrf_search(query_text, top_k=top_k, filters=filters)

        return SearchResponse(
            query=query_text,
            mode=mode,
            total=len(results),
            results=results,
        )

    def _hybrid_rrf_search(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[SearchFilterParams] = None,
        rrf_k: int = 60,
    ) -> List[SearchResultItem]:
        # 1. Fetch keyword candidates (2x top_k)
        keyword_hits = self.es_client.search_keyword(query, top_k=top_k * 2, filters=filters)

        # 2. Fetch semantic candidates (2x top_k)
        query_vector = self.embedding_service.embed_text(query)
        semantic_hits = self.chroma_client.search_semantic(query_vector, top_k=top_k * 2, filters=filters)

        # 3. Fuse with Reciprocal Rank Fusion
        rrf_scores: Dict[str, float] = {}
        item_map: Dict[str, SearchResultItem] = {}

        for rank, item in enumerate(keyword_hits):
            doc_id = item.id
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + (1.0 / (rrf_k + rank + 1))
            item_map[doc_id] = item

        for rank, item in enumerate(semantic_hits):
            doc_id = item.id
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + (1.0 / (rrf_k + rank + 1))
            if doc_id not in item_map:
                item_map[doc_id] = item

        # Sort combined results by RRF score
        sorted_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)
        fused_results: List[SearchResultItem] = []

        for cid in sorted_ids[:top_k]:
            item = item_map[cid]
            # Attach normalized RRF score
            item.score = round(rrf_scores[cid], 5)
            fused_results.append(item)

        return fused_results


search_service = SearchOrchestratorService()
