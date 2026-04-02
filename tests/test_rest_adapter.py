from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from confluence_section_mcp.adapters import ConfluenceRestAdapter
from confluence_section_mcp.config import RestConfig


class _FakeResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self._payload = json.dumps(payload).encode("utf-8")

    def read(self) -> bytes:
        return self._payload

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


class RestAdapterTests(unittest.TestCase):
    def test_cloud_get_page_uses_v2_pages_endpoint_and_basic_auth(self) -> None:
        seen: dict[str, object] = {}

        def fake_urlopen(request, context=None):  # type: ignore[no-untyped-def]
            seen["url"] = request.full_url
            seen["auth"] = request.get_header("Authorization")
            return _FakeResponse(
                {
                    "id": "123",
                    "title": "Cloud page",
                    "version": {"number": 7},
                    "spaceId": "42",
                    "body": {"storage": {"value": "<p>cloud</p>"}},
                }
            )

        adapter = ConfluenceRestAdapter(
            RestConfig(
                base_url="https://example.atlassian.net",
                api_flavor="auto",
                body_format="storage",
                email="user@example.com",
                api_token="secret",
                bearer_token=None,
                default_space_id=None,
                ssl_verify=False,
                ca_bundle=None,
            )
        )
        with patch("confluence_section_mcp.adapters.urlopen", fake_urlopen):
            snapshot = adapter.get_page("123")

        self.assertEqual(snapshot.title, "Cloud page")
        self.assertEqual(seen["url"], "https://example.atlassian.net/wiki/api/v2/pages/123?body-format=storage")
        self.assertTrue(str(seen["auth"]).startswith("Basic "))

    def test_server_get_page_uses_server_endpoint_and_bearer_auth(self) -> None:
        seen: dict[str, object] = {}

        def fake_urlopen(request, context=None):  # type: ignore[no-untyped-def]
            seen["url"] = request.full_url
            seen["auth"] = request.get_header("Authorization")
            return _FakeResponse(
                {
                    "id": "123",
                    "title": "Server page",
                    "version": {"number": 9},
                    "space": {"id": 77},
                    "body": {"storage": {"value": "<p>server</p>"}},
                }
            )

        adapter = ConfluenceRestAdapter(
            RestConfig(
                base_url="https://confluence.example.internal",
                api_flavor="auto",
                body_format="storage",
                email=None,
                api_token=None,
                bearer_token="pat-token",
                default_space_id=None,
                ssl_verify=False,
                ca_bundle=None,
            )
        )
        with patch("confluence_section_mcp.adapters.urlopen", fake_urlopen):
            snapshot = adapter.get_page("123")

        self.assertEqual(snapshot.title, "Server page")
        self.assertEqual(snapshot.space_id, "77")
        self.assertEqual(seen["url"], "https://confluence.example.internal/rest/api/content/123?expand=body.storage%2Cversion%2Cspace")
        self.assertEqual(seen["auth"], "Bearer pat-token")


if __name__ == "__main__":
    unittest.main()
