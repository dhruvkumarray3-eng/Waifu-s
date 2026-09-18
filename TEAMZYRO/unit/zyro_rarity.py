# ==========================================
# Creator: MrZyro
# Telegram: @MrZyro_dev
# GitHub: https://github.com/MrZyro
# ==========================================

rarity_map = {
    1: "🔵 Common",
    2: "🟣 Uncommon",
    3: "🔴 Medium",
    4: "🟠 Rare",
    5: "🟡 Legendary",
    6: "💮 Mystical",
    7: "⚜️ Divine",
    8: "⚡ CrossVerse",
    9: "✨ Cataphract",
    10: "🪞 Supreme",
}

# RARITY_NAMES updated according to rarity_map
RARITY_NAMES = [
    "🔵 Common",
    "🟣 Uncommon",
    "🔴 Medium",
    "🟠 Rare",
    "🟡 Legendary",
    "💮 Mystical",
    "⚜️ Divine",
    "⚡ CrossVerse",
    "✨ Cataphract",
    "🪞 Supreme",
]

# rarity_map2 updated according to rarity_map
rarity_map2 = {
    "🔵 Common": "🔵",
    "🟣 Uncommon": "🟣",
    "🔴 Medium": "🔴",
    "🟠 Rare": "🟠",
    "🟡 Legendary": "🟡",
    "💮 Mystical": "💮",
    "⚜️ Divine": "⚜️",
    "⚡ CrossVerse": "⚡",
    "✨ Cataphract": "✨",
    "🪞 Supreme": "🪞",
}

EVENT_EMOJI_MAP = {
    "CHIBI": "👶",
    "ROYALTY": "👑",
    "CHINESE": "🧧",
    "ASSEMBLY": "🎩",
    "KIMONO": "👘",
    "MAID": "🧹",
    "SCHOOL": "🎒",
    "BUNNY": "🐰",
    "BIKINI": "👙",
    "EGYPT": "🏺",
    "WEDDING": "💍",
    "NUN": "🌌",
    "PIRATE": "🏴‍☠️",
    "NURSES": "💉",
    "ANGELIC": "🪽",
    "POLICE": "🚓",
    "SHINOBI": "🥷",
    "KITTY": "🐾",
    "ATHLETE": "🏆",
    "ATHLETIC": "🏆",
    "GOTHIC": "🕷️",
    "YAKUZA": "🐲",
    "FIRST NAME": "🏹",
    "HALLOWEEN": "🎃",
    "CHRISTMAS": "🎄",
    "KNIGHT": "🛡️",
    "SHOGUN": "⛩️",
    "EROTIC": "🔞",
    "ECHHI": "🔞",
    "ECHI": "🔞",
    "EXOTIC": "✨",
    "AMV": "🎗️",
    "AMV EDITION": "🎗️",
}

def get_event_display(event_name: str) -> str:
    if not event_name:
        return ""
    key = str(event_name).strip().upper()
    emoji = EVENT_EMOJI_MAP.get(key, "")
    display_name = str(event_name).strip().upper()
    if emoji:
        return f"{emoji} {display_name}"
    return display_name


