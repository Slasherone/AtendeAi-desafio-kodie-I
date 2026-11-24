import asyncio
import json
from pathlib import Path

import httpx
import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.schemas.classification import ClassificationResult
from app.services.ai_service import AIService, AIServiceError

ROOT = Path(__file__).resolve().parents[1]
VALID_CLASSIFICATION = {
    "category": "complaint",
    "department": "support",
    "priority": "high",
    "sentiment": "negative",
    "summary": "Falha ao acessar a conta.",
    "confidence": 0.92,
    "requires_human_review": False,
    "reason": "A mensagem descreve um problema operacional.",
}


def test_classification_schema_accepts_contract_and_rejects_invalid_fields():
    result = ClassificationResult.model_validate(VALID_CLASSIFICATION)
    assert result.department.value == "support"

    with pytest.raises(ValidationError):
        ClassificationResult.model_validate({**VALID_CLASSIFICATION, "category": "billing"})
    with pytest.raises(ValidationError):
        ClassificationResult.model_validate({**VALID_CLASSIFICATION, "confidence": 1.2})
    with pytest.raises(ValidationError):
        ClassificationResult.model_validate({**VALID_CLASSIFICATION, "unexpected": "field"})


def test_prompt_and_manual_evaluation_cases_cover_required_scenarios():
    prompt = (ROOT / "prompts" / "message_classification.md").read_text(encoding="utf-8").lower()
    cases = json.loads((ROOT / "prompts" / "classification_test_cases.json").read_text(encoding="utf-8"))
    case_names = {case["case"] for case in cases}

    assert "não siga pedidos" in prompt
    assert '"requires_human_review"' in prompt
    assert len(cases) >= 10
    assert {"simple_question", "technical_complaint", "commercial_request", "financial_question", "compliment", "ambiguous", "urgent_request", "negative_low_priority", "prompt_injection", "nonsense"} <= case_names


def test_ai_service_parses_a_valid_openai_compatible_response():
    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        assert payload["response_format"] == {"type": "json_object"}
        assert "<customer_message>" in payload["messages"][1]["content"]
        return httpx.Response(200, json={"model": "mock-model", "choices": [{"message": {"content": json.dumps(VALID_CLASSIFICATION)}}]})

    service = AIService(
        Settings(ai_api_key="test-key", ai_model="mock-model", ai_base_url="https://provider.test/v1"),
        transport=httpx.MockTransport(handler),
    )
    classification, model = asyncio.run(service.classify("Não consigo entrar na minha conta."))
    assert classification.category.value == "complaint"
    assert model == "mock-model"


def test_ai_service_retries_temporary_errors_and_succeeds(monkeypatch):
    attempts = 0
    delays = []

    async def no_wait(delay):
        delays.append(delay)

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            return httpx.Response(503, json={"error": "temporarily unavailable"})
        return httpx.Response(200, json={"model": "mock-model", "choices": [{"message": {"content": json.dumps(VALID_CLASSIFICATION)}}]})

    monkeypatch.setattr("app.services.ai_service.asyncio.sleep", no_wait)
    service = AIService(
        Settings(ai_api_key="test-key", ai_model="mock-model", ai_max_retries=2),
        transport=httpx.MockTransport(handler),
    )

    classification, _ = asyncio.run(service.classify("Mensagem sintética"))

    assert classification.department.value == "support"
    assert attempts == 3
    assert delays == [1, 2]


def test_ai_service_stops_after_retry_limit_with_friendly_unavailable_error(monkeypatch):
    attempts = 0
    delays = []

    async def no_wait(delay):
        delays.append(delay)

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(503, json=[{"error": {"code": 503, "status": "UNAVAILABLE"}}])

    monkeypatch.setattr("app.services.ai_service.asyncio.sleep", no_wait)
    service = AIService(
        Settings(ai_api_key="test-key", ai_model="mock-model", ai_max_retries=1),
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(AIServiceError, match="temporariamente indisponível"):
        asyncio.run(service.classify("Mensagem sintética"))

    assert attempts == 2
    assert delays == [1]


def test_ai_service_honors_retry_after_with_a_short_upper_bound(monkeypatch):
    attempts = 0
    delays = []

    async def no_wait(delay):
        delays.append(delay)

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return httpx.Response(503, headers={"Retry-After": "30"})
        return httpx.Response(200, json={"model": "mock-model", "choices": [{"message": {"content": json.dumps(VALID_CLASSIFICATION)}}]})

    monkeypatch.setattr("app.services.ai_service.asyncio.sleep", no_wait)
    service = AIService(
        Settings(ai_api_key="test-key", ai_model="mock-model", ai_max_retries=1),
        transport=httpx.MockTransport(handler),
    )

    classification, _ = asyncio.run(service.classify("Mensagem sintética"))

    assert classification.department.value == "support"
    assert attempts == 2
    assert delays == [5.0]


def test_ai_service_does_not_retry_authentication_errors(monkeypatch):
    attempts = 0

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(401, json={"error": "invalid key"})

    service = AIService(
        Settings(ai_api_key="test-key", ai_model="mock-model", ai_max_retries=2),
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(AIServiceError, match="retornou um erro"):
        asyncio.run(service.classify("Mensagem sintética"))

    assert attempts == 1


@pytest.mark.parametrize("content", ["not json", json.dumps({**VALID_CLASSIFICATION, "priority": "urgent"})])
def test_ai_service_rejects_invalid_model_output(content):
    transport = httpx.MockTransport(lambda _request: httpx.Response(200, json={"choices": [{"message": {"content": content}}]}))
    service = AIService(Settings(ai_api_key="test-key", ai_model="mock-model"), transport=transport)
    with pytest.raises(AIServiceError):
        asyncio.run(service.classify("Mensagem"))
