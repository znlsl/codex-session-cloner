"""Top-level ``aik`` dispatcher and TUI hub.

Routes ``aik <tool> <subcommand>`` into the matching subpackage CLI:

* ``aik codex …`` → :func:`ai_cli_kit.codex.cli.main`
* ``aik claude …`` → :func:`ai_cli_kit.claude.cli.main`

When invoked with no arguments on an interactive TTY, opens an interactive hub
that lets the user pick a tool, then transfers control to that tool's TUI.

Backwards-compatible entry points (``codex-session-toolkit``, ``cst``,
``cc-clean``) bypass this dispatcher and call the per-tool ``main`` directly,
so existing scripts and shell aliases continue to work unchanged.
"""

from __future__ import annotations

import os
import sys
from typing import Optional, Sequence

from . import APP_COMMAND, APP_DISPLAY_NAME, __version__
from .core.tui.terminal import (
    Ansi,
    clear_screen,
    configure_text_streams,
    display_width,
    glyphs,
    is_interactive_terminal,
    read_key,
    render_box,
    style_text,
    term_width,
)


# Tool registry — pairs the public token (``codex`` / ``claude``) with the
# entry point function and the hub display copy. Adding a new sibling tool
# means appending one tuple here plus its launcher script.
_TOOLS = (
    ("codex", "Codex Session Toolkit", "ai_cli_kit.codex.cli", "克隆 / 导出 / 导入 / 修复 Codex 会话"),
    ("claude", "CC Clean (Claude Code)", "ai_cli_kit.claude.cli", "清理本地标识 / 遥测 / 历史，安全备份"),
)


def main(argv: Optional[Sequence[str]] = None) -> int:
    configure_text_streams()
    argv = list(sys.argv[1:] if argv is None else argv)

    # Help / version short-circuits — must precede the dispatch table so the
    # hub never gets entered when the user only wants info.
    if argv and argv[0] in {"-h", "--help", "help"}:
        _print_top_help()
        return 0
    if argv and argv[0] in {"-V", "--version"}:
        sys.stdout.write(f"{APP_COMMAND} {__version__}\n")
        return 0

    # Sub-tool dispatch.
    if argv and argv[0] in {token for token, _, _, _ in _TOOLS}:
        tool_token = argv[0]
        passthrough = argv[1:]
        return _dispatch_to_tool(tool_token, passthrough)

    # Unknown subcommand → show help with a hint.
    if argv and not argv[0].startswith("-"):
        sys.stderr.write(
            f"{APP_COMMAND}: unknown tool '{argv[0]}'. "
            f"Known tools: {', '.join(token for token, _, _, _ in _TOOLS)}\n"
        )
        _print_top_help(stream=sys.stderr)
        return 2

    # No args + interactive TTY → open the hub.
    if not argv and is_interactive_terminal():
        return _run_hub()

    # No args, non-interactive (piped / scripted) → just show help.
    _print_top_help()
    return 0


def _dispatch_to_tool(tool_token: str, passthrough: Sequence[str]) -> int:
    """Import the tool's CLI module on demand and call its ``main(argv)``."""
    import importlib

    module_name = next(module for token, _, module, _ in _TOOLS if token == tool_token)
    module = importlib.import_module(module_name)
    tool_main = getattr(module, "main", None)
    if not callable(tool_main):
        sys.stderr.write(f"{APP_COMMAND}: {module_name}.main is not callable\n")
        return 1
    return int(tool_main(list(passthrough)) or 0)


def _print_top_help(stream=None) -> None:
    out = stream or sys.stdout
    lines = [
        f"{APP_DISPLAY_NAME} {__version__}",
        "",
        f"Usage:  {APP_COMMAND} <tool> [args…]",
        f"        {APP_COMMAND}                   # interactive hub",
        f"        {APP_COMMAND} --help / --version",
        "",
        "Tools:",
    ]
    width = max(len(token) for token, _, _, _ in _TOOLS)
    for token, label, _, summary in _TOOLS:
        lines.append(f"  {token.ljust(width)}  {label}")
        lines.append(f"  {' ' * width}    {summary}")
    lines.extend([
        "",
        "Examples:",
        f"  {APP_COMMAND} codex clone-provider",
        f"  {APP_COMMAND} codex export-desktop-all --dry-run",
        f"  {APP_COMMAND} claude plan",
        f"  {APP_COMMAND} claude clean --preset safe --yes",
        "",
        "Backwards-compatible entry points still work:",
        "  codex-session-toolkit / cst   →  same as `aik codex …`",
        "  cc-clean                       →  same as `aik claude …`",
    ])
    out.write("\n".join(lines) + "\n")


# ---------------------------------------------------------------------------
# Interactive hub
# ---------------------------------------------------------------------------


