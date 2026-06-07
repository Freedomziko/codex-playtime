import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from scripts.codex_playtime import read_task_runtimes


class ReadTaskRuntimesTest(unittest.TestCase):
    def test_since_filters_by_task_completion_date(self):
        with tempfile.TemporaryDirectory() as tmp:
            codex_home = Path(tmp)
            sessions_dir = codex_home / "sessions"
            sessions_dir.mkdir()
            session_file = sessions_dir / "thread-a.jsonl"
            events = [
                {"type": "session_meta", "payload": {"id": "thread-a", "cwd": "C:\\repo-a"}},
                {
                    "type": "event_msg",
                    "payload": {"type": "task_complete", "duration_ms": 60_000},
                    "timestamp": "2026-06-01T09:01:00Z",
                },
                {
                    "type": "event_msg",
                    "payload": {"type": "task_complete", "duration_ms": 120_000},
                    "timestamp": "2026-06-05T09:01:00Z",
                },
            ]
            session_file.write_text("\n".join(json.dumps(event) for event in events), encoding="utf-8")

            runtimes = read_task_runtimes(codex_home, since=date(2026, 6, 2))

        self.assertEqual([runtime.seconds for runtime in runtimes], [120])


if __name__ == "__main__":
    unittest.main()
