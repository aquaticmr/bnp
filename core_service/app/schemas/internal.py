from typing import List, Optional
from pydantic import BaseModel


class DocumentChunkDTO(BaseModel):
    chunkId: str
    documentId: Optional[int] = None
    parentSectionId: Optional[str] = None
    prevChunkId: Optional[str] = None
    nextChunkId: Optional[str] = None
    pageNumber: int
    text: str


class EmbedChunksWebhookRequest(BaseModel):
    docId: int
    regulator: str
    chunks: List[DocumentChunkDTO]


class EmbedChunksWebhookResponse(BaseModel):
    success: bool
    docId: int
    chunks_processed: int
    message: str
