import logging
from typing import Any, Dict, List, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from app.core.config import settings
from app.schemas.search import SearchCitation, SearchFilterParams, SearchResultItem

logger = logging.getLogger(__name__)


class ResilientChromaClient:
    def __init__(
        self,
        collection_name: str = settings.CHROMADB_COLLECTION,
    ):
        self.collection_name = collection_name
        self._client: Optional[chromadb.ClientAPI] = None
        self._collection = None
        self._init_client()

    def _init_client(self):
        # 1. Attempt connection to Chroma HTTP server (e.g. Docker container)
        try:
            self._client = chromadb.HttpClient(
                host=settings.CHROMADB_HOST,
                port=settings.CHROMADB_PORT,
            )
            # Verify connectivity
            self._client.heartbeat()
            logger.info("Connected to ChromaDB HTTP service at %s:%d", settings.CHROMADB_HOST, settings.CHROMADB_PORT)
        except Exception as e:
            logger.warning(
                "ChromaDB HTTP service unreachable (%s). Initializing persistent local Chroma client at %s",
                e,
                settings.CHROMADB_PERSIST_DIR,
            )
            try:
                self._client = chromadb.PersistentClient(path=settings.CHROMADB_PERSIST_DIR)
            except Exception as pe:
                logger.error("Failed to initialize persistent Chroma client: %s. Falling back to EphemeralClient.", pe)
                self._client = chromadb.EphemeralClient()

        # 2. Get or create collection
        try:
            self._collection = self._client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            logger.info("ChromaDB collection '%s' ready.", self.collection_name)
        except Exception as ce:
            logger.error("Failed to obtain Chroma collection: %s", ce)

    def add_documents(
        self,
        ids: List[str],
        embeddings: List[List[float]],
        documents: List[str],
        metadatas: List[Dict[str, Any]],
    ):
        if not self._collection or not ids:
            return
        try:
            # Chroma expects metadata values to be str, int, float, or bool
            sanitized_metadatas = []
            for meta in metadatas:
                sanitized = {}
                for k, v in meta.items():
                    if v is not None:
                        sanitized[k] = str(v) if not isinstance(v, (int, float, bool)) else v
                sanitized_metadatas.append(sanitized)

            self._collection.upsert(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=sanitized_metadatas,
            )
            logger.info("Upserted %d vector records into collection '%s'", len(ids), self.collection_name)
        except Exception as exc:
            logger.error("Failed upserting vectors into Chroma: %s", exc)

    def search_semantic(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filters: Optional[SearchFilterParams] = None,
    ) -> List[SearchResultItem]:
        if not self._collection:
            return []

        where_filter = None
        if filters:
            conds = []
            if filters.regulator:
                conds.append({"regulator": filters.regulator})
            if filters.jurisdiction:
                conds.append({"jurisdiction": filters.jurisdiction})
            if filters.category:
                conds.append({"category": filters.category})

            if len(conds) == 1:
                where_filter = conds[0]
            elif len(conds) > 1:
                where_filter = {"$and": conds}

        try:
            results = self._collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where_filter,
                include=["documents", "metadatas", "distances"],
            )

            hits: List[SearchResultItem] = []
            ids = results.get("ids", [[]])[0]
            docs = results.get("documents", [[]])[0]
            metas = results.get("metadatas", [[]])[0]
            distances = results.get("distances", [[]])[0]

            for i in range(len(ids)):
                meta = metas[i] if i < len(metas) else {}
                dist = distances[i] if i < len(distances) else 0.5
                # Convert cosine distance to similarity score
                similarity = max(0.0, 1.0 - dist)

                doc_id_val = meta.get("document_id")
                page_num_val = meta.get("page_number", "1")

                hits.append(
                    SearchResultItem(
                        id=ids[i],
                        document_id=int(doc_id_val) if doc_id_val and str(doc_id_val).isdigit() else None,
                        file_name=meta.get("file_name", "Unknown Document"),
                        regulator=meta.get("regulator", "General"),
                        jurisdiction=meta.get("jurisdiction"),
                        category=meta.get("category"),
                        version=meta.get("version"),
                        page_number=int(page_num_val) if str(page_num_val).isdigit() else 1,
                        text=docs[i],
                        score=round(similarity, 4),
                        citation=SearchCitation(
                            document_name=meta.get("file_name", "Unknown Document"),
                            page_number=int(page_num_val) if str(page_num_val).isdigit() else 1,
                            chunk_id=ids[i],
                            parent_section_id=meta.get("parent_section_id"),
                        ),
                    )
                )

            return hits
        except Exception as exc:
            logger.error("ChromaDB vector search failed: %s", exc)
            return []


chroma_client = ResilientChromaClient()
