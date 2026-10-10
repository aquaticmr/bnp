from typing import Optional
from fastapi import APIRouter, Depends, Query
from app.core.security import verify_bearer_token
from app.schemas.search import (
    SearchFilterParams,
    SearchMode,
    SearchQueryRequest,
    SearchResponse,
)
from app.search.search_service import search_service

router = APIRouter(prefix="/search", tags=["Search & Retrieval"])


@router.post("", response_model=SearchResponse, summary="Perform Hybrid, Semantic, or Keyword regulatory search")
def perform_search(
    request: SearchQueryRequest,
    _auth: bool = Depends(verify_bearer_token),
) -> SearchResponse:
    """
    Retrieves regulatory paragraphs or clauses matching the query.
    Supports BM25 keyword matching, vector dense retrieval, or reciprocal rank hybrid fusion.
    """
    return search_service.search(request)


@router.get("", response_model=SearchResponse, summary="Query regulatory clauses via URL parameters")
def search_by_params(
    q: str = Query(..., min_length=1, description="Search query string"),
    mode: SearchMode = Query(default=SearchMode.HYBRID, description="Retrieval mode: keyword, semantic, or hybrid"),
    top_k: int = Query(default=5, ge=1, le=50, description="Max clauses to return"),
    regulator: Optional[str] = Query(default=None, description="Filter by regulator (e.g. MiFID II, EMIR)"),
    jurisdiction: Optional[str] = Query(default=None, description="Filter by jurisdiction (EU, US, UK)"),
    category: Optional[str] = Query(default=None, description="Filter by regulatory category"),
    _auth: bool = Depends(verify_bearer_token),
) -> SearchResponse:
    filters = SearchFilterParams(
        regulator=regulator,
        jurisdiction=jurisdiction,
        category=category,
    )
    request = SearchQueryRequest(
        query=q,
        mode=mode,
        top_k=top_k,
        filters=filters,
    )
    return search_service.search(request)
