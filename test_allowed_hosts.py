import unittest
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.testclient import TestClient

with patch("pathlib.Path.exists", lambda path: path.name in {"s3.env", "elastic.env"}):
    from config import parse_allowed_hosts


class AllowedHostsConfigTests(unittest.TestCase):
    def test_default_allowed_hosts(self):
        self.assertEqual(parse_allowed_hosts(None), ["localhost", "127.0.0.1"])
        self.assertEqual(parse_allowed_hosts(""), ["localhost", "127.0.0.1"])

    def test_multiple_comma_separated_hosts(self):
        self.assertEqual(
            parse_allowed_hosts("localhost,127.0.0.1,linuc.local"),
            ["localhost", "127.0.0.1", "linuc.local"],
        )

    def test_whitespace_and_empty_items(self):
        self.assertEqual(
            parse_allowed_hosts(" localhost, ,127.0.0.1,, linuc.local "),
            ["localhost", "127.0.0.1", "linuc.local"],
        )


class TrustedHostMiddlewareTests(unittest.TestCase):
    def setUp(self):
        app = FastAPI()
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=parse_allowed_hosts("localhost,linuc.local"),
        )

        @app.get("/")
        async def root():
            return {"status": "ok"}

        self.client = TestClient(app)

    def test_request_with_allowed_host(self):
        response = self.client.get("/", headers={"Host": "linuc.local"})

        self.assertEqual(response.status_code, 200)

    def test_request_with_disallowed_host(self):
        response = self.client.get("/", headers={"Host": "example.com"})

        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
