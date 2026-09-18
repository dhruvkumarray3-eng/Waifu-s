# ==========================================
# Creator: MrZyro
# Telegram: @MrZyro_dev
# GitHub: https://github.com/MrZyro
# ==========================================

# TEAMZYRO/commands/rarity.py
from TEAMZYRO import app, collection, user_collection, rarity_map
from pyrogram import filters, enums

def to_small_caps(text: str) -> str:
    small_caps_map = {
        'a': 'ᴀ', 'b': 'ʙ', 'c': 'ᴄ', 'd': 'ᴅ', 'e': 'ᴇ', 'f': 'ғ', 'g': 'ɢ',
        'h': 'ʜ', 'i': 'ɪ', 'j': 'ᴊ', 'k': 'ᴋ', 'l': 'ʟ', 'm': 'ᴍ', 'n': 'ɴ',
        'o': 'ᴏ', 'p': 'ᴘ', 'q': 'ǫ', 'r': 'ʀ', 's': 's', 't': 'ᴛ', 'u': 'ᴜ',
        'v': 'ᴠ', 'w': 'ᴡ', 'x': 'x', 'y': 'ʏ', 'z': 'ᴢ'
    }
    return "".join(small_caps_map.get(c.lower(), c) for c in text)

def make_progress_bar(current: int, total: int, length: int = 10) -> str:
    if total <= 0:
        return "░" * length
    percent = min(1.0, current / total)
    filled = int(round(percent * length))
    return "█" * filled + "░" * (length - filled)

@app.on_message(filters.command(["rarity", "raritychart"]))
async def rarity_count(client, message):
    try:
        user_id = message.from_user.id
        
        # Get user's claimed characters
        user_db = await user_collection.find_one({"id": user_id})
        user_chars = user_db.get("characters", []) if user_db else []
        
        # Count user's characters per rarity
        user_counts = {}
        for c in user_chars:
            r = c.get("rarity")
            if r:
                user_counts[r] = user_counts.get(r, 0) + 1

        rarity_list = list(rarity_map.values())
        
        total_db_all = 0
        total_user_all = 0
        
        lines = [
            "ᴀʀɪsᴇ ʏᴏᴜʀ ᴄʜᴀʀᴀᴄᴛᴇʀ:",
            "📊 **Rarity Chart**"
        ]
        
        for rarity in rarity_list:
            total_db = await collection.count_documents({"rarity": rarity})
            if total_db == 0:
                continue
                
            user_has = user_counts.get(rarity, 0)
            total_db_all += total_db
            total_user_all += min(user_has, total_db)
            
            percent = (user_has / total_db * 100) if total_db > 0 else 0.0
            p_bar = make_progress_bar(user_has, total_db)
            
            parts = rarity.split(" ", 1)
            emoji = parts[0]
            name = parts[1] if len(parts) > 1 else rarity
            small_name = to_small_caps(name)
            
            lines.append(f"{emoji} {small_name}")
            lines.append(f"      {p_bar} {user_has}/{total_db} ({percent:.0f}%)")
        
        overall_percent = (total_user_all / total_db_all * 100) if total_db_all > 0 else 0.0
        lines.append(f"\n📈 **Overall Progress:**")
        lines.append(f"   {total_user_all}/{total_db_all} ({overall_percent:.1f}%)")
        
        response_text = "\n".join(lines)
        await message.reply_text(response_text, parse_mode=enums.ParseMode.MARKDOWN)
        
    except Exception as e:
        await message.reply_text(f"⚠️ Error loading rarity chart: {str(e)}")
