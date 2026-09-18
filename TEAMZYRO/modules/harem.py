# ==========================================
# Creator: MrZyro
# Telegram: @MrZyro_dev
# GitHub: https://github.com/MrZyro
# ==========================================

from TEAMZYRO import *
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto, CallbackQuery, Message
from pyrogram.errors import ChatAdminRequired, UserNotParticipant, ChatWriteForbidden
from itertools import groupby
import math
from html import escape
import random
from pyrogram import enums
import asyncio
import os  # For environment variables

# 🔴 FIX: Ensure SUPPORT_CHANNEL is treated as an integer if it's a numeric ID
SUPPORT_CHANNEL = int(MUSJ_JOIN) if str(MUSJ_JOIN).lstrip('-').isdigit() else MUSJ_JOIN

async def check_support_channel(client: Client, user_id: int) -> bool:
    # Handle the 'x' owner variable safely if it exists
    if 'x' in globals() and user_id == x:
        return True
        
    try:
        member = await client.get_chat_member(SUPPORT_CHANNEL, user_id)
        # 🔴 FIX: Explicitly allow Owners, Admins, and Members to pass
        if member.status in [enums.ChatMemberStatus.OWNER, enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.MEMBER]:
            return True
        return False
    except UserNotParticipant:
        return False
    except ChatAdminRequired:
        print(f"Bot needs admin privileges in {SUPPORT_CHANNEL} to check membership.")
        return False
    except Exception as e:
        print(f"Error checking support channel membership: {e}")
        return False

# 🔴 FIX: New Helper Function to generate beautiful barrier messages dynamically
async def send_barrier_message(client: Client, event):
    try:
        # Fetch the chat dynamically to get its real title and invite link
        chat = await client.get_chat(SUPPORT_CHANNEL)
        chat_name = chat.title
        if chat.username:
            invite_link = f"https://t.me/{chat.username}"
        else:
            # If private, get or generate the invite link
            invite_link = chat.invite_link or await client.export_chat_invite_link(SUPPORT_CHANNEL)
    except Exception:
        chat_name = "our Support Channel"
        invite_link = SUPPORT_CHAT if 'SUPPORT_CHAT' in globals() else "https://t.me"

    keyboard = [[InlineKeyboardButton("🦋 Join Wisteria Domain", url=invite_link)]]
    text = (
        f"🦋 <b>𝖶𝖨𝖲𝖳𝖤𝖱𝖨𝖠 𝖡𝖠𝖱𝖱𝖨𝖤𝖱</b>\n\n"
        f"<blockquote>Ara ara~ To access your collection records, you must first pass through <b>{chat_name}</b>! Please join below.</blockquote>"
    )
    
    if isinstance(event, Message):
        await event.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=enums.ParseMode.HTML)
    else:
        # It's a CallbackQuery
        await event.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=enums.ParseMode.HTML)


async def fetch_user_characters(user_id):
    user = await user_collection.find_one({"id": user_id})
    if not user or 'characters' not in user:
        return None, '🦋 <i>Ara ara~ You have not collected any souls in your Butterfly Garden yet! Use commands like /guess to subdue them.</i>'
    characters = [c for c in user['characters'] if 'id' in c]
    if not characters:
        return None, '🦋 <i>Ara ara? I could not find any valid records inside your personal Corps Ledger.</i>'
    return characters, None

@app.on_message(filters.command(["harem", "collection"]))
async def harem_handler(client: Client, message: Message):
    user_id = message.from_user.id

    # Check if the user is in the support channel
    if not await check_support_channel(client, user_id):
        await send_barrier_message(client, message)
        return

    # Proceed with existing logic if user is in the channel
    page = 0
    user = await user_collection.find_one({"id": user_id})
    filter_type = user.get('filter_type', None) if user else None
    filter_value = user.get('filter_value', None) if user else None
    filter_rarity = user.get('filter_rarity', None) if user else None
    
    msg = await display_harem(client, message, user_id, page, filter_type=filter_type, filter_value=filter_value, filter_rarity=filter_rarity, is_initial=True)
    
    # Delete the message after 3 minutes (180 seconds)
    await asyncio.sleep(180)
    try:
        if msg:
            await msg.delete()
    except Exception as e:
        print(f"Error deleting message: {e}")

