"""AiriBot entry point, configuration, lifecycle, and event handling."""

from __future__ import annotations

import asyncio
import os
import platform
import time

import discord
from discord.ext import commands
from dotenv import load_dotenv

from core import console
from core.notify import StatusLayout, send_status

load_dotenv()


def _env_int(name: str, default: int = 0) -> int:
    value = os.getenv(name)
    if value in (None, ""):
        return default
    try:
        result = int(value)
    except ValueError as exc:
        raise SystemExit(f"Configuration error: {name} must be an integer.") from exc
    if result < 0:
        raise SystemExit(f"Configuration error: {name} cannot be negative.")
    return result


TOKEN = os.getenv("DISCORD_TOKEN", "").strip()
OWNER_ID = _env_int("OWNER_ID")
LOG_CHANNEL_ID = _env_int("LOG_CHANNEL_ID") or None
PREFIX = os.getenv("PREFIX", "$").strip() or "$"
SYNC_COMMANDS = os.getenv("SYNC_COMMANDS", "true").strip().lower() in {"1", "true", "yes", "on"}

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True


class AiriBot(commands.Bot):
    """Bot with centralized configuration and extension lifecycle."""

    def __init__(self) -> None:
        super().__init__(
            command_prefix=commands.when_mentioned_or(PREFIX),
            intents=intents,
            owner_id=OWNER_ID or None,
            help_command=None,
            case_insensitive=True,
            strip_after_prefix=True,
        )
        self.boot_time: float | None = None
        self.log_channel_id = LOG_CHANNEL_ID
        self.configured_prefix = PREFIX
        self.extensions_to_load = ("cogs.utility", "cogs.admin")
        self._ready_announced = False

    async def setup_hook(self) -> None:
        for extension in self.extensions_to_load:
            try:
                await self.load_extension(extension)
                console.ok(f"Loaded extension {extension}")
            except (commands.ExtensionError, ImportError) as exc:
                console.error(f"Could not load {extension}: {exc}")
        if SYNC_COMMANDS:
            try:
                synced = await self.tree.sync()
                console.ok(f"Synchronized {len(synced)} application command(s).")
            except discord.HTTPException as exc:
                console.error(f"Application command sync failed: {exc}")


bot = AiriBot()


@bot.event
async def on_ready() -> None:
    if bot.boot_time is None:
        bot.boot_time = time.monotonic()
    console.banner(
        bot_name=str(bot.user),
        bot_id=bot.user.id if bot.user else 0,
        prefix=PREFIX,
        owner_id=OWNER_ID,
        guild_count=len(bot.guilds),
        extra={"Python": platform.python_version(), "discord.py": discord.__version__},
    )
    if not bot._ready_announced:
        bot._ready_announced = True
        await bot.change_presence(activity=discord.Activity(
            type=discord.ActivityType.listening,
            name=f"{PREFIX}help | {len(bot.guilds)} servers",
        ))
        await send_status(bot, "AiriBot is online", [
            f"Signed in as **{bot.user}** (`{bot.user.id}`)",
            f"Servers: **{len(bot.guilds)}**",
            f"Prefix: `{PREFIX}` (or mention the bot)",
            f"Python: `{platform.python_version()}` · discord.py: `{discord.__version__}`",
        ], "ok")


@bot.event
async def on_command(ctx: commands.Context) -> None:
    location = f"#{ctx.channel}" if ctx.guild else "Direct Message"
    console.command_used(str(ctx.author), ctx.command.qualified_name if ctx.command else "unknown", location)


@bot.event
async def on_command_error(ctx: commands.Context, error: commands.CommandError) -> None:
    error = getattr(error, "original", error)
    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, commands.CommandOnCooldown):
        message, kind = f"Please try again in **{error.retry_after:.1f} seconds**.", "warn"
    elif isinstance(error, commands.MissingRequiredArgument):
        message, kind = f"Missing argument: `{error.param.name}`. Use `{PREFIX}help` for details.", "warn"
    elif isinstance(error, commands.BadArgument):
        message, kind = f"I couldn't parse that argument. Use `{PREFIX}help` for details.", "warn"
    elif isinstance(error, (commands.NotOwner, commands.MissingPermissions, commands.BotMissingPermissions)):
        message, kind = "You or the bot do not have permission to run that command.", "error"
    elif isinstance(error, commands.NoPrivateMessage):
        message, kind = "This command can only be used in a server.", "warn"
    elif isinstance(error, commands.DisabledCommand):
        message, kind = "That command is currently unavailable.", "warn"
    else:
        console.error(f"Command {getattr(ctx.command, 'qualified_name', 'unknown')} failed: {error!r}")
        message, kind = "Something went wrong while running that command. The issue has been logged.", "error"
    try:
        await ctx.reply(view=StatusLayout("Command response", [message], kind), mention_author=False)
    except discord.HTTPException:
        console.warn("Could not send a command error response.")


@bot.event
async def on_disconnect() -> None:
    console.warn("Disconnected from Discord; the client will attempt to reconnect.")


@bot.event
async def on_guild_join(guild: discord.Guild) -> None:
    console.info(f"Joined server {guild.name} ({guild.id}); now in {len(bot.guilds)} servers.")
    await send_status(bot, "Joined a server", [f"**{guild.name}** (`{guild.id}`)", f"Server count: {len(bot.guilds)}"], "info")


@bot.event
async def on_guild_remove(guild: discord.Guild) -> None:
    console.info(f"Left server {guild.name} ({guild.id}); now in {len(bot.guilds)} servers.")


async def main() -> None:
    if not TOKEN:
        raise SystemExit("DISCORD_TOKEN is missing. Add it to your local .env file before starting AiriBot.")
    console.clear_screen()
    console.section(f"Starting AiriBot · prefix {PREFIX}")
    async with bot:
        await bot.start(TOKEN)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.warn("Shutdown requested from the terminal.")
