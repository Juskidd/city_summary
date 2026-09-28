import unittest
from unittest.mock import patch

from clients.errors import ExternalServiceError, HTTPStatusError, NotFoundError
from clients.rates import get_rate
from clients.weather import get_weather


class ClientTests(unittest.TestCase):
    @patch("clients.weather.get_json")
    def test_weather(self, get):
        get.side_effect = [
            {"results": [{"latitude": 55.75, "longitude": 37.62}]},
            {"current": {"temperature_2m": -3.2, "weather_code": 0}},
        ]
        self.assertEqual(get_weather("Moscow"), {"temp_c": -3.2, "description": "ясно"})
        self.assertEqual(get.call_args.args[1]["latitude"], 55.75)
        self.assertEqual(get.call_args.args[1]["temperature_unit"], "celsius")

    @patch("clients.weather.get_json")
    def test_missing_city(self, get):
        for data in [{}, {"results": []}, {"generationtime_ms": 1}]:
            get.return_value = data
            with self.assertRaises(NotFoundError):
                get_weather("missing")

    @patch("clients.weather.get_json")
    def test_invalid_location(self, get):
        for data in [
            {"results": None},
            {"results": {}},
            {"results": [None]},
            {"results": [{}]},
            {"results": [{"latitude": True, "longitude": 0}]},
            {"results": [{"latitude": 91, "longitude": 0}]},
            {"error": True},
        ]:
            with self.subTest(data=data):
                get.return_value = data
                with self.assertRaises(ExternalServiceError):
                    get_weather("Moscow")

    @patch("clients.weather.get_json")
    def test_invalid_weather(self, get):
        for data in [
            {},
            {"current": []},
            {"current": {}},
            {"current": {"temperature_2m": None, "weather_code": 0}},
            {"current": {"temperature_2m": float("nan"), "weather_code": 0}},
            {"current": {"temperature_2m": 2, "weather_code": True}},
            {"current": {"temperature_2m": 2, "weather_code": 999}},
        ]:
            get.side_effect = [{"results": [{"latitude": 0, "longitude": 0}]}, data]
            with self.assertRaises(ExternalServiceError):
                get_weather("Moscow")

    @patch("clients.rates.get_json")
    def test_rates(self, get):
        get.return_value = {"base": "EUR", "quote": "RUB", "rate": 105.5}
        self.assertEqual(get_rate("eur"), 105.5)
        get.assert_called_once_with("https://api.frankfurter.dev/v2/rate/EUR/RUB")
        get.reset_mock()
        self.assertEqual(get_rate("RUB"), 1)
        get.assert_not_called()

    @patch("clients.rates.get_json")
    def test_missing_currency(self, get):
        for status in [404, 422]:
            get.side_effect = HTTPStatusError(status)
            with self.assertRaises(NotFoundError):
                get_rate("ZZZ")
        get.side_effect = HTTPStatusError(403)
        with self.assertRaises(ExternalServiceError):
            get_rate("USD")

    @patch("clients.rates.get_json")
    def test_invalid_rate(self, get):
        for value in [None, True, "92", 0, -1, float("inf"), float("nan"), 10**400]:
            get.return_value = {"base": "USD", "quote": "RUB", "rate": value}
            with self.assertRaises(ExternalServiceError):
                get_rate("USD")
        for data in [{}, {"base": "EUR", "quote": "RUB", "rate": 92}]:
            get.return_value = data
            with self.assertRaises(ExternalServiceError):
                get_rate("USD")
