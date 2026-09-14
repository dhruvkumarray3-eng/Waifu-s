# ==========================================
# Creator: MrZyro
# start.py – always replies on /start
# ==========================================

import os
import random
import time
from pyrogram import filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from TEAMZYRO import *
from TEAMZYRO.unit.zyro_help import HELP_DATA

SUPPORT_CHAT = os.getenv("SUPPORT_CHAT", "https://t.me/+cYkP7lDW0uY4MzVl")
UPDATE_CHAT = os.getenv("UPDATE_CHAT", "")
OWNER_URL = "https://t.me/powerstar_frogie"

START_TIME = time.time()


def get_uptime():
    s = int(time.time() - START_TIME)
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    return f"{h}h {m}m {sec}s"


def format_url(url: str):
    if not url:
        return None
    url = str(url).strip()
    if url.replace("-", "").isdigit():
        return None
    if url.startswith("@"):
        url = f"https://t.me/{url[1:]}"
    elif url.startswith("t.me/"):
        url = "https://" + url
    elif not url.startswith("http://") and not url.startswith("https://"):
        if " " in url or "/" in url:
            return None
        url = f"https://t.me/{url}"
    if "None" in url or " " in url:
        return None
    if not (url.startswith("https://") or url.startswith("http://")):
        return None
    return url


async def generate_start_message(client, message):
    bot_user = await client.get_me()
    bot_name = bot_user.first_name or "Bot"
    bot_username = bot_user.username

    try:
        ping = round(time.time() - message.date.timestamp(), 2)
    except Exception:
        ping = 0.0
    uptime = get_uptime()

    caption = (
        f"🦋 <b>Ara ara\~ Welcome to the Butterfly Mansion!</b> 🌸\n\n"
        f"<i>I am {bot_name}. It seems you've wandered straight into my laboratory. "
        f"Don't worry, the fresh wisteria fragrance will keep you safe from any nasty demons here.</i>\n\n"
        f"<blockquote>━━━━━━━▧▣▧━━━━━━━\n"
        f"⦾ <b>MISSION:</b> I track down roaming Slayers and trap wandering Demons in your chats.\n"
        f"⦾ <b>TRAINING:</b> Add me to your group and use /help to read my custom training manuals.\n"
        f"━━━━━━━▧▣▧━━━━━━━\n"
        f"⚡ <b>PULSE:</b> {ping} ms\n"
        f"⏳ <b>REST ZONE:</b> {uptime}</blockquote>"
    )

    buttons = []

    if bot_username:
        buttons.append([
            InlineKeyboardButton(
                "🦋 Deploy To Your Squad",
                url=f"https://t.me/{bot_username}?startgroup=true",
            )
        ])

    social = []
    support_url = format_url(SUPPORT_CHAT)
    if support_url:
        social.append(InlineKeyboardButton("💜 Support Mansion", url=support_url))
    update_url = format_url(UPDATE_CHAT)
    if update_url:
        social.append(InlineKeyboardButton("📢 Laboratory", url=update_url))
    if social:
        buttons.append(social)

    buttons.append([InlineKeyboardButton("🧪 Training Manual", callback_data="open_help")])

    owner_url = format_url(OWNER_URL)
    if owner_url:
        buttons.append([InlineKeyboardButton("Owner", url=owner_url)])

    return caption, buttons


async def generate_group_start_message(client):
    bot_user = await client.get_me()
    bot_name = bot_user.first_name or "Bot"
    bot_username = bot_user.username

    caption = (
        f"🦋 <i>Flap, flap... I am</i> <b>{bot_name}</b> 🌸\n\n"
        f"<blockquote>I am currently monitoring this chat area to detect and expose "
        f"hidden demons through message flows.\n\n"
        f"Use /help to access my specialized medical and combat manuals!</blockquote>"
    )

    buttons = []
    if bot_username:
        row = [
            InlineKeyboardButton(
                "🦋 Summon Me",
                url=f"https://t.me/{bot_username}?startgroup=true",
            )
        ]
        support_url = format_url(SUPPORT_CHAT)
        if support_url:
            row.append(InlineKeyboardButton("💜 Support", url=support_url))
        buttons.append(row)
    else:
        support_url = format_url(SUPPORT_CHAT)
        if support_url:
            buttons.append([InlineKeyboardButton("💜 Support", url=support_url)])

    return caption, buttons


async def send_media_message(message, media, caption, buttons):
    markup = InlineKeyboardMarkup(buttons) if buttons else None
    media = (media or "").strip()

    try:
        if media.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
            await message.reply_photo(
                photo=media,
                caption=caption,
                reply_markup=markup,
                parse_mode=enums.ParseMode.HTML,
            )
        elif media.lower().endswith(".gif"):
            await message.reply_animation(
                animation=media,
                caption=caption,
                reply_markup=markup,
                parse_mode=enums.ParseMode.HTML,
            )
        elif media:
            await message.reply_video(
                video=media,
                caption=caption,
                reply_markup=markup,
                parse_mode=enums.ParseMode.HTML,
            )
        else:
            await message.reply_text(
                caption,
                reply_markup=markup,
                parse_mode=enums.ParseMode.HTML,
            )
    except Exception as e:
        print(f"[start] media/button error: {e}")
        try:
            await message.reply_text(
                caption,
                reply_markup=markup,
                parse_mode=enums.ParseMode.HTML,
            )
        except Exception as e2:
            print(f"[start] text+buttons failed: {e2}")
            await message.reply_text(
                "🦋 Welcome! Bot is online.\nUse /help for commands."
            )


