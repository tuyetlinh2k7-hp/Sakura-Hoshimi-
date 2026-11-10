import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN", "")
PREFIX = os.getenv("PREFIX", "s!")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID", "0"))

admin_roles_raw = os.getenv("ADMIN_ROLE_IDS", "")
ADMIN_ROLE_IDS = [int(x.strip()) for x in admin_roles_raw.split(",") if x.strip().isdigit()]

ZALO_PHONE = os.getenv("ZALO_PHONE", "")
OWNER_DISCORD_TAG = os.getenv("OWNER_DISCORD_TAG", "")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
XKIRO_API_KEY = os.getenv("XKIRO_API_KEY", "")
AI_MODEL = os.getenv("AI_MODEL", "sensenova/sensenova-6.8-flash-lite")

LAVALINK_HOST = os.getenv("LAVALINK_HOST", "127.0.0.1")
LAVALINK_PORT = int(os.getenv("LAVALINK_PORT", "2334"))
LAVALINK_PASSWORD = os.getenv("LAVALINK_PASSWORD", "youshallnotpass")

music_tokens_raw = os.getenv("MUSIC_TOKENS", "")
MUSIC_TOKENS = [t.strip() for t in music_tokens_raw.split(",") if t.strip()]

tokens_raw = os.getenv("TOKENS", "")
TOKENS = [t.strip() for t in tokens_raw.split(",") if t.strip()]

WEB_PORT = int(os.getenv("WEB_PORT", "10272"))
WEB_BASE_URL = os.getenv("WEB_BASE_URL", "http://localhost:10272")
WEB_PASSWORD = os.getenv("WEB_PASSWORD", "")

DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID", "")
DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET", "")
DISCORD_REDIRECT_URI = os.getenv("DISCORD_REDIRECT_URI", "")

PKMC_API_KEY = os.getenv("PKMC_API_KEY", "")
FALIX_API_KEY = os.getenv("FALIX_API_KEY", "")

TOKEN_DIEM_DANH = os.getenv("TOKEN_DIEM_DANH", "")
MAP_DIEM_DANH_ID = int(os.getenv("MAP_DIEM_DANH_ID", "0"))

TOPGG_TOKEN = os.getenv("TOPGG_TOKEN", "")
TOPGG_WEBHOOK_AUTH = os.getenv("TOPGG_WEBHOOK_AUTH", "")
