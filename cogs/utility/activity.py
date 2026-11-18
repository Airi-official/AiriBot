"""Process-local AFK status and recent message snapshot commands."""

from __future__ import annotations

import time

import discord
from discord.ext import commands

from core.notify import StatusLayout
from ._shared import UtilityCog, fmt_duration


class ActivityTools(UtilityCog):
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot or not message.guild:
            return
        afk = self.state["afk"]
        if message.author.id in afk and not message.content.lstrip().startswith(f"{getattr(self.bot, 'configured_prefix', '$')}afk"):
            entry = afk.pop(message.author.id)
            try:
                await message.reply(view=StatusLayout("👋 Welcome back", [f"AFK cleared after {fmt_duration(time.time() - entry['since'])}."], "ok"), mention_author=False, delete_after=8)
            except discord.HTTPException:
                pass
        for member in message.mentions:
            if member.id in afk and member.id != message.author.id:
                entry = afk[member.id]
                try:
                    await message.reply(view=StatusLayout(f"💤 {member.display_name} is AFK", [entry["reason"], f"Away for {fmt_duration(time.time() - entry['since'])}."], "warn"), mention_author=False)
                except discord.HTTPException:
                    pass

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message) -> None:
        if message.author.bot:
            return
        self.state["deleted"][message.channel.id] = {"author": str(message.author), "content": message.content or "(no text content)", "at": time.time()}

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message) -> None:
        if not before.author.bot and before.content != after.content:
            self.state["edited"][before.channel.id] = {"author": str(before.author), "before": before.content or "(empty)", "after": after.content or "(empty)", "at": time.time()}

    @commands.command(name="afk")
    async def afk(self, ctx: commands.Context, *, reason: str = "AFK") -> None:
        self.state["afk"][ctx.author.id] = {"reason": reason[:300], "since": time.time()}
        await ctx.reply(view=StatusLayout("💤 AFK set", [f"I'll let people know: *{reason[:300]}*"], "ok"), mention_author=False)

    @commands.command(name="snipe")
    @commands.guild_only()
    async def snipe(self, ctx: commands.Context) -> None:
        entry = self.state["deleted"].get(ctx.channel.id)
        if not entry:
            await ctx.reply(view=StatusLayout("🔍 Snipe", ["Nothing recently deleted here."], "warn"))
            return
        await ctx.reply(view=StatusLayout("🔍 Last deleted message", [f"**{entry['author']}**", entry['content'][:1500], f"{fmt_duration(time.time() - entry['at'])} ago"], "info"))

    @commands.command(name="editsnipe")
    @commands.guild_only()
    async def editsnipe(self, ctx: commands.Context) -> None:
        entry = self.state["edited"].get(ctx.channel.id)
        if not entry:
            await ctx.reply(view=StatusLayout("✏️ Edit snipe", ["Nothing recently edited here."], "warn"))
            return
        await ctx.reply(view=StatusLayout("✏️ Last edited message", [f"**{entry['author']}**", f"**Before:** {entry['before'][:700]}", f"**After:** {entry['after'][:700]}", f"{fmt_duration(time.time() - entry['at'])} ago"], "info"))


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ActivityTools(bot))
