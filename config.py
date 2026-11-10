import os
from dotenv import load_dotenv

# Load environment variables from .env file if available
load_dotenv()

# ==============================================================================
# PRIMARY DISCORD BOT CONFIGURATION
# ==============================================================================
# Main Discord bot token
TOKEN = os.getenv("DISCORD_TOKEN", "")

# Default command prefix (e.g. "s!")
PREFIX = os.getenv("PREFIX", "s!")

# Primary bot owner's Discord User ID (full administrator access)
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

# Channel ID for system logs and exception notifications (0 = disabled)
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID", "0"))

# Role IDs with administrator privileges across servers (parsed from comma-separated string)
admin_roles_raw = os.getenv("ADMIN_ROLE_IDS", "")
ADMIN_ROLE_IDS = [int(x.strip()) for x in admin_roles_raw.split(",") if x.strip().isdigit()]

# Owner contact information displayed on support and help pages
ZALO_PHONE = os.getenv("ZALO_PHONE", "")
OWNER_DISCORD_TAG = os.getenv("OWNER_DISCORD_TAG", "")

# ==============================================================================
# ARTIFICIAL INTELLIGENCE & LLM PROVIDERS
# ==============================================================================
# API keys for AI chat, tarot interpretations, and conversational features
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
XKIRO_API_KEY = os.getenv("XKIRO_API_KEY", "")

# Default AI model identifier
AI_MODEL = os.getenv("AI_MODEL", "sensenova/sensenova-6.8-flash-lite")

# ==============================================================================
# AUDIO & LAVALINK STREAMING CONFIGURATION
# ==============================================================================
# Lavalink v4 audio server connection details
LAVALINK_HOST = os.getenv("LAVALINK_HOST", "127.0.0.1")
LAVALINK_PORT = int(os.getenv("LAVALINK_PORT", "2334"))
LAVALINK_PASSWORD = os.getenv("LAVALINK_PASSWORD", "youshallnotpass")

# Secondary worker bot tokens for multi-channel concurrent music playback
music_tokens_raw = os.getenv("MUSIC_TOKENS", "")
MUSIC_TOKENS = [t.strip() for t in music_tokens_raw.split(",") if t.strip()]

tokens_raw = os.getenv("TOKENS", "")
TOKENS = [t.strip() for t in tokens_raw.split(",") if t.strip()]

# ==============================================================================
# WEB DASHBOARD & DISCORD OAUTH2 LOGIN
# ==============================================================================
# Port for the web dashboard server
WEB_PORT = int(os.getenv("WEB_PORT", "10272"))

# Base URL for web dashboard routing and OAuth callbacks
WEB_BASE_URL = os.getenv("WEB_BASE_URL", "http://localhost:10272")

# Optional fallback dashboard access password
WEB_PASSWORD = os.getenv("WEB_PASSWORD", "")

# Discord OAuth2 credentials for web dashboard user authentication
DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID", "")
DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET", "")
DISCORD_REDIRECT_URI = os.getenv("DISCORD_REDIRECT_URI", "")

# ==============================================================================
# MINECRAFT INTEGRATION & EXTERNAL SERVICES (OPTIONAL)
# ==============================================================================
# API key for Pterodactyl-managed Minecraft servers
PKMC_API_KEY = os.getenv("PKMC_API_KEY", "")

# API key for Falixnodes Minecraft hosting control
FALIX_API_KEY = os.getenv("FALIX_API_KEY", "")

# Auxiliary bot token and channel ID for attendance check-in systems
TOKEN_DIEM_DANH = os.getenv("TOKEN_DIEM_DANH", "")
MAP_DIEM_DANH_ID = int(os.getenv("MAP_DIEM_DANH_ID", "0"))

# ==============================================================================
# TOP.GG BOT LISTING & WEBHOOK (OPTIONAL)
# ==============================================================================
# Top.gg API Token for querying remote upvotes
TOPGG_TOKEN = os.getenv("TOPGG_TOKEN", "")

# Webhook authorization header for instant vote processing
TOPGG_WEBHOOK_AUTH = os.getenv("TOPGG_WEBHOOK_AUTH", "")
