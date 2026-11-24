"""Make one small live classification request using the configured AI service."""

import asyncio
import argparse
import sys

import httpx

from app.core.config import get_settings
from app.services.ai_service import AIConfigurationError, AIService, AIServiceError


async def check(timeout: float | None = None) -> int:
    settings = get_settings() if timeout is None else get_settings().__class__(ai_timeout=timeout)
    try:
        result, model = await AIService(settings).classify(
            "Não consigo acessar minha conta desde ontem; o aplicativo apresenta erro."
        )
    except AIConfigurationError as exc:
        print(f"AI_CONNECTION=NOT_CONFIGURED ({exc})")
        return 2
    except AIServiceError as exc:
        cause = exc.__cause__
        if isinstance(cause, httpx.HTTPStatusError):
            print(f"AI_CONNECTION=FAILED status={cause.response.status_code}")
            try:
                detail = cause.response.json().get("error", {}).get("message", "")
                if settings.ai_api_key:
                    detail = detail.replace(settings.ai_api_key, "[redacted]")
                if detail:
                    print(f"DETAIL={detail[:300]}")
            except (ValueError, AttributeError):
                pass
        elif isinstance(cause, httpx.TimeoutException):
            print("AI_CONNECTION=FAILED timeout")
        else:
            print(f"AI_CONNECTION=FAILED ({exc})")
        return 1

    print("AI_CONNECTION=OK")
    print(f"model={model}")
    print(f"category={result.category.value}")
    print(f"department={result.department.value}")
    print(f"priority={result.priority.value}")
    print(f"sentiment={result.sentiment.value}")
    print(f"confidence={result.confidence:.2f}")
    print(f"requires_human_review={result.requires_human_review}")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout", type=float, help="override AI_TIMEOUT for this check")
    args = parser.parse_args()
    sys.exit(asyncio.run(check(args.timeout)))
