# ==========================================
# history.py  –  Bot stats, cgrant, join/leave/start logs
# ==========================================

import time
from datetime import datetime
from pyrogram import filters
from pyrogram.types import Message
from pyrogram.enums import ParseMode, ChatMemberStatus

from TEAMZYRO import (
    app, db, user_collection, collection,
    group_user_totals_collection, OWNER_ID, BOT_LOGGING, require_power
)

sudo_users = db["sudo_users"]
START_TIME = time.time()


# ---------- helpers ----------
async def is_sudo_or_owner(user_id: int) -> bool:
    if user_id == OWNER_ID:
        return True
    doc = await sudo_users.find_one({"_id": user_id})
    return bool(doc)


async def send_log(text: str):
    if not BOT_LOGGING:
        return
    try:
        await app.send_message(int(BOT_LOGGING) if str(BOT_LOGGING).lstrip("-").isdigit() else BOT_LOGGING, text)
    except Exception as e:
        print(f"[history] log failed: {e}")


def get_uptime() -> str:
    s = int(time.time() - START_TIME)
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    d, h = divmod(h, 24)
    if d:
        return f"{d}d {h}h {m}m {sec}s"
    return f"{h}h {m}m {sec}s"


# =========================================================
# /data  –  Bot statistics (Owner + Sudo only)
# =========================================================
@app.on_message(filters.command(["data", "botdata", "botstats"]))
async def bot_data_cmd(client, message: Message):
    if not await is_sudo_or_owner(message.from_user.id):
        return await message.reply("⚠️ Only **Owner / Sudo** can use this command.")

    status = await message.reply("📊 Collecting statistics...")

    try:
        total_users = await user_collection.count_documents({})
        total_chars_db = await collection.count_documents({})  # master character pool

        # Total characters owned by all users (sum of lengths)
        pipeline = [
            {"$project": {"count": {"$size": {"$ifNull": ["$characters", []]}}}},
            {"$group": {"_id": None, "total": {"$sum": "$count"}}}
        ]
        owned_agg = await user_collection.aggregate(pipeline).to_list(1)
        total_owned = owned_agg[0]["total"] if owned_agg else 0

        # Groups where bot is tracked
        total_groups = await group_user_totals_collection.count_documents({})

        # Users with at least 1 character
        users_with_chars = await user_collection.count_documents(
            {"characters.0": {"$exists": True}}
        )

        # Total balance in economy
        bal_agg = await user_collection.aggregate([
            {"$group": {"_id": None, "total": {"$sum": {"$ifNull": ["$balance", 0]}}}}
        ]).to_list(1)
        total_balance = bal_agg[0]["total"] if bal_agg else 0

        # Sudo count
        sudo_count = await sudo_users.count_documents({})

        text = (
            f"📊 <b>BOT STATISTICS</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"👥 <b>Total Users:</b> <code>{total_users}</code>\n"
            f"🎭 <b>Users with chars:</b> <code>{users_with_chars}</code>\n"
            f"📁 <b>Tracked Groups:</b> <code>{total_groups}</code>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🃏 <b>Characters in DB:</b> <code>{total_chars_db}</code>\n"
            f"📦 <b>Total owned (all users):</b> <code>{total_owned}</code>\n"
            f"💰 <b>Total coins in economy:</b> <code>{total_balance}</code>\n"
            f"🛠 <b>Sudo users:</b> <code>{sudo_count}</code>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"⏱ <b>Uptime:</b> <code>{get_uptime()}</code>\n"
            f"📅 <b>Generated:</b> <code>{datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}</code>"
        )
        await status.edit_text(text, parse_mode=ParseMode.HTML)
    except Exception as e:
        await status.edit_text(f"❌ Error while collecting stats:\n<code>{e}</code>", parse_mode=ParseMode.HTML)


