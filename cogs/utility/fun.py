"""Fun, calculator, poll, and color commands."""

from __future__ import annotations

import asyncio
import random

import discord
from discord.ext import commands

from core import imagegen
from core.notify import StatusLayout
from ._shared import UtilityCog, image_container, safe_calculate

ANSWERS = [
    "It is certain.", "Without a doubt.", "Yes, definitely.", "You may rely on it.",
    "Most likely.", "Outlook good.", "Signs point to yes.", "Ask again later.",
    "Cannot predict now.", "Don't count on it.", "My reply is no.", "Very doubtful.",
]
COLORS = {"red":"#ED4245", "green":"#57F287", "blue":"#5865F2", "yellow":"#FEE75C", "pink":"#EB459E", "orange":"#FFA500", "purple":"#9B59B6", "white":"#FFFFFF", "black":"#000000", "teal":"#1ABC9C"}


class PollView(discord.ui.LayoutView):
    def __init__(self, question: str, options: list[str]) -> None:
        super().__init__(timeout=600)
        self.options = options
        self.votes: dict[int, int] = {}
        self.body = discord.ui.TextDisplay(self.render())
        container = discord.ui.Container(accent_color=discord.Colour.gold())
        container.add_item(discord.ui.TextDisplay(f"### 📊 {question[:200]}"))
        container.add_item(discord.ui.Separator())
        container.add_item(self.body)
        row = discord.ui.ActionRow()
        for index, option in enumerate(options):
            button = discord.ui.Button(label=f"{index + 1}. {option[:60]}", style=discord.ButtonStyle.primary)
            button.callback = self.make_callback(index)
            row.add_item(button)
        container.add_item(row)
        self.add_item(container)

    def render(self) -> str:
        total = len(self.votes)
        lines = []
        for index, option in enumerate(self.options):
            count = sum(vote == index for vote in self.votes.values())
            pct = round(count / total * 100) if total else 0
            lines.append(f"**{index + 1}.** {option} — `{count}` vote(s), {pct}%")
        return "\n".join(lines)

    def make_callback(self, index: int):
        async def callback(interaction: discord.Interaction) -> None:
            self.votes[interaction.user.id] = index
            self.body.content = self.render()
            await interaction.response.edit_message(view=self)
        return callback


class Fun(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command(name="calc")
    async def calc(self, ctx: commands.Context, *, expression: str) -> None:
        try:
            result = safe_calculate(expression)
        except (ValueError, SyntaxError, ArithmeticError, OverflowError):
            await ctx.reply(view=StatusLayout("🧮 Calculator", ["Only safe basic arithmetic is supported."], "error"))
            return
        await ctx.reply(view=StatusLayout("🧮 Calculator", [f"`{expression[:150]}` = **{result:g}**"], "ok"))

    @commands.command(name="choose")
    async def choose(self, ctx: commands.Context, *, options: str) -> None:
        choices = [item.strip() for item in options.split(",") if item.strip()]
        if len(choices) < 2:
            await ctx.reply(view=StatusLayout("🎲 Choose", ["Provide at least two comma-separated choices."], "warn"))
            return
        await ctx.reply(view=StatusLayout("🎲 I choose…", [random.choice(choices)[:500]], "ok"))

    @commands.command(name="8ball")
    async def eight_ball(self, ctx: commands.Context, *, question: str) -> None:
        await ctx.reply(view=StatusLayout("🎱 Magic 8-Ball", [f"*{question[:500]}*", random.choice(ANSWERS)], "info"))

    @commands.command(name="poll")
    async def poll(self, ctx: commands.Context, *, content: str) -> None:
        parts = [part.strip() for part in content.split("|") if part.strip()]
        if len(parts) < 3 or len(parts[0]) > 200:
            await ctx.reply(view=StatusLayout("📊 Poll", ["Format: `$poll question | option 1 | option 2` (up to 4 options)."], "warn"))
            return
        await ctx.reply(view=PollView(parts[0], parts[1:5]))

    @commands.command(name="color", aliases=["colour"])
    async def color(self, ctx: commands.Context, *, value: str = "random") -> None:
        value = value.strip().lower()
        if value in {"random", "rand", ""}:
            hex_color, rgb = ("#{:02X}{:02X}{:02X}".format(*(random.randint(0, 255) for _ in range(3))), None)
            rgb = tuple(int(hex_color[index:index + 2], 16) for index in (1, 3, 5))
        else:
            raw = COLORS.get(value, value).lstrip("#")
            if len(raw) == 3:
                raw = "".join(char * 2 for char in raw)
            if len(raw) != 6 or any(char not in "0123456789abcdef" for char in raw):
                await ctx.reply(view=StatusLayout("🎨 Color", ["Use a named color, hex code, or `random`."], "warn"))
                return
            hex_color = "#" + raw.upper()
            rgb = tuple(int(raw[index:index + 2], 16) for index in (0, 2, 4))
        buffer = await asyncio.to_thread(imagegen.render_color_card, hex_color, rgb)
        view = image_container(f"### 🎨 {hex_color}", "color.png", discord.Colour.from_rgb(*rgb))
        await ctx.reply(view=view, file=discord.File(buffer, filename="color.png"))


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Fun(bot))