async def display_harem(client, message, user_id, page, filter_type=None, filter_value=None, filter_rarity=None, is_initial=False, callback_query=None):
    try:
        # Check support channel membership again for callback queries
        if not is_initial and not await check_support_channel(client, user_id):
            await send_barrier_message(client, callback_query)
            return

        characters, error = await fetch_user_characters(user_id)
        if error:
            if is_initial:
                await message.reply_text(error, parse_mode=enums.ParseMode.HTML)
            else:
                await callback_query.message.edit_text(error, parse_mode=enums.ParseMode.HTML)
            return

        # Calculate total and AMV character counts
        total_characters = len(characters)
        amv_characters = len([c for c in characters if 'vid_url' in c])

        # Sort characters by anime and ID
        characters = sorted(characters, key=lambda x: (x.get('anime', ''), x.get('id', '')))

        # Apply filter by type or rarity
        if filter_type == "RARITY" and filter_value:
            characters = [c for c in characters if c.get('rarity') == filter_value]
        elif filter_type == "EVENT" and filter_value:
            val = filter_value.lower()
            characters = [
                c for c in characters 
                if val in (c.get('event') or '').lower() or val in (c.get('type') or '').lower() or val in (c.get('anime') or '').lower() or val in (c.get('rarity') or '').lower()
            ]
        elif filter_rarity:
            characters = [c for c in characters if c.get('rarity') == filter_rarity]

        if not characters:
            keyboard = [
                [InlineKeyboardButton("🦋 Reset Filters", callback_data=f"remove_filter:{user_id}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            no_rarity_text = (
                f"🦋 <b>𝖦𝖠𝖱𝖣𝖤𝖭 𝖨𝖭𝖲𝖯𝖤𝖢𝖳𝖨𝖮𝖭</b>\n\n"
                f"<blockquote>Ara ara! No souls matching your active filter (<b>{filter_value or filter_rarity or 'Filter'}</b>) were found. Use the button below to reset.</blockquote>"
            )
            if is_initial:
                await message.reply_text(no_rarity_text, reply_markup=reply_markup, parse_mode=enums.ParseMode.HTML)
            else:
                await callback_query.message.edit_text(no_rarity_text, reply_markup=reply_markup, parse_mode=enums.ParseMode.HTML)
            return

        # Group characters by ID and count duplicates
        character_counts = {k: len(list(v)) for k, v in groupby(characters, key=lambda x: x['id'])}
        unique_characters = list({character['id']: character for character in characters}.values())
        total_pages = math.ceil(len(unique_characters) / 15)

        # Ensure page is within valid range
        if page < 0 or page >= total_pages:
            page = 0

        # Get user first name
        user_db = await user_collection.find_one({"id": user_id})
        user_first_name = user_db.get("first_name", "User") if user_db else "User"

        # Build harem message
        harem_message = f"🌸 <b>{escape(user_first_name)} 's HAREM</b> (Page {page+1}/{total_pages})\n\n"
        if filter_type or filter_value or filter_rarity:
            active_val = filter_value or filter_rarity
            harem_message += f"🎯 <b>FILTER ({filter_type or 'RARITY'}):</b> {active_val}\n\n"

        harem_message += "<blockquote>"
        # Get characters for the current page
        current_characters = unique_characters[page * 15:(page + 1) * 15]
        current_grouped_characters = {k: list(v) for k, v in groupby(current_characters, key=lambda x: x['anime'])}

        # Add character details to the message
        for anime, chars in current_grouped_characters.items():
            total_anime_chars = await collection.count_documents({"anime": anime})
            harem_message += f'⛩️ <b>{anime}</b> ({len(chars)}/{total_anime_chars})\n'
            for character in chars:
                count = character_counts[character['id']]
                rarity_emoji = rarity_map2.get(character.get('rarity'), '⚪️')
                harem_message += f'  ◈ [ {rarity_emoji} ] {character["id"]} {character["name"]} (x{count})\n'
            harem_message += '\n'
        harem_message = harem_message.rstrip() + "</blockquote>"

        # Add inline buttons for collection and video-only collection with blue/red circles
        keyboard = [
            [
                InlineKeyboardButton(f"🔵 Collection ({total_characters})", switch_inline_query_current_chat=f"collection.{user_id}"),
                InlineKeyboardButton(f"💌 AMV ({amv_characters})", switch_inline_query_current_chat=f"collection.{user_id}.AMV")
            ]
        ]

        if total_pages > 1:
            nav_buttons = []
            if page > 0:
                nav_buttons.append(InlineKeyboardButton("🦋 ⬅️", callback_data=f"harem:{page-1}:{user_id}:{filter_rarity or 'None'}"))
            if page < total_pages - 1:
                nav_buttons.append(InlineKeyboardButton("➡️ 🦋", callback_data=f"harem:{page+1}:{user_id}:{filter_rarity or 'None'}"))
            keyboard.append(nav_buttons)

        reply_markup = InlineKeyboardMarkup(keyboard)

        # Select a random character for the image/video
        image_character = None
        user = await user_collection.find_one({"id": user_id})
        if user and 'favorites' in user and user['favorites']:
            favorite_character_id = user['favorites'][0]
            image_character = next((c for c in characters if c['id'] == favorite_character_id), None)

        if not image_character:
            image_character = random.choice(characters) if characters else None

        # Send or edit the harem message with media
        if is_initial:
            if image_character:
                if 'vid_url' in image_character:
                    return await message.reply_video(
                        video=image_character['vid_url'],
                        caption=harem_message,
                        reply_markup=reply_markup,
                        parse_mode=enums.ParseMode.HTML
                    )
                elif 'img_url' in image_character:
                    return await message.reply_photo(
                        photo=image_character['img_url'],
                        caption=harem_message,
                        reply_markup=reply_markup,
                        parse_mode=enums.ParseMode.HTML
                    )
                else:
                    return await message.reply_text(harem_message, reply_markup=reply_markup, parse_mode=enums.ParseMode.HTML)
            else:
                return await message.reply_text(harem_message, reply_markup=reply_markup, parse_mode=enums.ParseMode.HTML)
        else:
            if image_character:
                if 'vid_url' in image_character:
                    await callback_query.message.edit_media(
                        media=InputMediaPhoto(image_character['vid_url'], caption=harem_message),
                        reply_markup=reply_markup
                    )
                elif 'img_url' in image_character:
                    await callback_query.message.edit_media(
                        media=InputMediaPhoto(image_character['img_url'], caption=harem_message),
                        reply_markup=reply_markup
                    )
                else:
                    await callback_query.message.edit_text(harem_message, reply_markup=reply_markup, parse_mode=enums.ParseMode.HTML)
            else:
                await callback_query.message.edit_text(harem_message, reply_markup=reply_markup, parse_mode=enums.ParseMode.HTML)

    except Exception as e:
        print(f"Error in display_harem: {e}")
        error_msg = "🦋 <i>Ara ara~ The butterflies encountered a brief storm. Please refresh your canvas.</i>"
        if is_initial:
            await message.reply_text(error_msg, parse_mode=enums.ParseMode.HTML)
        else:
            await callback_query.message.edit_text(error_msg, parse_mode=enums.ParseMode.HTML)

@app.on_callback_query(filters.regex(r"^remove_filter"))
async def remove_filter_callback(client: Client, callback_query: CallbackQuery):
    try:
        _, user_id = callback_query.data.split(':')
        user_id = int(user_id)

        if callback_query.from_user.id != user_id:
            await callback_query.answer("🦋 This isn't your Butterfly Garden to touch~", show_alert=True)
            return

        # Check support channel membership
        if not await check_support_channel(client, user_id):
            await send_barrier_message(client, callback_query)
            return

        # Reset the filter to "All" in the database
        await user_collection.update_one({"id": user_id}, {"$set": {"filter_rarity": None}}, upsert=True)

        # Delete the current message
        await callback_query.message.delete()

        # Notify the user that the filter has been removed
        await callback_query.answer("🦋 Filter removed seamlessly. Showing all target rarities!", show_alert=True)
    except Exception as e:
        print(f"Error in remove_filter callback: {e}")

@app.on_callback_query(filters.regex(r"^harem"))
async def harem_callback(client: Client, callback_query: CallbackQuery):
    try:
        data = callback_query.data
        _, page, user_id, filter_rarity = data.split(':')
        page = int(page)
        user_id = int(user_id)
        filter_rarity = None if filter_rarity == 'None' else filter_rarity

        if callback_query.from_user.id != user_id:
            await callback_query.answer("🦋 This isn't your Butterfly Garden to flip through~", show_alert=True)
            return

        await display_harem(client, callback_query.message, user_id, page, filter_rarity, is_initial=False, callback_query=callback_query)
    except Exception as e:
        print(f"Error in harem callback: {e}")

EVENT_TAGS = [
    ("👶 CHIBI", "CHIBI"), ("👑 ROYALTY", "ROYALTY"), ("🧧 CHINESE", "CHINESE"),
    ("🎩 ASSEMBLY", "ASSEMBLY"), ("👘 KIMONO", "KIMONO"), ("🧹 MAID", "MAID"),
    ("🎒 SCHOOL", "SCHOOL"), ("🐰 BUNNY", "BUNNY"), ("👙 BIKINI", "BIKINI"),
    ("🏺 EGYPT", "EGYPT"), ("💍 WEDDING", "WEDDING"), ("🌑 NUN", "NUN"),
    ("🏴‍☠️ PIRATE", "PIRATE"), ("💉 NURSES", "NURSES"), ("🪽 ANGELIC", "ANGELIC"),
    ("🚓 POLICE", "POLICE"), ("🥷 SHINOBI", "SHINOBI"), ("🐾 KITTY", "KITTY"),
    ("🏆 ATHLETIC", "ATHLETIC"), ("🕷 GOTHIC", "GOTHIC"), ("🐲 YAKUZA", "YAKUZA"),
    ("🏹 FIRST NAME", "FIRST NAME"), ("🎃 HALLOWEEN", "HALLOWEEN"), ("🎄 CHRISTMAS", "CHRISTMAS"),
    ("🛡 KNIGHT", "KNIGHT"), ("⛩ SHOGUN", "SHOGUN"), ("🔞 EROTIC", "EROTIC"),
    ("✨ EXOTIC", "EXOTIC")
]

def get_hmode_text(filter_type, filter_value):
    f_type = filter_type.upper() if filter_type else "NONE"
    f_val = filter_value.upper() if filter_value else "NONE"
    return (
        "<b>YOUR CURRENT H-MODE SETTINGS:</b>\n\n"
        f"<blockquote><b>FILTER TYPE: {f_type}</b>\n"
        f"<b>FILTER VALUE: {f_val}</b></blockquote>\n\n"
        "TO CHANGE IT USE THE BUTTONS BELOW."
    )

def get_hmode_main_keyboard(user_id):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("BY RARITY", callback_data=f"hmode_sub:{user_id}:rarity"),
            InlineKeyboardButton("BY TYPES", callback_data=f"hmode_sub:{user_id}:types")
        ],
        [InlineKeyboardButton("DEFAULT", callback_data=f"hmode_set:{user_id}:DEFAULT:NONE")]
    ])

