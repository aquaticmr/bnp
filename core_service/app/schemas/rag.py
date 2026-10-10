from typing import List, Optional
from pydantic import BaseModel, Field
from app.schemas.search import SearchCitation


class RagQueryRequest(BaseModel):
    query: str = Field(..., min_length=2, description="Compliance or regulatory question")
    regulator_filter: Optional[str] = Field(default=None, description="Optional regulator constraint")
    top_k: int = Field(default=4, ge=1, le=10, description="Number of context passages to ground the answer")


class RagQueryResponse(BaseModel):
    query: str
    answer: str
    citations: List[SearchCitation]
    grounded: bool
    retrieved_chunks_count: int
