"""Bot administration, diagnostics, and dynamically generated help commands."""

from __future__ import annotations

import platform
import time
from typing import Optional

import discord
import psutil
from discord.ext import commands

from core.notify import StatusLayout


def _duration(seconds: float) -> str:
    seconds = max(0, int(seconds))
    days, seconds = divmod(seconds, 86_400)
    hours, seconds = divmod(seconds, 3_600)
    minutes, seconds = divmod(seconds, 60)
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    parts.append(f"{seconds}s")
    return " ".join(parts)


class Admin(commands.Cog):
    """Owner controls and user-facing bot health/help commands."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command(name="help", aliases=["commands"])
    async def help_command(self, ctx: commands.Context, *, query: Optional[str] = None) -> None:
        """Show all commands, or detailed usage for one command."""
        prefix = getattr(self.bot, "configured_prefix", "$" )
        if query:
            command = self.bot.get_command(query.strip())
            if command is None:
                await ctx.reply(view=StatusLayout("Command not found", [f"No command named `{query}` exists.", f"Use `{prefix}help` to browse commands."], "warn"))
                return
            usage = f"{prefix}{command.qualified_name} {command.signature}".strip()
            await ctx.reply(view=StatusLayout(
                f"Help · {command.qualified_name}",
                [command.help or command.short_doc or "No description provided.", f"**Usage:** `{usage}`", f"**Aliases:** {', '.join(command.aliases) or 'None'}"],
                "info",
            ))
            return

        groups: dict[str, list[str]] = {}
        for command in sorted(self.bot.commands, key=lambda item: item.qualified_name):
            if command.hidden:
                continue
            category = command.cog_name or "General"
            groups.setdefault(category, []).append(f"`{prefix}{command.qualified_name}` — {command.short_doc or 'No description'}")
        lines = []
        for category, entries in groups.items():
            lines.append(f"**{category}**")
            lines.extend(entries)
        lines.append(f"Use `{prefix}help <command>` for command details. Commands also work when you mention the bot.")
        await ctx.reply(view=StatusLayout("AiriBot command center", lines, "info"))

    @commands.command(name="botstatus", aliases=["status", "dashboard"])
    async def bot_status(self, ctx: commands.Context) -> None:
        """Show uptime, latency, runtime, and process resource usage."""
        boot_time = getattr(self.bot, "boot_time", None)
        uptime = _duration(time.monotonic() - boot_time) if boot_time else "Starting"
        process = psutil.Process()
        memory_mb = process.memory_info().rss / (1024 * 1024)
        cpu_percent = process.cpu_percent(interval=None)
        member_count = sum(guild.member_count or 0 for guild in self.bot.guilds)
        lines = [
            f"**Uptime:** {uptime}",
            f"**Latency:** {round(self.bot.latency * 1000)} ms",
            f"**Servers / cached members:** {len(self.bot.guilds):,} / {member_count:,}",
            f"**Process:** {cpu_percent:.1f}% CPU · {memory_mb:.1f} MiB RAM",
            f"**Runtime:** Python {platform.python_version()} · discord.py {discord.__version__}",
        ]
        await ctx.reply(view=StatusLayout("AiriBot · live status", lines, "ok"))

    @commands.command(name="extensions", aliases=["cogs"])
    @commands.is_owner()
    async def extensions(self, ctx: commands.Context) -> None:
        """List loaded cogs (bot owner only)."""
        cogs = sorted(self.bot.cogs)
        await ctx.reply(view=StatusLayout("Loaded extensions", cogs or ["No extensions are loaded."], "info"))

    @commands.command(name="reload", aliases=["reloadcog"])
    @commands.is_owner()
    async def reload_extension(self, ctx: commands.Context, *, extension: str) -> None:
        """Reload an extension by dotted module name (bot owner only)."""
        if not extension.startswith("cogs."):
            extension = f"cogs.{extension}"
        try:
            await self.bot.reload_extension(extension)
        except (commands.ExtensionError, ImportError) as exc:
            await ctx.reply(view=StatusLayout("Reload failed", [f"`{extension}`", str(exc)[:700]], "error"))
            return
        await ctx.reply(view=StatusLayout("Extension reloaded", [f"Successfully reloaded `{extension}`."], "ok"))

    @commands.command(name="synccommands", aliases=["sync"])
    @commands.is_owner()
    async def sync_commands(self, ctx: commands.Context) -> None:
        """Synchronize application commands with Discord (bot owner only)."""
        try:
            synced = await self.bot.tree.sync()
        except discord.HTTPException as exc:
            await ctx.reply(view=StatusLayout("Command sync failed", [str(exc)[:700]], "error"))
            return
        await ctx.reply(view=StatusLayout("Commands synchronized", [f"Synced {len(synced)} application command(s)."], "ok"))

    @commands.command(name="shutdown", aliases=["stopbot"])
    @commands.is_owner()
    async def shutdown(self, ctx: commands.Context) -> None:
        """Gracefully stop the bot (bot owner only)."""
        await ctx.reply(view=StatusLayout("Shutting down", ["The bot is closing its Discord connection."], "warn"))
        await self.bot.close()


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Admin(bot))
