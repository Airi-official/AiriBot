# Project update · AiriBot

- **Version:** Beta (no numeric release version is declared).
- **Date:** 18 พฤศจิกายน พ.ศ. 2569 (18 November 2026).
- **Time:** Not recorded; the commit timestamp is the authoritative update time.

## Consolidated feature update

- Reworked `main.py` configuration parsing, extension startup, lifecycle/status events, guild join logging, and command error responses.
- Added `cogs/admin.py` with dynamic help, bot diagnostics, extension listing/reloading, command synchronization, and graceful shutdown. Administrative controls are owner-only.
- Improved `core/console.py` with a reusable Rich startup dashboard and terminal-safe output.
- Improved `core/notify.py` with reusable, bounded Components V2 status cards and safe log-channel fallback behavior.
- Expanded `README.md` with setup, environment configuration, intents, security guidance, and command examples.

## Stability and configuration

- Install dependencies using `python -m pip install -r requirements.txt`.
- Configure `DISCORD_TOKEN` locally in `.env`; do not commit secrets.
- Use `SYNC_COMMANDS=false` to disable automatic application-command syncing at startup.
- New bot-status metrics use the existing `psutil` dependency; no additional package was introduced.