def get_hmode_rarity_keyboard(user_id):
    keyboard = []
    row = []
    for rarity, emoji in rarity_map2.items():
        if "Supreme" in rarity or "🪞" in emoji:
            continue
        row.append(InlineKeyboardButton(f"{emoji} {rarity}", callback_data=f"hmode_set:{user_id}:RARITY:{rarity}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data=f"hmode_main:{user_id}")])
    return InlineKeyboardMarkup(keyboard)

def get_hmode_types_keyboard(user_id):
    keyboard = []
    row = []
    for label, tag in EVENT_TAGS:
        row.append(InlineKeyboardButton(label, callback_data=f"hmode_set:{user_id}:EVENT:{tag}"))
        if len(row) == 3:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data=f"hmode_main:{user_id}")])
    return InlineKeyboardMarkup(keyboard)

@app.on_message(filters.command("hmode"))
async def hmode_handler(client: Client, message: Message):
    user_id = message.from_user.id

    if not await check_support_channel(client, user_id):
        await send_barrier_message(client, message)
        return

    user = await user_collection.find_one({"id": user_id})
    filter_type = user.get('filter_type') if user else None
    filter_value = user.get('filter_value') or user.get('filter_rarity') if user else None

    text = get_hmode_text(filter_type, filter_value)
    markup = get_hmode_main_keyboard(user_id)
    await message.reply_text(text, reply_markup=markup, parse_mode=enums.ParseMode.HTML)

