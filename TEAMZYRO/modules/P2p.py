# ==========================================
# P2P Marketplace Module
# ==========================================

import uuid
from datetime import datetime
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ParseMode
from TEAMZYRO import (
    app, user_collection, collection,
    P2P_CHANNEL, OWNER_ID
)

# Mongo collection for active listings
p2p_collection = user_collection.database["p2p_listings"]   # or db["p2p_listings"]


# ---------- helpers ----------
async def get_user_character(user_id: int, char_id: str):
    user = await user_collection.find_one({"id": user_id})
    if not user or "characters" not in user:
        return None, None
    for char in user["characters"]:
        if str(char.get("id")) == str(char_id):
            return user, char
    return user, None


def format_listing_caption(listing, char):
    return (
        f"🛒 <b>P2P Listing</b>\n\n"
        f"👤 Seller: <a href='tg://user?id={listing['seller_id']}'>{listing.get('seller_name', 'User')}</a>\n"
        f"🆔 ID: <code>{char['id']}</code>\n"
        f"📛 Name: <b>{char['name']}</b>\n"
        f"📺 Anime: {char['anime']}\n"
        f"💎 Rarity: {char['rarity']}\n"
        f"💰 Price: <b>{listing['price']}</b> coins\n"
        f"📅 Listed: {listing['created_at'].strftime('%Y-%m-%d %H:%M')}"
    )


# ---------- /sell character_id coins ----------
@app.on_message(filters.command("sell") & filters.private)
async def sell_character(client, message):
    if not P2P_CHANNEL:
        return await message.reply("❌ P2P channel not configured.")

    args = message.command
    if len(args) != 3:
        return await message.reply(
            "Usage:\n`/sell <character_id> <price>`\n\nExample:\n`/sell 05 5000`",
            parse_mode=ParseMode.MARKDOWN
        )

    char_id = args[1]
    try:
        price = int(args[2])
        if price < 1:
            raise ValueError
    except ValueError:
        return await message.reply("❌ Price must be a positive number.")

    user_id = message.from_user.id
    user, char = await get_user_character(user_id, char_id)

    if not char:
        return await message.reply(f"❌ You don't own character `{char_id}`.", parse_mode=ParseMode.MARKDOWN)

    # Check if already listed
    existing = await p2p_collection.find_one({
        "seller_id": user_id,
        "char_id": str(char_id),
        "status": "active"
    })
    if existing:
        return await message.reply("❌ This character is already listed. Use /unsell first.")

    listing_id = str(uuid.uuid4())[:8]

    # Post to P2P channel
    caption = format_listing_caption(
        {
            "seller_id": user_id,
            "seller_name": message.from_user.first_name,
            "price": price,
            "created_at": datetime.utcnow()
        },
        char
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🛒 Buy Now", callback_data=f"p2p_buy_{listing_id}")]
    ])

    media_url = char.get("vid_url") or char.get("img_url")
    try:
        if char.get("vid_url"):
            msg = await client.send_video(
                chat_id=int(P2P_CHANNEL),
                video=char["vid_url"],
                caption=caption,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML
            )
        else:
            msg = await client.send_photo(
                chat_id=int(P2P_CHANNEL),
                photo=char.get("img_url"),
                caption=caption,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML
            )
    except Exception as e:
        return await message.reply(f"❌ Failed to post in P2P channel: {e}")

    # Save listing
    await p2p_collection.insert_one({
        "listing_id": listing_id,
        "seller_id": user_id,
        "seller_name": message.from_user.first_name,
        "char_id": str(char_id),
        "character": char,          # full snapshot
        "price": price,
        "status": "active",         # active / sold / cancelled
        "channel_message_id": msg.id,
        "created_at": datetime.utcnow()
    })

    await message.reply(
        f"✅ Character `{char_id}` listed for **{price}** coins!\n"
        f"Listing ID: `{listing_id}`",
        parse_mode=ParseMode.MARKDOWN
    )


# ---------- /unsell character_id ----------
@app.on_message(filters.command("unsell") & filters.private)
async def unsell_character(client, message):
    if len(message.command) != 2:
        return await message.reply("Usage: `/unsell <character_id>`", parse_mode=ParseMode.MARKDOWN)

    char_id = message.command[1]
    user_id = message.from_user.id

    listing = await p2p_collection.find_one({
        "seller_id": user_id,
        "char_id": str(char_id),
        "status": "active"
    })

    if not listing:
        return await message.reply("❌ No active listing found for this character.")

    # Delete message from channel
    try:
        await client.delete_messages(int(P2P_CHANNEL), listing["channel_message_id"])
    except Exception:
        pass

    await p2p_collection.update_one(
        {"_id": listing["_id"]},
        {"$set": {"status": "cancelled"}}
    )

    await message.reply(f"✅ Listing for character `{char_id}` removed.", parse_mode=ParseMode.MARKDOWN)


