"""Latency and generated bot information commands."""

from __future__ import annotations

import asyncio
import sys
import time

import discord
from discord.ext import commands

from core import imagegen
from ._shared import UtilityCog, fmt_duration, image_container


class Ping(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command(name="ping")
    async def ping(self, ctx: commands.Context) -> None:
        started = time.perf_counter()
        message = await ctx.reply("Measuring latency…")
        api_ms = round((time.perf_counter() - started) * 1000)
        ws_ms = round(self.bot.latency * 1000)
        buffer = await asyncio.to_thread(imagegen.render_ping_gauge, ws_ms, api_ms)
        await message.delete()
        await ctx.reply(view=image_container("### 🏓 Pong!", "ping.png"), file=discord.File(buffer, filename="ping.png"))


class BotInfo(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command(name="botinfo")
    async def botinfo(self, ctx: commands.Context) -> None:
        bot = self.bot
        uptime = fmt_duration(time.monotonic() - bot.boot_time) if getattr(bot, "boot_time", None) else "unknown"
        members = sum(guild.member_count or 0 for guild in bot.guilds)
        try:
            avatar = await bot.user.display_avatar.read()
        except (discord.HTTPException, AttributeError):
            avatar = None
        stats = [
            ("Guilds", f"{len(bot.guilds):,}", imagegen.BLURPLE),
            ("Users", f"{members:,}", imagegen.GREEN),
            ("Latency", f"{round(bot.latency * 1000)} ms", imagegen.YELLOW),
            ("Uptime", uptime, imagegen.PINK),
            ("discord.py", discord.__version__, imagegen.BLURPLE),
            ("Python", sys.version.split()[0], imagegen.GREEN),
        ]
        buffer = await asyncio.to_thread(imagegen.render_bot_info_card, str(bot.user), avatar, stats)
        await ctx.reply(view=image_container("### 🤖 Bot dashboard", "botinfo.png"), file=discord.File(buffer, filename="botinfo.png"))


class Uptime(UtilityCog):
    @commands.command(name="uptime")
    async def uptime(self, ctx: commands.Context) -> None:
        started = getattr(self.bot, "boot_time", None)
        await self.status(ctx, "⏱️ Uptime", [fmt_duration(time.monotonic() - started) if started else "Still starting up."], "info")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Ping(bot))
    await bot.add_cog(BotInfo(bot))
    await bot.add_cog(Uptime(bot))
