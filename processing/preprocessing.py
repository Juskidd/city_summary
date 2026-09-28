def prepare_weather(weather: dict) -> dict:
    return {**weather, "warm_clothes": weather["temp_c"] < 0}


def prepare_rate(currency: str, rate: float) -> dict:
    return {"currency": currency, "rate_to_rub": rate, "expensive": rate > 100}
