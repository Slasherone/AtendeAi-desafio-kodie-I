"""Probe the active n8n webhook and its internal callback without creating a record."""

import asyncio
import sys

import httpx

from app.core.config import get_settings


async def check() -> int:
    settings = get_settings()
    if not settings.n8n_webhook_url or not settings.n8n_api_token:
        print("N8N_WEBHOOK=NOT_CONFIGURED")
        return 2

    # This UUID is deliberately absent from SQLite; an active workflow should reach
    # the protected callback and receive the expected 404 without creating data.
    payload = {
        "attendance_id": "00000000-0000-4000-8000-000000000000",
        "idempotency_key": "atendeai-n8n-connection-check",
        "department": "support",
        "priority": "low",
        "summary": "Synthetic n8n connectivity probe",
        "requires_human_review": False,
        "classification": {
            "category": "question",
            "department": "support",
            "priority": "low",
            "sentiment": "neutral",
            "summary": "Synthetic connectivity check",
            "confidence": 0.99,
            "requires_human_review": False,
            "reason": "Diagnostic payload; it must not be persisted.",
        },
    }
    try:
        async with httpx.AsyncClient(timeout=settings.n8n_timeout) as client:
            response = await client.post(
                settings.n8n_webhook_url,
                json=payload,
                headers={"X-AtendeAI-Token": settings.n8n_api_token},
            )
    except httpx.TimeoutException:
        print("N8N_WEBHOOK=TIMEOUT")
        return 1
    except httpx.HTTPError as exc:
        print(f"N8N_WEBHOOK=CONNECTION_ERROR ({type(exc).__name__})")
        return 1

    try:
        body = response.json()
    except ValueError:
        body = {}
    detail = body.get("detail") or body.get("error_message") or body.get("message") or ""

    if response.status_code == 404 and "Atendimento encaminhável não encontrado" in str(detail):
        print("N8N_WEBHOOK=ACTIVE; WEBHOOK_AUTH=OK; INTERNAL_API_AUTH=OK; callback reached the API")
        return 0
    if response.status_code in {401, 403} and "Token interno inválido" in str(detail):
        print("N8N_WEBHOOK=ACTIVE; INTERNAL_API_AUTH_FAILED")
        return 1
    if response.status_code in {401, 403}:
        print(f"N8N_WEBHOOK=AUTH_FAILED status={response.status_code}; detail={str(detail)[:180]}")
        return 1
    if response.status_code == 502 and "registrar" in str(detail).lower():
        print(f"N8N_WEBHOOK=ACTIVE; HTTP_REQUEST_NODE_FAILED; detail={str(detail)[:180]}")
        return 1
    if response.status_code == 404:
        detail = response.text.replace(settings.n8n_api_token, "[redacted]")[:240]
        print("N8N_WEBHOOK=NOT_REGISTERED_OR_INACTIVE")
        if detail:
            print(f"DETAIL={detail}")
        return 1
    print(f"N8N_WEBHOOK=UNEXPECTED status={response.status_code}; detail={str(detail)[:180]}")
    return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(check()))
