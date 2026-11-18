"""Countdown timers and in-memory personal reminders."""

from __future__ import annotations

import asyncio
import itertools
import time

import discord
from discord.ext import commands

from core.notify import StatusLayout
from ._shared import UtilityCog, fmt_duration, parse_duration, progress_bar


class TimeTools(UtilityCog):
    def __init__(self, bot: commands.Bot) -> None:
        super().__init__(bot)
        self.tasks: dict[int, asyncio.Task] = {}

    def cog_unload(self) -> None:
        for task in self.tasks.values():
            task.cancel()

    @commands.command(name="timer")
    async def timer(self, ctx: commands.Context, duration: str, *, label: str = "Timer") -> None:
        seconds = parse_duration(duration)
        if not seconds or seconds > 10800:
            await ctx.reply(view=StatusLayout("⏲️ Timer", ["Use a duration such as `90s`, `5m`, or `1h30m` (maximum 3 hours)."], "warn"))
            return
        end = time.monotonic() + seconds
        view = discord.ui.LayoutView()
        container = discord.ui.Container(accent_color=discord.Colour.blurple())
        body = discord.ui.TextDisplay(f"`{progress_bar(0)}`\n**{fmt_duration(seconds)}** remaining")
        container.add_item(discord.ui.TextDisplay(f"### ⏲️ {label[:150]}"))
        container.add_item(body)
        view.add_item(container)
        message = await ctx.reply(view=view)
        interval = max(3, min(10, seconds // 15 or 1))
        try:
            while (remaining := end - time.monotonic()) > 0:
                await asyncio.sleep(min(interval, remaining))
                remaining = max(0, end - time.monotonic())
                body.content = f"`{progress_bar(1 - remaining / seconds)}`\n**{fmt_duration(remaining)}** remaining"
                await message.edit(view=view)
        except (discord.HTTPException, asyncio.CancelledError):
            return
        body.content = f"`{progress_bar(1)}`\n**Time's up!**"
        container.accent_color = discord.Colour.green()
        try:
            await message.edit(view=view, content=ctx.author.mention)
        except discord.HTTPException:
            pass

    @commands.command(name="remindme")
    async def remindme(self, ctx: commands.Context, duration: str, *, text: str) -> None:
        seconds = parse_duration(duration)
        if not seconds or seconds > 7 * 86400:
            await ctx.reply(view=StatusLayout("⏰ Reminder", ["Enter a valid duration up to 7 days, such as `10m` or `2d`."], "warn"))
            return
        reminder_id = self.state["next_reminder"]
        self.state["next_reminder"] += 1
        due = time.time() + seconds

        async def deliver() -> None:
            try:
                await asyncio.sleep(seconds)
                self.state["reminders"].pop(reminder_id, None)
                await ctx.reply(view=StatusLayout("⏰ Reminder", [f"{ctx.author.mention} — {text[:700]}"], "info"))
            except (discord.HTTPException, asyncio.CancelledError):
                pass
            finally:
                self.tasks.pop(reminder_id, None)

        self.state["reminders"][reminder_id] = {"user_id": ctx.author.id, "text": text[:700], "due": due}
        self.tasks[reminder_id] = asyncio.create_task(deliver())
        await ctx.reply(view=StatusLayout("⏰ Reminder set", [f"**#{reminder_id}** in **{fmt_duration(seconds)}**: {text[:300]}", "Reminders are kept in memory and will not survive a bot restart."], "ok"))

    @commands.command(name="reminders")
    async def reminders(self, ctx: commands.Context) -> None:
        mine = [(rid, item) for rid, item in self.state["reminders"].items() if item["user_id"] == ctx.author.id]
        lines = [f"**#{rid}** in {fmt_duration(item['due'] - time.time())} — {item['text']}" for rid, item in mine]
        await ctx.reply(view=StatusLayout("⏰ Your reminders", lines or ["You have no active reminders."], "info"))

    @commands.command(name="cancelreminder")
    async def cancel_reminder(self, ctx: commands.Context, reminder_id: int) -> None:
        item = self.state["reminders"].get(reminder_id)
        if not item or item["user_id"] != ctx.author.id:
            await ctx.reply(view=StatusLayout("⏰ Cancel reminder", ["No reminder with that ID belongs to you."], "warn"))
            return
        task = self.tasks.pop(reminder_id, None)
        if task:
            task.cancel()
        self.state["reminders"].pop(reminder_id, None)
        await ctx.reply(view=StatusLayout("⏰ Reminder cancelled", [f"**#{reminder_id}** — {item['text']}"], "ok"))


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(TimeTools(bot))
