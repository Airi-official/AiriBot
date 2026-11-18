"""Utility extension package: load each command module independently.

Add a command module beside this file; its setup(bot) function is loaded
automatically. Shared helpers live in _shared.py and are not extensions.
"""

from __future__ import annotations

import pkgutil

from discord.ext import commands


async def setup(bot: commands.Bot) -> None:
    for module in sorted(pkgutil.iter_modules(__path__), key=lambda entry: entry.name):
        if module.name.startswith("_"):
            continue
        await bot.load_extension(f"{__name__}.{module.name}")
