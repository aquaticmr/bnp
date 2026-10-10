import logging
import math
import re
from typing import Any, Dict, List, Optional
from elasticsearch import Elasticsearch
from app.core.config import settings
from app.schemas.search import SearchCitation, SearchFilterParams, SearchResultItem

logger = logging.getLogger(__name__)


class ResilientElasticsearchClient:
    def __init__(
        self,
        url: str = settings.ELASTICSEARCH_URL,
        index_name: str = settings.ELASTICSEARCH_INDEX,
    ):
        self.url = url
        self.index_name = index_name
        self._es: Optional[Elasticsearch] = None
        self._is_connected = False
        self._fallback_store: Dict[str, Dict[str, Any]] = {}
        self._init_connection()

    def _init_connection(self):
        try:
            self._es = Elasticsearch(
                self.url,
                request_timeout=settings.ELASTICSEARCH_TIMEOUT_SECONDS,
            )
            if self._es.ping():
                self._is_connected = True
                logger.info("Connected to Elasticsearch cluster at %s", self.url)
                self._ensure_index()
            else:
                self._is_connected = False
                logger.warning("Elasticsearch ping failed at %s. Operating in resilient fallback mode.", self.url)
        except Exception as e:
            self._is_connected = False
            logger.warning("Unable to reach Elasticsearch (%s). Using local resilient fallback store.", str(e))

    def _ensure_index(self):
        if not self._is_connected or not self._es:
            return
        try:
            if not self._es.indices.exists(index=self.index_name):
                mapping = {
                    "mappings": {
                        "properties": {
                            "chunkId": {"type": "keyword"},
                            "documentId": {"type": "long"},
                            "fileName": {"type": "keyword"},
                            "regulator": {"type": "keyword"},
                            "jurisdiction": {"type": "keyword"},
                            "category": {"type": "keyword"},
                            "version": {"type": "keyword"},
                            "parentSectionId": {"type": "keyword"},
                            "pageNumber": {"type": "integer"},
                            "effectiveDate": {"type": "date"},
                            "text": {"type": "text", "analyzer": "standard"},
                        }
                    }
                }
                self._es.indices.create(index=self.index_name, body=mapping)
                logger.info("Created Elasticsearch index: %s", self.index_name)
        except Exception as err:
            logger.error("Failed ensuring Elasticsearch index %s: %s", self.index_name, err)

    def index_clauses(self, clauses: List[Dict[str, Any]]):
        """
        Indexes chunks into Elasticsearch and syncs them to local fallback store.
        """
        for c in clauses:
            doc_id = str(c.get("chunkId", c.get("id", "")))
            self._fallback_store[doc_id] = dict(c)

        if self._is_connected and self._es:
            try:
                for c in clauses:
                    doc_id = str(c.get("chunkId", c.get("id", "")))
                    self._es.index(index=self.index_name, id=doc_id, document=c)
                self._es.indices.refresh(index=self.index_name)
                logger.info("Indexed %d clauses to Elasticsearch index %s", len(clauses), self.index_name)
            except Exception as e:
                logger.error("Failed indexing clauses to Elasticsearch: %s", e)

    def search_keyword(
        self,
        query_text: str,
        top_k: int = 5,
        filters: Optional[SearchFilterParams] = None,
    ) -> List[SearchResultItem]:
        """
        Performs BM25 keyword search over regulatory_clauses.
        """
        if self._is_connected and self._es:
            try:
                must_clauses = [
                    {
                        "multi_match": {
                            "query": query_text,
                            "fields": ["text^2", "parentSectionId", "fileName"],
                            "fuzziness": "AUTO",
                        }
                    }
                ]
                filter_clauses = []
                if filters:
                    if filters.regulator:
                        filter_clauses.append({"term": {"regulator": filters.regulator}})
                    if filters.jurisdiction:
                        filter_clauses.append({"term": {"jurisdiction": filters.jurisdiction}})
                    if filters.category:
                        filter_clauses.append({"term": {"category": filters.category}})

                body = {
                    "query": {
                        "bool": {
                            "must": must_clauses,
                            "filter": filter_clauses,
                        }
                    },
                    "size": top_k,
                }
                res = self._es.search(index=self.index_name, body=body)
                hits = res.get("hits", {}).get("hits", [])
                results = []
                for hit in hits:
                    src = hit.get("_source", {})
                    results.append(
                        SearchResultItem(
                            id=hit.get("_id"),
                            document_id=src.get("documentId"),
                            file_name=src.get("fileName", "Unknown"),
                            regulator=src.get("regulator", "General"),
                            jurisdiction=src.get("jurisdiction"),
                            category=src.get("category"),
                            version=src.get("version"),
                            page_number=src.get("pageNumber", 1),
                            text=src.get("text", ""),
                            score=float(hit.get("_score", 0.0)),
                            citation=SearchCitation(
                                document_name=src.get("fileName", "Unknown"),
                                page_number=src.get("pageNumber", 1),
                                chunk_id=hit.get("_id"),
                                parent_section_id=src.get("parentSectionId"),
                            ),
                        )
                    )
                return results
            except Exception as exc:
                logger.warning("Elasticsearch query failed (%s). Executing local BM25 fallback.", exc)

        return self._fallback_bm25_search(query_text, top_k, filters)

    def _fallback_bm25_search(
        self,
        query: str,
        top_k: int,
        filters: Optional[SearchFilterParams] = None,
    ) -> List[SearchResultItem]:
        terms = [t.lower() for t in re.findall(r"\w+", query) if len(t) > 2]
        scored_items = []

        for cid, doc in self._fallback_store.items():
            if filters:
                if filters.regulator and doc.get("regulator", "").lower() != filters.regulator.lower():
                    continue
                if filters.jurisdiction and doc.get("jurisdiction", "").lower() != filters.jurisdiction.lower():
                    continue
                if filters.category and doc.get("category", "").lower() != filters.category.lower():
                    continue

            text = doc.get("text", "").lower()
            section = str(doc.get("parentSectionId", "")).lower()
            score = 0.0

            for term in terms:
                count = text.count(term)
                if count > 0:
                    score += (count / (count + 1.2)) * 1.5
                if term in section:
                    score += 2.0

            if score > 0.0:
                scored_items.append((score, cid, doc))

        scored_items.sort(key=lambda x: x[0], reverse=True)
        results = []
        for score, cid, doc in scored_items[:top_k]:
            results.append(
                SearchResultItem(
                    id=cid,
                    document_id=doc.get("documentId"),
                    file_name=doc.get("fileName", "Unknown"),
                    regulator=doc.get("regulator", "General"),
                    jurisdiction=doc.get("jurisdiction"),
                    category=doc.get("category"),
                    version=doc.get("version"),
                    page_number=doc.get("pageNumber", 1),
                    text=doc.get("text", ""),
                    score=round(score, 4),
                    citation=SearchCitation(
                        document_name=doc.get("fileName", "Unknown"),
                        page_number=doc.get("pageNumber", 1),
                        chunk_id=cid,
                        parent_section_id=doc.get("parentSectionId"),
                    ),
                )
            )
        return results


elasticsearch_client = ResilientElasticsearchClient()
