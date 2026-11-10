from pathlib import Path
import os
import json
import discord
from discord.ext import commands

BASE_DIR = Path(__file__).parent.parent
MC_ADMINS_FILE = BASE_DIR / "data" / "mc_admins.json" # Thêm file cho MC Admin
MC_WHITELIST_FILE = BASE_DIR / "data" / "mc_whitelist.json" # Thêm file cho MC Whitelist

mc_admin_ids = set() 

# --- Thêm logic load MC Admin ---
if os.path.exists(MC_ADMINS_FILE):
    with open(
        MC_ADMINS_FILE,
        "r",
        encoding="utf-8"
    ) as f:
        try:
            mc_admin_ids = set(json.load(f))
        except json.JSONDecodeError:
            mc_admin_ids = set()
else:
    mc_admin_ids = set()

mc_whitelist = set()

# --- Thêm logic load MC Whitelist ---
if os.path.exists(MC_WHITELIST_FILE):
    with open(
        MC_WHITELIST_FILE,
        "r",
        encoding="utf-8"
    ) as f:
        try:
            mc_whitelist = set(json.load(f))
        except json.JSONDecodeError:
            mc_whitelist = set()

def save_mc_admins():
    """Lưu danh sách MC Admin vào file."""
    os.makedirs(os.path.dirname(MC_ADMINS_FILE), exist_ok=True)
    with open(
        MC_ADMINS_FILE,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            list(mc_admin_ids),
            f,
            indent=4
        )

def save_mc_whitelist():
    """Lưu danh sách MC Whitelist vào file."""
    os.makedirs(os.path.dirname(MC_WHITELIST_FILE), exist_ok=True)
    with open(
        MC_WHITELIST_FILE,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            list(mc_whitelist),
            f,
            indent=4
        )
#hàm kiểm tra admin
def is_mc_admin():
    """
    Check tùy chỉnh để xác thực người dùng là Owner chính hoặc MC Admin.
    """
    async def predicate(ctx: commands.Context) -> bool:
        # Owner chính luôn có quyền
        if await ctx.bot.is_owner(ctx.author):
            return True
        # Kiểm tra xem có phải MC Admin không
        if ctx.author.id in mc_admin_ids:
            return True
        
        # Nếu không phải cả hai, từ chối
        embed = discord.Embed(
            title="⛔ Truy Cập Bị Từ Chối",
            description="Bạn không có đủ quyền hạn (Owner/MC Admin) để sử dụng lệnh này.",
            color=discord.Color.red()
        )
        # Phân biệt giữa lệnh prefix và slash để gửi phản hồi
        if ctx.interaction:
            await ctx.interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await ctx.send(embed=embed)
        return False

    return commands.check(predicate)