# =========================================================
# /cgrant  –  Owner gifts any character to a user
# Usage:
#   Reply:  /cgrant <character_id>
#   Or:     /cgrant <user_id> <character_id>
# =========================================================
@app.on_message(filters.command(["cgrant", "grantchar"]))
async def cgrant_cmd(client, message: Message):
    if message.from_user.id != OWNER_ID:
        return await message.reply("⚠️ Only the **bot owner** can use /cgrant.")

    args = message.command
    target_id = None
    char_id = None

    if message.reply_to_message and message.reply_to_message.from_user:
        target_id = message.reply_to_message.from_user.id
        if len(args) != 2:
            return await message.reply(
                "Usage (reply):\n`/cgrant <character_id>`\n\nExample:\n`/cgrant 05`",
                parse_mode=ParseMode.MARKDOWN
            )
        char_id = args[1]
    else:
        if len(args) != 3:
            return await message.reply(
                "Usage:\n`/cgrant <user_id> <character_id>`\n"
                "Or reply to a user:\n`/cgrant <character_id>`",
                parse_mode=ParseMode.MARKDOWN
            )
        try:
            target_id = int(args[1])
        except ValueError:
            return await message.reply("❌ Invalid user ID.")
        char_id = args[2]

    # Find character in master DB
    char = await collection.find_one({"id": str(char_id)})
    if not char:
        # try without zero-pad / with zero-pad
        char = await collection.find_one({"id": char_id.zfill(2)})
    if not char:
        return await message.reply(f"❌ Character `{char_id}` not found in database.", parse_mode=ParseMode.MARKDOWN)

    # Ensure user exists
    user = await user_collection.find_one({"id": target_id})
    if not user:
        # create minimal user doc
        await user_collection.insert_one({
            "id": target_id,
            "characters": [],
            "balance": 0
        })

    # Push character (full copy, keep original fields)
    char_copy = {k: v for k, v in char.items() if k != "_id"}
    await user_collection.update_one(
        {"id": target_id},
        {"$push": {"characters": char_copy}}
    )

    name = char.get("name", "Unknown")
    rarity = char.get("rarity", "?")
    anime = char.get("anime", "?")

    await message.reply(
        f"✅ Granted character to user!\n\n"
        f"👤 User: <code>{target_id}</code>\n"
        f"🆔 ID: <code>{char.get('id')}</code>\n"
        f"📛 Name: <b>{name}</b>\n"
        f"📺 Anime: {anime}\n"
        f"💎 Rarity: {rarity}",
        parse_mode=ParseMode.HTML
    )

    # Notify user in DM
    try:
        await client.send_message(
            target_id,
            f"🎁 You received a character from the owner!\n\n"
            f"🆔 <code>{char.get('id')}</code>\n"
            f"📛 <b>{name}</b>\n"
            f"📺 {anime}\n"
            f"💎 {rarity}",
            parse_mode=ParseMode.HTML
        )
    except Exception:
        pass

    await send_log(
        f"#cgrant\n\n"
        f"Owner granted character `{char.get('id')}` ({name}) to user `{target_id}`."
    )


# =========================================================
# LOGS: Group join / leave / bot start
# =========================================================
@app.on_message(filters.new_chat_members)
async def history_new_members(client, message: Message):
    me = await client.get_me()
    if me.id not in [u.id for u in message.new_chat_members]:
        return

    added_by = message.from_user.mention if message.from_user else "Unknown"
    title = message.chat.title or "Unknown"
    username = f"@{message.chat.username}" if message.chat.username else "Private"
    chat_id = message.chat.id

    try:
        members = await client.get_chat_members_count(chat_id)
    except Exception:
        members = "?"

    text = (
        f"#NEWGROUP\n\n"
        f"📌 <b>Chat:</b> {title}\n"
        f"🔗 <b>Username:</b> {username}\n"
        f"🆔 <b>Chat ID:</b> <code>{chat_id}</code>\n"
        f"👥 <b>Members:</b> {members}\n"
        f"➕ <b>Added by:</b> {added_by}"
    )
    await send_log(text)

    # Optional: track group in DB
    await group_user_totals_collection.update_one(
        {"group_id": str(chat_id)},
        {"$set": {"title": title, "username": message.chat.username, "joined_at": datetime.utcnow()}},
        upsert=True
    )


@app.on_message(filters.left_chat_member)
async def history_left_member(client, message: Message):
    me = await client.get_me()
    if not message.left_chat_member or message.left_chat_member.id != me.id:
        return

    removed_by = message.from_user.mention if message.from_user else "Unknown"
    title = message.chat.title or "Unknown"
    username = f"@{message.chat.username}" if message.chat.username else "Private"
    chat_id = message.chat.id

    text = (
        f"#LEFTGROUP\n\n"
        f"📌 <b>Chat:</b> {title}\n"
        f"🔗 <b>Username:</b> {username}\n"
        f"🆔 <b>Chat ID:</b> <code>{chat_id}</code>\n"
        f"➖ <b>Removed by:</b> {removed_by}"
    )
    await send_log(text)


@app.on_message(filters.command("start") & filters.private)
async def history_start_log(client, message: Message):
    """Extra start log (start.py already has one – this is a clean detailed version)."""
    u = message.from_user
    text = (
        f"#START\n\n"
        f"👤 <b>User:</b> {u.mention}\n"
        f"🆔 <b>ID:</b> <code>{u.id}</code>\n"
        f"🔗 <b>Username:</b> @{u.username if u.username else 'none'}\n"
        f"📅 <b>Time:</b> {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}"
    )
    await send_log(text)
