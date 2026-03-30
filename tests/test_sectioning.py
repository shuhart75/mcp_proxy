from __future__ import annotations

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from confluence_section_mcp.orchestrator import WorkItem, _render_command
from confluence_section_mcp.sectioning import apply_section_replacements, build_layout


class SectioningTests(unittest.TestCase):
    def test_marked_sections_round_trip(self) -> None:
        source = (
            "Intro\n"
            "<!-- BEGIN:alpha -->\n"
            "one\n"
            "<!-- END:alpha -->\n"
            "Middle\n"
            "<!-- BEGIN:beta -->\n"
            "two\n"
            "<!-- END:beta -->\n"
        )
        layout = build_layout(source, strategy="markers", max_chars=50)
        self.assertEqual([section.id for section in layout.sections], ["alpha", "beta"])

        merged = apply_section_replacements(layout, {"beta": "\nupdated\n"})
        self.assertIn("updated", merged)
        self.assertIn("one", merged)

    def test_heading_split_fallback(self) -> None:
        source = "# One\nhello\n## Two\nworld\n"
        layout = build_layout(source, strategy="headings", max_chars=50)
        self.assertEqual(layout.strategy, "headings")
        self.assertGreaterEqual(len(layout.sections), 2)

    def test_heading_chunking_by_size(self) -> None:
        source = "# Big\n" + ("x" * 25) + "\n" + ("y" * 25) + "\n"
        layout = build_layout(source, strategy="headings", max_chars=20)
        self.assertGreaterEqual(len(layout.sections), 2)

    def test_command_render_keeps_unrelated_braces(self) -> None:
        item = WorkItem(
            section_id="intro",
            label="Intro",
            input_file="/tmp/in.md",
            output_file="/tmp/out.md",
            instruction_file="/tmp/prompt.txt",
            command="",
        )
        rendered = _render_command(
            "awk 'BEGIN{print \"x\"} {print}' {input_file} > {output_file}",
            item,
        )
        self.assertIn("BEGIN{print \"x\"}", rendered)
        self.assertIn("/tmp/in.md", rendered)
        self.assertIn("/tmp/out.md", rendered)


if __name__ == "__main__":
    unittest.main()
