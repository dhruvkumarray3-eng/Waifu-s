# ==========================================
# search.py – /search → character card + Who Have It
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

try:
    from TEAMZYRO import rarity_map2 as rarity_map
except Exception:
    rarity_map = {}


def char_caption(c: dict) -> str:
    return (
        f"**Discover this amazing character:**\n\n"
        f"🌸 **{c.get('name', '?')}**\n"
        f"🏖️ From: **{c.get('anime', '?')}**\n"
        f"🔮 Rarity: **{c.get('rarity', '?')}**\n"
        f"🆔 **{c.get('id', '?')}**"
    )


def build_keyboard(char_id: str, query: str, index: int, total: int, anime_only: bool):
    flag = "1" if anime_only else "0"
    nav = []
    if index > 0:
        nav.append(InlineKeyboardButton("⬅️", callback_data=f"srch|{query}|{index - 1}|{flag}"))
    if index < total - 1:
        nav.append(InlineKeyboardButton("➡️", callback_data=f"srch|{query}|{index + 1}|{flag}"))

    buttons = []
    if nav:
        buttons.append(nav)

    buttons.append([
        InlineKeyboardButton("👥 Who Have It", callback_data=f"srchwho_{char_id}")
    ])
    buttons.append([
        InlineKeyboardButton("🔎 Inline", switch_inline_query_current_chat=query or "")
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
        caption += f"\n\n📄 {index + 1}/{total}"
    kb = build_keyboard(str(c.get("id")), query, index, total, anime_only)
    media = c.get("vid_url") or c.get("img_url")

    if edit:
        try:
            if c.get("vid_url"):
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
                await target.edit_caption(caption=caption, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
        except Exception:
            try:
                await target.edit_caption(caption=caption, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
            except Exception:
                await target.edit_text(caption, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
        return

    # new message
    if c.get("vid_url"):
        await target.reply_video(media, caption=caption, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
    elif media:
        await target.reply_photo(media, caption=caption, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
    else:
        await target.reply_text(caption, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)


# ---------- /search ----------
@app.on_message(filters.command(["search", "find", "s"]))
async def search_cmd(client, message: Message):
    args = message.command

    # Only a single inline button — no long help text
    if len(args) < 2:
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔎 Open Inline Search", switch_inline_query_current_chat="")]
        ])
        return await message.reply_text("🔎", reply_markup=kb)

    anime_only = False
    if args[1].lower() == "anime":
        if len(args) < 3:
            return await message.reply_text("`/search anime <name>`", parse_mode=ParseMode.MARKDOWN)
        anime_only = True
        query = " ".join(args[2:]).strip()
    else:
        query = " ".join(args[1:]).strip()

    chars = await find_chars(query, anime_only)
    if not chars:
        return await message.reply_text(f"❌ No results for **{query}**", parse_mode=ParseMode.MARKDOWN)

    await send_card(message, chars[0], query, 0, len(chars), anime_only, edit=False)


# ---------- Next / Prev ----------
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


# ---------- Who Have It (own callback so it never clashes with check.py) ----------
@app.on_callback_query(filters.regex(r"^srchwho_"))
async def search_who_have(client, callback_query: CallbackQuery):
    char_id = callback_query.data.split("_", 1)[1]

    users = await user_collection.find({"characters.id": char_id}).to_list(10)
    if not users:
        return await callback_query.answer("No one owns this character yet!", show_alert=True)

    lines = ["", "**🏆 Who Have It:**"]
    for i, u in enumerate(users, 1):
        name = u.get("first_name") or "User"
        cnt = sum(1 for ch in u.get("characters", []) if str(ch.get("id")) == str(char_id))
        lines.append(f"{i}. [{name}](tg://user?id={u['id']}) — x{cnt}")

    old = callback_query.message.caption or callback_query.message.text or ""
    if "🏆 Who Have It" in old:
        base = old.split("🏆 Who Have It")[0].rstrip()
    else:
        base = old.rstrip()

    new_cap = base + "\n" + "\n".join(lines)

    try:
        await callback_query.message.edit_caption(
            caption=new_cap,
            reply_markup=callback_query.message.reply_markup,
            parse_mode=ParseMode.MARKDOWN,
        )
    except Exception:
        try:
            await callback_query.message.edit_text(
                new_cap,
                reply_markup=callback_query.message.reply_markup,
                parse_mode=ParseMode.MARKDOWN,
            )
        except Exception:
            return await callback_query.answer("Could not update.", show_alert=True)

    await callback_query.answer()
