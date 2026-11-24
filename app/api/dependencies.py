import secrets

from fastapi import Header, HTTPException, status

from app.core.config import get_settings


def require_internal_token(authorization: str | None = Header(default=None)) -> None:
    expected = get_settings().internal_api_token
    if not expected:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Integração interna não configurada.")
    provided = authorization.removeprefix("Bearer ") if authorization else ""
    if not secrets.compare_digest(provided, expected):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token interno inválido.")
