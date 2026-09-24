# ==========================================
# Creator: - 𝐀 𝐑 𝚺 𝐒 ( 𝐆 𝛐 𝐃 𝛐 𝐅 𝐖 𝚫 𝐑 ) !!
# Telegram: @Sexypremiums
# GitHub: https://github.com/dhruvkumarray3-eng
# ==========================================

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Telegram API credentials
api_id = os.getenv("API_ID", "")
api_hash = os.getenv("API_HASH", "")

# Bot Token
TOKEN = os.getenv("TOKEN", "")

# Logging & Logs Channel
BOT_LOGGING = os.getenv("BOT_LOGGING", "")
DATABASE_ID = os.getenv("DATABASE_ID", "")
FORCE_JOIN = os.getenv("FORCE_JOIN", "")
P2P_CHANNEL = os.getenv("P2P_CHANNEL", "")   # e.g. -1004337222126
# Database configuration
mongo_url = os.getenv("MONGO_URL", "")
backup_mongo_url = os.getenv("BACKUP_MONGO_URL", "")
DB_NAME = os.getenv("DB_NAME", "WAIFUBOT")

# Channels & Chats
SUPPORT_CHAT = os.getenv("SUPPORT_CHAT", "")
UPDATE_CHAT = os.getenv("UPDATE_CHAT", "")
MUSJ_JOIN = os.getenv("MUSJ_JOIN", "")

# Admin user configurations
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

# ImgBB API Key
IMGBB_API_KEY = os.getenv("IMGBB_API_KEY", "")

# Media Configurations
START_MEDIA = [
    os.getenv("START_MEDIA_1", "https://files.catbox.moe/5zrb1a.mp4"),
    os.getenv("START_MEDIA_1","https://files.catbox.moe/5zrb1a.mp4")
]

PHOTO_URL = [
    os.getenv("PHOTO_URL_1", "https://i.ibb.co/v6H9qNn7/file-0000000099dc71f5a902afba055b1567.png"),
    os.getenv("PHOTO_URL_2", "https://i.ibb.co/v6H9qNn7/file-0000000099dc71f5a902afba055b1567.png")
]

STATS_IMG = [
    os.getenv("STATS_IMG", "https://files.catbox.moe/gknnju.jpg")
]

