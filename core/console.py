"""
core/console.py
────────────────
All CLI/terminal presentation lives here: clearing the screen, the startup
banner, and colored helper functions for logging bot events to stdout.
Keeping this separate means main.py and the cogs just call console.info(...)
etc. instead of sprinkling print() everywhere.
"""

from __future__ import annotations

import os
import platform
import time

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()


def clear_screen() -> None:
    """Clear old terminal output on boot (cls on Windows, clear elsewhere)."""
    os.system("cls" if platform.system() == "Windows" else "clear")


def banner(bot_name: str, bot_id: int, prefix: str, owner_id: int, guild_count: int) -> None:
    table = Table.grid(padding=(0, 2))
    table.add_column(style="bold cyan", justify="right")
    table.add_column(style="white")
    table.add_row("Logged in as", f"{bot_name} ({bot_id})")
    table.add_row("Prefix", prefix)
    table.add_row("Owner ID", str(owner_id))
    table.add_row("Guilds", str(guild_count))
    table.add_row("Started", time.strftime("%Y-%m-%d %H:%M:%S"))

    console.print(Panel(table, title="[bold green] BOT ONLINE ", border_style="green", expand=False))


def section(title: str) -> None:
    console.rule(f"[bold yellow]{title}")


def ok(msg: str) -> None:
    console.print(f"[bold green]✓[/bold green] {msg}")


def warn(msg: str) -> None:
    console.print(f"[bold yellow]⚠[/bold yellow] {msg}")


def error(msg: str) -> None:
    console.print(f"[bold red]✗[/bold red] {msg}")


def info(msg: str) -> None:
    console.print(f"[bold blue]ℹ[/bold blue] {msg}")


def command_used(author: str, command: str, location: str) -> None:
    text = Text()
    text.append("▶ ", style="bold magenta")
    text.append(f"{author} ", style="bold white")
    text.append("used ", style="dim")
    text.append(f"{command} ", style="bold cyan")
    text.append(f"in {location}", style="dim")
    console.print(text)
  
