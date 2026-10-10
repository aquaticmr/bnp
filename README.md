# Reg IRIS – Microservices Platform Architecture

This repository contains the decoupled microservice components for **Reg IRIS (Intelligent Regulatory Repository & Impact Scanner)**:

```
ram/
├── demo 2/                     # Component 1: Regulatory Ingestion Service (Java / Spring Boot)
├── search_retrieval_service/   # Component 2: Intelligent Search & Retrieval Service (FastAPI :8001)
├── rules_engine_service/       # Component 3: Rules & Engine Impact Scanner Service (FastAPI :8002)
├── docker-compose.yml          # Single-command multi-service orchestration
└── README.md
```

---

## 1. Component Separation & Ports

| Component | Technology | Default Port | Responsibilities |
|---|---|---|---|
| **Ingestion Service** (`demo 2`) | Java / Spring Boot | `8080` | PDF/HTML upload, parsing, document storage in MinIO, versioning |
| **Search & Retrieval Service** (`search_retrieval_service`) | Python / FastAPI | `8001` | BM25 Elasticsearch keyword search, ChromaDB vector semantic search, hybrid RRF, grounded RAG Q&A |
| **Rules & Engine Service** (`rules_engine_service`) | Python / FastAPI | `8002` | Zero-code JSON rules engine, Impact Matrix trade evaluation, CSV export, "What's New" diff cards, schema gap analysis |

---

## 2. Running Individual Components Locally

### Component 2: Search & Retrieval Service
```bash
cd search_retrieval_service
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```
- Swagger UI: `http://localhost:8001/docs`
- Tests: `pytest tests -v` (7 tests pass)

### Component 3: Rules & Engine Service
```bash
cd rules_engine_service
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload
```
- Swagger UI: `http://localhost:8002/docs`
- Tests: `pytest tests -v` (10 tests pass)

---

## 3. Starting the Entire Stack with Docker Compose

To launch all infrastructure (PostgreSQL, Elasticsearch, ChromaDB, MinIO) and the microservice components together:

```bash
docker-compose up --build
```