# ---------- Buy button callback ----------
@app.on_callback_query(filters.regex(r"^p2p_buy_"))
async def p2p_buy_callback(client, callback_query):
    listing_id = callback_query.data.split("_")[-1]
    buyer_id = callback_query.from_user.id

    listing = await p2p_collection.find_one({"listing_id": listing_id, "status": "active"})
    if not listing:
        return await callback_query.answer("❌ This listing is no longer available.", show_alert=True)

    if buyer_id == listing["seller_id"]:
        return await callback_query.answer("❌ You can't buy your own listing.", show_alert=True)

    buyer = await user_collection.find_one({"id": buyer_id})
    if not buyer:
        return await callback_query.answer("❌ You are not registered.", show_alert=True)

    price = listing["price"]
    if buyer.get("balance", 0) < price:
        return await callback_query.answer("❌ Not enough coins!", show_alert=True)

    seller = await user_collection.find_one({"id": listing["seller_id"]})
    if not seller:
        return await callback_query.answer("❌ Seller not found.", show_alert=True)

    # Double-check seller still owns the character
    seller_has_char = any(str(c.get("id")) == str(listing["char_id"]) for c in seller.get("characters", []))
    if not seller_has_char:
        await p2p_collection.update_one({"_id": listing["_id"]}, {"$set": {"status": "cancelled"}})
        try:
            await callback_query.message.delete()
        except Exception:
            pass
        return await callback_query.answer("❌ Seller no longer owns this character.", show_alert=True)

    char = listing["character"]

    # Transfer character + coins
    # 1. Remove from seller
    await user_collection.update_one(
        {"id": listing["seller_id"]},
        {
            "$pull": {"characters": {"id": listing["char_id"]}},
            "$inc": {"balance": price}
        }
    )
    # 2. Add to buyer + deduct coins
    await user_collection.update_one(
        {"id": buyer_id},
        {
            "$push": {"characters": char},
            "$inc": {"balance": -price}
        }
    )

    # Mark sold
    await p2p_collection.update_one(
        {"_id": listing["_id"]},
        {"$set": {"status": "sold", "buyer_id": buyer_id, "sold_at": datetime.utcnow()}}
    )

    # Update / delete channel message
    try:
        await callback_query.message.edit_caption(
            caption=callback_query.message.caption + "\n\n✅ <b>SOLD</b>",
            reply_markup=None,
            parse_mode=ParseMode.HTML
        )
    except Exception:
        try:
            await callback_query.message.delete()
        except Exception:
            pass

    await callback_query.answer("✅ Purchase successful!", show_alert=True)

    # DM seller
    try:
        await client.send_message(
            listing["seller_id"],
            f"🎉 Your character was sold!\n\n"
            f"🆔 ID: `{listing['char_id']}`\n"
            f"📛 {char['name']}\n"
            f"💰 Received: **{price}** coins\n"
            f"👤 Buyer: {callback_query.from_user.mention}",
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception:
        pass

    # DM buyer confirmation
    try:
        await client.send_message(
            buyer_id,
            f"✅ You bought **{char['name']}** (`{listing['char_id']}`) for **{price}** coins!",
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception:
        pass


# ---------- /notsold  (show only active listings) ----------
@app.on_message(filters.command("notsold"))
async def notsold_list(client, message):
    active = await p2p_collection.find({"status": "active"}).sort("created_at", -1).to_list(30)

    if not active:
        return await message.reply("📭 No active P2P listings right now.")

    text = "🛒 <b>Active P2P Listings</b> (not sold)\n\n"
    for i, l in enumerate(active, 1):
        c = l["character"]
        text += (
            f"{i}. <code>{c['id']}</code> | {c['name']} | {c['rarity']}\n"
            f"   💰 {l['price']} coins | Seller: {l.get('seller_name', 'User')}\n\n"
        )

    text += "\nGo to the P2P channel to buy with the button."
    await message.reply(text, parse_mode=ParseMode.HTML)
