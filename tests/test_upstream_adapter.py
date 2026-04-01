from __future__ import annotations

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from confluence_section_mcp.adapters import UpstreamMcpPageAdapter
from confluence_section_mcp.config import UpstreamMcpConfig


class UpstreamAdapterTests(unittest.TestCase):
    def test_mcp_adapter_hides_upstream_and_round_trips_body(self) -> None:
        fake_server = Path(__file__).resolve().parent / "fixtures" / "fake_upstream_server.py"
        adapter = UpstreamMcpPageAdapter(
            UpstreamMcpConfig(
                command="python3",
                args=[str(fake_server)],
                env={},
                env_passthrough=[],
                call_timeout_ms=60000,
                get_page_tool="getConfluencePage",
                update_page_tool="updateConfluencePage",
                page_id_arg="pageId",
                body_arg="body",
                title_arg="title",
                get_page_extra_args={},
                update_page_extra_args={},
            )
        )
        try:
            snapshot = adapter.get_page("demo-page")
            self.assertIn("Original upstream text.", snapshot.body)
            self.assertEqual(snapshot.title, "demo-page")

            updated = adapter.update_page(
                page_id="demo-page",
                title="Hidden Upstream",
                body="<!-- BEGIN:intro -->\nUpdated via proxy.\n<!-- END:intro -->\n",
                version=snapshot.version,
            )
            self.assertIn("Updated via proxy.", updated.body)
            self.assertEqual(updated.version, 1)
        finally:
            adapter.close()


if __name__ == "__main__":
    unittest.main()
