"""
core/notify.py
───────────────
Sends styled status messages to a fixed "log channel" (LOG_CHANNEL_ID) using
Discord's Components V2 system (discord.ui.LayoutView / Container /
TextDisplay) instead of legacy embeds. Falls back silently if the channel
isn't configured or isn't reachable yet.
"""

from __future__ import annotations

import time

import discord


def _accent(kind: str) -> discord.Colour:
    return {
        "ok": discord.Colour.green(),
        "warn": discord.Colour.yellow(),
        "error": discord.Colour.red(),
        "info": discord.Colour.blurple(),
    }.get(kind, discord.Colour.blurple())


class StatusLayout(discord.ui.LayoutView):
    """A single Components V2 layout used for status cards everywhere in the
    bot (log channel posts, owner command replies, utility command replies).

    `footer`, if given, replaces the default timestamp line with custom
    subtext (e.g. "Requested by @user" or a usage hint) — still rendered in
    the same small, muted style via Discord's "-#" subtext markdown.
    """

    def __init__(self, title: str, lines: list[str], kind: str = "info", footer: str | None = None):
        super().__init__(timeout=None)
        container = discord.ui.Container(accent_color=_accent(kind))
        container.add_item(discord.ui.TextDisplay(f"### {title}"))
        container.add_item(discord.ui.Separator())
        body = "\n".join(f"- {line}" for line in lines) if lines else "—"
        container.add_item(discord.ui.TextDisplay(body))
        container.add_item(discord.ui.Separator())
        container.add_item(
            discord.ui.TextDisplay(footer if footer else f"-# <t:{int(time.time())}:F>")
        )
        self.add_item(container)


async def send_status(bot: discord.Client, title: str, lines: list[str], kind: str = "info") -> None:
    """Post a Components V2 status card to bot.log_channel_id, if set and found."""
    channel_id = getattr(bot, "log_channel_id", None)
    if not channel_id:
        return
    channel = bot.get_channel(channel_id)
    if channel is None:
        try:
            channel = await bot.fetch_channel(channel_id)
        except discord.HTTPException:
            return
    try:
        await channel.send(view=StatusLayout(title, lines, kind))
    except discord.HTTPException:
        pass