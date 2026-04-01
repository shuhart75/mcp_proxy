from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from lib_markdown_chunks import merge_from_manifest, split_markdown, write_workspace


class MarkdownChunksTests(unittest.TestCase):
    def test_split_by_heading_and_merge_round_trip(self) -> None:
        source = "# One\nhello\n## Two\nworld\n"
        strategy, chunks = split_markdown(source, max_chars=100)
        self.assertEqual(strategy, "headings")
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            source_path = root / "page.md"
            source_path.write_text(source, encoding="utf-8")
            manifest_path = write_workspace(source_path, root / "workspace", source, strategy, chunks)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            first_edited = Path(manifest["chunks"][0]["edited_path"])
            first_edited.write_text("# One\nupdated\n", encoding="utf-8")
            result = merge_from_manifest(manifest_path, root / "merged.md")
            self.assertEqual(result["chunks"], len(chunks))
            merged = (root / "merged.md").read_text(encoding="utf-8")
            self.assertIn("updated", merged)
            self.assertIn("world", merged)

    def test_split_by_markers(self) -> None:
        source = "<!-- BEGIN:intro -->\nA\n<!-- END:intro -->\n"
        strategy, chunks = split_markdown(source, max_chars=20)
        self.assertEqual(strategy, "markers")
        self.assertEqual(chunks[0].chunk_id, "intro")

    def test_merge_preserves_chunk_boundary_newlines(self) -> None:
        source = (
            "<!-- BEGIN:intro -->\n"
            "# Intro\n"
            "Original intro text.\n"
            "<!-- END:intro -->\n\n"
            "<!-- BEGIN:details -->\n"
            "## Details\n"
            "Original details text.\n"
            "<!-- END:details -->\n"
        )
        strategy, chunks = split_markdown(source, max_chars=80)
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            source_path = root / "page.md"
            source_path.write_text(source, encoding="utf-8")
            manifest_path = write_workspace(source_path, root / "workspace", source, strategy, chunks)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            first_edited = Path(manifest["chunks"][0]["edited_path"])
            first_edited.write_text(
                "<!-- BEGIN:intro -->\n# Intro\nUpdated intro wording.\n<!-- END:intro -->\n",
                encoding="utf-8",
            )
            merge_from_manifest(manifest_path, root / "merged.md")
            merged = (root / "merged.md").read_text(encoding="utf-8")
            self.assertEqual(
                merged,
                (
                    "<!-- BEGIN:intro -->\n"
                    "# Intro\n"
                    "Updated intro wording.\n"
                    "<!-- END:intro -->\n\n"
                    "<!-- BEGIN:details -->\n"
                    "## Details\n"
                    "Original details text.\n"
                    "<!-- END:details -->\n"
                ),
            )


if __name__ == "__main__":
    unittest.main()
