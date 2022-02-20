import enum
from typing import Optional


def bold(text: str) -> str:
    """Formats text for discord message as bold"""
    return f"**{text}**"


def italic(text: str) -> str:
    """Formats text for discord message as italic"""
    return f"*{text}*"


def underline(text: str) -> str:
    """Formats text for discord message as underlined"""
    return f"__{text}__"


def strikethrough(text: str) -> str:
    """Formats text for discord message as strikethrough"""
    return f"~~{text}~~"


def spoiler(text: str) -> str:
    """Formats text for discord message as spoiler"""
    return f"||{text}||"


def no_embed_link(url: str) -> str:
    """Makes link in discord message display without embedded website preview"""
    return f"<{url}>"


def link_in_embed(text: str, url: str) -> str:
    """Makes a clickable link inside embed"""
    return f"[{text}]({url})"


def quote_line(line: str) -> str:
    """Formats a text line for discord message as quote"""
    return f">{line}"


def inline_code(text: str) -> str:
    """Formats text for discord message as inline code"""
    return f"`{text}`"


def code_block(text: str, language: Optional[str]) -> str:
    """Formats text for discord message as code block"""
    return f"```{language or ''}\n" f"{text}" f"```"


def ansi_colors_block(text: str) -> str:
    """Formats text for discord message as code block that allows for arbitrary coloring and formatting"""
    return code_block(text, "ansi")


class AnsiStyles(enum.IntEnum):
    NORMAL = 0
    BOLD = 1
    UNDERLINE = 4


class AnsiTextColors(enum.IntEnum):
    GRAY = 30
    RED = 31
    GREEN = 32
    YELLOW = 33
    BLUE = 34
    PINK = 35
    CYAN = 36
    WHITE = 37


class AnsiBackgroundColors(enum.IntEnum):
    SOME_VERY_DARK_BLUE = 40
    ORANGE = 41
    GRAY = 42
    LIGHT_GRAY = 43
    EVEN_LIGHTER_GRAY = 44
    INDIGO = 45
    AGAIN_LIGHTER_GRAY = 46
    WHITE = 47


styles = AnsiStyles
colors = AnsiTextColors
bg_colors = AnsiBackgroundColors


def ansi_format(
    style: Optional[AnsiStyles] = None,
    color: Optional[AnsiTextColors] = None,
    background: Optional[AnsiBackgroundColors] = None,
) -> str:
    """Gives format prefix for ansi code block with selected styles"""
    text_style = ";".join(str(_style.value) for _style in (style, color, background) if _style)
    return f"[{text_style}m"


ansi_style_escape = "[0m"


def ansi_styled(
    text: str,
    style: Optional[AnsiStyles] = None,
    color: Optional[AnsiTextColors] = None,
    background: Optional[AnsiBackgroundColors] = None,
) -> str:
    """Formats text for ansi code block with selected styles"""
    return f"{ansi_format(style, color, background)}{text}{ansi_style_escape}"