# ==========================================
# Creator: MrZyro
# Telegram: @MrZyro_dev
# GitHub: https://github.com/MrZyro
# ==========================================

import random
from datetime import datetime, timedelta
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto, InputMediaVideo
from bson import ObjectId
from pyrogram import filters
from pyrogram.enums import ParseMode
from TEAMZYRO import *

user_shop_state = {}
active_shop_chats = {}
DEFAULT_DISCOUNT = 12

RARITY_PRICE = {
    "🔵 Common": 1000,
    "🟣 Uncommon": 2500,
    "🔴 Medium": 5000,
    "🟠 Rare": 10000,
    "🟡 Legendary": 15000,
}


def safe_split(data, sep="_", expected=2):
    parts = data.split(sep)
    if len(parts) < expected:
        parts += [None] * (expected - len(parts))
    return parts[:expected]


async def get_active_discount():
    discount = await discounts_collection.find_one({})
    if discount and discount.get("expires_at") and discount["expires_at"] > datetime.utcnow():
        return discount["percent"]
    return DEFAULT_DISCOUNT


# ---------------- DISCOUNT SYSTEM ---------------- #

@app.on_message(filters.command("discount"))
async def set_discount(client, message):
    if message.from_user.id != OWNER_ID:
        return await message.reply("🚫 Only owners can set discounts.")

    args = message.text.split()
    if len(args) < 3:
        return await message.reply(
            "Usage:\n/discount <percent> <duration>\n\n"
            "Example:\n"
            "/discount 30 1d\n"
            "/discount 25 12h"
        )

    try:
        percent = int(args[1])
    except ValueError:
        return await message.reply("❌ Invalid percent value!")

    duration = args[2].lower()
    if duration.endswith("h"):
        hours = int(duration[:-1])
        expires = datetime.utcnow() + timedelta(hours=hours)
    elif duration.endswith("d"):
        days = int(duration[:-1])
        expires = datetime.utcnow() + timedelta(days=days)
    else:
        return await message.reply("❌ Duration must end with 'h' or 'd'.")

    await discounts_collection.delete_many({})
    await discounts_collection.insert_one({
        "percent": percent,
        "expires_at": expires
    })

    await message.reply(
        f"✅ Discount of {percent}% set for {duration} successfully!"
    )


def is_video(url):
    if not url:
        return False
    return any(url.lower().endswith(ext) for ext in [".mp4", ".mov", ".webm"])


# ---------------- SHOP MENU ---------------- #

