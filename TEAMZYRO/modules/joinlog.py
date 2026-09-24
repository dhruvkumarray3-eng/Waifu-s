# ==========================================
# Creator: MrZyro
# Telegram: @MrZyro_dev
# GitHub: https://github.com/MrZyro
# ==========================================

import random
from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import Message
from TEAMZYRO import user_collection, app, BOT_LOGGING
from TEAMZYRO.unit.zyro_emoji import lightning, premium


MINIMUM_GROUP_MEMBERS = 20


async def send_log_message(chat_id: int, message: str):
    """Send a log message to the specified chat."""
    if not chat_id:
        return
    target = int(chat_id) if str(chat_id).lstrip("-").isdigit() else chat_id
    await app.send_message(chat_id=target, text=message, parse_mode=ParseMode.HTML)

@app.on_message(filters.new_chat_members)
async def on_new_chat_members(client: Client, message: Message):
    """Handle new chat members joining the chat."""
    bot_user = await client.get_me()
    
    # Check if the bot is one of the new members
    if bot_user.id in [user.id for user in message.new_chat_members]:
        added_by = message.from_user.mention if message.from_user else "ᴜɴᴋɴᴏᴡɴ ᴜsᴇʀ"
        chat_title = message.chat.title
        chat_id = message.chat.id
        chat_username = f"@{message.chat.username}" if message.chat.username else "ᴩʀɪᴠᴀᴛ"

        log_message = (
            f"{premium(20, '🆕')} <b>#NEWGROUP</b>\n\n"
            f"{premium(21, '📌')} <b>Chat:</b> {chat_title}\n"
            f"{premium(22, '🔗')} <b>Username:</b> {chat_username}\n"
            f"{premium(23, '➕')} <b>Added by:</b> {added_by}"
        )
        
        await send_log_message(BOT_LOGGING, log_message)

        try:
            chat_members_count = await client.get_chat_members_count(chat_id)
        except Exception as error:
            await send_log_message(
                BOT_LOGGING,
                f"{premium(24, '⚠️')} Could not check members for <code>{chat_id}</code>: "
                f"<code>{error}</code>",
            )
            return

        if chat_members_count < MINIMUM_GROUP_MEMBERS:
            leave_message = (
                f"{premium(25, '⚠️')} <b>Waifu Bot left this group.</b>\n\n"
                f"<blockquote>{premium(26, '👥')} <b>Members:</b> {chat_members_count}\n"
                f"{premium(27, '📏')} <b>Minimum required:</b> {MINIMUM_GROUP_MEMBERS}\n"
                f"{premium(28, '📝')} <b>Reason:</b> This group has fewer than "
                f"{MINIMUM_GROUP_MEMBERS} members.</blockquote>\n\n"
                f"{lightning(1)} Please add at least {MINIMUM_GROUP_MEMBERS} members "
                "before adding me again."
            )
            try:
                # Send the explanation before leaving, while the bot can still post.
                await client.send_message(
                    chat_id=chat_id,
                    text=leave_message,
                    parse_mode=ParseMode.HTML,
                )
            except Exception as error:
                print(f"[joinlog] could not send small-group explanation: {error}")

            await client.leave_chat(chat_id)
            await send_log_message(
                BOT_LOGGING,
                f"{premium(29, '🚪')} <b>#LEFTGROUP</b>\n\n"
                f"{premium(0, '📌')} <b>Chat:</b> {chat_title}\n"
                f"{premium(1, '👥')} <b>Members:</b> {chat_members_count}\n"
                f"{premium(2, '📝')} <b>Reason:</b> Fewer than {MINIMUM_GROUP_MEMBERS} members.",
            )

@app.on_message(filters.left_chat_member)
async def on_left_chat_member(_, message: Message):
    """Handle the bot leaving the chat."""
    bot_user = await app.get_me()
    
    # Check if the bot is the one that left
    if bot_user.id == message.left_chat_member.id:
        removed_by = message.from_user.mention if message.from_user else "ᴜɴᴋɴᴏᴡɴ ᴜsᴇʀ"
        chat_title = message.chat.title
        chat_id = message.chat.id
        chat_username = f"@{message.chat.username}" if message.chat.username else "ᴘʀɪᴠᴀᴛᴇ ᴄʜᴀᴛ"

        # Construct the log message
        log_message = (
            f"#leftgroup \n\n"
            f"chat name : {chat_title}\n"
            f"chat username : {chat_username}\n"
            f"remove by : {removed_by}\n"
        )
        
        await send_log_message(BOT_LOGGING, log_message)
