"""Reusable rich Components V2 status views and log-channel notifications."""

from __future__ import annotations

import time
from collections.abc import Sequence

import discord

_ACCENTS = {
    "ok": discord.Colour.green,
    "success": discord.Colour.green,
    "warn": discord.Colour.yellow,
    "warning": discord.Colour.yellow,
    "error": discord.Colour.red,
    "info": discord.Colour.blurple,
}


def _accent(kind: str) -> discord.Colour:
    return _ACCENTS.get(kind.lower(), discord.Colour.blurple)()


class StatusLayout(discord.ui.LayoutView):
    """A reusable Components V2 card with bounded content and optional footer."""

    def __init__(
        self,
        title: str,
        lines: Sequence[str],
        kind: str = "info",
        footer: str | None = None,
    ) -> None:
        super().__init__(timeout=None)
        container = discord.ui.Container(accent_color=_accent(kind))
        container.add_item(discord.ui.TextDisplay(f"### {title[:250]}"))
        container.add_item(discord.ui.Separator())
        safe_lines = [str(line).replace("\x00", "")[:900] for line in lines[:20]]
        body = "\n".join(f"- {line}" for line in safe_lines) if safe_lines else "—"
        container.add_item(discord.ui.TextDisplay(body[:3900]))
        container.add_item(discord.ui.Separator())
        container.add_item(discord.ui.TextDisplay((footer or f"-# <t:{int(time.time())}:F>")[:500]))
        self.add_item(container)


async def send_status(
    bot: discord.Client,
    title: str,
    lines: Sequence[str],
    kind: str = "info",
) -> bool:
    """Post a status card to the configured channel; safely return if unavailable."""
    channel_id = getattr(bot, "log_channel_id", None)
    if not channel_id:
        return False
    channel = bot.get_channel(channel_id)
    if channel is None:
        try:
            channel = await bot.fetch_channel(channel_id)
        except (discord.HTTPException, discord.Forbidden, discord.NotFound):
            return False
    if not hasattr(channel, "send"):
        return False
    try:
        await channel.send(view=StatusLayout(title, lines, kind))
        return True
    except (discord.HTTPException, discord.Forbidden):
        return False
