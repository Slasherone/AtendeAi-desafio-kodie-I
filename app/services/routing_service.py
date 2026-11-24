import httpx

from app.core.config import Settings, get_settings


class RoutingServiceError(Exception):
    """The routing automation could not complete successfully."""


class RoutingService:
    def __init__(self, settings: Settings | None = None, transport: httpx.AsyncBaseTransport | None = None):
        self.settings = settings or get_settings()
        self.transport = transport

    async def dispatch(self, payload: dict) -> dict | None:
        if not self.settings.n8n_webhook_url:
            return None
        if not self.settings.n8n_api_token:
            raise RoutingServiceError("O token de autenticação do n8n não está configurado.")
        headers = {}
        headers["X-AtendeAI-Token"] = self.settings.n8n_api_token
        try:
            async with httpx.AsyncClient(timeout=self.settings.n8n_timeout, transport=self.transport) as client:
                response = await client.post(self.settings.n8n_webhook_url, json=payload, headers=headers)
                response.raise_for_status()
                body = response.json()
            if not isinstance(body, dict) or body.get("status") not in {"completed", "success"}:
                raise RoutingServiceError("A automação não confirmou o encaminhamento.")
            return body
        except httpx.TimeoutException as exc:
            raise RoutingServiceError("O n8n excedeu o tempo limite.") from exc
        except httpx.HTTPError as exc:
            raise RoutingServiceError("Não foi possível comunicar com o n8n.") from exc


def get_routing_service() -> RoutingService:
    return RoutingService()
