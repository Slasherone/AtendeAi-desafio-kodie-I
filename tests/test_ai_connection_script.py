import asyncio
import json
import sys

import httpx

import scripts.check_ai_connection as check_script
from app.core.config import Settings
from app.schemas.classification import ClassificationResult
from app.services.ai_service import AIServiceError

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


def test_check_prints_validated_json_and_defaults_to_no_retries(monkeypatch, capsys):
    settings = Settings(
        ai_provider="openai_compatible",
        ai_api_key="must-not-be-printed",
        ai_model="mock-model",
        ai_max_retries=2,
    )
    monkeypatch.setattr(check_script, "get_settings", lambda: settings)

    class FakeAIService:
        def __init__(self, received_settings):
            assert received_settings.ai_max_retries == 0
            assert received_settings.ai_model == "mock-model"

        async def classify(self, message):
            assert message == "Mensagem sintética"
            return ClassificationResult.model_validate(VALID_CLASSIFICATION), "mock-model"

    monkeypatch.setattr(check_script, "AIService", FakeAIService)
    exit_code = asyncio.run(check_script.check("Mensagem sintética"))

    output = capsys.readouterr().out
    result = json.loads(output)
    assert exit_code == 0
    assert result["ok"] is True
    assert result["provider"] == "openai_compatible"
    assert result["model"] == "mock-model"
    assert result["max_retries"] == 0
    assert result["classification"]["department"] == "support"
    assert result["message_characters"] == len("Mensagem sintética")
    assert "must-not-be-printed" not in output
    assert "Mensagem sintética" not in output


def test_check_reports_provider_status_without_exposing_credentials(monkeypatch, capsys):
    settings = Settings(
        ai_provider="openai_compatible",
        ai_api_key="must-not-be-printed",
        ai_model="mock-model",
    )
    monkeypatch.setattr(check_script, "get_settings", lambda: settings)

    class FakeAIService:
        def __init__(self, _settings):
            pass

        async def classify(self, _message):
            request = httpx.Request("POST", "https://provider.test/chat/completions")
            response = httpx.Response(503, request=request)
            cause = httpx.HTTPStatusError("upstream error", request=request, response=response)
            raise AIServiceError(
                "O provedor está temporariamente indisponível.",
                failure_stage="upstream_http",
                upstream_status=503,
            ) from cause

    monkeypatch.setattr(check_script, "AIService", FakeAIService)
    exit_code = asyncio.run(check_script.check("Mensagem sintética"))

    output = capsys.readouterr().out
    result = json.loads(output)
    assert exit_code == 1
    assert result["ok"] is False
    assert result["error"] == "provider_http_error"
    assert result["failure_stage"] == "upstream_http"
    assert result["http_status"] == 503
    assert "must-not-be-printed" not in output


def test_cli_accepts_custom_message_timeout_and_retry_limit(monkeypatch):
    received = {}

    async def fake_check(message, timeout, max_retries):
        received.update(message=message, timeout=timeout, max_retries=max_retries)
        return 0

    monkeypatch.setattr(check_script, "check", fake_check)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "check_ai_connection",
            "--message",
            "Teste",
            "--timeout",
            "45",
            "--max-retries",
            "2",
        ],
    )

    assert check_script.main() == 0
    assert received == {"message": "Teste", "timeout": 45.0, "max_retries": 2}
