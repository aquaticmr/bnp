import logging
from typing import List
from sentence_transformers import SentenceTransformer
from app.core.config import settings
logger = logging.getLogger(__name__)

class EmbeddingService:

    def __init__(self, model_name: str=settings.EMBEDDING_MODEL_NAME):
        self.model_name = model_name
        self._model: SentenceTransformer = None

    @property
    def model(self) -> SentenceTransformer:
        if self._model is None:
            logger.info('Initializing embedding model: %s', self.model_name)
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def embed_text(self, text: str) -> List[float]:
        vector = self.model.encode(text, convert_to_numpy=True, normalize_embeddings=True)
        return vector.tolist()

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        vectors = self.model.encode(texts, batch_size=settings.EMBEDDING_BATCH_SIZE, convert_to_numpy=True, normalize_embeddings=True, show_progress_bar=False)
        return vectors.tolist()
embedding_service = EmbeddingService()