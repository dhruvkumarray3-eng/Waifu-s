# ==========================================
# search.py – /search → character card + Who Have It
# ==========================================

from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from pyrogram.enums import ParseMode
from TEAMZYRO import app, collection, user_collection

try:
    from TEAMZYRO import rarity_map2 as rarity_map
except Exception:
    rarity_map = {}


def char_caption(c: dict) -> str:
    return (
        f"🌟 **Character Info**\n"
        f"🆔 ID: `{c.get('id', '?')}`\n"
        f"📛 Name: {c.get('name', '?')}\n"
        f"📺 Anime: {c.get('anime', '?')}\n"
        f"💎 Rarity: {c.get('rarity', '?')}\n"
    )


def build_keyboard(char_id: str, query: str, index: int, total: int, anime_only: bool):
    flag = "1" if anime_only else "0"
    row = []
    if index > 0:
        row.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"srch|{query}|{index - 1}|{flag}"))
    if index < total - 1:
        row.append(InlineKeyboardButton("Next ➡️", callback_data=f"srch|{query}|{index + 1}|{flag}"))

    buttons = []
    if row:
        buttons.append(row)

    buttons.append([
        InlineKeyboardButton("👥 Who Have It", callback_data=f"whohaveit_{char_id}"),
    ])
    buttons.append([
        InlineKeyboardButton("🔎 Inline Search", switch_inline_query_current_chat=query),
    ])
    return InlineKeyboardMarkup(buttons)


async def find_chars(query: str, anime_only: bool = False):
    query = (query or "").strip()
    if not query:
        return []

    if anime_only:
        filt = {"anime": {"$regex": query, "$options": "i"}}
    else:
        filt = {
            "$or": [
                {"name": {"$regex": query, "$options": "i"}},
                {"anime": {"$regex": query, "$options": "i"}},
            ]
        }

    return await (
        collection.find(filt)
        .sort([("anime", 1), ("id", 1)])
        .to_list(length=50)  # max 50 results to browse
    )


async def send_char_card(message: Message, c: dict, query: str, index: int, total: int, anime_only: bool, edit: bool = False):
    caption = char_caption(c) + f"\n📄 Result **{index + 1}/{total}**"
    kb = build_keyboard(str(c.get("id")), query, index, total, anime_only)

    media = c.get("vid_url") or c.get("img_url")
    is_video = bool(c.get("vid_url"))

    try:
        if edit:
            # For edit we only change caption + buttons (media stays)
            await message.edit_caption(caption=caption, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
            return

        if is_video:
            await message.reply_video(video=media, caption=caption, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
        elif media:
            await message.reply_photo(photo=media, caption=caption, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
        else:
            await message.reply_text(caption, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
    except Exception:
        # fallback text
        if edit:
            await message.edit_text(caption, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
        else:
            await message.reply_text(caption, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)


# ---------- /search ----------
@app.on_message(filters.command(["search", "find", "s"]))
async def search_cmd(client, message: Message):
    args = message.command

    # No args → open inline in this chat
    if len(args) < 2:
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔎 Open Inline Search", switch_inline_query_current_chat="")]
        ])
        return await message.reply_text(
            "🔍 Tap below to search characters **inline**.\n\n"
            "Or use:\n"
            "`/search Nezuko`\n"
            "`/search Demon Slayer`\n"
            "`/search anime Jujutsu`",
            reply_markup=kb,
            parse_mode=ParseMode.MARKDOWN,
        )

    anime_only = False
    if args[1].lower() == "anime":
        if len(args) < 3:
            return await message.reply_text("Usage: `/search anime <anime name>`", parse_mode=ParseMode.MARKDOWN)
        anime_only = True
        query = " ".join(args[2:]).strip()
    else:
        query = " ".join(args[1:]).strip()

    chars = await find_chars(query, anime_only=anime_only)
    if not chars:
        return await message.reply_text(f"❌ No characters found for: **{query}**", parse_mode=ParseMode.MARKDOWN)

    # Show first result as full character card
    await send_char_card(message, chars[0], query, 0, len(chars), anime_only, edit=False)


# ---------- Next / Prev ----------
@app.on_callback_query(filters.regex(r"^srch\|"))
async def search_nav_cb(client, callback_query: CallbackQuery):
    try:
        # srch|query|index|flag
        parts = callback_query.data.split("|", 3)
        if len(parts) < 4:
            return await callback_query.answer("Invalid.", show_alert=True)

        _, query, index_s, flag = parts
        index = int(index_s)
        anime_only = flag == "1"

        chars = await find_chars(query, anime_only=anime_only)
        if not chars:
            return await callback_query.answer("No results.", show_alert=True)

        if index < 0 or index >= len(chars):
            return await callback_query.answer("No more results.", show_alert=True)

        c = chars[index]
        caption = char_caption(c) + f"\n📄 Result **{index + 1}/{len(chars)}**"
        kb = build_keyboard(str(c.get("id")), query, index, len(chars), anime_only)

        # Try replace media if photo/video changes
        media = c.get("vid_url") or c.get("img_url")
        try:
            if c.get("vid_url"):
                from pyrogram.types import InputMediaVideo
                await callback_query.message.edit_media(
                    media=InputMediaVideo(media, caption=caption, parse_mode=ParseMode.MARKDOWN),
                    reply_markup=kb,
                )
            elif media:
                from pyrogram.types import InputMediaPhoto
                await callback_query.message.edit_media(
                    media=InputMediaPhoto(media, caption=caption, parse_mode=ParseMode.MARKDOWN),
                    reply_markup=kb,
                )
            else:
                await callback_query.message.edit_caption(
                    caption=caption, reply_markup=kb, parse_mode=ParseMode.MARKDOWN
                )
        except Exception:
            await callback_query.message.edit_caption(
                caption=caption, reply_markup=kb, parse_mode=ParseMode.MARKDOWN
            )

        await callback_query.answer()
    except Exception as e:
        await callback_query.answer(f"Error: {e}", show_alert=True)


# ---------- Who Have It (same style as /check) ----------
# If check.py already has this handler, delete THIS block to avoid double handlers.
@app.on_callback_query(filters.regex(r"^whohaveit_"))
async def who_have_it_search(client, callback_query: CallbackQuery):
    character_id = callback_query.data.split("_", 1)[1]

    users = await user_collection.find({"characters.id": character_id}).to_list(length=10)
    if not users:
        return await callback_query.answer("No one owns this character yet!", show_alert=True)

    owner_text = "\n\n**🏆 Top owners:**\n"
    for i, user in enumerate(users, 1):
        user_name = user.get("first_name", "Unknown")
        count = sum(1 for ch in user.get("characters", []) if str(ch.get("id")) == str(character_id))
        owner_text += f"{i}. [{user_name}](tg://user?id={user['id']}) — x{count}\n"

    old = callback_query.message.caption or ""
    # Don't stack list multiple times
    if "🏆 Top owners" in old:
        base = old.split("🏆 Top owners")[0].rstrip()
    else:
        base = old

    try:
        await callback_query.message.edit_caption(
            caption=base + owner_text,
            reply_markup=callback_query.message.reply_markup,
            parse_mode=ParseMode.MARKDOWN,
        )
    except Exception:
        await callback_query.answer("Could not update caption.", show_alert=True)
        return

    await callback_query.answer()
