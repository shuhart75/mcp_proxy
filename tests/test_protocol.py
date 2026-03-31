from __future__ import annotations

import io
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from confluence_section_mcp.server import _read_message


class ProtocolTests(unittest.TestCase):
    def test_read_message_accepts_lf_only_headers(self) -> None:
        payload = {"jsonrpc": "2.0", "id": 1, "method": "ping"}
        body = json.dumps(payload).encode("utf-8")
        raw = b"Content-Length: " + str(len(body)).encode("ascii") + b"\n\n" + body
        parsed = _read_message(io.BytesIO(raw))
        self.assertEqual(parsed, payload)


if __name__ == "__main__":
    unittest.main()