@app.on_message(filters.command("start") & filters.private, group=0)
async def start_private_command(client, message):
    # Always reply something first
    try:
        wait = await message.reply_text("🦋 Loading...")
    except Exception as e:
        print(f"[start] cannot reply at all: {e}")
        return

    try:
        existing_user = await user_collection.find_one({"id": message.from_user.id})
        if not existing_user:
            await user_collection.insert_one({
                "id": message.from_user.id,
                "username": message.from_user.username,
                "first_name": message.from_user.first_name,
                "last_name": message.from_user.last_name,
                "start_time": time.time(),
            })
    except Exception as e:
        print(f"[start] db: {e}")

    try:
        caption, buttons = await generate_start_message(client, message)
    except Exception as e:
        print(f"[start] generate: {e}")
        try:
            await wait.edit_text("🦋 Welcome! Bot is online.\nUse /help")
        except Exception:
            await message.reply_text("🦋 Welcome! Bot is online.\nUse /help")
        return

    try:
        media = random.choice(START_MEDIA) if START_MEDIA else ""
    except Exception as e:
        print(f"[start] media pick: {e}")
        media = ""

    # Delete loading, then send real start
    try:
        await wait.delete()
    except Exception:
        pass

    try:
        await send_media_message(message, media, caption, buttons)
    except Exception as e:
        print(f"[start] send_media: {e}")
        try:
            await message.reply_text(
                caption,
                reply_markup=InlineKeyboardMarkup(buttons) if buttons else None,
                parse_mode=enums.ParseMode.HTML,
            )
        except Exception as e2:
            print(f"[start] text fail: {e2}")
            await message.reply_text("🦋 Welcome! Use /help")

    # Optional log (history.py also logs — fine if both run)
    if BOT_LOGGING:
        try:
            await app.send_message(
                chat_id=BOT_LOGGING,
                text=(
                    f"{message.from_user.mention} just started the bot.\n\n"
                    f"<b>User ID:</b> <code>{message.from_user.id}</code>\n"
                    f"<b>Username:</b> @{message.from_user.username}"
                ),
            )
        except Exception as e:
            print(f"Failed to send start log: {e}")


@app.on_message(filters.command("start") & filters.group, group=0)
async def start_group_command(client, message):
    try:
        caption, buttons = await generate_group_start_message(client)
        try:
            media = random.choice(START_MEDIA) if START_MEDIA else ""
        except Exception:
            media = ""
        await send_media_message(message, media, caption, buttons)
    except Exception as e:
        print(f"[start group] fail: {e}")
        try:
            await message.reply_text("🦋 Bot is online. Use /help")
        except Exception:
            pass


def find_help_modules():
    buttons = []
    for module_name, module_data in HELP_DATA.items():
        button_name = module_data.get("HELP_NAME", "Unknown")
        buttons.append(
            InlineKeyboardButton(button_name, callback_data=f"help_{module_name}")
        )
    return [buttons[i : i + 3] for i in range(0, len(buttons), 3)]


@app.on_callback_query(filters.regex("^open_help$"))
async def show_help_menu(client, query: CallbackQuery):
    buttons = find_help_modules()
    buttons.append(
        [InlineKeyboardButton("⬅️ Return to Mansion", callback_data="back_to_home")]
    )
    text = (
        "⚙️ <b>🦋 BUTTERFLY MANSION HELP MENU</b>\n\n"
        "<blockquote>Select a target directory below.\n"
        "Commands use the prefix: /</blockquote>"
    )
    try:
        await query.message.edit_caption(
            caption=text,
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode=enums.ParseMode.HTML,
        )
    except Exception:
        try:
            await query.message.edit_text(
                text=text,
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=enums.ParseMode.HTML,
            )
        except Exception:
            await query.answer("Could not open help.", show_alert=True)


@app.on_callback_query(filters.regex(r"^help_(.+)"))
async def show_help(client, query: CallbackQuery):
    module_name = query.data.split("_", 1)[1]
    module_data = HELP_DATA.get(module_name, {})
    help_text = module_data.get("HELP", "No help for this module.")
    buttons = [[InlineKeyboardButton("⬅️ Back to Laboratory", callback_data="open_help")]]
    full_text = f"🧪 <b>{module_name.upper()} Clinical Records:</b>\n\n{help_text}"
    try:
        await query.message.edit_caption(
            caption=full_text,
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode=enums.ParseMode.HTML,
        )
    except Exception:
        try:
            await query.message.edit_text(
                text=full_text,
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=enums.ParseMode.HTML,
            )
        except Exception:
            await query.answer("Could not load help.", show_alert=True)


@app.on_callback_query(filters.regex("^back_to_home$"))
async def back_to_home(client, query: CallbackQuery):
    try:
        caption, buttons = await generate_start_message(client, query.message)
        markup = InlineKeyboardMarkup(buttons) if buttons else None
        try:
            await query.message.edit_caption(
                caption=caption,
                reply_markup=markup,
                parse_mode=enums.ParseMode.HTML,
            )
        except Exception:
            await query.message.edit_text(
                text=caption,
                reply_markup=markup,
                parse_mode=enums.ParseMode.HTML,
            )
    except Exception as e:
        await query.answer(str(e)[:100], show_alert=True)
