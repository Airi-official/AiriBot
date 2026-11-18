"""Server, channel, role, and member-count commands."""

from __future__ import annotations

import discord
from discord.ext import commands

from core.notify import StatusLayout


class ServerInfo(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command(name="serverinfo")
    @commands.guild_only()
    async def serverinfo(self, ctx: commands.Context) -> None:
        guild = ctx.guild
        lines = [
            f"**Owner:** {guild.owner or 'Unknown'}", f"**Members:** {guild.member_count or 0:,}",
            f"**Roles:** {len(guild.roles)}", f"**Text channels:** {len(guild.text_channels)} · **Voice channels:** {len(guild.voice_channels)}",
            f"**Boosts:** {guild.premium_subscription_count or 0} (tier {guild.premium_tier})",
            f"**Created:** <t:{int(guild.created_at.timestamp())}:D>",
        ]
        await ctx.reply(view=StatusLayout(f"🏠 {guild.name}", lines, "info"))

    @commands.command(name="membercount")
    @commands.guild_only()
    async def membercount(self, ctx: commands.Context) -> None:
        guild = ctx.guild
        humans = sum(not member.bot for member in guild.members)
        bots = sum(member.bot for member in guild.members)
        await ctx.reply(view=StatusLayout("👥 Member count", [
            f"**Reported total:** {guild.member_count or 0:,}", f"**Cached humans:** {humans:,}", f"**Cached bots:** {bots:,}",
        ], "info"))

    @commands.command(name="servericon")
    @commands.guild_only()
    async def servericon(self, ctx: commands.Context) -> None:
        if ctx.guild.icon is None:
            await ctx.reply(view=StatusLayout("No server icon", ["This server has no icon set."], "warn"))
            return
        view = discord.ui.LayoutView()
        box = discord.ui.Container(accent_color=discord.Colour.blurple())
        box.add_item(discord.ui.TextDisplay(f"### 🖼️ {ctx.guild.name}'s icon"))
        box.add_item(discord.ui.MediaGallery(discord.MediaGalleryItem(ctx.guild.icon.url)))
        view.add_item(box)
        await ctx.reply(view=view)

    @commands.command(name="channelinfo")
    @commands.guild_only()
    async def channelinfo(self, ctx: commands.Context, channel: discord.abc.GuildChannel | None = None) -> None:
        channel = channel or ctx.channel
        lines = [f"**Type:** {channel.type}", f"**ID:** `{channel.id}`", f"**Created:** <t:{int(channel.created_at.timestamp())}:D>"]
        if isinstance(channel, discord.TextChannel):
            lines += [f"**Topic:** {channel.topic or '—'}", f"**NSFW:** {'Yes' if channel.is_nsfw() else 'No'}"]
        await ctx.reply(view=StatusLayout(f"# {channel.name}", lines, "info"))

    @commands.command(name="roleinfo")
    @commands.guild_only()
    async def roleinfo(self, ctx: commands.Context, *, role: discord.Role) -> None:
        await ctx.reply(view=StatusLayout(f"🎭 {role.name}", [
            f"**Color:** {role.color}", f"**Members:** {len(role.members)}", f"**Position:** {role.position}",
            f"**Mentionable:** {'Yes' if role.mentionable else 'No'}", f"**Hoisted:** {'Yes' if role.hoist else 'No'}",
            f"**Created:** <t:{int(role.created_at.timestamp())}:D>",
        ], "info"))


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ServerInfo(bot))
