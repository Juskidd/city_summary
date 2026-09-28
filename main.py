import argparse
import json
import re
import sys

from clients.errors import ExternalServiceError, NotFoundError
from processing.service import build_city_summary


def city_argument(value: str) -> str:
    value = value.strip()
    if not value:
        raise argparse.ArgumentTypeError("Название города не должно быть пустым")
    return value


def currency_argument(value: str) -> str:
    value = value.strip().upper()
    if not re.fullmatch(r"[A-Z]{3}", value):
        raise argparse.ArgumentTypeError(
            "Код валюты должен состоять из 3 латинских букв"
        )
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Погода и курс валюты для города")
    parser.add_argument(
        "--city", required=True, type=city_argument, help="Название города"
    )
    parser.add_argument(
        "--currency", default="USD", type=currency_argument, help="ISO-код валюты"
    )
    parser.add_argument("--json", action="store_true", help="Вывести сводку в JSON")
    args = parser.parse_args(argv)
    try:
        summary = build_city_summary(args.city, args.currency)
    except NotFoundError as exc:
        print(f"Ошибка: {exc}", file=sys.stderr)
        return 3
    except ExternalServiceError as exc:
        print(f"Ошибка: {exc}", file=sys.stderr)
        return 4

    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False))
    else:
        weather, rates = summary["weather"], summary["rates"]
        print(f"Город: {summary['city']}")
        print(f"Погода: {weather['temp_c']:.1f}°C, {weather['description']}")
        print(f"Тёплая одежда: {'да' if weather['warm_clothes'] else 'нет'}")
        print(f"{rates['currency']}→RUB: {rates['rate_to_rub']:.2f}")
        print(f"Дорогой курс: {'да' if rates['expensive'] else 'нет'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
