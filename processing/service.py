from clients.rates import get_rate
from clients.weather import get_weather
from processing.preprocessing import prepare_rate, prepare_weather


def build_city_summary(city: str, currency: str = "USD") -> dict:
    city = city.strip()
    currency = currency.strip().upper()
    rate = get_rate(currency)
    weather = get_weather(city)
    return {
        "city": city,
        "weather": prepare_weather(weather),
        "rates": prepare_rate(currency, rate),
    }
