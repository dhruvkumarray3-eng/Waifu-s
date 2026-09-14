# ==========================================
# search.py – /search by anime or character name
# ==========================================

from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from pyrogram.enums import ParseMode
from TEAMZYRO import app, collection

# rarity emoji map (fallback if rarity_map2 missing)
try:
    from TEAMZYRO import rarity_map2 as rarity_map
except Exception:
    rarity_map = {}


async def run_search(query: str, page: int = 1, anime_only: bool = False):
    """Search DB by name and/or anime. Returns (characters, total, error)."""
    query = (query or "").strip()
    if not query:
        return [], 0, "Please provide a name.\n\nUsage:\n`/search Nezuko`\n`/search Demon Slayer`\n`/search anime Jujutsu`"

    per_page = 10
    skip = (page - 1) * per_page

    if anime_only:
        filt = {"anime": {"$regex": query, "$options": "i"}}
    else:
        filt = {
            "$or": [
                {"name": {"$regex": query, "$options": "i"}},
                {"anime": {"$regex": query, "$options": "i"}},
            ]
        }

    total = await collection.count_documents(filt)
    if total == 0:
        return [], 0, f"No results for: **{query}**"

    chars = await (
        collection.find(filt)
        .sort([("anime", 1), ("id", 1)])
        .skip(skip)
        .limit(per_page)
        .to_list(length=per_page)
    )
    return chars, total, None


def build_response(query: str, characters: list, total: int, page: int, anime_only: bool):
    per_page = 10
    skip = (page - 1) * per_page
    mode = "Anime" if anime_only else "Name/Anime"

    text = (
        f"🔍 **Search** ({mode})\n"
        f"Query: `{query}`\n"
        f"**Total:** {total}  |  **Page:** {page}\n\n"
    )

    for i, c in enumerate(characters, start=1 + skip):
        emoji = rarity_map.get(c.get("rarity"), "❓")
        text += (
            f"◈⌠{emoji}⌡ **{c.get('name', '?')}**\n"
            f"   📺 {c.get('anime', '?')}\n"
            f"   🆔 `{c.get('id', '?')}`  |  {c.get('rarity', '?')}\n\n"
        )

    # callback data: searchpage|query|page|0or1
    flag = "1" if anime_only else "0"
    buttons = []
    row = []
    if page > 1:
        row.append(
            InlineKeyboardButton(
                "⬅️ Back",
                callback_data=f"searchpage|{query}|{page - 1}|{flag}",
            )
        )
    if skip + per_page < total:
        row.append(
            InlineKeyboardButton(
                "➡️ Next",
                callback_data=f"searchpage|{query}|{page + 1}|{flag}",
            )
        )
    if row:
        buttons.append(row)

    # Inline tip button (opens bot inline with same query)
    buttons.append([
        InlineKeyboardButton(
            "🔎 Open Inline Search",
            switch_inline_query_current_chat=query,
        )
    ])

    return text, InlineKeyboardMarkup(buttons) if buttons else None


# ---------- /search ----------
@app.on_message(filters.command(["search", "find", "s"]))
async def search_cmd(client, message: Message):
    args = message.command
    if len(args) < 2:
        return await message.reply_text(
            "🔍 **Character / Anime Search**\n\n"
            "Usage:\n"
            "`/search <name>` – search name **or** anime\n"
            "`/search anime <anime name>` – anime only\n\n"
            "Examples:\n"
            "`/search Nezuko`\n"
            "`/search Demon Slayer`\n"
            "`/search anime Jujutsu Kaisen`\n\n"
            "Inline: type `@YourBotName Demon Slayer` in any chat.",
            parse_mode=ParseMode.MARKDOWN,
        )

    anime_only = False
    if args[1].lower() == "anime":
        if len(args) < 3:
            return await message.reply_text(
                "Usage: `/search anime <anime name>`",
                parse_mode=ParseMode.MARKDOWN,
            )
        anime_only = True
        query = " ".join(args[2:]).strip()
    else:
        query = " ".join(args[1:]).strip()

    characters, total, err = await run_search(query, page=1, anime_only=anime_only)
    if err:
        return await message.reply_text(err, parse_mode=ParseMode.MARKDOWN)

    text, markup = build_response(query, characters, total, 1, anime_only)
    await message.reply_text(text, reply_markup=markup, parse_mode=ParseMode.MARKDOWN)


# ---------- Pagination ----------
@app.on_callback_query(filters.regex(r"^searchpage\|"))
async def search_page_cb(client, callback_query: CallbackQuery):
    try:
        # searchpage|query|page|flag
        parts = callback_query.data.split("|", 3)
        if len(parts) < 4:
            return await callback_query.answer("Invalid data.", show_alert=True)

        _, query, page_s, flag = parts
        page = int(page_s)
        anime_only = flag == "1"

        characters, total, err = await run_search(query, page=page, anime_only=anime_only)
        if err:
            await callback_query.message.edit_text(err, parse_mode=ParseMode.MARKDOWN)
            return await callback_query.answer()

        text, markup = build_response(query, characters, total, page, anime_only)
        await callback_query.message.edit_text(
            text,
            reply_markup=markup,
            parse_mode=ParseMode.MARKDOWN,
        )
        await callback_query.answer()
    except Exception as e:
        await callback_query.answer(f"Error: {e}", show_alert=True)
