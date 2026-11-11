from importlib.resources import files

from rich.align import Align
from rich.console import Group
from rich.panel import Panel
from rich.text import Text

from dnocer import __version__


def print_banner(console):
    logo_path = files("dnocer").joinpath(
        "assets", "dnocer-logo.txt"
    )

    logo_art = logo_path.read_text(encoding="utf-8")

    logo = Text(
        logo_art,
        style="bold bright_white",
        justify="center",
        no_wrap=True,
    )

    content = Text()
    content.append("DNOCER\n", style="bold white")
    content.append(
        "PROJECT INTELLIGENCE & SAFE REPAIR COMPANION\n",
        style="white",
    )
    content.append(
        f"Version {__version__}",
        style="dim white",
    )

    banner = Group(
        Align.center(logo),
        Text(""),
        Align.center(content),
    )

    console.print(
        Panel(
            banner,
            border_style="#777777",
            padding=(1, 2),
            expand=False,
        ),
        justify="center",
    )