def _run_hub() -> int:
    """Two-card picker: arrow keys / number / Enter to launch a tool's own TUI.

    Designed as the "front door" — minimal text, two big highlighted cards,
    one-key entry. The user should immediately see two clearly-labelled
    options and not need to read documentation to pick one.
    """
    selected = 0
    sys.stdout.write("\033[?1049h\033[?25l")  # alt screen + hide cursor
    sys.stdout.flush()
    last_signature: Optional[tuple] = None
    try:
        while True:
            signature = (selected, term_width())
            if signature != last_signature:
                _render_hub(selected)
                last_signature = signature
            key = read_key(timeout_ms=None if os.name != "nt" else 500)
            if key is None:
                continue
            if key in ("UP", "k", "K"):
                selected = (selected - 1) % len(_TOOLS)
                continue
            if key in ("DOWN", "j", "J"):
                selected = (selected + 1) % len(_TOOLS)
                continue
            if key == "ENTER":
                sys.stdout.write("\033[?25h\033[?1049l")
                sys.stdout.flush()
                return _dispatch_to_tool(_TOOLS[selected][0], [])
            if isinstance(key, str) and key.isdigit():
                idx = int(key) - 1
                if 0 <= idx < len(_TOOLS):
                    sys.stdout.write("\033[?25h\033[?1049l")
                    sys.stdout.flush()
                    return _dispatch_to_tool(_TOOLS[idx][0], [])
                continue
            key_lower = (key or "").lower()
            if key_lower in {"q", "quit", "exit"} or key == "ESC":
                return 0
    finally:
        sys.stdout.write("\033[?25h\033[?1049l")
        sys.stdout.flush()


def _render_hub(selected: int) -> None:
    pointer = glyphs().get("pointer", ">")
    cols = term_width()
    # Card width tries to feel "big and obvious" without overflowing narrow
    # terminals. 72 cols is a Goldilocks default; we cap at 90 for ultrawide.
    card_width = max(40, min(cols - 4, 90))

    clear_screen()
    sys.stdout.write("\033[H")

    # Banner — kept text-only (no pixel-art) so it renders identically on
    # every terminal and doesn't dwarf the two cards which are the actual UI.
    banner_text = "AI CLI KIT"
    subtitle = f"{APP_DISPLAY_NAME} v{__version__}  ·  统一 AI CLI 工具箱"
    banner = style_text(banner_text, Ansi.BOLD, Ansi.BRIGHT_CYAN)
    hint = style_text(subtitle, Ansi.DIM)
    sys.stdout.write("\n")
    sys.stdout.write(_centered(banner, cols) + "\n")
    sys.stdout.write(_centered(hint, cols) + "\n")
    sys.stdout.write("\n")

    # Two big cards — selected one gets BRIGHT_CYAN+BOLD border + bright label,
    # the other dims down so the active choice is unmistakable at a glance.
    for idx, (_token, label, _module, summary) in enumerate(_TOOLS):
        is_selected = idx == selected
        if is_selected:
            border_codes = (Ansi.BOLD, Ansi.BRIGHT_CYAN)
            number = style_text(f"{idx + 1}", Ansi.BOLD, Ansi.BRIGHT_CYAN)
            label_styled = style_text(label, Ansi.BOLD, Ansi.UNDERLINE, Ansi.BRIGHT_CYAN)
            summary_styled = style_text(summary, Ansi.BRIGHT_BLUE)
        else:
            border_codes = (Ansi.DIM,)
            number = style_text(f"{idx + 1}", Ansi.DIM)
            label_styled = style_text(label, Ansi.DIM)
            summary_styled = style_text(summary, Ansi.DIM)

        card_lines = [
            f"  {number}.  {label_styled}",
            f"      {summary_styled}",
        ]
        rendered = render_box(card_lines, width=card_width, border_codes=border_codes)

        # Inject a left-margin pointer on the middle line of the selected card
        # so users see a clear "you are here" without having to track colour.
        prefix_active = style_text(pointer, Ansi.BOLD, Ansi.BRIGHT_CYAN) + " "
        prefix_idle = "  "
        for line_idx, line in enumerate(rendered):
            indent = "  "  # left-align the cards to the terminal
            marker = prefix_active if (is_selected and line_idx == 1) else prefix_idle
            sys.stdout.write(indent + marker + line + "\n")
        sys.stdout.write("\n")

    footer = style_text(
        "  ↑↓ 选择    Enter / 数字键 进入    q 退出",
        Ansi.DIM,
    )
    sys.stdout.write(footer + "\n")
    sys.stdout.flush()


def _centered(text: str, cols: int) -> str:
    width = display_width(text)
    pad = max(0, (cols - width) // 2)
    return (" " * pad) + text


if __name__ == "__main__":
    raise SystemExit(main())
