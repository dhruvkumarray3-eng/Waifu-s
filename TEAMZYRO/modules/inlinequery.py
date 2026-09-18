# ==========================================
# inlinequery.py
# Inline search + Who Have It button under character image
# ==========================================

import re
import time
from html import escape
from cachetools import TTLCache
from telegram import (
    Update,
    InlineQueryResultPhoto,
    InlineQueryResultVideo,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import InlineQueryHandler, CallbackQueryHandler, CallbackContext
from TEAMZYRO import application, user_collection
from TEAMZYRO.unit.zyro_inline import *


all_characters_cache = TTLCache(maxsize=10000, ttl=36000)
user_collection_cache = TTLCache(maxsize=10000, ttl=60)


def who_have_keyboard(char_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Who Have It", callback_data=f"whohaveit_{char_id}")]
    ])


async def inlinequery(update: Update, context: CallbackContext) -> None:
    query = update.inline_query.query
    offset = int(update.inline_query.offset) if update.inline_query.offset else 0
    user = None

    if query.startswith("collection."):
        user_id, *search_terms = (
            query.split(" ")[0].split(".")[1],
            " ".join(query.split(" ")[1:]),
        )
        if user_id.isdigit():
            user = user_collection_cache.get(user_id) or await get_user_collection(user_id)
            if user:
                user_collection_cache[user_id] = user
                all_characters = list(
                    {
                        char["id"]: char
                        for char in user.get("characters", [])
                        if "id" in char
                    }.values()
                )
                if search_terms:
                    regex = re.compile(" ".join(search_terms), re.IGNORECASE)
                    all_characters = [
                        char
                        for char in all_characters
                        if regex.search(char.get("name", ""))
                        or regex.search(char.get("anime", ""))
                    ]
            else:
                all_characters = []
        else:
            all_characters = []
    else:
        if query:
            all_characters = await search_characters(query)
        else:
            all_characters = (
                all_characters_cache.get("all_characters") or await get_all_characters()
            )
            all_characters_cache["all_characters"] = all_characters

    if ".AMV" in query:
        all_characters = [c for c in all_characters if "vid_url" in c]
    else:
        all_characters = [c for c in all_characters if "img_url" in c]

    characters = all_characters[offset : offset + 50]
    next_offset = str(offset + len(characters)) if len(characters) == 50 else None

    results = []
    for character in characters:
        char_id = str(character.get("id", ""))

        caption = (
            f"🧩 <b>Character Details:</b>\n\n"
            f"🆔 <b>ID:</b> <code>{escape(char_id)}</code>\n"
            f"🪪 <b>Name:</b> {escape(str(character.get('name', '?')))}\n"
            f"📼 <b>Anime:</b> {escape(str(character.get('anime', '?')))}\n"
            f"🪙 <b>Rarity:</b> {escape(str(character.get('rarity', '?')))}\n"
        )

        kb = who_have_keyboard(char_id)

        if "vid_url" in character:
            thumbnail_url = character.get("thum_url", "https://envs.sh/6Y3.jpg")
            results.append(
                InlineQueryResultVideo(
                    id=f"{char_id}_{time.time()}",
                    video_url=character["vid_url"],
                    mime_type="video/mp4",
                    thumbnail_url=thumbnail_url,
                    title=str(character.get("name", "?")),
                    description=(
                        f"From: {character.get('anime', '?')} | "
                        f"Rarity: {character.get('rarity', '?')}"
                    ),
                    caption=caption,
                    parse_mode="HTML",
                    reply_markup=kb,
                )
            )
        elif "img_url" in character:
            results.append(
                InlineQueryResultPhoto(
                    id=f"{char_id}_{time.time()}",
                    photo_url=character["img_url"],
                    thumbnail_url=character["img_url"],
                    caption=caption,
                    parse_mode="HTML",
                    reply_markup=kb,
                )
            )

    await update.inline_query.answer(results, next_offset=next_offset, cache_time=5)


async def who_have_it_callback(update: Update, context: CallbackContext) -> None:
    q = update.callback_query
    if not q or not q.data:
        return

    character_id = q.data.split("_", 1)[1]
    users = await user_collection.find({"characters.id": character_id}).to_list(10)

    if not users:
        await q.answer("No one owns this character yet!", show_alert=True)
        return

    owner_text = "\n\n<b>🏆 Top 10 Users Who Own This Character:</b>\n\n"
    for i, u in enumerate(users, 1):
        name = escape(str(u.get("first_name", "Unknown")))
        count = sum(
            1
            for ch in u.get("characters", [])
            if str(ch.get("id")) == str(character_id)
        )
        owner_text += f'{i}. <a href="tg://user?id={u["id"]}">{name}</a> — x{count}\n'

    base = ""
    if q.message:
        base = q.message.caption_html or q.message.caption or ""
    if "Top 10 Users" in base:
        base = base.split("🏆")[0].rstrip()

    await q.answer()
    try:
        await q.edit_message_caption(
            caption=base + owner_text,
            parse_mode="HTML",
            reply_markup=None,
        )
    except Exception:
        pass


application.add_handler(InlineQueryHandler(inlinequery, block=False))
application.add_handler(
    CallbackQueryHandler(who_have_it_callback, pattern=r"^whohaveit_", block=False)
)
