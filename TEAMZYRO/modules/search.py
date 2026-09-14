
# ==========================================
# search.py
# /search → Search Waifus (inline) button
# flood → block all commands for 10 minutes
# Who Have It on INLINE image = inlinequery.py
# ==========================================

import time
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from pyrogram.enums import ParseMode
from TEAMZYRO import app

try:
    from pyrogram import StopPropagation
except ImportError:
    try:
        from pyrogram.dispatcher import StopPropagation
    except ImportError:
        class StopPropagation(Exception):
            pass


# ===================== FLOOD =====================
_flood = {}
FLOOD_LIMIT = 3
FLOOD_WINDOW = 8
FLOOD_BLOCK = 10 * 60


def _data(uid: int) -> dict:
    return _flood.setdefault(
        uid,
        {"count": 0, "start": 0.0, "blocked_until": 0.0, "last_warn": 0.0},
    )


def is_blocked(uid: int) -> float:
    left = _data(uid).get("blocked_until", 0) - time.time()
    return left if left > 0 else 0.0


def hit_flood(uid: int) -> float:
    now = time.time()
    d = _data(uid)
    if d.get("blocked_until", 0) > now:
        return d["blocked_until"] - now
    if now - d.get("start", 0) > FLOOD_WINDOW:
        d["count"] = 0
        d["start"] = now
    d["count"] = d.get("count", 0) + 1
    if d["count"] > FLOOD_LIMIT:
        d["blocked_until"] = now + FLOOD_BLOCK
        d["count"] = 0
        d["start"] = now
        return FLOOD_BLOCK
    return 0.0


async def _warn(message: Message, left: float):
    if not message.from_user:
        return
    d = _data(message.from_user.id)
    now = time.time()
    if now - d.get("last_warn", 0) < 4:
        return
    d["last_warn"] = now
    mins = max(1, int((left + 59) // 60))
    await message.reply_text(
        f"🚫 You are blocked for **{mins} minute(s)**\nReason: Flooding",
        parse_mode=ParseMode.MARKDOWN,
    )


@app.on_message(filters.regex(r"^/") & filters.incoming, group=-10)
async def flood_gate(client, message: Message):
    if not message.from_user:
        return
    left = is_blocked(message.from_user.id)
    if left > 0:
        await _warn(message, left)
        raise StopPropagation


@app.on_message(filters.command(["search", "find", "s"]))
async def search_cmd(client, message: Message):
    if not message.from_user:
        return

    left = hit_flood(message.from_user.id)
    if left > 0:
        await _warn(message, left)
        raise StopPropagation

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔎 Search Waifus", switch_inline_query_current_chat="")]
    ])
    await message.reply_text(
        "ℹ️ To search waifu click on button below",
        reply_markup=kb,
    )
