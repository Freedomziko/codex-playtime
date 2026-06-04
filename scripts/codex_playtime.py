from __future__ import annotations

import argparse
import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class TaskRuntime:
    thread_id: str
    thread_name: str
    cwd: str
    seconds: float


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
                item = json.loads(line.lstrip("\ufeff"))
            except json.JSONDecodeError:
                continue
            thread_id = item.get("id")
            thread_name = item.get("thread_name")
            if thread_id and thread_name:
                names[thread_id] = thread_name

    return names


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
                    item = json.loads(line.lstrip("\ufeff"))
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


def format_duration(seconds: float) -> str:
    minutes = round(seconds / 60)
    hours, mins = divmod(minutes, 60)
    if hours:
        return f"{hours}h {mins}m"
    return f"{mins}m"


def build_report(
    names: dict[str, str],
    by_thread: dict[str, float],
    by_project: dict[str, float],
    limit: int,
) -> dict[str, Any]:
    total = sum(by_thread.values())

    top_chats = [
        {
            "thread_id": thread_id,
            "name": names.get(thread_id, thread_id),
            "seconds": seconds,
            "duration": format_duration(seconds),
        }
        for thread_id, seconds in sorted(by_thread.items(), key=lambda item: item[1], reverse=True)[:limit]
    ]
    top_projects = [
        {
            "cwd": cwd,
            "seconds": seconds,
            "duration": format_duration(seconds),
        }
        for cwd, seconds in sorted(by_project.items(), key=lambda item: item[1], reverse=True)[:limit]
    ]

    return {
        "total_seconds": total,
        "total_duration": format_duration(total),
        "top_chats": top_chats,
        "top_projects": top_projects,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Estimate Codex task runtime from local session logs.")
    parser.add_argument("--codex-home", default=str(Path.home() / ".codex"))
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the summary as JSON for scripts or dashboards.",
    )
    parser.add_argument(
        "--no-archived",
        action="store_true",
        help="Only scan active sessions and skip archived_sessions.",
    )
    args = parser.parse_args()

    runtimes = read_task_runtimes(Path(args.codex_home), include_archived=not args.no_archived)
    names, by_thread, by_project = summarize(runtimes)
    report = build_report(names, by_thread, by_project, args.limit)

    if args.json:
        print(json.dumps(report, indent=2))
        return 0

    print(f"Total Codex task runtime: {report['total_duration']}")
    print()
    print("Top chats:")
    for chat in report["top_chats"]:
        print(f"- {chat['name']}: {chat['duration']}")

    print()
    print("Top projects:")
    for project in report["top_projects"]:
        print(f"- {project['cwd']}: {project['duration']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
