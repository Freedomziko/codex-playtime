from __future__ import annotations

import argparse
import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path


@dataclass
class TaskRuntime:
    thread_id: str
    thread_name: str
    cwd: str
    seconds: float
    completed_at: datetime | None


def iter_session_files(codex_home: Path, include_archived: bool = True):
    session_roots = [codex_home / "sessions"]
    if include_archived:
        session_roots.append(codex_home / "archived_sessions")

    for sessions_dir in session_roots:
        if sessions_dir.exists():
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


def parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None

    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def read_task_runtimes(codex_home: Path, include_archived: bool = True) -> list[TaskRuntime]:
    runtimes: list[TaskRuntime] = []
    indexed_names = read_thread_names(codex_home)

    for path in iter_session_files(codex_home, include_archived=include_archived):
        thread_id = ""
        thread_name = path.stem
        cwd = ""

        with path.open("r", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                try:
                    item = json.loads(line)
                except json.JSONDecodeError:
                    continue

                payload = item.get("payload") or {}
                item_type = item.get("type")

                if item_type == "session_meta":
                    thread_id = payload.get("id") or thread_id
                    cwd = payload.get("cwd") or cwd
                    thread_name = indexed_names.get(thread_id, thread_name)
                    continue

                if item_type == "turn_context":
                    cwd = payload.get("cwd") or cwd
                    continue

                if payload.get("thread_name"):
                    thread_name = payload["thread_name"]

                if item_type == "event_msg" and payload.get("type") == "task_complete":
                    duration_ms = payload.get("duration_ms")
                    if isinstance(duration_ms, (int, float)) and duration_ms >= 0:
                        runtimes.append(
                            TaskRuntime(
                                thread_id=thread_id or path.stem,
                                thread_name=thread_name,
                                cwd=cwd,
                                seconds=duration_ms / 1000,
                                completed_at=parse_timestamp(item.get("timestamp")),
                            )
                        )

    return runtimes


def summarize(runtimes: list[TaskRuntime]):
    by_thread: dict[str, float] = defaultdict(float)
    names: dict[str, str] = {}
    by_project: dict[str, float] = defaultdict(float)

    for runtime in runtimes:
        by_thread[runtime.thread_id] += runtime.seconds
        names[runtime.thread_id] = runtime.thread_name
        if runtime.cwd:
            by_project[runtime.cwd] += runtime.seconds

    return names, by_thread, by_project


def summarize_recent(runtimes: list[TaskRuntime], now: datetime | None = None) -> tuple[float, float]:
    now = now or datetime.now().astimezone()
    today = now.date()
    week_start = now - timedelta(days=7)
    today_total = 0.0
    week_total = 0.0

    for runtime in runtimes:
        if runtime.completed_at is None:
            continue

        completed_at = runtime.completed_at.astimezone(now.tzinfo)
        if completed_at.date() == today:
            today_total += runtime.seconds
        if completed_at >= week_start:
            week_total += runtime.seconds

    return today_total, week_total


def format_duration(seconds: float) -> str:
    minutes = round(seconds / 60)
    hours, mins = divmod(minutes, 60)
    if hours:
        return f"{hours}h {mins}m"
    return f"{mins}m"


def main() -> int:
    parser = argparse.ArgumentParser(description="Estimate Codex task runtime from local session logs.")
    parser.add_argument("--codex-home", default=str(Path.home() / ".codex"))
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument(
        "--no-archived",
        action="store_true",
        help="Only scan active sessions and skip archived_sessions.",
    )
    args = parser.parse_args()

    runtimes = read_task_runtimes(Path(args.codex_home), include_archived=not args.no_archived)
    names, by_thread, by_project = summarize(runtimes)

    total = sum(by_thread.values())
    print(f"Total Codex task runtime: {format_duration(total)}")
    today_total, week_total = summarize_recent(runtimes)
    print(f"Today: {format_duration(today_total)}")
    print(f"Last 7 days: {format_duration(week_total)}")
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
