from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from confluence_section_mcp.adapters import build_adapter
from confluence_section_mcp.gigacode_settings import build_app_config_from_gigacode_settings


class GigaCodeSettingsTests(unittest.TestCase):
    def test_builds_mcp_config_from_gigacode_settings(self) -> None:
        fake_server = Path(__file__).resolve().parent / "fixtures" / "fake_upstream_server.py"
        settings = {
            "mcpServers": {
                "Atlassian": {
                    "command": "python3",
                    "args": [str(fake_server)],
                    "env": {
                        "CONFLUENCE_URL": "https://example.invalid",
                        "CONFLUENCE_SSL_VERIFY": False,
                    },
                }
            }
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            settings_path = Path(tmpdir) / "settings.json"
            settings_path.write_text(json.dumps(settings), encoding="utf-8")
            config = build_app_config_from_gigacode_settings(str(settings_path))

        self.assertEqual(config.mode, "mcp")
        assert config.upstream_mcp is not None
        self.assertEqual(config.upstream_mcp.command, "python3")
        self.assertEqual(config.upstream_mcp.args, ["-u", str(fake_server)])
        self.assertEqual(config.upstream_mcp.page_id_arg, "page_id")
        self.assertEqual(config.upstream_mcp.body_arg, "content")
        self.assertEqual(config.upstream_mcp.env["CONFLUENCE_SSL_VERIFY"], "false")
        self.assertEqual(config.upstream_mcp.env["PYTHONUNBUFFERED"], "1")
        self.assertTrue(config.upstream_mcp.get_page_extra_args["convert_to_markdown"])

    def test_built_config_can_fetch_from_upstream(self) -> None:
        fake_server = Path(__file__).resolve().parent / "fixtures" / "fake_upstream_server.py"
        settings = {
            "mcpServers": {
                "Atlassian": {
                    "command": "python3",
                    "args": [str(fake_server)],
                    "env": {},
                }
            }
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            settings_path = Path(tmpdir) / "settings.json"
            settings_path.write_text(json.dumps(settings), encoding="utf-8")
            config = build_app_config_from_gigacode_settings(str(settings_path))
            adapter = build_adapter(config)
            try:
                snapshot = adapter.get_page("demo-page")
            finally:
                adapter.close()

        self.assertEqual(snapshot.page_id, "demo-page")
        self.assertIn("Original upstream text.", snapshot.body)


if __name__ == "__main__":
    unittest.main()
