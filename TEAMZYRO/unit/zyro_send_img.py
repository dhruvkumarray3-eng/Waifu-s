# ==========================================
# Creator: MrZyro
# Telegram: @MrZyro_dev
# GitHub: https://github.com/MrZyro
# ==========================================

from TEAMZYRO import *
from TEAMZYRO.unit.zyro_rarity import rarity_map2
import random
import asyncio
import time
from telegram import Update
from telegram.ext import CallbackContext

log = "-1002155818429"

async def expire_character(chat_id, message_id, char_timestamp, context):
    await asyncio.sleep(300)  # 5 minutes (300 seconds)
    if chat_id in last_characters and last_characters[chat_id].get('timestamp') == char_timestamp:
        if chat_id not in first_correct_guesses and not last_characters[chat_id].get('ranaway', False):
            last_characters[chat_id]['ranaway'] = True
            try:
                await context.bot.delete_message(chat_id, message_id)
            except Exception:
                pass
            try:
                await context.bot.send_message(
                    chat_id,
                    "🦋 <i>Oh dear, the target detected our poison incense and fled into the dark!</i>",
                    parse_mode='HTML'
                )
            except Exception as e:
                print(f"Error sending runaway message: {e}")

RARITY_WEIGHTS = {
    "🔵 Common": (40, True),             # Most frequent
    "🟣 Uncommon": (30, True),           # Less frequent than Common
    "🔴 Medium": (20, True),             # Medium rarity
    "🟠 Rare": (15, True),               # Rare
    "🟡 Legendary": (10, True),          # Rare but obtainable
    "💮 Mystical": (8, True),            # Very rare
    "⚜️ Divine": (6, True),              # Extremely rare
    "⚡ CrossVerse": (4, True),          # Ultra-rare
    "✨ Cataphract": (3, False),         # Special rarity
    "🪞 Supreme": (1.2, True),           # Very rare supreme rarity
    "🎐 Celestial": (2.5, True),         # Cosmic themed rarity
    "❄️ Winter": (2, False),             # Winter themed rarity
    "💝 Valentine": (2, False),          # Valentine's rarity
    "🎃 Halloween": (1.8, False),        # Halloween themed rarity
    "🎄 Christmas Special": (1.5, False),# Christmas themed rarity
    "🎭 Cosplay Master 🎭": (1, True),   # Exclusive cosplay edition
    "🧧 Events": (0.8, False),           # Limited-time event rarity
    "🍑 Echhi": (0.6, True),             # Adult-themed rarity
    "🎗️ AMV Edition": (0.5, False),     # AMV special rarity
    "🌧 Rainy": (2.0, False),            # Rainy event rarity
}


FORCED_RARITY = None

async def send_image(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id

    global FORCED_RARITY
    if FORCED_RARITY:
        all_characters = list(await collection.find({"rarity": FORCED_RARITY}).to_list(length=None))
        if not all_characters:
            # Fallback to any character with that rarity
            all_characters = list(await collection.find({"rarity": {"$regex": FORCED_RARITY, "$options": "i"}}).to_list(length=None))
        if all_characters:
            selected_character = random.choice(all_characters)
        else:
            selected_character = None
    else:
        selected_character = None

    if not selected_character:
        # Fetch all characters from MongoDB
        all_characters = list(await collection.find({"rarity": {"$in": [k for k, v in RARITY_WEIGHTS.items() if v[1]]}}).to_list(length=None))

        if not all_characters:
            await context.bot.send_message(chat_id, "No characters found with allowed rarities in the database.")
            return

        # Filter characters with valid rarity
        available_characters = [
            c for c in all_characters 
            if 'id' in c and c.get('rarity') is not None and RARITY_WEIGHTS.get(c['rarity'], (0, False))[1]
        ]

        if not available_characters:
            await context.bot.send_message(chat_id, "No available characters with the allowed rarities.")
            return

        # Weighted random selection
        cumulative_weights = []
        cumulative_weight = 0
        for character in available_characters:
            cumulative_weight += RARITY_WEIGHTS.get(character.get('rarity'), (1, False))[0]
            cumulative_weights.append(cumulative_weight)

        rand = random.uniform(0, cumulative_weight)
        for i, character in enumerate(available_characters):
            if rand <= cumulative_weights[i]:
                selected_character = character
                break

        if not selected_character:
            selected_character = random.choice(available_characters)

    char_timestamp = time.time()
    last_characters[chat_id] = selected_character
    last_characters[chat_id]['timestamp'] = char_timestamp
    last_characters[chat_id]['ranaway'] = False

    if chat_id in first_correct_guesses:
        del first_correct_guesses[chat_id]

    rarity_name = selected_character.get('rarity', '')
    rarity_emoji = rarity_map2.get(rarity_name, '🟣')

    caption_text = (
        f"{rarity_emoji} <b>ᴛʜᴇ ɢᴀᴛᴇ ᴡᴀꜱ ꜱᴘᴀᴡɴᴇᴅ!!</b>\n"
        f"<b>ᴀᴅᴅ ᴛʜɪꜱ ᴄʜᴀʀᴀᴄᴛᴇʀ ᴛᴏ ʏᴏᴜʀ ᴀʀᴍʏ</b>\n"
        f"<b>ʙʏ ꜱᴇɴᴅɪɴɢ /slice ɴᴀᴍᴇ</b>"
    )

    # Check if the character has a video URL
    if 'vid_url' in selected_character:
        sent_message = await context.bot.send_video(
            chat_id=chat_id,
            video=selected_character['vid_url'],
            caption=caption_text,
            parse_mode='HTML'
        )
    else:
        sent_message = await context.bot.send_photo(
            chat_id=chat_id,
            photo=selected_character['img_url'],
            caption=caption_text,
            parse_mode='HTML'
        )

    # Schedule message deletion and runaway notice after 5 minutes
    asyncio.create_task(expire_character(chat_id, sent_message.message_id, char_timestamp, context))
