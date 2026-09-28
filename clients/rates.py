from clients.errors import ExternalServiceError, HTTPStatusError, NotFoundError
from clients.http import get_json, number

RATES_URL = "https://api.frankfurter.dev/v2/rate"


def get_rate(currency: str) -> float:
    currency = currency.strip().upper()
    if currency == "RUB":
        return 1.0
    try:
        data = get_json(f"{RATES_URL}/{currency}/RUB")
    except HTTPStatusError as exc:
        if exc.status_code in (404, 422):
            raise NotFoundError(
                f"Валюта или курс к RUB не найдены: {currency}"
            ) from exc
        raise
    if data.get("base") != currency or data.get("quote") != "RUB":
        raise ExternalServiceError("В ответе курса неверная валютная пара")
    rate = number(data.get("rate"), "rate")
    if rate <= 0:
        raise ExternalServiceError("Курс валюты должен быть положительным")
    return rate
