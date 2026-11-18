# AiriBot · Project Update

## Release and timestamp

- **Release:** Beta — no numbered version has been published.
- **Commit recorded:** 18 November 2026, 18:07:16 UTC.
- **Thailand local time (ICT, UTC+7):** 19 November 2026, 01:07:16 (พ.ศ. 2569).

The date differs by one day because the commit was made shortly after midnight in Thailand. The UTC timestamp is from the latest feature-update commit.

## Updates included

- **Application startup (`main.py`):** added validated environment-variable parsing, configurable extension loading and command synchronization, lifecycle/status reporting, and clearer command error handling.
- **Administration (`cogs/admin.py`):** added dynamic help, bot status/resource diagnostics, extension listing and reloading, manual command synchronization, and graceful shutdown. Administrative commands are owner-only.
- **Terminal display (`core/console.py`):** expanded the Rich startup dashboard and made terminal clearing conditional on an interactive console.
- **Status messages (`core/notify.py`):** added reusable Components V2 status cards, bounded message content, and safer behavior when the configured log channel is inaccessible.
- **Documentation (`README.md`):** expanded setup instructions, required intents, environment configuration, command examples, and security notes.

The existing utility commands and dependencies were retained; the bot-status command uses the already-listed `psutil` package.

## Before the next release

- Assign and document a numbered version only when a release is actually published.
- Run a Python syntax check and test startup, command loading, help, owner-only controls, and missing-permission/error paths.
- Verify documented commands and configuration against the current code, then update this note with the next release's actual changes and timestamp.
- Keep `.env` and bot tokens out of commits; review Discord permissions and intents before deployment.

Install dependencies with `python -m pip install -r requirements.txt`.
