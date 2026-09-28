import io
import json
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch

import requests

from main import main
from tests.helpers import response


class CLITests(unittest.TestCase):
    @patch("clients.http.requests.get")
    def test_end_to_end_output(self, get):
        for json_flag in [False, True]:
            get.side_effect = [
                response(data={"base": "USD", "quote": "RUB", "rate": 92.15}),
                response(data={"results": [{"latitude": 55, "longitude": 37}]}),
                response(data={"current": {"temperature_2m": -3.2, "weather_code": 0}}),
            ]
            stdout, stderr = io.StringIO(), io.StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                code = main(["--city", "Moscow"] + (["--json"] if json_flag else []))
            self.assertEqual(code, 0)
            self.assertEqual(stderr.getvalue(), "")
            if json_flag:
                summary = json.loads(stdout.getvalue())
                self.assertEqual(summary["rates"]["currency"], "USD")
                self.assertIs(summary["weather"]["warm_clothes"], True)
            else:
                self.assertIn("USD→RUB: 92.15", stdout.getvalue())
                self.assertIn("Тёплая одежда: да", stdout.getvalue())

    @patch("main.build_city_summary")
    def test_arguments(self, build):
        for args in [
            [],
            ["--city", " "],
            ["--city", "Moscow", "--currency", "US"],
            ["--city", "Moscow", "--currency", "123"],
            ["--unknown"],
        ]:
            with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
                main(args)
            self.assertEqual(error.exception.code, 2)
        build.assert_not_called()

    @patch("clients.http.time.sleep")
    @patch("clients.http.requests.get")
    def test_error_codes(self, get, sleep):
        cases = [
            ([response(422)], 3),
            (
                [
                    response(data={"base": "USD", "quote": "RUB", "rate": 90}),
                    response(data={"results": []}),
                ],
                3,
            ),
            ([requests.Timeout()] * 3, 4),
            ([response(503) for _ in range(3)], 4),
            ([response(data={"rate": "bad"})], 4),
        ]
        for replies, expected in cases:
            get.side_effect = replies
            stdout, stderr = io.StringIO(), io.StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                code = main(["--city", "Moscow"])
            self.assertEqual(code, expected)
            self.assertEqual(stdout.getvalue(), "")
            self.assertIn("Ошибка:", stderr.getvalue())
