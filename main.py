import asyncio
import os
import time
import platform
import psutil
import discord
from discord.ext import commands
from dotenv import load_dotenv

from core import console
from core.notify import send_status

# ─────────────────────────────────────────
#  Configuration & Environment Setup
# ─────────────────────────────────────────
load_dotenv()

TOKEN          = os.getenv("DISCORD_TOKEN")
OWNER_ID       = int(os.getenv("OWNER_ID", "0"))
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID", "0")) or None
PREFIX         = os.getenv("PREFIX", "$")

if not TOKEN:
    raise SystemExit(
        "❌ CRITICAL ERROR: DISCORD_TOKEN is not set in the .env file. "
        "Please configure your environment variables before running AiriBot."
    )

# ─────────────────────────────────────────
#  Bot Initialization with Advanced Intents
# ─────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True
intents.guilds = True

class AiriBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=commands.when_mentioned_or(PREFIX),
            intents=intents,
            owner_id=OWNER_ID,
            help_command=None, # We use a custom interactive help system
        )
        self.boot_time = None
        self.log_channel_id = LOG_CHANNEL_ID

    async def setup_hook(self) -> None:
        """Load cogs and synchronize global/guild slash commands."""
        await self.load_extensions()
        
        # Sync application slash commands with Discord API
        try:
            synced = await self.tree.sync()
            console.ok(f"Synced {len(synced)} slash command(s).")
        except Exception as e:
            console.error(f"Failed to sync slash commands: {e}")

    async def load_extensions(self) -> None:
        console.section("Loading AiriBot Modules (Cogs)")
        initial_extensions = [
            "cogs.utility",
            # "cogs.moderation",
            # "cogs.music",
        ]
        for ext in initial_extensions:
            try:
                await self.load_extension(ext)
                console.ok(f"Loaded extension: {ext}")
            except Exception as e:
                console.error(f"Failed to load extension {ext}: {e}")

bot = AiriBot()

# ─────────────────────────────────────────
#  Event Listeners
# ─────────────────────────────────────────
@bot.event
async def on_ready() -> None:
    bot.boot_time = time.time()
    
    console.clear_screen()
    console.banner(
        bot_name=str(bot.user),
        bot_id=bot.user.id,
        prefix=PREFIX,
        owner_id=OWNER_ID,
        guild_count=len(bot.guilds),
    )

    # Rich Presence with Dynamic Status Rotation or Activity
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.streaming,
            name=f"{PREFIX}help | Airi Development",
            url="https://twitch.tv/airi"
        )
    )

    if bot.log_channel_id:
        await send_status(
            bot,
            title="✨ AiriBot Online & Operational",
            lines=[
                f"• Logged in as: **{bot.user}** (`{bot.user.id}`)",
                f"• Active Guilds: **{len(bot.guilds)}** servers",
                f"• Command Prefix: `{PREFIX}`",
                f"• Python Version: `{platform.python_version()}`",
                f"• Discord.py: `{discord.__version__}`"
            ],
            kind="ok",
        )

@bot.event
async def on_command(ctx: commands.Context) -> None:
    location = f"#{ctx.channel}" if ctx.guild else "Direct Message"
    console.command_used(str(ctx.author), ctx.command.qualified_name, location)

@bot.event
async def on_command_error(ctx: commands.Context, error: commands.CommandError) -> None:
    if isinstance(error, commands.CommandNotFound):
        return
    
    # Styled Error Embed for better user experience
    error_embed = discord.Embed(
        title="⚠️ Command Execution Error",
        color=discord.Color.brand_red(),
        timestamp=discord.utils.utcnow()
    )
    
    if isinstance(error, commands.MissingRequiredArgument):
        error_embed.description = f"Missing required argument: `{error.param.name}`\nPlease check usage instructions."
    elif isinstance(error, commands.NotOwner):
        error_embed.description = "🚫 This command is strictly restricted to the bot owner."
    elif isinstance(error, commands.MissingPermissions):
        error_embed.description = "🚫 You do not have the required permissions to execute this command."
    elif isinstance(error, commands.CommandOnCooldown):
        error_embed.description = f"⏱️ Command on cooldown. Please retry in `{error.retry_after:.1f}` seconds."
    else:
        error_embed.description = f"An unexpected error occurred:\n```py\n{str(error)[:500]}\n```"
        console.error(f"Command error in {ctx.command}: {error}")

    try:
        await ctx.reply(embed=error_embed, ephemeral=True)
    except discord.HTTPException:
        await ctx.send(embed=error_embed)

@bot.event
async def on_disconnect() -> None:
    console.warn("⚠️ Disconnected from Discord Gateway — attempting automatic reconnection...")

# ─────────────────────────────────────────
#  Main Entry Point
# ─────────────────────────────────────────
async def main() -> None:
    console.clear_screen()
    console.section(f"Launching AiriBot • All in one (Prefix: {PREFIX})")
    async with bot:
        await bot.start(TOKEN)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.warn("🛑 Shutdown requested manually via Ctrl+C.")
