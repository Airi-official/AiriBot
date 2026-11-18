# AiriBot

AiriBot is a configurable, prefix-based Discord bot built with Python and discord.py. It combines everyday server utilities with image cards, interactive Components V2 layouts, owner controls, and a live diagnostic dashboard.

> **Release:** Beta (no numbered release has been published yet).

## Highlights

- **Command center:** browse commands and inspect usage with `$help` and `$help <command>`.
- **Bot diagnostics:** `$botstatus` shows uptime, gateway latency, cached server/member totals, and process CPU/RAM.
- **Server and profile utilities:** inspect members, roles, channels, servers, avatars, and colors.
- **Interactive tools:** polls, countdown timers, reminders, AFK status, and deleted/edited message snapshots.
- **Visual output:** generated latency, bot-stat, and color cards, with reusable Components V2 status panels.
- **Owner controls:** list/reload extensions, synchronize application commands, and gracefully shut down the process.
- **Operational visibility:** richer startup dashboard, log-channel notifications, and clearer command error handling.

## Requirements

- Python 3.10 or newer
- A Discord bot application and token
- Message Content and Server Members intents enabled in the Discord Developer Portal

## Setup

1. Clone the repository and enter the project directory.
2. Install runtime dependencies:

   ```bash
   python -m pip install -r requirements.txt
   ```

3. Create a `.env` file in the project root (never commit this file):

   ```dotenv
   DISCORD_TOKEN=your-discord-bot-token
   OWNER_ID=your-discord-user-id
   LOG_CHANNEL_ID=your-log-channel-id
   PREFIX=$
   SYNC_COMMANDS=true
   ```

   `DISCORD_TOKEN` is required. `OWNER_ID` and `LOG_CHANNEL_ID` may be left unset; the prefix defaults to `$`. Set `SYNC_COMMANDS=false` to skip automatic application-command synchronization at startup.

4. Invite the bot with only the permissions needed by the enabled commands. Commands that manage server settings or messages may need additional Discord permissions.
5. Start the bot:

   ```bash
   python main.py
   ```

## Commands

The default prefix is `$`; commands can also be called by mentioning the bot. Use `$help` for the live command list and `$help <command>` for detailed usage.

Examples:

| Command | Purpose |
| --- | --- |
| `$ping`, `$botinfo`, `$botstatus`, `$uptime` | Latency, bot information, diagnostics, and uptime |
| `$avatar [member]`, `$userinfo [member]`, `$serverinfo`, `$membercount` | User and server information |
| `$channelinfo [channel]`, `$roleinfo <role>`, `$servericon` | Channel, role, and server-icon details |
| `$color blue`, `$calc 12 * 3`, `$choose tea, coffee`, `$8ball Will it work?` | Visual color card, arithmetic, and lightweight fun commands |
| `$poll Lunch? | Pizza | Sushi` | Interactive poll with up to four choices |
| `$timer 5m Break`, `$remindme 1h Check in`, `$reminders` | Timers and reminders |
| `$afk [reason]`, `$snipe`, `$editsnipe` | AFK status and recent message snapshots |
| `$extensions`, `$reload utility`, `$synccommands`, `$shutdown` | Owner-only bot administration |

Owner-only commands use the configured `OWNER_ID` or the Discord application's owner. Message snapshot commands only retain recent data in memory and do not provide persistent moderation logs.

## Dependencies and project notes

Install/update dependencies with `python -m pip install -r requirements.txt`. See [`note.md`](note.md) for the latest project changes and release/date information.
