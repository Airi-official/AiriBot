# AiriBot

**AiriBot** is a beta Discord bot written in Python. It includes utility commands, interactive Components V2 replies, generated image cards, and styled terminal status output.

> **Project version:** Beta — a numeric release version has not yet been declared.

## Features

- Utility commands for bot, server, member, channel, and role information.
- Image cards for latency, bot statistics, and color swatches.
- Interactive polls, timers, reminders, AFK status, and message sniping.
- Styled startup and status messages.

## Requirements

- Python 3.10 or newer
- A Discord bot application and token

## Setup

1. Clone the repository and enter its directory.
2. Install dependencies:

   ```bash
   python -m pip install -r requirements.txt
   ```

3. Create a `.env` file in the project root:

   ```dotenv
   DISCORD_TOKEN=your-discord-bot-token
   OWNER_ID=your-discord-user-id
   LOG_CHANNEL_ID=your-log-channel-id
   PREFIX=$
   ```

   `DISCORD_TOKEN` is required. `OWNER_ID`, `LOG_CHANNEL_ID`, and `PREFIX` have defaults in the bot configuration.

4. In the Discord Developer Portal, enable the **Message Content Intent** and **Server Members Intent** for the bot if needed. Invite the bot with the permissions required for the commands you plan to use.
5. Start the bot:

   ```bash
   python main.py
   ```

## Commands

The default command prefix is `$` (or mention the bot). Examples include:

- `$ping`, `$botinfo`, `$uptime`
- `$avatar`, `$userinfo`, `$serverinfo`, `$channelinfo`, `$roleinfo`
- `$color blue`, `$calc 12 * 3`, `$choose tea, coffee`
- `$poll Lunch? | Pizza | Sushi`
- `$timer 5m Break`, `$remindme 1h Check in`
- `$afk`, `$snipe`, `$editsnipe`

Some commands require a server context. Check the command implementation and your bot's permissions/intents for details.

## Dependencies

Runtime dependencies are listed in [`requirements.txt`](requirements.txt). Install or update them with `python -m pip install -r requirements.txt`.

## Project notes

See [`note.md`](note.md) for the latest project update. The developer's original note is also available at [`notr_from_dev/Note.md`](notr_from_dev/Note.md).
