# AiriBot

AiriBot is a configurable, prefix-based Discord bot built with Python and discord.py. Utility commands now live in a package of focused extension modules instead of one large `cogs/utility.py` file.

## Project structure

```text
main.py
cogs/
├── admin.py
└── utility/
    ├── __init__.py       # discovers and loads command modules
    ├── _shared.py        # shared helpers and process-local state
    ├── activity.py       # AFK and message snapshots
    ├── fun.py            # calculator, choices, 8-ball, polls, colors
    ├── profiles.py       # avatar and user information
    ├── server.py         # server, member, channel, role information
    └── time_tools.py     # timers and reminders
```

Add a Python module under `cogs/utility/` with an async `setup(bot)` function to add another utility extension. Files beginning with `_` are helper modules and are not loaded as extensions. Restart the bot after adding or renaming modules; the owner can reload an extension using `$reload utility.<module>`.

## Features and commands

- **Bot info:** `$ping`, `$botinfo`, `$botstatus`, `$uptime`
- **Profiles and server:** `$avatar`, `$userinfo`, `$serverinfo`, `$membercount`, `$servericon`, `$channelinfo`, `$roleinfo`
- **Fun and visuals:** `$calc`, `$choose`, `$8ball`, `$poll`, `$color`
- **Activity and time:** `$afk`, `$snipe`, `$editsnipe`, `$timer`, `$remindme`, `$reminders`, `$cancelreminder`
- **Owner commands:** `$help`, `$extensions`, `$reload`, `$synccommands`, `$shutdown`
- **Displays:** generated image cards, Components V2 status layouts, and a Rich terminal startup dashboard

## Setup

Requirements: Python 3.10+, a Discord bot token, and the Message Content and Server Members intents enabled in the Developer Portal.

1. Install packages: `python -m pip install -r requirements.txt`
2. Create a local `.env` file (do not commit it):

   ```dotenv
   DISCORD_TOKEN=your-discord-bot-token
   OWNER_ID=your-discord-user-id
   LOG_CHANNEL_ID=your-log-channel-id
   PREFIX=$
   SYNC_COMMANDS=true
   ```

3. Invite the bot with only the permissions needed by the commands.
4. Start it with `python main.py`.

Reminders, AFK state, and message snapshots are held in memory and are cleared when the bot restarts. See [`note.md`](note.md) for the latest project notes.
