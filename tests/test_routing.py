import asyncio
import json
from pathlib import Path

import httpx
import pytest

from app.core.config import Settings
from app.services.routing_service import RoutingService, RoutingServiceError

ROOT = Path(__file__).resolve().parents[1]


def test_routing_posts_authenticated_payload_and_parses_result():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["X-AtendeAI-Token"] == "webhook-secret"
        assert json.loads(request.content)["attendance_id"] == "attendance-1"
        return httpx.Response(200, json={"status": "completed", "department": "support", "execution_id": "n8n-42"})

    service = RoutingService(
        Settings(n8n_webhook_url="https://n8n.test/webhook", n8n_api_token="webhook-secret"),
        transport=httpx.MockTransport(handler),
    )
    result = asyncio.run(service.dispatch({"attendance_id": "attendance-1"}))
    assert result["execution_id"] == "n8n-42"


def test_routing_refuses_unconfigured_auth_and_non_success_response():
    missing_token = RoutingService(Settings(n8n_webhook_url="https://n8n.test/webhook", n8n_api_token=""))
    with pytest.raises(RoutingServiceError, match="token"):
        asyncio.run(missing_token.dispatch({}))

    failing = RoutingService(
        Settings(n8n_webhook_url="https://n8n.test/webhook", n8n_api_token="secret"),
        transport=httpx.MockTransport(lambda _request: httpx.Response(200, json={"status": "failed"})),
    )
    with pytest.raises(RoutingServiceError, match="não confirmou"):
        asyncio.run(failing.dispatch({}))


def test_workflow_json_has_all_department_routes_and_credential_placeholders():
    workflow = json.loads((ROOT / "workflows" / "atendeai-workflow.json").read_text(encoding="utf-8"))
    node_names = {node["name"] for node in workflow["nodes"]}
    assert {"Webhook AtendeAI", "Validar payload", "Roteamento por departamento", "Registrar encaminhamento no FastAPI", "Responder ao FastAPI"} <= node_names
    assert {"Destino — Suporte", "Destino — Financeiro", "Destino — Comercial", "Destino — Atendimento geral"} <= node_names
    assert "CONFIGURE_WEBHOOK_HEADER_AUTH" in json.dumps(workflow)
    assert "CONFIGURE_INTERNAL_API_HEADER_AUTH" in json.dumps(workflow)
    callback = next(node for node in workflow["nodes"] if node["name"] == "Registrar encaminhamento no FastAPI")
    assert callback["parameters"]["url"] == "={{ 'http://api:8000/api/v1/internal/attendances/' + $json.attendance_id + '/route' }}"
    assert callback["parameters"]["options"]["response"]["response"]["neverError"] is True
