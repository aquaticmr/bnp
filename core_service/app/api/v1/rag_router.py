from fastapi import APIRouter, Depends
from app.core.security import verify_bearer_token
from app.rag.rag_pipeline import rag_pipeline
from app.schemas.rag import RagQueryRequest, RagQueryResponse

router = APIRouter(prefix="/rag", tags=["RAG & AI-Assisted Q&A"])


@router.post("/ask", response_model=RagQueryResponse, summary="Submit compliance question for grounded answer with citations")
async def ask_regulatory_question(
    request: RagQueryRequest,
    _auth: bool = Depends(verify_bearer_token),
) -> RagQueryResponse:
    """
    Retrieves the most relevant regulatory clauses from the repository,
    grounds an audit-ready response, and attaches precise document citations and page numbers.
    """
    return await rag_pipeline.answer_query(request)


@router.get("/health", summary="Check RAG components connectivity")
def rag_health_check():
    return {
        "status": "healthy",
        "embedding_model": "all-MiniLM-L6-v2",
        "vector_dimensions": 384,
        "grounding_enforced": True,
    }
