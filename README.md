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

## Run it

Clone the repo and run the script with Python:

```powershell
git clone https://github.com/Freedomziko/codex-playtime.git
cd codex-playtime
python .\scripts\codex_playtime.py
```

On macOS or Linux, the command is usually:

```bash
python3 ./scripts/codex_playtime.py
```

The script reads your local Codex data from `~/.codex` by default. It scans both active sessions and archived sessions, then prints total runtime, top chats, and top projects.

If your Codex home is somewhere else:

```powershell
python .\scripts\codex_playtime.py --codex-home C:\Users\Name\.codex
```

If you only want active sessions and want to skip archived sessions:

```powershell
python .\scripts\codex_playtime.py --no-archived
```

If Windows says Python was not found, install Python from [python.org](https://www.python.org/downloads/) or disable the Microsoft Store Python alias in Windows app execution aliases.

## Development

Run the parser tests with:

```powershell
python -m unittest discover -s tests
```

## What it counts

`codex-playtime` sums Codex's recorded `task_complete.duration_ms` values from local session logs. That means it counts completed Codex task runtime, not total wall-clock time while a chat tab is open.
