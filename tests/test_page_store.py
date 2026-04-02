from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from confluence_section_mcp.adapters import PageSnapshot
from lib_page_store import read_snapshot_from_file_root, write_snapshot_to_file_root


class PageStoreTests(unittest.TestCase):
    def test_round_trip_snapshot_to_file_root(self) -> None:
        snapshot = PageSnapshot(
            page_id="123",
            title="Title",
            version=7,
            body="<h1>Scope</h1><p>Alpha</p>",
            body_format="storage",
            space_id="42",
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            stored = write_snapshot_to_file_root(snapshot, root)
            self.assertTrue(Path(stored["page_path"]).exists())
            loaded = read_snapshot_from_file_root("123", root)
            self.assertEqual(loaded.title, "Title")
            self.assertEqual(loaded.version, 7)
            self.assertEqual(loaded.body_format, "storage")
            self.assertEqual(loaded.space_id, "42")
            self.assertIn("Alpha", loaded.body)


if __name__ == "__main__":
    unittest.main()
