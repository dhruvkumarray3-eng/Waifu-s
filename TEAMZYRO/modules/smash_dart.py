# ==========================================
# Creator: MrZyro
# Telegram: @MrZyro_dev
# GitHub: https://github.com/MrZyro
# ==========================================

import random
import asyncio
import time
from datetime import datetime
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto, InputMediaVideo, Message, CallbackQuery
from bson import ObjectId
from TEAMZYRO import app, user_collection, collection

user_dart_progress = {}
user_smash_state = {}
active_smash_chats = {}
user_smash_cooldowns = {}

SMASH_RARITIES = ['🔵 Common', '🟣 Uncommon', '🔴 Medium', '🟠 Rare', '🟡 Legendary']


def is_video(url):
    if not url:
        return False
    return any(url.lower().endswith(ext) for ext in [".mp4", ".mov", ".webm"])


# ==================== /DART COMMAND ==================== #

@app.on_message(filters.command(["dart", "darts"]))
async def dart_handler(client: Client, message: Message):
    user_id = message.from_user.id
    today = datetime.utcnow().date()

    if user_id not in user_dart_progress or user_dart_progress[user_id]["date"] != today:
        user_dart_progress[user_id] = {"date": today, "count": 0}

    current_count = user_dart_progress[user_id]["count"]

    if current_count >= 5:
        return await message.reply_text(
            "🎯 <b>Ara ara! You have reached your daily limit of 5 darts for today! Come back tomorrow.</b>",
            parse_mode=enums.ParseMode.HTML
        )

    # Send animated Telegram dart dice first
    try:
        await client.send_dice(chat_id=message.chat.id, emoji="🎯")
        await asyncio.sleep(2.5)  # Wait for animated dart throw to land
    except Exception as e:
        print(f"Error sending animated dart dice: {e}")

    # Calculate reward between 3 and 12 coins
    coins_won = random.randint(3, 12)
    user_dart_progress[user_id]["count"] += 1
    new_count = user_dart_progress[user_id]["count"]

    # Update balance in MongoDB
    user = await user_collection.find_one({'id': user_id})
    if user:
        await user_collection.update_one({'id': user_id}, {'$inc': {'balance': coins_won}})
        new_balance = user.get('balance', 0) + coins_won
    else:
        new_balance = coins_won
        await user_collection.insert_one({
            'id': user_id,
            'username': message.from_user.username,
            'first_name': message.from_user.first_name,
            'characters': [],
            'balance': coins_won
        })

    reply_text = (
        f"🎯 <b>DART THROW RESULT</b>\n\n"
        f"🎯 <i>You threw a precision dart straight into the target!</i>\n"
        f"💰 <b>Earned:</b> +{coins_won} Wisteria Coins 💴\n"
        f"💳 <b>Total Balance:</b> {new_balance} Coins\n"
        f"📊 <b>Attempts Today:</b> {new_count}/5"
    )

    await message.reply_text(reply_text, parse_mode=enums.ParseMode.HTML)


# ==================== /SMASH COMMAND ==================== #

async def fetch_smash_character():
    # Pick a random rarity equally from the allowed rarities
    target_rarity = random.choice(SMASH_RARITIES)
    pipeline = [{'$match': {'rarity': target_rarity}}, {'$sample': {'size': 1}}]
    cursor = collection.aggregate(pipeline)
    chars = await cursor.to_list(length=1)
    if not chars:
        # Fallback to any character in DB
        pipeline = [{'$sample': {'size': 1}}]
        cursor = collection.aggregate(pipeline)
        chars = await cursor.to_list(length=1)
    return chars[0] if chars else None


