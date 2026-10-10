# Reg IRIS – Core Intelligence Service

Microservices-based Regulatory Intelligence Hub and Impact Scanner for global banking compliance (MiFID II, EMIR, Dodd-Frank, FCA).

## Architectural Domains

The service is organized into decoupled, production-grade components:

1. **Intelligent Search & Retrieval Domain (`app/search`)**:
   - **BM25 Keyword Search**: Full-text querying over `regulatory_clauses` index via Elasticsearch.
   - **Semantic Vector Search**: Dense sentence embeddings using `sentence-transformers/all-MiniLM-L6-v2` (384-dimensional vectors) in ChromaDB.
   - **Hybrid Retrieval**: Combines keyword precision and semantic recall via Reciprocal Rank Fusion (RRF).
   - **Citation & Lineage**: Every retrieved paragraph returns document name, page number, clause ID, and section title.
   - **Filters**: Multi-attribute filtering across `regulator`, `jurisdiction`, `category`, and dates.

2. **Rules & Engine Domain (`app/engine`)**:
   - **Data-Driven Rule Execution**: 100% data-driven; zero hardcoded if/else statements. Rules defined in declarative JSON format.
   - **Condition Evaluator**: Supports validation operators (`lei_valid`, `positive_number`, `iso8601_valid`, `in_set`, `date_after`, `regex_match`, etc.).
   - **Impact Matrix Engine**: Evaluates trade records against regulatory rule sets. Produces structured trade-to-rule mapping with failure explanations, severity levels, pagination, filtering, and CSV export.

3. **RAG & Conversational Q&A (`app/rag`)**:
   - Grounded compliance assistant strictly constrained to retrieved regulatory clauses to prevent hallucinations.
   - Attaches verified clickable citations to every answer.
   - Pluggable provider architecture supporting local Ollama models (`mistral:instruct`, `llama3`), OpenAI-compatible gateways, and deterministic synthesizers.

4. **Versioning & "What's New" Diff Alerts (`app/services`)**:
   - Tracks document uploads, version histories, and parent-child document lineage.
   - Generates "What's New" summary cards detailing regulator, effective date, and delta modifications between versions.
   - Exposes mock notification feeds for dashboard Alert Panels.

5. **Gap Analysis & Compliance Checklists (`app/services`)**:
   - Cross-references trade-reporting schema attributes against regulatory mandates.
   - Computes framework compliance scores and identifies missing attributes.
   - Provides operational compliance verification checklists.

6. **Ingestion Webhook (`app/api/v1/internal_router.py`)**:
   - `POST /api/v1/internal/embed-chunks`: Synchronizes parsed chunks directly from the Spring Boot Ingestion Service into Elasticsearch and ChromaDB.

---

## Directory Structure

```
core_service/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── alerts_router.py       # What's New cards & notifications
│   │       ├── api_router.py          # Master v1 router
│   │       ├── gap_analysis_router.py  # Schema gap analysis & checklist
│   │       ├── internal_router.py      # Spring Boot ingestion webhook
│   │       ├── rag_router.py           # Grounded Q&A assistant
│   │       ├── rules_router.py         # Rules engine & Impact Matrix
│   │       └── search_router.py        # Keyword, semantic & hybrid search
│   ├── core/
│   │   ├── config.py                  # Pydantic Settings configuration
│   │   └── security.py                # Optional static Bearer token authentication
│   ├── db/
│   │   ├── models.py                  # SQLAlchemy relational models
│   │   ├── seed.py                    # Seed clauses and metadata
│   │   └── session.py                 # Resilient PostgreSQL / SQLite session
│   ├── engine/
│   │   ├── evaluator.py               # Data-driven JSON condition evaluator
│   │   ├── impact_matrix.py           # Impact matrix computation & CSV export
│   │   ├── operators.py               # Predicate operators registry
│   │   └── rule_loader.py             # JSON rule deserializer
│   ├── rag/
│   │   ├── llm_provider.py            # Ollama / OpenAI / Synthesizer provider
│   │   ├── prompt_templates.py        # Grounding & citation prompt templates
│   │   └── rag_pipeline.py            # Retrieval-augmented generation orchestrator
│   ├── schemas/                       # Pydantic DTO models
│   ├── search/
│   │   ├── chroma_client.py           # ChromaDB client with persistent fallback
│   │   ├── elasticsearch_client.py    # Elasticsearch BM25 client with fallback
│   │   ├── embeddings.py              # all-MiniLM-L6-v2 sentence embeddings
│   │   └── search_service.py          # Search orchestrator with RRF
│   ├── services/
│   │   ├── diff_service.py            # What's New card generator
│   │   ├── gap_analysis_service.py    # Schema compliance gap analysis
│   │   └── versioning_service.py      # Relational document version audit trail
│   └── main.py                        # FastAPI application entrypoint
├── data/
│   ├── metadata/doc_metadata.csv      # Seed metadata
│   ├── queries.txt                    # Sample compliance queries
│   ├── rules/regulatory_rules.json    # Declarative regulatory rules
│   ├── schema/reporting_schema.json   # Canonical trade reporting schema
│   └── trades/sample_trades.csv       # 200 sample trades with injected errors
├── tests/                             # 29 automated unit & integration tests
├── Dockerfile                         # Container definition
├── requirements.txt                   # Pinned Python dependencies
└── README.md
```

---

## Getting Started

### 1. Running Locally with Python
```bash
cd core_service
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Interactive OpenAPI Swagger UI is available at:
`http://localhost:8000/docs`

### 2. Running Automated Unit Tests
```bash
cd core_service
pytest tests -v
```

All 29 tests execute across the rules engine, impact matrix, search, RAG, and API routers.

### 3. Running with Docker Compose
From the root repository:
```bash
docker-compose up --build
```
