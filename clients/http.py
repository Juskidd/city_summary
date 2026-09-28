import math
import time
from typing import Any

import requests

from clients.errors import ExternalServiceError, HTTPStatusError

TIMEOUT = 10
ATTEMPTS = 3
RETRY_STATUSES = {429, 500, 502, 503, 504}


def retry_delay(value: str | None, attempt: int) -> float:
    """Числовой Retry-After задаёт минимальную паузу между попытками."""
    backoff = float(2**attempt)
    try:
        seconds = float(value) if value is not None else 0.0
    except ValueError:
        return backoff
    if not math.isfinite(seconds) or seconds < 0:
        return backoff
    return max(backoff, seconds)


def get_json(url: str, params: dict | None = None) -> dict[str, Any]:
    for attempt in range(ATTEMPTS):
        try:
            response = requests.get(
                url,
                params=params,
                timeout=TIMEOUT,
                headers={"Accept": "application/json"},
            )
        except (
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError,
        ) as exc:
            if attempt == ATTEMPTS - 1:
                raise ExternalServiceError(
                    "Нет соединения с внешним сервисом после 3 попыток"
                ) from exc
            time.sleep(2**attempt)
            continue
        except requests.exceptions.RequestException as exc:
            raise ExternalServiceError("Не удалось выполнить внешний запрос") from exc

        with response:
            status = response.status_code
            if status in RETRY_STATUSES:
                if attempt == ATTEMPTS - 1:
                    raise ExternalServiceError(
                        f"Внешний сервис недоступен после 3 попыток (HTTP {status})"
                    )
                delay = retry_delay(
                    response.headers.get("Retry-After") if status == 429 else None,
                    attempt,
                )
            elif not 200 <= status < 300:
                raise HTTPStatusError(status)
            else:
                content_type = response.headers.get("Content-Type", "").split(";")[0]
                content_type = content_type.strip().lower()
                if content_type != "application/json" and not content_type.endswith(
                    "+json"
                ):
                    raise ExternalServiceError("Внешний сервис вернул ответ не в JSON")
                try:
                    data = response.json()
                except ValueError as exc:
                    raise ExternalServiceError(
                        "Внешний сервис вернул повреждённый JSON"
                    ) from exc
                if not isinstance(data, dict):
                    raise ExternalServiceError(
                        "Ожидался JSON-объект от внешнего сервиса"
                    )
                return data
        time.sleep(delay)
    raise ExternalServiceError("Исчерпаны попытки запроса")


def number(value: Any, field: str) -> float:
    if type(value) not in (int, float):
        raise ExternalServiceError(f"Некорректное числовое поле: {field}")
    try:
        result = float(value)
    except OverflowError as exc:
        raise ExternalServiceError(f"Слишком большое значение: {field}") from exc
    if not math.isfinite(result):
        raise ExternalServiceError(f"Неконечное значение: {field}")
    return result
