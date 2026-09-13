# ==========================================
# Creator: MrZyro
# Telegram: @MrZyro_dev
# GitHub: https://github.com/MrZyro
# ==========================================

from TEAMZYRO import *
from TEAMZYRO import application
from html import escape
import asyncio
import time
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from pyrogram import enums
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

@app.on_message(filters.command(["guess", "protecc", "collect", "grab", "hunt","catch","slice","hug","cute","take"]))
async def guess(client: Client, message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    today = datetime.utcnow().date()

    if await check_cooldown(user_id):
        remaining_time = await get_remaining_cooldown(user_id)
        await message.reply_text(
            f"🦋 <i>Ara ara~ You are moving a bit too fast! Please wait {remaining_time} seconds before using another command.</i>",
            parse_mode=enums.ParseMode.HTML
        )
        return

    if 'name' not in last_characters.get(chat_id, {}):
        await message.reply_text("🦋 <i>Ara ara? There are no active targets tracked in this sector right now.</i>", parse_mode=enums.ParseMode.HTML)
        return
    
    if chat_id not in last_characters:
        await message.reply_text("🦋 <i>Ara ara? There are no active targets tracked in this sector right now.</i>", parse_mode=enums.ParseMode.HTML)
        return

    if chat_id in first_correct_guesses:
        await message.reply_text("🦋 <i>Too late~ This soul has already been safely guided away!</i>", parse_mode=enums.ParseMode.HTML)
        return

    if last_characters[chat_id].get('ranaway', False):
        await message.reply_text("🦋 <i>Oh dear, the target detected our poison incense and fled into the dark!</i>", parse_mode=enums.ParseMode.HTML)
        return 

    guess = ' '.join(message.command[1:]).lower() if len(message.command) > 1 else ''
    
    if "()" in guess or "&" in guess.lower():
        await message.reply_text("🦋 <i>Fufufu~ You shouldn't try using those strange characters in your response!❌</i>", parse_mode=enums.ParseMode.HTML)
        return

    name_parts = last_characters[chat_id]['name'].lower().split()
    
    if sorted(name_parts) == sorted(guess.split()) or any(part == guess for part in name_parts):
        first_correct_guesses[chat_id] = user_id
        for task in asyncio.all_tasks():
            if task.get_name() == f"expire_session_{chat_id}":
                task.cancel()
                break

        timestamp = last_characters[chat_id].get('timestamp')
        if timestamp:
            time_taken = time.time() - timestamp
            time_taken_str = f"{int(time_taken)} seconds"
        else:
            time_taken_str = "Unknown time"

        if user_id not in user_guess_progress or user_guess_progress[user_id]["date"] != today:
            user_guess_progress[user_id] = {"date": today, "count": 0}

        user_guess_progress[user_id]["count"] += 1
        
        # Fetch user from MongoDB
        user = await user_collection.find_one({'id': user_id})
        if user:
            update_fields = {}
            if message.from_user.username != user.get('username'):
                update_fields['username'] = message.from_user.username
            if message.from_user.first_name != user.get('first_name'):
                update_fields['first_name'] = message.from_user.first_name
            if update_fields:
                await user_collection.update_one({'id': user_id}, {'$set': update_fields})
            
            await user_collection.update_one({'id': user_id}, {'$push': {'characters': last_characters[chat_id]}})
      
        else:
            await user_collection.insert_one({
                'id': user_id,
                'username': message.from_user.username,
                'first_name': message.from_user.first_name,
                'characters': [last_characters[chat_id]],
            })

        # Update group count in top_global_groups_collection (new code)
        if message.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
            group_name = message.chat.title or f"Group_{chat_id}"
            await top_global_groups_collection.update_one(
                {'chat_id': chat_id},
                {
                    '$set': {'group_name': group_name},
                    '$inc': {'count': 1}
                },
                upsert=True
            )

        await react_to_message(chat_id, message.id)

        # Fetch user to update balance
        user = await user_collection.find_one({'id': user_id})
        if user:
            current_balance = user.get('balance', 0)
            new_balance = current_balance + 40
            await user_collection.update_one({'id': user_id}, {'$set': {'balance': new_balance}})
        else:
            new_balance = 40
            await user_collection.insert_one({
                'id': user_id,
                'username': message.from_user.username,
                'first_name': message.from_user.first_name,
                'characters': [last_characters[chat_id]],
                'balance': 40
            })

        keyboard = [[InlineKeyboardButton("🦋 View Butterfly Garden", switch_inline_query_current_chat=f"collection.{user_id}")]]
        await message.reply_text(
            f'🦋 <b>My, my! What an absolutely exquisite execution~</b> 🌸\n'
            f'Congratulations <b><a href="tg://user?id={user_id}">{escape(message.from_user.first_name)}</a></b>, you successfully subdued a target! 🎉\n\n'
            f'<blockquote>📛 <b>𝖭𝖠𝖬𝖤:</b> {last_characters[chat_id]["name"]}\n'
            f'🌈 <b>𝖠𝖭𝖨𝖬𝖤:</b> {last_characters[chat_id]["anime"]}\n'
            f'✨ <b>𝖱𝖠𝖱𝖨𝖳𝖸:</b> {last_characters[chat_id]["rarity"]}\n\n'
            f'⏱️ <b>𝖡𝖱𝖤𝖠𝖳𝖧𝖨𝖭𝖦 𝖳𝖨𝖬𝖤:</b> {time_taken_str}\n'
            f'💰 <b>𝖤𝖠𝖱𝖭𝖤earned:</b> +40 Wisteria Coins 💴\n'
            f'💳 <b>𝖳𝖮𝖳𝖠𝖫 𝖡𝖠𝖫𝖠𝖭𝖢𝖤:</b> {new_balance} Coins\n\n'
            f'This character has been guided straight into your personal Corps Ledger. Use /harem to look through your garden.</blockquote>',
            parse_mode=enums.ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        message_id = last_characters[chat_id].get('message_id')
        incorrect_text = (
            "🦋 <b>𝖤𝖷𝖤𝖢𝖴𝖳𝖨𝖮𝖭 𝖥𝖠𝖨𝖫𝖤𝖣</b> 🧪\n\n"
            "<blockquote>Fufufu~ That answer is incorrect. Take a closer look before swinging your blade again!</blockquote>"
        )
        if message_id:
            keyboard = [
                [InlineKeyboardButton("🔍 Scout Media Again", url=f"https://t.me/c/{str(chat_id)[4:]}/{message_id}")],
            ]
            await message.reply_text(
                incorrect_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=enums.ParseMode.HTML
            )
        else:
            await message.reply_text(
                incorrect_text,
                parse_mode=enums.ParseMode.HTML
            )