@app.on_callback_query(filters.regex(r"^hmode_main:"))
async def hmode_main_callback(client: Client, callback_query: CallbackQuery):
    try:
        _, user_id = callback_query.data.split(':')
        user_id = int(user_id)

        if callback_query.from_user.id != user_id:
            return await callback_query.answer("🦋 This setting belongs to another user~", show_alert=True)

        user = await user_collection.find_one({"id": user_id})
        filter_type = user.get('filter_type') if user else None
        filter_value = user.get('filter_value') or user.get('filter_rarity') if user else None

        text = get_hmode_text(filter_type, filter_value)
        markup = get_hmode_main_keyboard(user_id)
        await callback_query.message.edit_text(text, reply_markup=markup, parse_mode=enums.ParseMode.HTML)
        await callback_query.answer()
    except Exception as e:
        print(f"Error in hmode_main callback: {e}")

@app.on_callback_query(filters.regex(r"^hmode_sub:"))
async def hmode_sub_callback(client: Client, callback_query: CallbackQuery):
    try:
        _, user_id, menu_type = callback_query.data.split(':')
        user_id = int(user_id)

        if callback_query.from_user.id != user_id:
            return await callback_query.answer("🦋 This setting belongs to another user~", show_alert=True)

        user = await user_collection.find_one({"id": user_id})
        filter_type = user.get('filter_type') if user else None
        filter_value = user.get('filter_value') or user.get('filter_rarity') if user else None
        text = get_hmode_text(filter_type, filter_value)

        if menu_type == "rarity":
            markup = get_hmode_rarity_keyboard(user_id)
        else:
            markup = get_hmode_types_keyboard(user_id)

        await callback_query.message.edit_text(text, reply_markup=markup, parse_mode=enums.ParseMode.HTML)
        await callback_query.answer()
    except Exception as e:
        print(f"Error in hmode_sub callback: {e}")

@app.on_callback_query(filters.regex(r"^hmode_set:"))
async def hmode_set_callback(client: Client, callback_query: CallbackQuery):
    try:
        _, user_id, mode_type, mode_val = callback_query.data.split(':', 3)
        user_id = int(user_id)

        if callback_query.from_user.id != user_id:
            return await callback_query.answer("🦋 This setting belongs to another user~", show_alert=True)

        if mode_type == "DEFAULT":
            new_type = None
            new_val = None
        else:
            new_type = mode_type
            new_val = mode_val

        await user_collection.update_one(
            {"id": user_id},
            {"$set": {
                "filter_type": new_type,
                "filter_value": new_val,
                "filter_rarity": new_val if new_type == "RARITY" else None
            }},
            upsert=True
        )

        text = get_hmode_text(new_type, new_val)
        markup = get_hmode_main_keyboard(user_id)
        await callback_query.message.edit_text(text, reply_markup=markup, parse_mode=enums.ParseMode.HTML)
        await callback_query.answer(f"✅ Filter updated to {new_val if new_val else 'DEFAULT'}", show_alert=True)
    except Exception as e:
        print(f"Error in hmode_set callback: {e}")
