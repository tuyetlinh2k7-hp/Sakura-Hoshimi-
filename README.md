<div align="center">

# 🌸 SakuraBot - Modern Multipurpose Discord Bot & Web Dashboard

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![discord.py](https://img.shields.io/badge/discord.py-2.7.1%2B-5865F2.svg?logo=discord&logoColor=white)](https://github.com/Rapptz/discord.py)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Lavalink](https://img.shields.io/badge/Audio-Lavalink%20v4-red.svg)](https://github.com/lavalink-devs/Lavalink)
[![AI Powered](https://img.shields.io/badge/AI-Gemini%20%7C%20OpenAI%20%7C%20Groq-orange.svg)](https://ai.google.dev/)

**SakuraBot** is a powerful, production-ready open-source Discord bot built with Python. It features a sleek real-time **Web Dashboard**, multi-worker music streaming, an immersive anime **Waifu Gacha & Economy** ecosystem, multi-provider **AI Chatbots**, remote **Minecraft Server Management**, and enterprise-grade server security modules.

[✨ Features](#-key-features) • [📁 Structure](#-project-structure) • [🚀 Quick Start](#-quick-start--installation) • [⚙️ Configuration](#️-environment-variables-env) • [📖 Command Reference](#-command-reference) • [🤝 Contributing](#-contributing--license)

---

</div>

## ✨ Key Features

### 🛡️ 1. Comprehensive Server Security & Auto-Moderation
- **Unified Anti-Exploit**: All-in-one server protection against raids, server nuking, chat floods, unauthorized invite links, and phishing URLs.
- **Intelligent AutoMod**: Real-time profanity and blacklist filters, spam pattern recognition, and anti-toxicity moderation.
- **Detailed Audit & Logging**: Tracks message edits/deletions, voice channel events, member join/leave, server boosts, audit logs, and automatic emoji reactions.

### 🎵 2. Multi-Worker Music Streaming (Wavelink & Lavalink v4)
- High-fidelity 24/7 audio playback powered by **Lavalink v4** and **Wavelink**.
- **Multi-Token Worker Architecture**: Distribute audio playback across a pool of secondary music bots, allowing multiple voice channels to stream independently without lag.

### 🤖 3. Multi-Provider AI Assistant (LLM Integration)
- Supports top-tier AI providers: **Google Gemini**, **Groq (LLaMA 3)**, and **OpenAI GPT**.
- Dedicated AI conversation channels with context memory.
- Contextual **AI Tarot Card Readings** and **Zodiac Horoscope** interpretations.

### 🎮 4. Minigames & Full-Featured Economy System
- **Waifu Gacha System**: Collect, level up, and trade hundreds of anime & gaming characters with transparent drop rates.
- **Realistic Banking & Market**: Savings accounts with customizable terms and interest, loans, P2P player market, jobs (`work`), mining (`mining`), and fishing (`fishing`).
- **Social Gameplay**: Marriage system (`marriage`), Jail sentence system (`jail`), Daily streak rewards (`streaks`), and unlockable achievements.
- **Entertaining Minigames**: Word Chain game (900,000+ words dictionary), Tic-Tac-Toe / Gomoku (XO), Trivia (Who Wants to Be a Millionaire), and Casino games (Dice, Blackjack).

### 🌐 5. Modern Web Dashboard
- Secure login using **Discord OAuth2**.
- Automatically scopes servers based on the logged-in user's Administrator privileges.
- Live resource monitoring (CPU, RAM, Uptime) with a live terminal console stream.
- Web-based bot file manager and remote configuration editor.

### ⛏️ 6. Minecraft Integration & Gaming Services
- Remote Minecraft server monitoring and console controls (integrated with Falixnodes API).
- Secure Discord-to-Minecraft player account verification system.
- Automated daily HoYoLab check-in for Genshin Impact, Honkai: Star Rail, and Zenless Zone Zero.

---

## 📁 Project Structure

```plaintext
SakuraBot/
├── Anti/                 # Defense modules: anti-raid, anti-nuke, anti-spam, link filters
├── Check/                # Helper utilities, permissions, prefix handlers, and decorators
├── Command/              # Discord command cogs (music, economy, gacha, games, admin, etc.)
├── Database/             # SQLite connection class and database schema initializers
├── Logs_vi/              # Event logging and audit tracking cogs
├── data/                 # Dictionaries, game assets, template configs, and database scripts
├── languages/            # Multi-language localization files (vi, en, ja, cn)
├── view/                 # Interactive Discord UI Components (Buttons, Selects, Modals)
├── web/                  # Web Dashboard (FastAPI/aiohttp backend, HTML templates, CSS/JS)
├── scripts/              # Helper and maintenance scripts
├── config.py             # Centralized environment variable loader
├── .env.example          # Sample environment variables template
├── .gitignore            # Git exclusion rules for secrets, databases, and temporary files
├── requirements.txt      # Python dependencies list
└── run.py                # Main bot startup entrypoint
```

---

## 🚀 Quick Start & Installation

### Prerequisites
- **Python**: Version `3.10` or higher (Recommended: 3.11 or 3.12).
- **Git**: Installed on your system.
- **Java**: Version `17` or higher (only required if self-hosting a Lavalink server).

### Step 1: Clone the repository
```bash
git clone https://github.com/<your-username>/Sakura-Hoshimi-.git
cd Sakura-Hoshimi-
```

### Step 2: Create a virtual environment & install dependencies
```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment:
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install all required dependencies
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables
Copy the sample `.env.example` file to `.env`:
```bash
# On Windows CMD/PowerShell:
copy .env.example .env
# On Linux/macOS:
cp .env.example .env
```
Open `.env` in your preferred editor (VSCode, Notepad, Nano) and provide your configuration:
- `DISCORD_TOKEN`: Your bot token from the [Discord Developer Portal](https://discord.com/developers/applications).
- `PREFIX`: Default bot command prefix (e.g. `s!`).
- `OWNER_ID`: Your Discord User ID.
- `GEMINI_API_KEY` / `OPENAI_API_KEY`: API keys for AI chat and Tarot readings.
- `LAVALINK_HOST`, `LAVALINK_PASSWORD`: Connection details for your Lavalink audio server.

### Step 4: Run the Bot
```bash
python run.py
```
> [!TIP]
> Once the bot connects successfully, the Web Dashboard will be available at `http://localhost:10272` (or the port defined in your `.env`).

---

## ⚙️ Environment Variables (.env)

| Variable | Required | Description |
| :--- | :---: | :--- |
| `DISCORD_TOKEN` | **Yes** | Primary Discord bot token from Developer Portal. |
| `PREFIX` | No | Command prefix for text commands (Default: `s!`). |
| `OWNER_ID` | **Yes** | Discord User ID of the bot owner for privileged commands. |
| `GEMINI_API_KEY` | No | Google Gemini API Key (available free at Google AI Studio). |
| `GROQ_API_KEY` | No | Groq Cloud API Key for ultra-fast LLaMA inference. |
| `OPENAI_API_KEY` | No | OpenAI API Key for GPT-4o / GPT-3.5 models. |
| `LAVALINK_HOST` | No | Lavalink server host IP (Default: `127.0.0.1`). |
| `LAVALINK_PORT` | No | Lavalink server port (Default: `2334`). |
| `LAVALINK_PASSWORD` | No | Lavalink server authentication password. |
| `WEB_PORT` | No | Web Dashboard listening port (Default: `10272`). |
| `DISCORD_CLIENT_ID` | No | Application Client ID for Discord OAuth2 web login. |
| `DISCORD_CLIENT_SECRET` | No | Application Client Secret for Discord OAuth2 web login. |

---

## 📖 Command Reference

Here are some of the most commonly used commands (assuming the default prefix `s!`):

| Command | Category | Description |
| :--- | :--- | :--- |
| `s!help` | General | Displays the interactive help menu and full command list. |
| `s!ping` | General | Checks bot latency and Discord gateway ping. |
| `s!play <song name / URL>` | Music | Plays music from YouTube, Spotify, or SoundCloud via Lavalink. |
| `s!stop` / `s!skip` / `s!queue` | Music | Controls audio playback, skips tracks, or views the queue. |
| `s!gacha` | Games | Opens the Waifu Gacha interactive anime banner menu. |
| `s!bank` | Economy | Manages personal bank accounts, savings terms, and loans. |
| `s!work` | Economy | Complete daily shifts to earn in-game currency. |
| `s!fish` / `s!mine` | Economy | Fish in waters or mine caves for valuable resources. |
| `s!anti` | Moderation | Configures server defense and anti-exploit rules (Admin only). |
| `s!setlog` | Moderation | Sets up designated log channels for various server events. |
| `s!ai <prompt>` | AI | Direct conversation with the multilingual AI assistant. |
| `s!tarot` | AI / Fun | Draws a Tarot card with AI-generated spiritual interpretation. |

---

## 🔒 Security & Best Practices

> [!WARNING]
> - **Never commit your `.env` file**: It contains sensitive credentials. The `.gitignore` is configured by default to ignore `.env` and `cookies.txt`.
> - **Database Privacy**: Production SQLite databases (`*.db`) and user data are intentionally omitted from public release. Upon initial startup, the bot creates fresh databases automatically.

---

## 🤝 Contributing & License

- Please read [CONTRIBUTING.md](CONTRIBUTING.md) before submitting feature proposals or Pull Requests.
- This project is open-source software licensed under the **MIT License**. See [LICENSE](LICENSE) for details.

---

<div align="center">
  <sub>Crafted with passion for the global Discord developer community 🌸</sub>
</div>
