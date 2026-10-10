import pytest
from app.schemas.search import (
    SearchFilterParams,
    SearchMode,
    SearchQueryRequest,
)
from app.search.search_service import search_service


def test_search_keyword_mode():
    req = SearchQueryRequest(
        query="Legal Entity Identifier",
        mode=SearchMode.KEYWORD,
        top_k=3,
    )
    resp = search_service.search(req)

    assert resp.total > 0
    assert len(resp.results) <= 3
    top_hit = resp.results[0]
    assert top_hit.citation.document_name is not None
    assert top_hit.citation.page_number > 0
    assert top_hit.citation.chunk_id is not None


def test_search_semantic_mode():
    req = SearchQueryRequest(
        query="reporting trades to a trade repository",
        mode=SearchMode.SEMANTIC,
        top_k=3,
    )
    resp = search_service.search(req)

    assert resp.total > 0
    assert len(resp.results) <= 3
    top_hit = resp.results[0]
    assert top_hit.text is not None


def test_search_hybrid_mode():
    req = SearchQueryRequest(
        query="MiFID II RTS 22 price and venue",
        mode=SearchMode.HYBRID,
        top_k=4,
    )
    resp = search_service.search(req)

    assert resp.total > 0
    for res in resp.results:
        assert res.score > 0.0


def test_search_with_regulator_filter():
    req = SearchQueryRequest(
        query="reporting",
        mode=SearchMode.KEYWORD,
        top_k=5,
        filters=SearchFilterParams(regulator="EMIR"),
    )
    resp = search_service.search(req)

    for item in resp.results:
        assert item.regulator.upper() == "EMIR"
