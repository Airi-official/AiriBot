"""Consistent, readable terminal output for AiriBot."""

from __future__ import annotations

import os
import platform
import time
from collections.abc import Mapping
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console(highlight=False)


def clear_screen() -> None:
    """Clear the terminal when attached to an interactive console."""
    if console.is_terminal:
        os.system("cls" if platform.system() == "Windows" else "clear")


def banner(
    bot_name: str,
    bot_id: int,
    prefix: str,
    owner_id: int,
    guild_count: int,
    extra: Mapping[str, Any] | None = None,
) -> None:
    """Display a compact, extensible startup/status dashboard."""
    table = Table.grid(padding=(0, 2))
    table.add_column(style="bold cyan", justify="right")
    table.add_column(style="white")
    table.add_row("Bot", f"{bot_name} · {bot_id}")
    table.add_row("Prefix", f"{prefix} (or mention)")
    table.add_row("Owner ID", str(owner_id) if owner_id else "Not configured")
    table.add_row("Servers", f"{guild_count:,}")
    table.add_row("Started", time.strftime("%Y-%m-%d %H:%M:%S %Z"))
    for key, value in (extra or {}).items():
        table.add_row(str(key), str(value))
    console.print(Panel(table, title="[bold green] AIRIBOT · ONLINE ", border_style="green", expand=False))


def section(title: str) -> None:
    console.rule(f"[bold yellow]{title}")


def ok(msg: str) -> None:
    console.print(f"[bold green]✓[/bold green] {msg")


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
