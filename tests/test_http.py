import unittest
from unittest.mock import patch

import requests

from clients.errors import ExternalServiceError, HTTPStatusError
from clients.http import get_json, retry_delay
from tests.helpers import response


class HTTPTests(unittest.TestCase):
    @patch("clients.http.time.sleep")
    @patch("clients.http.requests.get")
    def test_retry_then_success(self, get, sleep):
        for failure in [
            requests.Timeout(),
            requests.ConnectionError(),
            500,
            502,
            503,
            504,
            429,
        ]:
            with self.subTest(failure=failure):
                get.reset_mock()
                sleep.reset_mock()
                get.side_effect = [
                    response(failure) if isinstance(failure, int) else failure,
                    response(failure) if isinstance(failure, int) else failure,
                    response(data={"ok": True}),
                ]
                self.assertEqual(get_json("https://example.test"), {"ok": True})
                self.assertEqual(get.call_count, 3)
                self.assertEqual([c.args[0] for c in sleep.call_args_list], [1, 2])
                for call in get.call_args_list:
                    self.assertLessEqual(call.kwargs["timeout"], 10)
                    self.assertGreater(call.kwargs["timeout"], 0)

    @patch("clients.http.time.sleep")
    @patch("clients.http.requests.get")
    def test_exhaustion(self, get, sleep):
        for failure in [
            requests.Timeout(),
            requests.ConnectionError(),
            500,
            502,
            503,
            504,
            429,
        ]:
            with self.subTest(failure=failure):
                get.reset_mock()
                sleep.reset_mock()
                get.side_effect = [
                    response(failure) if isinstance(failure, int) else failure
                    for _ in range(3)
                ]
                with self.assertRaises(ExternalServiceError):
                    get_json("https://example.test")
                self.assertEqual(get.call_count, 3)
                self.assertEqual(sleep.call_count, 2)

    @patch("clients.http.time.sleep")
    @patch("clients.http.requests.get")
    def test_retry_after(self, get, sleep):
        get.side_effect = [response(429, headers={"Retry-After": "7"}), response()]
        get_json("https://example.test")
        sleep.assert_called_once_with(7)
        for value in [None, "bad", "-5", "inf", "NaN", "Mon, 01 Jan 2024"]:
            self.assertEqual(retry_delay(value, 1), 2)
        self.assertEqual(retry_delay("3.5", 0), 3.5)

    @patch("clients.http.requests.get")
    def test_permanent_errors_not_retried(self, get):
        for status in [400, 401, 403, 404, 422]:
            with self.subTest(status=status):
                get.reset_mock()
                get.return_value = response(status)
                with self.assertRaises(HTTPStatusError) as error:
                    get_json("https://example.test")
                self.assertEqual(error.exception.status_code, status)
                get.assert_called_once()

    @patch("clients.http.requests.get")
    def test_invalid_json(self, get):
        broken = response()
        broken._content = b"{bad"
        for result in [
            broken,
            response(data=[]),
            response(headers={"Content-Type": "text/html"}),
        ]:
            get.return_value = result
            with self.assertRaises(ExternalServiceError):
                get_json("https://example.test")
