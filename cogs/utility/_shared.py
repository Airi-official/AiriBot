"""Common presentation, parsing, and state helpers for utility command cogs."""

from __future__ import annotations

import ast
import operator
import random
import re
import time
from typing import Any

import discord
from discord.ext import commands

from core.notify import StatusLayout

DURATION_RE = re.compile(r"(\d+)\s*([dhms])", re.IGNORECASE)
DURATION_UNITS = {"d": 86400, "h": 3600, "m": 60, "s": 1}
ALLOWED_OPS = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod, ast.Pow: operator.pow, ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def fmt_duration(seconds: float) -> str:
    seconds = max(0, int(seconds))
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    return " ".join(part for part in (
        f"{days}d" if days else "", f"{hours}h" if hours else "",
        f"{minutes}m" if minutes else "", f"{seconds}s",
    ) if part) or "0s"


def parse_duration(text: str) -> int | None:
    matches = list(DURATION_RE.finditer(text))
    if not matches or "".join(match.group(0).replace(" ", "") for match in matches).lower() != re.sub(r"\s+", "", text).lower():
        return None
    total = sum(int(amount) * DURATION_UNITS[unit.lower()] for amount, unit in (match.groups() for match in matches))
    return total or None


def safe_calculate(expression: str) -> int | float:
    if len(expression) > 100:
        raise ValueError("Expression is too long")

    def evaluate(node: ast.AST) -> int | float:
        if isinstance(node, ast.Expression):
            return evaluate(node.body)
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in ALLOWED_OPS:
            left, right = evaluate(node.left), evaluate(node.right)
            if isinstance(node.op, ast.Pow) and abs(right) > 100:
                raise ValueError("Exponent is too large")
            result = ALLOWED_OPS[type(node.op)](left, right)
            if abs(result) > 1e100:
                raise ValueError("Result is too large")
            return result
        if isinstance(node, ast.UnaryOp) and type(node.op) in ALLOWED_OPS:
            return ALLOWED_OPS[type(node.op)](evaluate(node.operand))
        raise ValueError("Only basic arithmetic is supported")

    return evaluate(ast.parse(expression, mode="eval"))


def progress_bar(pct: float, width: int = 22) -> str:
    filled = round(width * max(0.0, min(1.0, pct)))
    return "█" * filled + "░" * (width - filled)


def image_container(title: str, filename: str, accent: discord.Colour | None = None) -> discord.ui.LayoutView:
    view = discord.ui.LayoutView()
    container = discord.ui.Container(accent_color=accent or discord.Colour.blurple())
    container.add_item(discord.ui.TextDisplay(title))
    container.add_item(discord.ui.MediaGallery(discord.MediaGalleryItem(f"attachment://{filename}")))
    view.add_item(container)
    return view


def utility_state(bot: commands.Bot) -> dict[str, Any]:
    """Process-local state shared by AFK, snapshots, timers, and reminders."""
    state = getattr(bot, "utility_state", None)
    if state is None:
        state = bot.utility_state = {
            "afk": {}, "deleted": {}, "edited": {}, "reminders": {}, "next_reminder": 1,
        }
    return state


class UtilityCog(commands.Cog):
    """Convenient common base for independently loaded utility commands."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.state = utility_state(bot)

    async def status(self, ctx: commands.Context, title: str, lines: list[str], kind: str = "info") -> None:
        await ctx.reply(view=StatusLayout(title, lines, kind), mention_author=False)


def random_color() -> tuple[str, tuple[int, int, int]]:
    rgb = tuple(random.randint(0, 255) for _ in range(3))
    return "#{:02X}{:02X}{:02X}".format(*rgb), rgb


def now() -> float:
    return time.time()
