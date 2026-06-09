---
name: codex-playtime
description: Show Codex task runtime stats by reading local Codex session logs. Use when the user asks for Codex hours, playtime, runtime, time spent in chats, or time spent in projects.
---

# Codex Playtime

Use this skill to show local Codex runtime stats.

## Workflow

1. Run the bundled script:

```powershell
python .\scripts\codex_playtime.py
```

If `python` points to the Microsoft Store alias or is unavailable, use the Codex desktop bundled Python from `codex_app.load_workspace_dependencies`.

2. Summarize the output for the user. The default count includes both active `sessions` and `archived_sessions`.

3. If the user questions the numbers, explain that the script sums Codex's recorded `task_complete.duration_ms` values from local session logs. This counts completed Codex task runtime, not wall-clock time between unrelated messages.

## Useful Options

```powershell
python .\scripts\codex_playtime.py --limit 20
python .\scripts\codex_playtime.py --today
python .\scripts\codex_playtime.py --week
python .\scripts\codex_playtime.py --since 2026-06-01
python .\scripts\codex_playtime.py --codex-home C:\Users\Name\.codex
python .\scripts\codex_playtime.py --no-archived
```

## Notes

- The script reads local files only.
- Long-running Codex tasks count for their recorded duration.
- Open or aborted tasks may not count until Codex records a completed task.
