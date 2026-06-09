from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from scripts.codex_playtime import parse_session_timestamp, read_task_runtimes


class CodexPlaytimeTests(unittest.TestCase):
    def test_parse_session_timestamp_accepts_iso_z_suffix(self) -> None:
        parsed = parse_session_timestamp("2026-06-09T10:15:30Z")

        self.assertEqual(parsed, datetime(2026, 6, 9, 10, 15, 30, tzinfo=timezone.utc))

    def test_read_task_runtimes_filters_by_completion_date(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            codex_home = Path(temp_dir)
            sessions_dir = codex_home / "sessions" / "2026" / "06" / "09"
            sessions_dir.mkdir(parents=True)
            session_path = sessions_dir / "thread.jsonl"
            records = [
                {
                    "type": "session_meta",
                    "payload": {
                        "id": "thread-1",
                        "cwd": "C:/workspace/example",
                    },
                },
                {
                    "timestamp": "2026-06-08T23:59:59Z",
                    "type": "event_msg",
                    "payload": {
                        "type": "task_complete",
                        "duration_ms": 30_000,
                    },
                },
                {
                    "timestamp": "2026-06-09T00:00:00Z",
                    "type": "event_msg",
                    "payload": {
                        "type": "task_complete",
                        "duration_ms": 90_000,
                    },
                },
            ]
            session_path.write_text("\n".join(json.dumps(record) for record in records), encoding="utf-8")

            runtimes = read_task_runtimes(
                codex_home,
                since=datetime(2026, 6, 9, tzinfo=timezone.utc),
            )

        self.assertEqual(len(runtimes), 1)
        self.assertEqual(runtimes[0].seconds, 90)
        self.assertEqual(runtimes[0].thread_id, "thread-1")


if __name__ == "__main__":
    unittest.main()
