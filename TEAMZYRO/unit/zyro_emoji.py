"""Shared Telegram custom-emoji helpers.

The IDs are public Telegram custom-emoji document IDs supplied by the bot
owner.  The visible character is kept as accessible fallback text; Telegram
renders the custom emoji entity when the ID is valid.
"""

from __future__ import annotations

import html
PREMIUM_EMOJI_IDS = (
    "6086639764251873025",
    "6242354082741230982",
    "6064381676060937106",
    "5291933173674957761",
    "6325826291102652174",
    "6325724977119107388",
    "6325814870784611442",
    "6325816971023619278",
    "6325337042788029862",
    "6125242144329307158",
    "6242337293714070030",
    "6242488747145829251",
    "6242024203483095341",
    "6242194146749060860",
    "6241991905329027377",
    "6242186729340541187",
    "6242343572956256818",
    "6269456709358459481",
    "5386587088873331829",
    "6181235916435101802",
    "6113897533677771141",
    "6114123268568914133",
    "6113663268981577878",
    "6113982157418404889",
    "6111877370040295004",
    "6120763081850097645",
    "6120928798868246569",
    "6120897827859075223",
    "6190701977110847373",
)

LIGHTNING_EMOJI_IDS = (
    "6100194943031055090",
    "6100682589322874156",
    "6100143880164872147",
    "6102479500560305483",
    "6100142153588019385",
    "6100427043063729958",
    "6100446112718524075",
    "6100178089579384501",
)


def custom_emoji(emoji_id: str, fallback: str = "✨") -> str:
    """Return Telegram HTML for one custom emoji entity."""
    # Telegram requires the text covered by a custom-emoji entity to be one
    # character.  Variation selectors are presentation hints, not part of the
    # fallback character, and make symbols such as ⚡️ two code points long.
    safe_fallback = (fallback or "✨").replace("\ufe0f", "").replace("\ufe0e", "")
    if len(safe_fallback) != 1:
        safe_fallback = safe_fallback[0]
    return (
        f'<tg-emoji emoji-id="{int(emoji_id)}">'
        f"{html.escape(safe_fallback)}</tg-emoji>"
    )


def premium(index: int = 0, fallback: str = "✨") -> str:
    """Pick one of the supplied premium emoji IDs deterministically."""
    emoji_id = PREMIUM_EMOJI_IDS[index % len(PREMIUM_EMOJI_IDS)]
    return custom_emoji(emoji_id, fallback)


def lightning(index: int = 0, fallback: str = "⚡") -> str:
    """Pick one of the supplied lightning custom emoji IDs."""
    emoji_id = LIGHTNING_EMOJI_IDS[index % len(LIGHTNING_EMOJI_IDS)]
    return custom_emoji(emoji_id, fallback)


def lightning_row() -> str:
    """Return all supplied lightning emojis for a decorative divider."""
    return " ".join(lightning(index) for index in range(len(LIGHTNING_EMOJI_IDS)))


def render_help_text(raw_text: str) -> str:
    """Convert the existing help markdown into safe HTML with premium markers."""
    text = html.escape(raw_text, quote=False)

    # Support multiple bold/code sections without changing the source data.
    bold_open = True
    while "**" in text:
        text = text.replace("**", "<b>" if bold_open else "</b>", 1)
        bold_open = not bold_open

    code_open = True
    while "`" in text:
        text = text.replace("`", "<code>" if code_open else "</code>", 1)
        code_open = not code_open

    lines = []
    for index, line in enumerate(text.splitlines()):
        if line.strip():
            lines.append(f"{premium(index, '🔹')} {line}")
        else:
            lines.append(line)
    return "\n".join(lines)


def premium_row(count: int, fallback: str = "✨") -> str:
    """Build a short row of distinct custom emojis for decorative separators."""
    return " ".join(premium(index, fallback) for index in range(count))