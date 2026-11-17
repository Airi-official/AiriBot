"""
cogs/utility.py  (v2 — advanced command set, modern design)
──────────────────────────────────────────────────────────
PREFIX commands only (commands.command) — nothing here is a slash/app
command. Every reply uses Components V2 (discord.ui.LayoutView /
Container / TextDisplay / Section / MediaGallery) via core.notify.StatusLayout
or a purpose-built layout, never legacy embeds.

`ping` and `botinfo` render a generated PNG (core/imagegen.py v3 — the
"glass dashboard" redesign: gradient ring gauge for ping, tiled stat card
for botinfo). `avatar` / `servericon` / `color` also show images (real CDN
avatar/icon, or a generated swatch).

Command list
────────────
  info & images
    $ping                         latency ring gauge (image)
    $botinfo                      bot stat dashboard (image)
    $avatar [member]              a member's avatar, full size
    $servericon                    this server's icon
    $color <hex|random>            colour swatch card (image)
    $userinfo [member]            info about a member
    $serverinfo                    info about this server
    $membercount                   quick member count
    $channelinfo [channel]         info about a channel
    $roleinfo <role>               info about a role
    $uptime                         how long the bot has been running

  calculators & fun
    $calc <expression>             safe arithmetic calculator
    $choose <a, b, c, ...>         randomly pick one option
    $8ball <question>              magic 8-ball
    $poll <q> | <a> | <b> [| c|d]  button-based live poll

  advanced / stateful
    $afk [reason]                   toggle AFK status; auto-clears when you
                                     post again, and replies for you if
                                     someone pings you while you're away
    $snipe                          show the last deleted message here
    $editsnipe                      show the last edited message here
    $timer <duration> [label]       live-updating countdown with a
                                     progress bar (e.g. $timer 2m Pizza)
    $remindme <duration> <text>     schedule a reminder
    $reminders                      list your active reminders
    $cancelreminder <id>            cancel one of your reminders
"""

from __future__ import annotations

import ast
import asyncio
import io
import itertools
import operator
import random
import re
import time
from typing import Optional

import discord
from discord.ext import commands

from core import imagegen
from core.notify import StatusLayout

# ── shared formatting helpers ───────────────────────────────────────


def _fmt_duration(seconds: float) -> str:
    seconds = int(seconds)
    d, seconds = divmod(seconds, 86400)
    h, seconds = divmod(seconds, 3600)
    m, s = divmod(seconds, 60)
    parts = [f"{d}d" if d else "", f"{h}h" if h else "", f"{m}m" if m else "", f"{s}s"]
    return " ".join(p for p in parts if p) or "0s"


_DURATION_RE = re.compile(r"(\d+)\s*([dhms])", re.IGNORECASE)
_DURATION_UNITS = {"d": 86400, "h": 3600, "m": 60, "s": 1}


def _parse_duration(text: str) -> Optional[int]:
    matches = _DURATION_RE.findall(text)
    if not matches:
        return None
    total = sum(int(amount) * _DURATION_UNITS[unit.lower()] for amount, unit in matches)
    return total or None


def _progress_bar(pct: float, width: int = 22) -> str:
    pct = max(0.0, min(1.0, pct))
    filled = round(width * pct)
    return "█" * filled + "░" * (width - filled)


