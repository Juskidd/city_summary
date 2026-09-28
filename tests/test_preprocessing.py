import unittest
from unittest.mock import patch

from processing.preprocessing import prepare_rate, prepare_weather
from processing.service import build_city_summary


class ProcessingTests(unittest.TestCase):
    def test_thresholds_and_no_mutation(self):
        for temp, expected in [(-0.1, True), (0, False), (2, False)]:
            source = {"temp_c": temp, "description": "ясно"}
            self.assertIs(prepare_weather(source)["warm_clothes"], expected)
            self.assertNotIn("warm_clothes", source)
        for rate, expected in [(99, False), (100, False), (100.01, True)]:
            self.assertIs(prepare_rate("USD", rate)["expensive"], expected)

    @patch(
        "processing.service.get_weather",
        return_value={"temp_c": -1, "description": "ясно"},
    )
    @patch("processing.service.get_rate", return_value=101)
    def test_summary(self, rate, weather):
        summary = build_city_summary(" Moscow ", " eur ")
        self.assertEqual(
            summary,
            {
                "city": "Moscow",
                "weather": {"temp_c": -1, "description": "ясно", "warm_clothes": True},
                "rates": {"currency": "EUR", "rate_to_rub": 101, "expensive": True},
            },
        )
        rate.assert_called_once_with("EUR")
        weather.assert_called_once_with("Moscow")
