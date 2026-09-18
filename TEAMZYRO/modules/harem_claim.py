# ==========================================
# Creator: MrZyro
# Telegram: @MrZyro_dev
# GitHub: https://github.com/MrZyro
# ==========================================

import asyncio
from pyrogram import Client, filters, types as t
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta
from TEAMZYRO import ZYRO as bot
from TEAMZYRO import user_collection, collection, user_nguess_progress, user_guess_progress, FORCE_JOIN as chat, FORCE_JOIN_LINK

claim_lock = {}

# Helper function to format time remaining until next claim
async def format_time_delta(delta):
    seconds = delta.total_seconds()
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{int(hours)}h {int(minutes)}m {int(seconds)}s" if hours or minutes or seconds else "0s"

# Fetch unique characters not yet claimed by the user (or sample from target rarities if all claimed)
async def get_unique_characters(user_id, target_rarities=['🔵 Common', '🟣 Uncommon', '🔴 Medium', '🟠 Rare', '🟡 Legendary']):
    try:
        user_data = await user_collection.find_one({'id': user_id}, {'characters.id': 1})
        claimed_ids = [char['id'] for char in user_data.get('characters', [])] if user_data else []

        # Try unclaimed characters of target rarities first
        pipeline = [
            {'$match': {'rarity': {'$in': target_rarities}, 'id': {'$nin': claimed_ids}}},
            {'$sample': {'size': 1}}
        ]
        cursor = collection.aggregate(pipeline)
        characters = await cursor.to_list(length=None)
        
        if not characters:
            # Fallback to any character of target rarities
            pipeline = [
                {'$match': {'rarity': {'$in': target_rarities}}},
                {'$sample': {'size': 1}}
            ]
            cursor = collection.aggregate(pipeline)
            characters = await cursor.to_list(length=None)
            
        if not characters:
            # General fallback to any character in DB
            pipeline = [{'$sample': {'size': 1}}]
            cursor = collection.aggregate(pipeline)
            characters = await cursor.to_list(length=None)

        return characters if characters else []
    except Exception as e:
        print(f"Error retrieving unique characters: {e}")
        return []

# Command handler for the daily claim (mclaim)
@bot.on_message(filters.command(["hclaim", "claim"]))
async def mclaim(_, message: t.Message):
    user_id = message.from_user.id
    mention = message.from_user.mention

    # Prevent multiple claims at the same time
    if user_id in claim_lock:
        await message.reply_text("Your claim request is already being processed. Please wait.")
        return

    claim_lock[user_id] = True
    try:
        # Fetch user data or create a new user if not found
        user_data = await user_collection.find_one({'id': user_id})
        if not user_data:
            user_data = {
                'id': user_id,
                'username': message.from_user.username,
                'characters': [],
                'last_daily_reward': None
            }
            await user_collection.insert_one(user_data)

        # Check if the user has already claimed within 24 hours
        last_claimed_date = user_data.get('last_daily_reward')
        if last_claimed_date:
            now = datetime.utcnow()
            elapsed = now - last_claimed_date
            if elapsed < timedelta(hours=24):
                remaining_time = timedelta(hours=24) - elapsed
                formatted_time = await format_time_delta(remaining_time)
                return await message.reply_text(f"⏳ **You've already claimed today! Next reward in:** `{formatted_time}`")

        # Fetch a unique character for the user
        unique_characters = await get_unique_characters(user_id)
        if not unique_characters:
            return await message.reply_text("🚫 *No characters available to claim at the moment. Please try again later.*")

        # Update user data with the new character and claim time
        await user_collection.update_one(
            {'id': user_id},
            {'$push': {'characters': {'$each': unique_characters}}, '$set': {'last_daily_reward': datetime.utcnow()}}
        )

        # Send the character's image and info
        for character in unique_characters:
            event = character.get('event') or character.get('type')
            caption_lines = [
                f"🎊 ℂ𝕆ℕ𝔾ℝ𝔸𝕋𝕌𝕃𝔸𝕋𝕀𝕆ℕ𝕊 {mention}! 🎉",
                f"🌸 𝐍𝐚𝐦𝐞 : {character['name']}",
                f"🌈 𝐑𝐚𝐫𝐢𝐭𝐲 : {character['rarity']}",
                f"⛩️ 𝐀𝐧𝐢𝐦𝐞 : {character['anime']}",
            ]
            if event:
                caption_lines.append(f"🎪 𝐄𝐯𝐞𝐧𝐭 : {event}")
            caption_lines.append("💫 ℭ𝔬𝔪𝔢 𝔟𝔞𝔠𝔨 𝔱𝔬𝔪𝔬𝔯𝔯𝔬𝔴 𝔣𝔬𝔯 𝔞𝔫𝔬𝔱𝔥𝔢𝔯 𝔠𝔩𝔞𝔦𝔪!")

            await message.reply_photo(
                photo=character['img_url'],
                caption="\n".join(caption_lines)
            )

    except Exception as e:
        print(f"Error in mclaim command: {e}")
        await message.reply_text("❌ *An unexpected error occurred.*")

    finally:
        # Remove the user from claim lock to allow future claims
        claim_lock.pop(user_id, None)
