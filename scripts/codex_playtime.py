from __future__ import annotations

import argparse
import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_IDLE_MINUTES = 10


@dataclass
class SessionEvent:
    timestamp: datetime
    thread_id: str
    thread_name: str
    cwd: str


def parse_timestamp(value: str) -> datetime:
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value).astimezone(timezone.utc)


def iter_session_files(codex_home: Path):
    sessions_dir = codex_home / "sessions"
    if not sessions_dir.exists():
        return
    yield from sessions_dir.rglob("*.jsonl")


def read_thread_names(codex_home: Path) -> dict[str, str]:
    names: dict[str, str] = {}
    index_path = codex_home / "session_index.jsonl"
    if not index_path.exists():
        return names

    with index_path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            thread_id = item.get("id")
            thread_name = item.get("thread_name")
            if thread_id and thread_name:
                names[thread_id] = thread_name

    return names


def read_events(codex_home: Path) -> list[SessionEvent]:
    events: list[SessionEvent] = []
    indexed_names = read_thread_names(codex_home)

    for path in iter_session_files(codex_home):
        thread_id = ""
        thread_name = path.stem
        cwd = ""

        with path.open("r", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                try:
                    item = json.loads(line)
                except json.JSONDecodeError:
                    continue

                timestamp_raw = item.get("timestamp")
                if not timestamp_raw:
                    continue

                payload = item.get("payload") or {}
                if item.get("type") == "session_meta":
                    thread_id = payload.get("id") or thread_id
                    cwd = payload.get("cwd") or cwd
                    thread_name = indexed_names.get(thread_id, thread_name)

                if payload.get("thread_name"):
                    thread_name = payload["thread_name"]

                events.append(
                    SessionEvent(
                        timestamp=parse_timestamp(timestamp_raw),
                        thread_id=thread_id or path.stem,
                        thread_name=thread_name,
                        cwd=cwd,
                    )
                )

    return sorted(events, key=lambda event: event.timestamp)


def summarize(events: list[SessionEvent], idle_minutes: int):
    idle_seconds = idle_minutes * 60
    by_thread: dict[str, float] = defaultdict(float)
    names: dict[str, str] = {}
    by_project: dict[str, float] = defaultdict(float)

    grouped: dict[str, list[SessionEvent]] = defaultdict(list)
    for event in events:
        grouped[event.thread_id].append(event)
        names[event.thread_id] = event.thread_name

    for thread_id, thread_events in grouped.items():
        for current, next_event in zip(thread_events, thread_events[1:]):
            gap = (next_event.timestamp - current.timestamp).total_seconds()
            if 0 <= gap <= idle_seconds:
                by_thread[thread_id] += gap
                if current.cwd:
                    by_project[current.cwd] += gap

    return names, by_thread, by_project


def format_duration(seconds: float) -> str:
    minutes = round(seconds / 60)
    hours, mins = divmod(minutes, 60)
    if hours:
        return f"{hours}h {mins}m"
    return f"{mins}m"


def main() -> int:
    parser = argparse.ArgumentParser(description="Estimate active time in Codex session logs.")
    parser.add_argument("--codex-home", default=str(Path.home() / ".codex"))
    parser.add_argument("--idle-minutes", type=int, default=DEFAULT_IDLE_MINUTES)
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()

    events = read_events(Path(args.codex_home))
    names, by_thread, by_project = summarize(events, args.idle_minutes)

    total = sum(by_thread.values())
    print(f"Total active Codex time: {format_duration(total)}")
    print()
    print("Top chats:")
    for thread_id, seconds in sorted(by_thread.items(), key=lambda item: item[1], reverse=True)[: args.limit]:
        print(f"- {names.get(thread_id, thread_id)}: {format_duration(seconds)}")

    print()
    print("Top projects:")
    for cwd, seconds in sorted(by_project.items(), key=lambda item: item[1], reverse=True)[: args.limit]:
        print(f"- {cwd}: {format_duration(seconds)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
