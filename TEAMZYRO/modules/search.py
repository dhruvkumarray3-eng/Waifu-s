# ==========================================
# search.py – /search character card + Who Have It (same as /check)
# ==========================================

from pyrogram import filters
from pyrogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    Message,
    CallbackQuery,
    InputMediaPhoto,
    InputMediaVideo,
)
from pyrogram.enums import ParseMode
from TEAMZYRO import app, collection, user_collection


def char_caption(c: dict) -> str:
    return (
        f"🌟 **Character Info**\n"
        f"🆔 ID: `{c.get('id', '?')}`\n"
        f"📛 Name: {c.get('name', '?')}\n"
        f"📺 Anime: {c.get('anime', '?')}\n"
        f"💎 Rarity: {c.get('rarity', '?')}\n"
    )


def build_keyboard(char_id: str, query: str, index: int, total: int, anime_only: bool):
    """Same Who Have It button as check.py + optional next/prev only."""
    flag = "1" if anime_only else "0"
    buttons = []

    nav = []
    if index > 0:
        nav.append(InlineKeyboardButton("⬅️", callback_data=f"srch|{query}|{index - 1}|{flag}"))
    if index < total - 1:
        nav.append(InlineKeyboardButton("➡️", callback_data=f"srch|{query}|{index + 1}|{flag}"))
    if nav:
        buttons.append(nav)

    # EXACT same as /check
    buttons.append([
        InlineKeyboardButton("Who Have It", callback_data=f"whohaveit_{char_id}")
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
    return await collection.find(filt).sort([("anime", 1), ("id", 1)]).to_list(50)


async def send_card(target, c, query, index, total, anime_only, edit=False):
    caption = char_caption(c)
    if total > 1:
        caption += f"\n📄 {index + 1}/{total}"
    kb = build_keyboard(str(c.get("id")), query, index, total, anime_only)
    media = c.get("vid_url") or c.get("img_url")

    if edit:
        try:
            if c.get("vid_url") and media:
                await target.edit_media(
                    InputMediaVideo(media, caption=caption, parse_mode=ParseMode.MARKDOWN),
                    reply_markup=kb,
                )
            elif media:
                await target.edit_media(
                    InputMediaPhoto(media, caption=caption, parse_mode=ParseMode.MARKDOWN),
                    reply_markup=kb,
                )
            else:
                await target.edit_caption(
                    caption=caption, reply_markup=kb, parse_mode=ParseMode.MARKDOWN
                )
        except Exception:
            try:
                await target.edit_caption(
                    caption=caption, reply_markup=kb, parse_mode=ParseMode.MARKDOWN
                )
            except Exception:
                pass
        return

    if c.get("vid_url") and media:
        await target.reply_video(
            media, caption=caption, reply_markup=kb, parse_mode=ParseMode.MARKDOWN
        )
    elif media:
        await target.reply_photo(
            media, caption=caption, reply_markup=kb, parse_mode=ParseMode.MARKDOWN
        )
    else:
        await target.reply_text(caption, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)


@app.on_message(filters.command(["search", "find", "s"]))
async def search_cmd(client, message: Message):
    args = message.command

    if len(args) < 2:
        return await message.reply_text(
            "`/search <name or anime>`",
            parse_mode=ParseMode.MARKDOWN,
        )

    anime_only = False
    if args[1].lower() == "anime":
        if len(args) < 3:
            return await message.reply_text(
                "`/search anime <anime name>`",
                parse_mode=ParseMode.MARKDOWN,
            )
        anime_only = True
        query = " ".join(args[2:]).strip()
    else:
        query = " ".join(args[1:]).strip()

    chars = await find_chars(query, anime_only)
    if not chars:
        return await message.reply_text(
            f"❌ No results for **{query}**",
            parse_mode=ParseMode.MARKDOWN,
        )

    await send_card(message, chars[0], query, 0, len(chars), anime_only, edit=False)


@app.on_callback_query(filters.regex(r"^srch\|"))
async def search_nav(client, callback_query: CallbackQuery):
    try:
        _, query, index_s, flag = callback_query.data.split("|", 3)
        index = int(index_s)
        anime_only = flag == "1"
        chars = await find_chars(query, anime_only)
        if not chars or index < 0 or index >= len(chars):
            return await callback_query.answer("No more.", show_alert=True)

        await send_card(
            callback_query.message,
            chars[index],
            query,
            index,
            len(chars),
            anime_only,
            edit=True,
        )
        await callback_query.answer()
    except Exception as e:
        await callback_query.answer(str(e)[:200], show_alert=True)


# Who Have It — only if check.py does NOT already handle whohaveit_
# If check.py already has this, DELETE this whole handler.
@app.on_callback_query(filters.regex(r"^whohaveit_"))
async def who_have_it(client, callback_query: CallbackQuery):
    character_id = callback_query.data.split("_", 1)[1]

    users = await user_collection.find({"characters.id": character_id}).to_list(10)
    if not users:
        return await callback_query.answer("No one owns this character yet!", show_alert=True)

    owner_text = "\n\n**🏆 Top 10 Users Who Own This Character:**\n\n"
    for i, user in enumerate(users, 1):
        user_name = user.get("first_name", "Unknown")
        count = sum(
            1 for char in user.get("characters", [])
            if str(char.get("id")) == str(character_id)
        )
        owner_text += f"{i}. [{user_name}](tg://user?id={user['id']}) — x{count}\n"

    base = callback_query.message.caption or ""
    if "🏆 Top 10 Users" in base:
        base = base.split("🏆 Top 10 Users")[0].rstrip()

    try:
        await callback_query.message.edit_caption(
            caption=base + owner_text,
            reply_markup=None,
            parse_mode=ParseMode.MARKDOWN,
        )
    except Exception:
        await callback_query.answer("Could not update.", show_alert=True)
        return

    await callback_query.answer()
