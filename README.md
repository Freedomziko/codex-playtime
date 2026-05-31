# codex-playtime

track how long youve vibe coded innit

Small tools for checking how much time you spend in Codex chats and projects.

The basic idea is to read local Codex session logs, group events by thread, and estimate active time with an idle cutoff so it does not count a chat sitting open overnight.

## First target

- total Codex time
- time by thread
- time by project/workspace
- today and weekly summaries

## Rough method

Count the gap between nearby events. Ignore or cap long gaps as idle time.

```text
event at 10:00
event at 10:04 -> count 4 minutes
event at 13:30 -> idle gap, do not count the whole thing
```