@app.on_message(filters.command(["smash", "pass", "smashpass"]))
async def smash_handler(client: Client, message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    current_time = time.time()

    # Check 5-minute cooldown
    if user_id in user_smash_cooldowns:
        cooldown_end = user_smash_cooldowns[user_id]
        if current_time < cooldown_end:
            remaining = int(cooldown_end - current_time)
            mins, secs = divmod(remaining, 60)
            time_str = f"{mins}m {secs}s" if mins > 0 else f"{secs}s"
            return await message.reply_text(
                f"⏳ <b>Ara ara~ You are on a 5-minute cooldown before using /smash again!</b>\n"
                f"Please wait <b>{time_str}</b>.",
                parse_mode=enums.ParseMode.HTML
            )

    if chat_id in active_smash_chats:
        active_user_id = active_smash_chats[chat_id]
        keyboard = [[InlineKeyboardButton("❌ Cancel Active Smash", callback_data=f"cancel_smash_{active_user_id}")]]
        return await message.reply_text(
            "⚠️ <b>A smash session is already active in this chat!</b>\nUse /cancel or click below to cancel the current session to start a new one.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=enums.ParseMode.HTML
        )

    char = await fetch_smash_character()
    if not char:
        return await message.reply_text("🚫 No characters available to smash right now.")

    active_smash_chats[chat_id] = user_id
    user_smash_state[user_id] = {
        "character": char,
        "chat_id": chat_id,
        "user_id": user_id
    }

    await send_smash_card(client, message, user_id, is_initial=True)


async def send_smash_card(client, event, user_id, is_initial=False):
    state = user_smash_state.get(user_id)
    if not state:
        return

    char = state["character"]
    caption = (
        f"🔥 <b>SMASH OR PASS?</b> 🔥\n\n"
        f"🪪 <b>Name:</b> {char['name']}\n"
        f"⛩️ <b>Anime:</b> {char['anime']}\n"
        f"🪙 <b>Rarity:</b> {char['rarity']}\n"
        f"🆔 <b>ID:</b> <code>{char['id']}</code>"
    )

    keyboard = [
        [
            InlineKeyboardButton("💚 Smash", callback_data=f"smash_do_smash_{user_id}"),
            InlineKeyboardButton("💔 Pass", callback_data=f"smash_do_pass_{user_id}")
        ],
        [InlineKeyboardButton("❌ Cancel Smash", callback_data=f"cancel_smash_{user_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    img_url = char.get("img_url") or char.get("vid_url") or "https://files.catbox.moe/ohi1vs.jpg"

    if is_initial:
        if is_video(img_url):
            await event.reply_video(video=img_url, caption=caption, reply_markup=reply_markup, parse_mode=enums.ParseMode.HTML)
        else:
            await event.reply_photo(photo=img_url, caption=caption, reply_markup=reply_markup, parse_mode=enums.ParseMode.HTML)
    else:
        try:
            if is_video(img_url):
                await event.message.edit_media(media=InputMediaVideo(media=img_url, caption=caption, parse_mode=enums.ParseMode.HTML), reply_markup=reply_markup)
            else:
                await event.message.edit_media(media=InputMediaPhoto(media=img_url, caption=caption, parse_mode=enums.ParseMode.HTML), reply_markup=reply_markup)
        except Exception:
            try:
                await event.message.edit_caption(caption=caption, reply_markup=reply_markup, parse_mode=enums.ParseMode.HTML)
            except Exception as e:
                print(f"Error rendering smash card: {e}")


@app.on_callback_query(filters.regex(r"^smash_do_"))
async def smash_action_callback(client: Client, callback_query: CallbackQuery):
    parts = callback_query.data.split("_")
    action = parts[2]  # "smash" or "pass"
    target_user_id = int(parts[3])

    if callback_query.from_user.id != target_user_id:
        return await callback_query.answer("🦋 This smash session belongs to another user~", show_alert=True)

    state = user_smash_state.get(target_user_id)
    if not state:
        return await callback_query.answer("Smash session expired! Please run /smash again.", show_alert=True)

    # Set 5-minute (300s) cooldown after performing an action
    user_smash_cooldowns[target_user_id] = time.time() + 300

    char = state["character"]
    user_id = callback_query.from_user.id

    if action == "smash":
        # 70% win chance
        is_win = random.random() < 0.70
        if is_win:
            await user_collection.update_one(
                {'id': user_id},
                {
                    '$push': {'characters': {
                        '_id': ObjectId(),
                        'img_url': char.get('img_url', ''),
                        'vid_url': char.get('vid_url', ''),
                        'name': char['name'],
                        'anime': char['anime'],
                        'rarity': char['rarity'],
                        'id': char['id']
                    }}
                },
                upsert=True
            )
            result_alert = f"🎉 SMASH SUCCESSFUL! You won {char['name']}!"
        else:
            result_alert = f"❌ SMASH FAILED! {char['name']} rejected your attempt!"
    else:
        result_alert = f"💔 PASS! You passed on {char['name']}."

    await callback_query.answer(result_alert, show_alert=True)

    # End current smash session & clean up so cooldown applies next time
    user_smash_state.pop(target_user_id, None)
    active_smash_chats.pop(callback_query.message.chat.id, None)
    try:
        await callback_query.message.delete()
    except Exception:
        pass


@app.on_callback_query(filters.regex(r"^cancel_smash_"))
async def cancel_smash_callback(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    chat_id = callback_query.message.chat.id

    # Set 5-minute cooldown on cancel as well
    user_smash_cooldowns[user_id] = time.time() + 300

    user_smash_state.pop(user_id, None)
    active_smash_chats.pop(chat_id, None)

    try:
        await callback_query.message.delete()
    except Exception:
        pass
    await callback_query.answer("Smash session closed! (5-minute cooldown active)", show_alert=True)
