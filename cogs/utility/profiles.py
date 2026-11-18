"""Member profile and avatar commands."""

from __future__ import annotations

from typing import Optional

import discord
from discord.ext import commands

from core.notify import StatusLayout


class Profiles(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command(name="avatar")
    async def avatar(self, ctx: commands.Context, member: Optional[discord.Member] = None) -> None:
        member = member or ctx.author
        view = discord.ui.LayoutView()
        box = discord.ui.Container(accent_color=discord.Colour.blurple())
        box.add_item(discord.ui.TextDisplay(f"### 🖼️ {member.display_name}'s avatar"))
        box.add_item(discord.ui.MediaGallery(discord.MediaGalleryItem(member.display_avatar.url)))
        view.add_item(box)
        await ctx.reply(view=view)

    @commands.command(name="userinfo")
    @commands.guild_only()
    async def userinfo(self, ctx: commands.Context, member: Optional[discord.Member] = None) -> None:
        member = member or ctx.author
        joined = f"<t:{int(member.joined_at.timestamp())}:D>" if member.joined_at else "Unknown"
        lines = [
            f"**Username:** {member}", f"**ID:** `{member.id}`",
            f"**Joined server:** {joined}", f"**Account created:** <t:{int(member.created_at.timestamp())}:D>",
            f"**Top role:** {member.top_role.mention if member.top_role else '—'}",
            f"**Roles:** {max(0, len(member.roles) - 1)}",
        ]
        view = discord.ui.LayoutView()
        box = discord.ui.Container(accent_color=member.color or discord.Colour.blurple())
        section = discord.ui.Section(
            discord.ui.TextDisplay(f"### {member.display_name}\n" + "\n".join(lines)),
            accessory=discord.ui.Thumbnail(member.display_avatar.url),
        )
        box.add_item(section)
        view.add_item(box)
        await ctx.reply(view=view)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Profiles(bot))
