from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from confluence_section_mcp.config import load_app_config


class ConfigTests(unittest.TestCase):
    def test_loads_mcp_config_from_json_file(self) -> None:
        payload = {
            "mode": "mcp",
            "upstream_mcp": {
                "command": "/tmp/python",
                "args": ["/tmp/mcp-atlassian"],
                "env": {
                    "CONFLUENCE_URL": "https://example.atlassian.net"
                },
                "get_page_tool": "confluence_get_page",
                "update_page_tool": "confluence_update_page",
                "page_id_arg": "page_id",
                "body_arg": "content",
                "title_arg": "title",
                "get_page_extra_args": {
                    "convert_to_markdown": True
                },
                "update_page_extra_args": {
                    "content_format": "markdown"
                }
            }
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "config.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            config = load_app_config(str(path))

        self.assertEqual(config.mode, "mcp")
        assert config.upstream_mcp is not None
        self.assertEqual(config.upstream_mcp.command, "/tmp/python")
        self.assertEqual(config.upstream_mcp.args, ["/tmp/mcp-atlassian"])
        self.assertEqual(config.upstream_mcp.env["CONFLUENCE_URL"], "https://example.atlassian.net")
        self.assertEqual(config.upstream_mcp.get_page_tool, "confluence_get_page")
        self.assertTrue(config.upstream_mcp.get_page_extra_args["convert_to_markdown"])


if __name__ == "__main__":
    unittest.main()
