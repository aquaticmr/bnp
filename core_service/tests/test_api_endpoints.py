import io
import pytest


def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "operational"
    assert "endpoints" in data


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_search_api_post(client):
    payload = {
        "query": "Legal Entity Identifier LEI",
        "mode": "hybrid",
        "top_k": 3,
    }
    response = client.post("/api/v1/search", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == payload["query"]
    assert "results" in data
    assert len(data["results"]) > 0
    assert "citation" in data["results"][0]


def test_search_api_get(client):
    response = client.get("/api/v1/search?q=EMIR+Article+9&mode=keyword&top_k=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) > 0


def test_rules_catalog_endpoint(client):
    response = client.get("/api/v1/rules")
    assert response.status_code == 200
    data = response.json()
    assert data["total_rules"] >= 5
    assert len(data["rules"]) > 0


def test_impact_matrix_endpoint(client):
    response = client.get("/api/v1/rules/impact-matrix?page=1&page_size=20")
    assert response.status_code == 200
    data = response.json()
    assert "total_records" in data
    assert "total_violations" in data
    assert "compliant_trades" in data
    assert "items" in data
    assert len(data["items"]) > 0


def test_impact_matrix_csv_export(client):
    response = client.get("/api/v1/rules/impact-matrix/export-csv")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "Trade_ID,Rule_ID" in response.text


def test_rag_query_endpoint(client):
    payload = {
        "query": "What are the LEI requirements under EMIR?",
        "top_k": 3,
    }
    response = client.post("/api/v1/rag/ask", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert len(data["citations"]) > 0
    assert data["grounded"] is True


def test_alerts_endpoint(client):
    response = client.get("/api/v1/alerts")
    assert response.status_code == 200
    data = response.json()
    assert "alerts" in data
    assert "unread_count" in data


def test_gap_analysis_endpoint(client):
    response = client.get("/api/v1/gap-analysis?regulator=EMIR")
    assert response.status_code == 200
    data = response.json()
    assert data["regulator"] == "EMIR"
    assert "compliance_score_percentage" in data
    assert len(data["gaps"]) > 0


def test_checklist_endpoint(client):
    response = client.get("/api/v1/checklist?framework=MiFID+II")
    assert response.status_code == 200
    data = response.json()
    assert data["framework"] == "MiFID II"
    assert data["total_checks"] > 0


def test_internal_embed_chunks_webhook(client):
    payload = {
        "docId": 99,
        "regulator": "TEST_REGULATOR",
        "chunks": [
            {
                "chunkId": "TEST-CHUNK-01",
                "documentId": 99,
                "parentSectionId": "Section 1",
                "pageNumber": 1,
                "text": "All test trades must be reported within 24 hours.",
            }
        ],
    }
    response = client.post("/api/v1/internal/embed-chunks", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["chunks_processed"] == 1
