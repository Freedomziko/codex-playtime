# codex-playtime

track how long youve vibe coded innit

Small tools for checking how long Codex has spent working in chats and projects.

The basic idea is to read local Codex session logs, find completed Codex turns, and add up their recorded runtime.

## First target

- total Codex time
- time by thread
- time by project/workspace
- today and weekly summaries

## Rough method

Count each completed Codex task using the duration recorded in the local session log.

```text
task_complete duration_ms: 102956 -> count 1m 43s
task_complete duration_ms: 7200000 -> count 2h
```
