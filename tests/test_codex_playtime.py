from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.codex_playtime import read_task_runtimes, summarize


def write_jsonl(path: Path, rows: list[dict] | list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            if isinstance(row, str):
                handle.write(row + "\n")
            else:
                handle.write(json.dumps(row) + "\n")


class CodexPlaytimeTests(unittest.TestCase):
    def test_reads_active_and_archived_sessions_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            codex_home = Path(tmp)
            write_jsonl(
                codex_home / "session_index.jsonl",
                [
                    {"id": "active-thread", "thread_name": "Active chat"},
                    {"id": "archived-thread", "thread_name": "Archived chat"},
                ],
            )
            write_jsonl(
                codex_home / "sessions" / "2026" / "active.jsonl",
                [
                    {"type": "session_meta", "payload": {"id": "active-thread", "cwd": "C:/work/app"}},
                    {"type": "event_msg", "payload": {"type": "task_complete", "duration_ms": 90000}},
                ],
            )
            write_jsonl(
                codex_home / "archived_sessions" / "2025" / "archived.jsonl",
                [
                    {"type": "session_meta", "payload": {"id": "archived-thread", "cwd": "C:/work/archive"}},
                    {"type": "event_msg", "payload": {"type": "task_complete", "duration_ms": 30000}},
                ],
            )

            names, by_thread, by_project = summarize(read_task_runtimes(codex_home))

        self.assertEqual(names["active-thread"], "Active chat")
        self.assertEqual(names["archived-thread"], "Archived chat")
        self.assertEqual(by_thread["active-thread"], 90)
        self.assertEqual(by_thread["archived-thread"], 30)
        self.assertEqual(by_project["C:/work/app"], 90)
        self.assertEqual(by_project["C:/work/archive"], 30)

    def test_can_skip_archived_sessions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            codex_home = Path(tmp)
            write_jsonl(
                codex_home / "sessions" / "active.jsonl",
                [{"type": "event_msg", "payload": {"type": "task_complete", "duration_ms": 60000}}],
            )
            write_jsonl(
                codex_home / "archived_sessions" / "archived.jsonl",
                [{"type": "event_msg", "payload": {"type": "task_complete", "duration_ms": 60000}}],
            )

            runtimes = read_task_runtimes(codex_home, include_archived=False)

        self.assertEqual(len(runtimes), 1)

    def test_ignores_malformed_and_negative_duration_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            codex_home = Path(tmp)
            write_jsonl(
                codex_home / "sessions" / "chat.jsonl",
                [
                    "{not valid json",
                    {"type": "turn_context", "payload": {"cwd": "C:/work/current"}},
                    {"type": "event_msg", "payload": {"type": "task_complete", "duration_ms": -1}},
                    {"type": "event_msg", "payload": {"type": "task_complete", "duration_ms": 45000}},
                ],
            )

            runtimes = read_task_runtimes(codex_home)

        self.assertEqual(len(runtimes), 1)
        self.assertEqual(runtimes[0].cwd, "C:/work/current")
        self.assertEqual(runtimes[0].seconds, 45)


if __name__ == "__main__":
    unittest.main()
