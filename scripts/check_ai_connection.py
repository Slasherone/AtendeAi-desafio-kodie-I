"""Send one message to the configured AI provider and print its validated result."""

import argparse
import asyncio
import json
import sys
from time import perf_counter

import httpx

from app.core.config import get_settings
from app.services.ai_service import AIConfigurationError, AIService, AIServiceError

DEFAULT_MESSAGE = "Não consigo acessar minha conta desde ontem; o aplicativo apresenta erro."


def _positive_timeout(value: str) -> float:
    try:
        timeout = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("informe um número em segundos") from exc
    if not 1 <= timeout <= 180:
        raise argparse.ArgumentTypeError("o timeout deve ficar entre 1 e 180 segundos")
    return timeout


def _retry_count(value: str) -> int:
    try:
        retries = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("informe um número inteiro") from exc
    if not 0 <= retries <= 3:
        raise argparse.ArgumentTypeError("o número de retries deve ficar entre 0 e 3")
    return retries


def _print_json(result: dict) -> None:
    print(json.dumps(result, ensure_ascii=False, indent=2))


async def check(
    message: str = DEFAULT_MESSAGE,
    timeout: float | None = None,
    max_retries: int = 0,
) -> int:
    settings = get_settings()
    overrides = {"ai_max_retries": max_retries}
    if timeout is not None:
        overrides["ai_timeout"] = timeout
    settings = settings.model_copy(update=overrides)

    started_at = perf_counter()
    try:
        classification, model = await AIService(settings).classify(message)
    except AIConfigurationError as exc:
        _print_json(
            {
                "ok": False,
                "error": "not_configured",
                "message": str(exc),
                "provider": settings.ai_provider,
                "elapsed_seconds": round(perf_counter() - started_at, 2),
            }
        )
        return 2
    except AIServiceError as exc:
        cause = exc.__cause__
        error = {
            "ok": False,
            "error": "classification_failed",
            "message": str(exc),
            "failure_stage": exc.failure_stage,
            "provider": settings.ai_provider,
            "elapsed_seconds": round(perf_counter() - started_at, 2),
            "max_retries": settings.ai_max_retries,
        }
        if exc.upstream_status is not None:
            error["error"] = "provider_http_error"
            error["http_status"] = exc.upstream_status
        elif isinstance(cause, httpx.HTTPStatusError):
            error["error"] = "provider_http_error"
            error["http_status"] = cause.response.status_code
        elif isinstance(cause, (httpx.TimeoutException, TimeoutError)):
            error["error"] = "timeout"
        elif isinstance(cause, httpx.HTTPError):
            error["error"] = "connection_error"
        _print_json(error)
        return 1

    _print_json(
        {
            "ok": True,
            "provider": settings.ai_provider,
            "model": model,
            "elapsed_seconds": round(perf_counter() - started_at, 2),
            "message_characters": len(message),
            "max_retries": settings.ai_max_retries,
            "classification": classification.model_dump(mode="json"),
        }
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--message",
        default=DEFAULT_MESSAGE,
        help="mensagem a classificar; se omitida, usa uma mensagem sintética",
    )
    parser.add_argument(
        "--timeout",
        type=_positive_timeout,
        help="timeout total em segundos (padrão: AI_TIMEOUT)",
    )
    parser.add_argument(
        "--max-retries",
        type=_retry_count,
        default=0,
        help="retries para erros transitórios; 0 faz uma única tentativa (padrão: 0)",
    )
    args = parser.parse_args()
    if not args.message.strip():
        parser.error("--message não pode estar vazia")
    return asyncio.run(check(args.message, args.timeout, args.max_retries))


if __name__ == "__main__":
    sys.exit(main())
