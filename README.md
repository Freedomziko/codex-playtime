# codex-playtime

track how long youve vibe coded innit

Small tools for checking how long Codex chats and projects have been running.

The basic idea is to read local Codex session logs, group events by thread, and add up the time between events.

## First target

- total Codex time
- time by thread
- time by project/workspace
- today and weekly summaries

## Rough method

Count the gap between nearby events in the same chat.

```text
event at 10:00
event at 10:04 -> count 4 minutes
event at 13:30 -> count the full gap
```
