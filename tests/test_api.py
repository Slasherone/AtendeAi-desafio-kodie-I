import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.routes.attendances import get_ai_service, get_routing_service
from app.core.config import get_settings
from app.database.base import Base
from app.database.connection import get_db
from app.main import app
from app.schemas.classification import ClassificationResult
from app.services.routing_service import RoutingServiceError


class FakeAIService:
    def __init__(self, confidence=0.94):
        self.confidence = confidence

    async def classify(self, _message):
        return ClassificationResult(
            category="complaint",
            department="support",
            priority="high",
            sentiment="negative",
            summary="Cliente relata falha ao acessar a conta.",
            confidence=self.confidence,
            requires_human_review=False,
            reason="A mensagem descreve um problema técnico.",
        ), "mock-model"


class FakeRoutingService:
    async def dispatch(self, _payload):
        return None


class FailingRoutingService:
    async def dispatch(self, _payload):
        raise RoutingServiceError("Falha simulada no n8n.")


@pytest.fixture
def client(monkeypatch, tmp_path):
    monkeypatch.setenv("INTERNAL_API_TOKEN", "test-internal-token")
    monkeypatch.setenv("AI_CONFIDENCE_THRESHOLD", "0.70")
    monkeypatch.setenv("N8N_WEBHOOK_URL", "")
    get_settings.cache_clear()

    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    test_session = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def override_db():
        db = test_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_ai_service] = lambda: FakeAIService()
    app.dependency_overrides[get_routing_service] = lambda: FakeRoutingService()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    engine.dispose()
    get_settings.cache_clear()


def create_one(client, message="Não consigo acessar minha conta desde ontem."):
    return client.post("/api/v1/attendances", json={"source": "web", "message": message})


def test_health_and_attendance_create_list_and_detail(client):
    assert client.get("/health").json()["status"] == "ok"
    assert "AtendeAI" in client.get("/").text
    assert "import { api }" in client.get("/assets/js/app.js").text
    created = create_one(client)
    assert created.status_code == 201
    record = created.json()
    assert record["status"] == "classified"
    assert record["classification"]["department"] == "support"
    assert record["routing"]["status"] == "pending"

    listed = client.get("/api/v1/attendances", params={"search": "acessar", "page": 1, "page_size": 5})
    assert listed.status_code == 200
    assert listed.json()["total"] == 1
    assert listed.json()["items"][0]["id"] == record["id"]

    detail = client.get(f"/api/v1/attendances/{record['id']}")
    assert detail.status_code == 200
    assert "desde ontem" in detail.json()["original_message"]


def test_low_confidence_requires_human_review_and_blocks_dispatch(client):
    app.dependency_overrides[get_ai_service] = lambda: FakeAIService(confidence=0.5)
    created = create_one(client)
    data = created.json()
    assert data["status"] == "pending_review"
    assert data["classification"]["requires_human_review"] is True
    assert data["classification"]["review_reason"]
    assert data["routing"]["status"] == "held"
    retry = client.post(f"/api/v1/attendances/{data['id']}/dispatch")
    assert retry.status_code == 409


def test_routing_failure_preserves_the_classification(client, monkeypatch):
    monkeypatch.setenv("N8N_WEBHOOK_URL", "http://n8n.test/webhook/atendeai/route")
    get_settings.cache_clear()
    app.dependency_overrides[get_routing_service] = lambda: FailingRoutingService()

    response = create_one(client)
    data = response.json()

    assert response.status_code == 201
    assert data["status"] == "routing_failed"
    assert data["classification"]["department"] == "support"
    assert data["routing"]["status"] == "failed"
    assert data["routing"]["error_message"] == "Falha simulada no n8n."


def test_internal_route_requires_token_and_is_idempotent(client):
    created = create_one(client).json()
    endpoint = f"/api/v1/internal/attendances/{created['id']}/route"
    data = {"department": "support", "status": "completed", "execution_id": "execution-123"}
    assert client.post(endpoint, json=data).status_code == 401

    response = client.post(endpoint, json=data, headers={"Authorization": "Bearer test-internal-token"})
    assert response.status_code == 200
    assert response.json()["status"] == "completed"
    assert client.post(endpoint, json=data, headers={"Authorization": "Bearer test-internal-token"}).status_code == 200
    assert client.get(f"/api/v1/attendances/{created['id']}").json()["status"] == "routed"


def test_create_validates_message_and_department_mismatch(client):
    assert client.post("/api/v1/attendances", json={"message": ""}).status_code == 422
    assert client.post("/api/v1/attendances", json={"message": "   "}).status_code == 422
    created = create_one(client).json()
    mismatch = client.post(
        f"/api/v1/internal/attendances/{created['id']}/route",
        json={"department": "financial", "status": "completed"},
        headers={"Authorization": "Bearer test-internal-token"},
    )
    assert mismatch.status_code == 409


def test_analytics_use_persisted_records(client):
    create_one(client)
    overview = client.get("/api/v1/analytics/overview").json()
    assert overview["total"] == 1
    assert overview["classified"] == 1
    distribution = client.get("/api/v1/analytics/distribution").json()
    assert {item["key"] for item in distribution["department"]} == {"support"}
    timeline = client.get("/api/v1/analytics/timeline", params={"days": 7}).json()
    assert len(timeline["items"]) == 7
    assert sum(item["count"] for item in timeline["items"]) == 1
