import json
import os
from pathlib import Path
import discord
from discord.ext import commands
from discord import app_commands

from config import OWNER_ID

BASE_DIR = Path(__file__).resolve().parent.parent
ADMIN_ROLES_FILE = BASE_DIR / "data" / "admin_roles.json"
admin_roles: dict[str, list[int]] = {}


def load_admin_roles():
    """Tải danh sách vai trò admin từ file JSON (giữ nguyên tham chiếu vùng nhớ)."""
    if ADMIN_ROLES_FILE.exists():
        try:
            with open(ADMIN_ROLES_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    admin_roles.clear()
                    admin_roles.update(data)
        except (json.JSONDecodeError, OSError):
            pass


def save_admin_roles():
    """Lưu danh sách vai trò admin vào file JSON."""
    ADMIN_ROLES_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(ADMIN_ROLES_FILE, "w", encoding="utf-8") as f:
        json.dump(admin_roles, f, indent=4, ensure_ascii=False)


load_admin_roles()



def _check_is_admin(user: discord.Member | discord.User, guild: discord.Guild | None) -> bool:
    if user.id == OWNER_ID:
        return True
    if guild is None or not isinstance(user, discord.Member):
        return False
    if user.guild_permissions.administrator:
        return True

    guild_admin_roles = admin_roles.get(str(guild.id), [])
    user_role_ids = {role.id for role in user.roles}
    return any(int(role_id) in user_role_ids for role_id in guild_admin_roles)


def is_owner():
    """Check decorator kiểm tra người dùng có phải là Owner của bot không (Hỗ trợ cả Prefix & Slash)."""
    def predicate_ctx(ctx: commands.Context) -> bool:
        return ctx.author.id == OWNER_ID

    def predicate_inter(interaction: discord.Interaction) -> bool:
        return interaction.user.id == OWNER_ID

    def decorator(func):
        func = commands.check(predicate_ctx)(func)
        func = app_commands.check(predicate_inter)(func)
        return func

    return decorator


def has_admin_role():
    """
    Check decorator kiểm tra người dùng có vai trò Admin hoặc là Owner.
    Hoạt động mượt mà trên cả Prefix Command, Slash Command và Hybrid Command.
    """
    def predicate_ctx(ctx: commands.Context) -> bool:
        return _check_is_admin(ctx.author, ctx.guild)

    def predicate_inter(interaction: discord.Interaction) -> bool:
        return _check_is_admin(interaction.user, interaction.guild)

    def decorator(func):
        func = commands.check(predicate_ctx)(func)
        func = app_commands.check(predicate_inter)(func)
        return func

    return decorator
