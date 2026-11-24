from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    return {"status": "ok", "service": "AtendeAI API"}


@router.get("/api/v1/services/health")
def service_health():
    settings = get_settings()
    return {
        "api": "ok",
        "ai": "configured" if settings.ai_api_key and settings.ai_model else "not_configured",
        "n8n": "configured" if settings.n8n_webhook_url else "not_configured",
    }
