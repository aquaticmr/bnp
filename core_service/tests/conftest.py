import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.seed import seed_database_and_indices


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Initializes schema and seed clauses before tests run."""
    seed_database_and_indices()


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client
