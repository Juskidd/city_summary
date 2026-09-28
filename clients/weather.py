from clients.errors import ExternalServiceError, NotFoundError
from clients.http import get_json, number

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
DESCRIPTIONS = {
    0: "ясно",
    1: "преимущественно ясно",
    2: "переменная облачность",
    3: "пасмурно",
    45: "туман",
    48: "туман с изморозью",
    51: "слабая морось",
    53: "морось",
    55: "сильная морось",
    56: "слабая ледяная морось",
    57: "сильная ледяная морось",
    61: "небольшой дождь",
    63: "дождь",
    65: "сильный дождь",
    66: "слабый ледяной дождь",
    67: "сильный ледяной дождь",
    71: "небольшой снег",
    73: "снег",
    75: "сильный снег",
    77: "снежные зёрна",
    80: "слабый ливень",
    81: "ливень",
    82: "сильный ливень",
    85: "слабый снежный ливень",
    86: "сильный снежный ливень",
    95: "гроза",
    96: "гроза со слабым градом",
    99: "гроза с сильным градом",
}


def get_weather(city: str) -> dict:
    location = get_json(GEOCODING_URL, {"name": city, "count": 1, "language": "ru"})
    if location.get("error"):
        raise ExternalServiceError("Ошибка сервиса геокодирования")
    # При отсутствии города Open-Meteo не присылает ключ results.
    if "results" not in location or location["results"] == []:
        raise NotFoundError(f"Город не найден: {city}")
    results = location["results"]
    if not isinstance(results, list) or not isinstance(results[0], dict):
        raise ExternalServiceError("Некорректный список городов")
    lat = number(results[0].get("latitude"), "latitude")
    lon = number(results[0].get("longitude"), "longitude")
    if not -90 <= lat <= 90 or not -180 <= lon <= 180:
        raise ExternalServiceError("Координаты города вне допустимого диапазона")
    data = get_json(
        WEATHER_URL,
        {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,weather_code",
            "temperature_unit": "celsius",
        },
    )
    current = data.get("current")
    if data.get("error") or not isinstance(current, dict):
        raise ExternalServiceError("В ответе погоды отсутствует объект current")
    temperature = number(current.get("temperature_2m"), "temperature_2m")
    code = current.get("weather_code")
    if type(code) is not int or code not in DESCRIPTIONS:
        raise ExternalServiceError("Неизвестный или некорректный код погоды")
    return {"temp_c": temperature, "description": DESCRIPTIONS[code]}