# Safe arithmetic evaluator for $calc — no arbitrary code execution
_ALLOWED_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _safe_eval(node):
    if isinstance(node, ast.Expression):
        return _safe_eval(node.body)
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError("Only numbers are allowed.")
    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_OPS:
        return _ALLOWED_OPS[type(node.op)](_safe_eval(node.left), _safe_eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_OPS:
        return _ALLOWED_OPS[type(node.op)](_safe_eval(node.operand))
    raise ValueError("Expression contains something that isn't basic arithmetic.")


def safe_calculate(expression: str) -> float:
    tree = ast.parse(expression, mode="eval")
    return _safe_eval(tree.body if isinstance(tree, ast.Expression) else tree)


def image_container(title_md: str, filename: str, accent: discord.Colour = discord.Colour.blurple()) -> discord.ui.LayoutView:
    """LayoutView whose Container shows a title + a MediaGallery image that
    points at an attachment the caller sends alongside (file=...)."""
    view = discord.ui.LayoutView()
    container = discord.ui.Container(accent_color=accent)
    container.add_item(discord.ui.TextDisplay(title_md))
    container.add_item(discord.ui.MediaGallery(discord.MediaGalleryItem(f"attachment://{filename}")))
    view.add_item(container)
    return view


_8BALL_ANSWERS = [
    "It is certain.", "Without a doubt.", "Yes, definitely.", "You may rely on it.",
    "Most likely.", "Outlook good.", "Signs point to yes.",
    "Reply hazy, try again.", "Ask again later.", "Cannot predict now.",
    "Don't count on it.", "My reply is no.", "Outlook not so good.", "Very doubtful.",
]

_NAMED_COLORS = {
    "red": "#ED4245", "green": "#57F287", "blue": "#5865F2", "yellow": "#FEE75C",
    "pink": "#EB459E", "orange": "#FFA500", "purple": "#9B59B6", "white": "#FFFFFF",
    "black": "#000000", "teal": "#1ABC9C",
}


def _resolve_color(text: str) -> tuple[str, tuple[int, int, int]]:
    text = text.strip().lower()
    if text in ("random", "rand", ""):
        rgb = tuple(random.randint(0, 255) for _ in range(3))
        return "#{:02X}{:02X}{:02X}".format(*rgb), rgb
    if text in _NAMED_COLORS:
        text = _NAMED_COLORS[text]
    text = text.lstrip("#")
    if len(text) == 3:
        text = "".join(c * 2 for c in text)
    if len(text) != 6 or any(c not in "0123456789abcdefABCDEF" for c in text):
        raise ValueError("not a valid color")
    rgb = tuple(int(text[i:i + 2], 16) for i in (0, 2, 4))
    return f"#{text.upper()}", rgb


# ── Poll view (Components V2 buttons) ──────────────────────────────


class PollView(discord.ui.LayoutView):
    def __init__(self, question: str, options: list[str]):
        super().__init__(timeout=600)
        self.options = options
        self.votes: dict[int, int] = {}

        self.container = discord.ui.Container(accent_color=discord.Colour.gold())
        self.container.add_item(discord.ui.TextDisplay(f"### 📊 {question}"))
        self.container.add_item(discord.ui.Separator())
        self.body = discord.ui.TextDisplay(self._render_body())
        self.container.add_item(self.body)

        row = discord.ui.ActionRow()
        for i, option in enumerate(options):
            btn = discord.ui.Button(label=f"{i + 1}. {option[:60]}", style=discord.ButtonStyle.primary, custom_id=f"poll_{i}")
            btn.callback = self._make_callback(i)
            row.add_item(btn)
        self.container.add_item(row)
        self.add_item(self.container)

    def _render_body(self) -> str:
        total = len(self.votes) or 1
        lines = []
        for i, option in enumerate(self.options):
            count = sum(1 for v in self.votes.values() if v == i)
            pct = round(count / total * 100)
            lines.append(f"**{i + 1}.** {option} — `{_progress_bar(count / total, 10)}` {count} vote(s), {pct}%")
        return "\n".join(lines)

    def _make_callback(self, index: int):
        async def callback(interaction: discord.Interaction):
            self.votes[interaction.user.id] = index
            self.body.content = self._render_body()
            await interaction.response.edit_message(view=self)
        return callback


# ── the cog ──────────────────────────────────────────────────────────


class Utility(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.afk: dict[int, dict] = {}                 # user_id -> {reason, since}
        self.last_deleted: dict[int, dict] = {}         # channel_id -> {author, content, at}
        self.last_edited: dict[int, dict] = {}           # channel_id -> {author, before, after, at}
        self._reminder_ids = itertools.count(1)
        self.reminders: dict[int, dict] = {}             # id -> {user_id, channel_id, text, fire_at, task}

    def cog_unload(self) -> None:
        for r in self.reminders.values():
            r["task"].cancel()

    # ── listeners: afk / snipe / editsnipe ───────────────────────────

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot or not message.guild:
            return

        prefix = self.bot.command_prefix if isinstance(self.bot.command_prefix, str) else "$"

        # clear the sender's own AFK (unless this message IS the $afk command itself)
        if message.author.id in self.afk and not message.content.startswith(f"{prefix}afk"):
            info = self.afk.pop(message.author.id)
            duration = _fmt_duration(time.time() - info["since"])
            try:
                await message.reply(
                    view=StatusLayout("👋 Welcome back", [f"I removed your AFK status. You were away for **{duration}**."], "ok"),
                    mention_author=False,
                    delete_after=8,
                )
            except discord.HTTPException:
                pass

        # notify if an AFK user was pinged
        for member in message.mentions:
            if member.id in self.afk and member.id != message.author.id:
                info = self.afk[member.id]
                ago = _fmt_duration(time.time() - info["since"])
                reason = info["reason"] or "AFK"
                try:
                    await message.reply(
                        view=StatusLayout(f"💤 {member.display_name} is AFK", [reason, f"-# away for {ago}"], "warn"),
                        mention_author=False,
                    )
                except discord.HTTPException:
                    pass

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message) -> None:
        if message.author.bot and message.content == "":
            return
        self.last_deleted[message.channel.id] = {
            "author": str(message.author),
            "content": message.content or "*(no text content — embed, file, or sticker)*",
            "at": time.time(),
        }

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message) -> None:
        if before.author.bot or before.content == after.content:
            return
        self.last_edited[before.channel.id] = {
            "author": str(before.author),
            "before": before.content or "*(empty)*",
            "after": after.content or "*(empty)*",
            "at": time.time(),
        }

    # ── ping: image ───────────────────────────────────────────────
    @commands.command(name="ping")
    async def ping(self, ctx: commands.Context) -> None:
        start = time.perf_counter()
        placeholder = await ctx.reply("⏳ Measuring...")
        api_ms = round((time.perf_counter() - start) * 1000)
        ws_ms = round(self.bot.latency * 1000)

        buffer = await asyncio.to_thread(imagegen.render_ping_gauge, ws_ms, api_ms)
        file = discord.File(buffer, filename="ping.png")
        view = image_container("### 🏓 Pong!", "ping.png")

        await placeholder.delete()
        await ctx.reply(view=view, file=file)

    # ── botinfo: image dashboard ─────────────────────────────────────
    @commands.command(name="botinfo")
    async def botinfo(self, ctx: commands.Context) -> None:
        import sys as _sys

        bot = self.bot
        uptime = _fmt_duration(time.time() - bot.boot_time) if getattr(bot, "boot_time", None) else "unknown"
        member_total = sum(g.member_count or 0 for g in bot.guilds)

        try:
            avatar_bytes = await bot.user.display_avatar.read()
        except Exception:
            avatar_bytes = None

        stats = [
            ("Guilds", f"{len(bot.guilds):,}", imagegen.BLURPLE),
            ("Users", f"{member_total:,}", imagegen.GREEN),
            ("Latency", f"{round(bot.latency * 1000)} ms", imagegen.YELLOW),
            ("Uptime", uptime, imagegen.PINK),
            ("discord.py", discord.__version__, imagegen.BLURPLE),
            ("Python", f"{_sys.version_info.major}.{_sys.version_info.minor}.{_sys.version_info.micro}", imagegen.GREEN),
        ]
        buffer = await asyncio.to_thread(imagegen.render_bot_info_card, str(bot.user), avatar_bytes, stats)
        file = discord.File(buffer, filename="botinfo.png")
        view = image_container("### 🤖 Bot Dashboard", "botinfo.png")
        await ctx.reply(view=view, file=file)

    # ── avatar / servericon / color: images ───────────────────────────
    @commands.command(name="avatar")
    async def avatar(self, ctx: commands.Context, member: Optional[discord.Member] = None) -> None:
        member = member or ctx.author
        view = discord.ui.LayoutView()
        container = discord.ui.Container(accent_color=discord.Colour.blurple())
        container.add_item(discord.ui.TextDisplay(f"### 🖼️ {member.display_name}'s avatar"))
        container.add_item(discord.ui.MediaGallery(discord.MediaGalleryItem(member.display_avatar.url)))
        view.add_item(container)
        await ctx.reply(view=view)

    @commands.command(name="servericon")
    @commands.guild_only()
    async def servericon(self, ctx: commands.Context) -> None:
        g = ctx.guild
        if g.icon is None:
            await ctx.reply(view=StatusLayout("No server icon", ["This server has no icon set."], "warn"))
            return
        view = discord.ui.LayoutView()
        container = discord.ui.Container(accent_color=discord.Colour.blurple())
        container.add_item(discord.ui.TextDisplay(f"### 🖼️ {g.name}'s icon"))
        container.add_item(discord.ui.MediaGallery(discord.MediaGalleryItem(g.icon.url)))
        view.add_item(container)
        await ctx.reply(view=view)

    @commands.command(name="color", aliases=["colour"])
    async def color(self, ctx: commands.Context, *, value: str = "random") -> None:
        try:
            hex_color, rgb = _resolve_color(value)
        except ValueError:
            await ctx.reply(view=StatusLayout("🎨 Color", ["Give me a hex code (`#5865F2`), a name (`blue`), or `random`."], "warn"))
            return
        buffer = await asyncio.to_thread(imagegen.render_color_card, hex_color, rgb)
        file = discord.File(buffer, filename="color.png")
        view = image_container(f"### 🎨 {hex_color}", "color.png", accent=discord.Colour.from_rgb(*rgb))
        await ctx.reply(view=view, file=file)

    # ── userinfo: text + thumbnail accessory ─────────────────────────
    @commands.command(name="userinfo")
    @commands.guild_only()
    async def userinfo(self, ctx: commands.Context, member: Optional[discord.Member] = None) -> None:
        member = member or ctx.author
        view = discord.ui.LayoutView()
        container = discord.ui.Container(accent_color=member.color or discord.Colour.blurple())

        info_text = (
            f"### {member.display_name}\n"
            f"**Username:** {member}\n"
            f"**ID:** `{member.id}`\n"
            f"**Joined server:** <t:{int(member.joined_at.timestamp())}:D>\n"
            f"**Account created:** <t:{int(member.created_at.timestamp())}:D>\n"
            f"**Top role:** {member.top_role.mention if member.top_role else '—'}\n"
            f"**Roles:** {len(member.roles) - 1}"
        )
        section = discord.ui.Section(discord.ui.TextDisplay(info_text), accessory=discord.ui.Thumbnail(member.display_avatar.url))
        container.add_item(section)
        view.add_item(container)
        await ctx.reply(view=view)

    # ── serverinfo / membercount ──────────────────────────────────────
    @commands.command(name="serverinfo")
    @commands.guild_only()
    async def serverinfo(self, ctx: commands.Context) -> None:
        g = ctx.guild
        lines = [
            f"**Owner:** {g.owner}",
            f"**Members:** {g.member_count:,}",
            f"**Roles:** {len(g.roles)}",
            f"**Text channels:** {len(g.text_channels)}  •  **Voice channels:** {len(g.voice_channels)}",
            f"**Boosts:** {g.premium_subscription_count} (tier {g.premium_tier})",
            f"**Created:** <t:{int(g.created_at.timestamp())}:D>",
        ]
        await ctx.reply(view=StatusLayout(f"🏠 {g.name}", lines, "info"))

    @commands.command(name="membercount")
    @commands.guild_only()
    async def membercount(self, ctx: commands.Context) -> None:
        g = ctx.guild
        humans = sum(1 for m in g.members if not m.bot)
        bots = sum(1 for m in g.members if m.bot)
        await ctx.reply(view=StatusLayout("👥 Member count", [f"**Total:** {g.member_count:,}", f"**Humans:** {humans:,}", f"**Bots:** {bots:,}"], "info"))

    # ── channelinfo / roleinfo ────────────────────────────────────────
    @commands.command(name="channelinfo")
    @commands.guild_only()
    async def channelinfo(self, ctx: commands.Context, channel: Optional[discord.abc.GuildChannel] = None) -> None:
        channel = channel or ctx.channel
        lines = [
            f"**Name:** {channel.name}",
            f"**Type:** {str(channel.type).title()}",
            f"**ID:** `{channel.id}`",
            f"**Created:** <t:{int(channel.created_at.timestamp())}:D>",
        ]
        if isinstance(channel, discord.TextChannel):
            lines.append(f"**Topic:** {channel.topic or '—'}")
            lines.append(f"**NSFW:** {'Yes' if channel.is_nsfw() else 'No'}")
        await ctx.reply(view=StatusLayout(f"# {channel.name}", lines, "info"))

    @commands.command(name="roleinfo")
    @commands.guild_only()
    async def roleinfo(self, ctx: commands.Context, *, role: discord.Role) -> None:
        lines = [
            f"**Color:** {str(role.color)}",
            f"**Members:** {len(role.members)}",
            f"**Position:** {role.position}",
            f"**Mentionable:** {'Yes' if role.mentionable else 'No'}",
            f"**Hoisted:** {'Yes' if role.hoist else 'No'}",
            f"**Created:** <t:{int(role.created_at.timestamp())}:D>",
        ]
        await ctx.reply(view=StatusLayout(f"🎭 {role.name}", lines, "info"))

    # ── uptime ─────────────────────────────────────────────────────────
    @commands.command(name="uptime")
    async def uptime(self, ctx: commands.Context) -> None:
        if not getattr(self.bot, "boot_time", None):
            await ctx.reply(view=StatusLayout("Uptime", ["Still starting up..."], "warn"))
            return
        await ctx.reply(view=StatusLayout("⏱️ Uptime", [_fmt_duration(time.time() - self.bot.boot_time)], "info"))

    # ── calc / choose / 8ball ────────────────────────────────────────
    @commands.command(name="calc")
    async def calc(self, ctx: commands.Context, *, expression: str) -> None:
        try:
            result = safe_calculate(expression)
            await ctx.reply(view=StatusLayout("🧮 Calculator", [f"`{expression}` = **{result:g}**"], "ok"))
        except Exception:
            await ctx.reply(view=StatusLayout("🧮 Calculator", ["Couldn't evaluate that. Only numbers and + - * / // % ** ( ) are supported."], "error"))

    @commands.command(name="choose")
    async def choose(self, ctx: commands.Context, *, options: str) -> None:
        choices = [o.strip() for o in options.split(",") if o.strip()]
        if len(choices) < 2:
            await ctx.reply(view=StatusLayout("🎲 Choose", ["Give me at least two options, separated by commas."], "warn"))
            return
        await ctx.reply(view=StatusLayout("🎲 I choose...", [f"**{random.choice(choices)}**"], "ok"))

    @commands.command(name="8ball")
    async def eight_ball(self, ctx: commands.Context, *, question: str) -> None:
        await ctx.reply(view=StatusLayout("🎱 Magic 8-Ball", [f"*{question}*", random.choice(_8BALL_ANSWERS)], "info"))

    # ── poll ───────────────────────────────────────────────────────────
    @commands.command(name="poll")
    async def poll(self, ctx: commands.Context, *, content: str) -> None:
        parts = [p.strip() for p in content.split("|") if p.strip()]
        if len(parts) < 3:
            await ctx.reply(view=StatusLayout("📊 Poll", ["Format: `$poll question | option 1 | option 2 [| option 3] [| option 4]`"], "warn"))
            return
        question, *options = parts
        await ctx.reply(view=PollView(question, options[:4]))

    # ── afk ────────────────────────────────────────────────────────────
    @commands.command(name="afk")
    async def afk_cmd(self, ctx: commands.Context, *, reason: str = "AFK") -> None:
        self.afk[ctx.author.id] = {"reason": reason, "since": time.time()}
        await ctx.reply(view=StatusLayout("💤 AFK set", [f"I'll let people know: *{reason}*"], "ok"))

    # ── snipe / editsnipe ────────────────────────────────────────────
    @commands.command(name="snipe")
    @commands.guild_only()
    async def snipe(self, ctx: commands.Context) -> None:
        data = self.last_deleted.get(ctx.channel.id)
        if not data:
            await ctx.reply(view=StatusLayout("🔍 Snipe", ["Nothing recently deleted here."], "warn"))
            return
        ago = _fmt_duration(time.time() - data["at"])
        await ctx.reply(view=StatusLayout("🔍 Last deleted message", [f"**{data['author']}**", data["content"], f"-# {ago} ago"], "info"))

    @commands.command(name="editsnipe")
    @commands.guild_only()
    async def editsnipe(self, ctx: commands.Context) -> None:
        data = self.last_edited.get(ctx.channel.id)
        if not data:
            await ctx.reply(view=StatusLayout("✏️ Edit snipe", ["Nothing recently edited here."], "warn"))
            return
        ago = _fmt_duration(time.time() - data["at"])
        lines = [f"**{data['author']}**", f"**Before:** {data['before']}", f"**After:** {data['after']}", f"-# {ago} ago"]
        await ctx.reply(view=StatusLayout("✏️ Last edited message", lines, "info"))

    # ── timer: live countdown with a progress bar ─────────────────────
    @commands.command(name="timer")
    async def timer(self, ctx: commands.Context, duration: str, *, label: str = "Timer") -> None:
        seconds = _parse_duration(duration)
        if not seconds or seconds > 3 * 3600:
            await ctx.reply(view=StatusLayout("⏲️ Timer", ["Give a duration like `90s`, `5m`, `1h30m` (max 3h)."], "warn"))
            return

        end_at = time.monotonic() + seconds
        view = discord.ui.LayoutView()
        container = discord.ui.Container(accent_color=discord.Colour.blurple())
        container.add_item(discord.ui.TextDisplay(f"### ⏲️ {label}"))
        body = discord.ui.TextDisplay(f"`{_progress_bar(0)}`\n**{_fmt_duration(seconds)}** remaining")
        container.add_item(body)
        view.add_item(container)
        message = await ctx.reply(view=view)

        interval = max(3, min(10, seconds // 15 or 1))
        try:
            while True:
                remaining = end_at - time.monotonic()
                if remaining <= 0:
                    break
                await asyncio.sleep(min(interval, remaining))
                remaining = max(0, end_at - time.monotonic())
                pct = 1 - (remaining / seconds)
                body.content = f"`{_progress_bar(pct)}`\n**{_fmt_duration(remaining)}** remaining"
                try:
                    await message.edit(view=view)
                except discord.HTTPException:
                    return
        finally:
            body.content = f"`{_progress_bar(1)}`\n**Time's up!**"
            container.accent_color = discord.Colour.green()
            try:
                await message.edit(view=view, content=f"{ctx.author.mention}")
            except discord.HTTPException:
                pass

    # ── reminders: set / list / cancel ───────────────────────────────
    @commands.command(name="remindme")
    async def remindme(self, ctx: commands.Context, duration: str, *, text: str) -> None:
        seconds = _parse_duration(duration)
        if not seconds:
            await ctx.reply(view=StatusLayout("⏰ Reminder", ["Couldn't parse that duration. Try `10m`, `1h30m`, `2d`."], "warn"))
            return
        if seconds > 7 * 86400:
            await ctx.reply(view=StatusLayout("⏰ Reminder", ["Max reminder length is 7 days."], "warn"))
            return

        reminder_id = next(self._reminder_ids)
        fire_at = time.time() + seconds

        async def _wait_and_remind(rid: int):
            await asyncio.sleep(seconds)
            self.reminders.pop(rid, None)
            try:
                await ctx.reply(view=StatusLayout("⏰ Reminder", [f"{ctx.author.mention} — {text}"], "info"))
            except discord.HTTPException:
                pass

        task = asyncio.create_task(_wait_and_remind(reminder_id))
        self.reminders[reminder_id] = {"user_id": ctx.author.id, "text": text, "fire_at": fire_at, "task": task}

        await ctx.reply(view=StatusLayout(
            "⏰ Reminder set",
            [f"**#{reminder_id}** in **{_fmt_duration(seconds)}**: {text}"],
            "ok",
            footer=f"-# Use $reminders to see all, $cancelreminder {reminder_id} to cancel this one",
        ))

    @commands.command(name="reminders")
    async def list_reminders(self, ctx: commands.Context) -> None:
        mine = [(rid, r) for rid, r in self.reminders.items() if r["user_id"] == ctx.author.id]
        if not mine:
            await ctx.reply(view=StatusLayout("⏰ Your reminders", ["You have no active reminders."], "info"))
            return
        lines = [f"**#{rid}** in {_fmt_duration(r['fire_at'] - time.time())} — {r['text']}" for rid, r in mine]
        await ctx.reply(view=StatusLayout("⏰ Your reminders", lines, "info"))

    @commands.command(name="cancelreminder")
    async def cancel_reminder(self, ctx: commands.Context, reminder_id: int) -> None:
        r = self.reminders.get(reminder_id)
        if not r or r["user_id"] != ctx.author.id:
            await ctx.reply(view=StatusLayout("⏰ Cancel reminder", ["No reminder with that ID belongs to you."], "warn"))
            return
        r["task"].cancel()
        self.reminders.pop(reminder_id, None)
        await ctx.reply(view=StatusLayout("⏰ Reminder cancelled", [f"**#{reminder_id}** — {r['text']}"], "ok"))


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Utility(bot))