@app.on_message(filters.command(["shop", "hshop", "hshopmenu"]))
async def shop_menu(client, message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    if chat_id in active_shop_chats:
        active_user_id = active_shop_chats[chat_id]
        keyboard = [[InlineKeyboardButton("❌ Cancel Active Shop", callback_data=f"cancel_shop_{active_user_id}")]]
        return await message.reply_text(
            "⚠️ **A shop session is already active in this chat!**\nUse `/cancel` or click below to cancel the current session to open a new one.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )

    active_shop_chats[chat_id] = user_id

    keyboard = []
    for i, r in enumerate(RARITY_PRICE.keys()):
        keyboard.append(
            [InlineKeyboardButton(r, callback_data=f"xeno_{i}_{user_id}")]
        )
    keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_shop_{user_id}")])

    await message.reply_photo(
        photo="https://files.catbox.moe/ohi1vs.jpg",
        caption="🌟 **Choose a rarity to browse the Bazaar!**",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


@app.on_message(filters.command("cancel"))
async def cancel_cmd(client, message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    if chat_id in active_shop_chats:
        active_shop_chats.pop(chat_id, None)
        user_shop_state.pop(user_id, None)
        await message.reply_text("✅ Active shop session canceled.")


# ---------------- SHOW RARITY ---------------- #

@app.on_callback_query(filters.regex(r"^xeno_\d+"))
async def show_rarity_list(client, callback_query):
    parts = callback_query.data.split("_")
    index = int(parts[1])

    rarity_list = list(RARITY_PRICE.keys())
    if index < 0 or index >= len(rarity_list):
        return await callback_query.answer("Invalid rarity selection!", show_alert=True)

    rarity = rarity_list[index]
    user_id = callback_query.from_user.id
    chat_id = callback_query.message.chat.id

    characters = await collection.find({"rarity": rarity}).to_list(None)
    if not characters:
        return await callback_query.answer("No characters found for this rarity!", show_alert=True)

    random.shuffle(characters)

    user_shop_state[user_id] = {
        "rarity": rarity,
        "index": 0,
        "characters": characters[:5],
        "user_id": user_id,
        "chat_id": chat_id
    }

    await render_shop_character(client, callback_query, user_id)
    await callback_query.answer()


# ---------------- RENDER CHARACTER ---------------- #

async def render_shop_character(client, callback_query, user_id):
    data = user_shop_state.get(user_id)
    if not data:
        return await callback_query.answer("Shop session expired. Please run /shop again!", show_alert=True)

    index = data["index"]
    characters = data["characters"]
    char = characters[index]

    price = RARITY_PRICE.get(char["rarity"], 1000)
    discount = await get_active_discount()
    discounted_price = int(price * (100 - discount) / 100)

    caption = (
        f"💎 <b>{char['name']}</b>\n"
        f"🏯 <b>Anime:</b> {char['anime']}\n"
        f"⭐ <b>Rarity:</b> {char['rarity']}\n"
        f"💰 <b>Price:</b> {discounted_price} Star Coins ({discount}% off!)\n"
        f"🆔 <b>ID:</b> <code>{char['id']}</code>\n"
        f"📍 <b>Item:</b> {index + 1}/{len(characters)}"
    )

    keyboard = [
        [
            InlineKeyboardButton("⬅️ Prev", callback_data="prev_char"),
            InlineKeyboardButton("🪄 Claim", callback_data=f"claim_{index}"),
            InlineKeyboardButton("➡️ Next", callback_data="next_char"),
        ],
        [InlineKeyboardButton("🔄 Refresh (5000💫)", callback_data="refresh_chars")],
        [InlineKeyboardButton("❌ Cancel Shop", callback_data=f"cancel_shop_{user_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    img_url = char.get("img_url") or char.get("vid_url") or "https://files.catbox.moe/ohi1vs.jpg"

    try:
        if is_video(img_url):
            await callback_query.message.edit_media(
                media=InputMediaVideo(media=img_url, caption=caption, parse_mode=ParseMode.HTML),
                reply_markup=reply_markup
            )
        else:
            await callback_query.message.edit_media(
                media=InputMediaPhoto(media=img_url, caption=caption, parse_mode=ParseMode.HTML),
                reply_markup=reply_markup
            )
    except Exception:
        try:
            await callback_query.message.edit_caption(
                caption=caption,
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            print(f"Error editing shop message media/caption: {e}")


# ---------------- NAVIGATION ---------------- #

@app.on_callback_query(filters.regex("^next_char$"))
async def next_character(client, callback_query):
    user_id = callback_query.from_user.id
    state = user_shop_state.get(user_id)

    if not state:
        return await callback_query.answer("Start from /shop again!", show_alert=True)

    if state["index"] >= len(state["characters"]) - 1:
        return await callback_query.answer("No more characters available on this page!", show_alert=True)

    state["index"] += 1
    await render_shop_character(client, callback_query, user_id)
    await callback_query.answer()


@app.on_callback_query(filters.regex("^prev_char$"))
async def prev_character(client, callback_query):
    user_id = callback_query.from_user.id
    state = user_shop_state.get(user_id)

    if not state:
        return await callback_query.answer("Start from /shop again!", show_alert=True)

    if state["index"] <= 0:
        return await callback_query.answer("Already at first character!", show_alert=True)

    state["index"] -= 1
    await render_shop_character(client, callback_query, user_id)
    await callback_query.answer()


# ---------------- REFRESH ---------------- #

@app.on_callback_query(filters.regex("^refresh_chars$"))
async def refresh_characters(client, callback_query):
    user_id = callback_query.from_user.id
    state = user_shop_state.get(user_id)

    if not state:
        return await callback_query.answer("Start from /shop again!", show_alert=True)

    user = await user_collection.find_one({"id": user_id})
    balance = user.get("balance", 0) if user else 0

    if balance < 5000:
        return await callback_query.answer("❌ You don't have enough coins! Refresh costs 5000 coins.", show_alert=True)

    # Deduct 5000 coins
    await user_collection.update_one({"id": user_id}, {"$inc": {"balance": -5000}})

    rarity = state["rarity"]
    characters = await collection.find({"rarity": rarity}).to_list(None)
    if not characters:
        return await callback_query.answer("No characters found for this rarity!", show_alert=True)

    random.shuffle(characters)
    state["characters"] = characters[:5]
    state["index"] = 0

    await render_shop_character(client, callback_query, user_id)
    await callback_query.answer("🔄 Shop refreshed with new characters (-5000 coins)!", show_alert=True)


# ---------------- CLAIM ---------------- #

@app.on_callback_query(filters.regex(r"^claim_\d+$"))
async def claim_character(client, callback_query):
    _, index_str = safe_split(callback_query.data, "_", 2)

    user_id = callback_query.from_user.id
    state = user_shop_state.get(user_id)

    if not state:
        return await callback_query.answer("Open shop again!", show_alert=True)

    char = state["characters"][int(index_str)]
    user = await user_collection.find_one({"id": user_id})

    if not user:
        return await callback_query.answer("Register first!", show_alert=True)

    price = RARITY_PRICE.get(char["rarity"], 1000)
    discount = await get_active_discount()
    discounted_price = int(price * (100 - discount) / 100)

    if user.get("balance", 0) < discounted_price:
        return await callback_query.answer("Not enough Star Coins!", show_alert=True)

    await user_collection.update_one(
        {"id": user_id},
        {
            "$inc": {"balance": -discounted_price},
            "$push": {"characters": {
                "_id": ObjectId(),
                "img_url": char["img_url"],
                "name": char["name"],
                "anime": char["anime"],
                "rarity": char["rarity"],
                "id": char["id"]
            }}
        }
    )

    await callback_query.answer(f"🎉 You claimed {char['name']}!", show_alert=True)


# ---------------- CANCEL SHOP ---------------- #

@app.on_callback_query(filters.regex(r"^cancel_shop"))
async def cancel_shop_callback(client, callback_query):
    user_id = callback_query.from_user.id
    chat_id = callback_query.message.chat.id

    user_shop_state.pop(user_id, None)
    active_shop_chats.pop(chat_id, None)

    try:
        await callback_query.message.delete()
    except Exception:
        pass
    await callback_query.answer("Shop session closed!", show_alert=True)
