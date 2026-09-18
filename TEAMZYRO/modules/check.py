# ==========================================
# Creator: MrZyro
# check.py – /check + Who Have It (normal + inline)
# ==========================================

from TEAMZYRO import app, collection as character_collection, user_collection
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.enums import ParseMode


@app.on_message(filters.command("check"))
async def check_character(client, message):
    args = message.command
    if len(args) < 2:
        await message.reply_text(
            "Please provide a Character ID:\n`/check <character_id>`",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    character_id = str(args[1])
    character = await character_collection.find_one({"id": character_id})

    if not character:
        # try zero-padded id e.g. 1 -> 01
        character = await character_collection.find_one({"id": character_id.zfill(2)})
        if character:
            character_id = str(character.get("id"))
        else:
            await message.reply_text("Character not found.")
            return

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Who Have It", callback_data=f"whohaveit_{character_id}")]
    ])

    text = (
        f"🧩 **Character Details:**\n\n"
        f"🆔 **ID:** `{character_id}`\n"
        f"🪪 **Name:** {character.get('name', '?')}\n"
        f"📼 **Anime:** {character.get('anime', '?')}\n"
        f"🪙 **Rarity:** {character.get('rarity', '?')}\n"
    )

    if character.get("vid_url"):
        await message.reply_video(
            character["vid_url"],
            caption=text,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN,
        )
    elif character.get("img_url"):
        await message.reply_photo(
            character["img_url"],
            caption=text,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN,
        )
    else:
        await message.reply_text(
            text,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN,
        )


@app.on_callback_query(filters.regex(r"^whohaveit_"))
async def who_have_it(client, callback_query: CallbackQuery):
    character_id = callback_query.data.split("_", 1)[1]

    users = await user_collection.find({"characters.id": character_id}).to_list(length=10)

    if not users:
        await callback_query.answer("No one owns this character yet!", show_alert=True)
        return

    owner_text = "\n\n**🏆 Top 10 Users Who Own This Character:**\n\n"
    for i, user in enumerate(users, 1):
        user_name = user.get("first_name", "Unknown")
        count = sum(
            1
            for char in user.get("characters", [])
            if str(char.get("id")) == str(character_id)
        )
        owner_text += f"{i}. [{user_name}](tg://user?id={user['id']}) — x{count}\n"

    # Base caption (works when message exists)
    base = ""
    if callback_query.message:
        base = callback_query.message.caption or callback_query.message.text or ""

    if "🏆 Top 10 Users" in base:
        base = base.split("🏆 Top 10 Users")[0].rstrip()

    new_caption = (base + owner_text) if base else owner_text.strip()

    # IMPORTANT: edit_message_caption works for normal + inline (message may be None)
    try:
        await callback_query.edit_message_caption(
            caption=new_caption,
            reply_markup=None,
        )
    except Exception:
        try:
            await callback_query.edit_message_text(
                text=new_caption,
                reply_markup=None,
                disable_web_page_preview=True,
            )
        except Exception as e:
            await callback_query.answer(f"Could not update: {e}", show_alert=True)
            return

    await callback_query.answer()
