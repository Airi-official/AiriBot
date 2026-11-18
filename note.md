# AiriBot · Project Update

## Modular utility commands

- Replaced the single large utility command module with the `cogs/utility/` extension package.
- Added separate focused modules for activity/snapshots, fun and visual commands, profiles, server information, and timers/reminders.
- Added `_shared.py` for reusable formatting, safe arithmetic, duration parsing, image layouts, and process-local command state.
- The package extension automatically discovers and loads Python command modules; helper modules beginning with `_` are skipped.
- Updated `main.py` to load the utility package and admin extension, and corrected command-error unwrapping and reporting.
- Updated `README.md` with the package structure, module loading behavior, commands, setup, and state persistence notes.

## Maintenance notes

- New extensions under `cogs/utility/` should expose `async def setup(bot)`.
- Restart after adding/renaming an extension; reload with `$reload utility.<module>` when supported.
- AFK state, message snapshots, and reminders are in-memory only and do not persist across restarts.
- Keep `.env` and bot tokens out of commits.
