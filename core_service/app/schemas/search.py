from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class SearchMode(str, Enum):
    KEYWORD = "keyword"
    SEMANTIC = "semantic"
    HYBRID = "hybrid"


class SearchFilterParams(BaseModel):
    regulator: Optional[str] = None
    jurisdiction: Optional[str] = None
    category: Optional[str] = None
    effective_date_from: Optional[str] = None
    effective_date_to: Optional[str] = None


class SearchCitation(BaseModel):
    document_name: str
    page_number: int
    chunk_id: str
    parent_section_id: Optional[str] = None


class SearchResultItem(BaseModel):
    id: str
    document_id: Optional[int] = None
    file_name: str
    regulator: str
    jurisdiction: Optional[str] = None
    category: Optional[str] = None
    version: Optional[str] = None
    page_number: int
    text: str
    score: float
    citation: SearchCitation


class SearchQueryRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Natural language or keyword search query")
    mode: SearchMode = Field(default=SearchMode.HYBRID, description="Retrieval mechanism")
    top_k: int = Field(default=5, ge=1, le=50, description="Maximum number of passages to return")
    filters: Optional[SearchFilterParams] = None


class SearchResponse(BaseModel):
    query: str
    mode: SearchMode
    total: int
    results: List[SearchResultItem]
