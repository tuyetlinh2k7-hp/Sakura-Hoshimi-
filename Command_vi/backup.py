import discord
from discord.ext import commands, tasks
from discord import app_commands
import json
import os
import asyncio
from datetime import datetime, timezone
from Checks_vi.i18n import t

BACKUP_DIR = "data/backups"
MAX_BACKUPS_PER_GUILD = 15  # Tối đa 15 bản backup gần nhất cho mỗi server


class CreateBackupModal(discord.ui.Modal, title="Tạo bản sao lưu mới"):
    description = discord.ui.TextInput(
        label="Mô tả cho bản sao lưu này",
        placeholder="Ví dụ: Trước khi thay đổi lớn, Cấu trúc ổn định...",
        required=False,
        max_length=100
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)

        cog = interaction.client.get_cog("BackupCog")
        if not cog:
            return await interaction.followup.send(t(interaction.guild, "BACKUP_ERROR_NO_COG"), ephemeral=True)

        try:
            desc_val = self.description.value.strip() or "Không có mô tả"
            backup_file_path = await cog.create_backup(interaction.guild, interaction.user, desc_val)
            embed = discord.Embed(
                title=t(interaction.guild, "BACKUP_SUCCESS_TITLE"),
                description=t(
                    interaction.guild,
                    "BACKUP_SUCCESS_DESC",
                    guild_name=interaction.guild.name,
                    filename=os.path.basename(backup_file_path)
                ),
                color=discord.Color.green()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            await interaction.followup.send(t(interaction.guild, "BACKUP_CREATE_ERROR", error=e), ephemeral=True)


class ConfirmLoadView(discord.ui.View):
    def __init__(self, author_id: int, cog_instance, filename: str):
        super().__init__(timeout=60)
        self.author_id = author_id
        self.cog = cog_instance
        self.filename = filename
        self.sync_mode = False        # Mặc định False (Wipe cũ tạo mới), Bật True (Đồng bộ không xóa kênh cũ)
        self.restore_member_roles = True
        self.create_safety_backup = True

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(t(interaction.guild, "BACKUP_NOT_YOURS"), ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Chế độ Sync (Giữ tin nhắn): TẮT", style=discord.ButtonStyle.secondary, emoji="🔄", row=1)
    async def toggle_sync_mode(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.sync_mode = not self.sync_mode
        button.label = f"Chế độ Sync (Giữ tin nhắn): {'BẬT' if self.sync_mode else 'TẮT'}"
        button.style = discord.ButtonStyle.success if self.sync_mode else discord.ButtonStyle.secondary
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="Gán lại Role TV: BẬT", style=discord.ButtonStyle.primary, emoji="👥", row=2)
    async def toggle_member_roles(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.restore_member_roles = not self.restore_member_roles
        button.label = f"Gán lại Role TV: {'BẬT' if self.restore_member_roles else 'TẮT'}"
        button.style = discord.ButtonStyle.primary if self.restore_member_roles else discord.ButtonStyle.secondary
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="Sao lưu an toàn: BẬT", style=discord.ButtonStyle.primary, emoji="🛡️", row=2)
    async def toggle_safety_backup(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.create_safety_backup = not self.create_safety_backup
        button.label = f"Sao lưu an toàn: {'BẬT' if self.create_safety_backup else 'TẮT'}"
        button.style = discord.ButtonStyle.primary if self.create_safety_backup else discord.ButtonStyle.secondary
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="XÁC NHẬN KHÔI PHỤC", style=discord.ButtonStyle.danger, emoji="‼️", row=3)
    async def confirm_load(self, interaction: discord.Interaction, button: discord.ui.Button):
        mode_text = "Đồng bộ hóa (Giữ nguyên tin nhắn cũ)" if self.sync_mode else "Khôi phục toàn diện (Xóa cấu trúc cũ)"
        await interaction.response.edit_message(
            content=f"⏳ Đang tiến hành xử lý ({mode_text})... Vui lòng chờ!",
            embed=None,
            view=None
        )
        try:
            await self.cog.load_backup(
                interaction.guild,
                self.filename,
                requester=interaction.user,
                sync_mode=self.sync_mode,
                restore_members=self.restore_member_roles,
                safety_backup=self.create_safety_backup
            )
        except Exception as e:
            try:
                await interaction.user.send(t(interaction.guild, "BACKUP_RESTORE_ERROR", error=e))
            except discord.Forbidden:
                pass

    @discord.ui.button(label="Hủy", style=discord.ButtonStyle.secondary, emoji="❌", row=3)
    async def cancel_load(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content=t(interaction.guild, "BACKUP_CANCELLED"), embed=None, view=None)


class LoadBackupView(discord.ui.View):
    def __init__(self, author_id: int, cog_instance, guild_id: int, backups: list):
        super().__init__(timeout=60)
        self.author_id = author_id
        self.cog = cog_instance

        options = []
        for backup in backups[:25]:
            info = self.cog.get_backup_info(guild_id, backup)
            desc = info.get("description") or "Không có mô tả"
            date_str = info.get("date") or "N/A"
            options.append(
                discord.SelectOption(
                    label=backup,
                    description=f"[{date_str}] {desc}"[:100],
                    value=backup,
                    emoji="📦"
                )
            )

        self.select_menu = discord.ui.Select(placeholder="Chọn một bản sao lưu để khôi phục...", options=options)
        self.select_menu.callback = self.select_callback
        self.add_item(self.select_menu)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(t(interaction.guild, "BACKUP_NOT_YOURS"), ephemeral=True)
            return False
        return True

    async def select_callback(self, interaction: discord.Interaction):
        filename = self.select_menu.values[0]
        stats = await asyncio.to_thread(self.cog.get_backup_stats, interaction.guild_id, filename)

        embed = discord.Embed(
            title=t(interaction.guild, "BACKUP_WARN_TITLE"),
            description=t(interaction.guild, "BACKUP_WARN_DESC", filename=filename),
            color=discord.Color.dark_red()
        )
        if stats:
            embed.add_field(
                name="📊 Thống kê bản sao lưu",
                value=(
                    f"• **Mô tả:** {stats['description']}\n"
                    f"• **Ngày tạo:** `{stats['date']}`\n"
                    f"• **Vai trò (Roles):** `{stats['roles']}`\n"
                    f"• **Danh mục (Categories):** `{stats['categories']}`\n"
                    f"• **Kênh (Channels):** `{stats['channels']}`\n"
                    f"• **Danh sách cấm (Bans):** `{stats['bans']} người`"
                ),
                inline=False
            )
        await interaction.response.edit_message(
            embed=embed,
            view=ConfirmLoadView(interaction.user.id, self.cog, filename)
        )


class ExportBackupView(discord.ui.View):
    def __init__(self, author_id: int, cog_instance, guild_id: int, backups: list):
        super().__init__(timeout=60)
        self.author_id = author_id
        self.cog = cog_instance

        options = [
            discord.SelectOption(label=b, description=self.cog.get_backup_info(guild_id, b).get("description", "")[:100], value=b, emoji="📥")
            for b in backups[:25]
        ]
        self.select_menu = discord.ui.Select(placeholder="Chọn bản sao lưu để tải file JSON...", options=options)
        self.select_menu.callback = self.select_callback
        self.add_item(self.select_menu)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(t(interaction.guild, "BACKUP_NOT_YOURS"), ephemeral=True)
            return False
        return True

    async def select_callback(self, interaction: discord.Interaction):
        filename = self.select_menu.values[0]
        file_path = os.path.join(BACKUP_DIR, str(interaction.guild_id), filename)
        if not os.path.exists(file_path):
            return await interaction.response.edit_message(content="❌ File sao lưu không tồn tại.", embed=None, view=None)

        await interaction.response.edit_message(
            content=f"📦 Dưới đây là file sao lưu `{filename}` của bạn:",
            embed=None,
            view=None,
            attachments=[discord.File(file_path, filename=filename)]
        )


class DeleteBackupView(discord.ui.View):
    def __init__(self, author_id: int, cog_instance, guild_id: int, backups: list):
        super().__init__(timeout=60)
        self.author_id = author_id
        self.cog = cog_instance

        options = [
            discord.SelectOption(label=b, description=self.cog.get_backup_info(guild_id, b).get("description", "")[:100], value=b, emoji="🗑️")
            for b in backups[:25]
        ]
        self.select_menu = discord.ui.Select(placeholder="Chọn một bản sao lưu để xóa...", options=options)
        self.select_menu.callback = self.select_callback
        self.add_item(self.select_menu)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(t(interaction.guild, "BACKUP_NOT_YOURS"), ephemeral=True)
            return False
        return True

    async def select_callback(self, interaction: discord.Interaction):
        filename = self.select_menu.values[0]
        try:
            await asyncio.to_thread(self.cog.delete_backup, interaction.guild_id, filename)
            msg = t(interaction.guild, "BACKUP_DELETE_SUCCESS", filename=filename)
        except FileNotFoundError:
            msg = t(interaction.guild, "BACKUP_DELETE_NOT_FOUND")
        except Exception as e:
            msg = t(interaction.guild, "BACKUP_DELETE_ERROR", error=e)

        await interaction.response.edit_message(content=msg, embed=None, view=None)


class BackupControlView(discord.ui.View):
    def __init__(self, author_id: int, cog_instance):
        super().__init__(timeout=180)
        self.author_id = author_id
        self.cog = cog_instance

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(t(interaction.guild, "BACKUP_NOT_YOURS"), ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Tạo Sao Lưu", style=discord.ButtonStyle.success, emoji="💾", row=1)
    async def create_backup(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(CreateBackupModal())

    @discord.ui.button(label="Khôi phục Sao lưu", style=discord.ButtonStyle.danger, emoji="🔄", row=1)
    async def load_backup(self, interaction: discord.Interaction, button: discord.ui.Button):
        backups = await asyncio.to_thread(self.cog.get_backups_for_guild, interaction.guild_id)
        if not backups:
            return await interaction.response.send_message(t(interaction.guild, "BACKUP_NO_BACKUPS_RESTORE"), ephemeral=True)

        embed = discord.Embed(
            title=t(interaction.guild, "BACKUP_SELECT_TITLE"),
            description=t(interaction.guild, "BACKUP_SELECT_DESC"),
            color=discord.Color.orange()
        )
        await interaction.response.send_message(
            embed=embed,
            view=LoadBackupView(interaction.user.id, self.cog, interaction.guild_id, backups),
            ephemeral=True
        )

    @discord.ui.button(label="Danh Sách & Thống Kê", style=discord.ButtonStyle.primary, emoji="📜", row=2)
    async def list_backups(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        backups = await asyncio.to_thread(self.cog.get_backups_for_guild, interaction.guild_id)

        if not backups:
            return await interaction.followup.send(t(interaction.guild, "BACKUP_NO_BACKUPS"), ephemeral=True)

        embed = discord.Embed(
            title=t(interaction.guild, "BACKUP_LIST_TITLE", guild_name=interaction.guild.name),
            color=discord.Color.blue()
        )
        description = ""
        for i, backup in enumerate(backups[:15], 1):
            stats = await asyncio.to_thread(self.cog.get_backup_stats, interaction.guild_id, backup)
            description += (
                f"**{i}.** `{backup}` (`{stats.get('roles', 0)} roles`, `{stats.get('channels', 0)} kênh`)\n"
                f"   - Ngày: {stats.get('date', 'N/A')}\n"
                f"   - Mô tả: *{stats.get('description', 'N/A')}*\n\n"
            )

        embed.description = description
        embed.set_footer(text=f"Tối đa {MAX_BACKUPS_PER_GUILD} bản sao lưu mỗi server.")
        await interaction.followup.send(embed=embed, ephemeral=True)

    @discord.ui.button(label="Tải File (Export)", style=discord.ButtonStyle.secondary, emoji="📥", row=2)
    async def export_backup_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        backups = await asyncio.to_thread(self.cog.get_backups_for_guild, interaction.guild_id)
        if not backups:
            return await interaction.response.send_message(t(interaction.guild, "BACKUP_NO_BACKUPS"), ephemeral=True)

        embed = discord.Embed(
            title="📥 Xuất file sao lưu (Export JSON)",
            description="Chọn bản sao lưu bên dưới để tải file `.json` về máy.",
            color=discord.Color.teal()
        )
        await interaction.response.send_message(
            embed=embed,
            view=ExportBackupView(interaction.user.id, self.cog, interaction.guild_id, backups),
            ephemeral=True
        )

    @discord.ui.button(label="Xóa Sao Lưu", style=discord.ButtonStyle.secondary, emoji="🗑️", row=2)
    async def delete_backup_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        backups = await asyncio.to_thread(self.cog.get_backups_for_guild, interaction.guild_id)
        if not backups:
            return await interaction.response.send_message(t(interaction.guild, "BACKUP_NO_BACKUPS_DELETE"), ephemeral=True)

        embed = discord.Embed(
            title=t(interaction.guild, "BACKUP_DELETE_TITLE"),
            description=t(interaction.guild, "BACKUP_DELETE_DESC"),
            color=discord.Color.dark_red()
        )
        await interaction.response.send_message(
            embed=embed,
            view=DeleteBackupView(interaction.user.id, self.cog, interaction.guild_id, backups),
            ephemeral=True
        )


class BackupCog(commands.Cog, name="BackupCog"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        os.makedirs(BACKUP_DIR, exist_ok=True)
        self._active_guilds = set()
        self.auto_backup_task.start()

    def cog_unload(self):
        self.auto_backup_task.cancel()

    @tasks.loop(hours=24)
    async def auto_backup_task(self):
        """Tự động sao lưu định kỳ mỗi 24 giờ cho tất cả các server mà bot đang tham gia."""
        await self.bot.wait_until_ready()
        for guild in self.bot.guilds:
            try:
                await self.create_backup(guild, self.bot.user, "[Auto-Task] Sao lưu định kỳ hàng ngày")
            except Exception as e:
                print(f"[BackupCog] Lỗi auto-backup cho guild {guild.id}: {e}")

    def get_backups_for_guild(self, guild_id: int) -> list:
        guild_backup_dir = os.path.join(BACKUP_DIR, str(guild_id))
        if not os.path.exists(guild_backup_dir):
            return []
        return sorted([f for f in os.listdir(guild_backup_dir) if f.endswith('.json')], reverse=True)

    def get_backup_info(self, guild_id: int, filename: str) -> dict:
        file_path = os.path.join(BACKUP_DIR, str(guild_id), filename)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return {
                "date": data.get("backup_date"),
                "user_id": data.get("backup_user_id"),
                "description": data.get("backup_description")
            }
        except Exception:
            return {}

    def get_backup_stats(self, guild_id: int, filename: str) -> dict:
        file_path = os.path.join(BACKUP_DIR, str(guild_id), filename)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            channels_count = len(data.get("channels", [])) or (
                len(data.get("text_channels", [])) + len(data.get("voice_channels", []))
            )
            return {
                "date": data.get("backup_date", "N/A"),
                "description": data.get("backup_description", "Không có mô tả"),
                "roles": len(data.get("roles", [])),
                "categories": len(data.get("categories", [])),
                "channels": channels_count,
                "bans": len(data.get("bans", []))
            }
        except Exception:
            return {}

    def delete_backup(self, guild_id: int, filename: str):
        file_path = os.path.join(BACKUP_DIR, str(guild_id), filename)
        if os.path.exists(file_path):
            os.remove(file_path)
        else:
            raise FileNotFoundError("File sao lưu không tồn tại.")

    def _enforce_backup_limit(self, guild_id: int):
        backups = self.get_backups_for_guild(guild_id)
        if len(backups) > MAX_BACKUPS_PER_GUILD:
            for old_backup in backups[MAX_BACKUPS_PER_GUILD:]:
                try:
                    self.delete_backup(guild_id, old_backup)
                except Exception:
                    pass

    def _build_overwrites(self, guild: discord.Guild, overwrites_data: list, role_map: dict) -> dict:
        overwrites = {}
        for ow in overwrites_data:
            target = None
            if ow.get("type") == "role":
                old_id = ow.get("id")
                if old_id == guild.id or ow.get("is_default"):
                    target = guild.default_role
                else:
                    target = role_map.get(old_id) or discord.utils.get(guild.roles, name=ow.get("name"))
            elif ow.get("type") == "member":
                target = guild.get_member(ow.get("id"))

            if target:
                allow = discord.Permissions(ow.get("allow", 0))
                deny = discord.Permissions(ow.get("deny", 0))
                overwrites[target] = discord.PermissionOverwrite.from_pair(allow, deny)
        return overwrites

    async def _restore_channel(self, guild: discord.Guild, chan_data: dict, role_map: dict, category: discord.CategoryChannel = None):
        overwrites = self._build_overwrites(guild, chan_data.get("overwrites", []), role_map)
        c_type = chan_data.get("type", "text")
        name = chan_data["name"]

        try:
            if c_type == "text":
                return await guild.create_text_channel(
                    name=name, category=category, topic=chan_data.get("topic"),
                    slowmode_delay=chan_data.get("slowmode_delay", 0), nsfw=chan_data.get("nsfw", False),
                    overwrites=overwrites, reason="Khôi phục từ backup"
                )
            elif c_type == "voice":
                bitrate = min(chan_data.get("bitrate", 64000), int(guild.bitrate_limit))
                return await guild.create_voice_channel(
                    name=name, category=category, bitrate=bitrate, user_limit=chan_data.get("user_limit", 0),
                    overwrites=overwrites, reason="Khôi phục từ backup"
                )
            elif c_type == "stage":
                return await guild.create_stage_channel(
                    name=name, category=category, topic=chan_data.get("topic"),
                    overwrites=overwrites, reason="Khôi phục từ backup"
                )
            elif c_type == "forum":
                return await guild.create_forum(
                    name=name, category=category, topic=chan_data.get("topic"),
                    slowmode_delay=chan_data.get("slowmode_delay", 0), nsfw=chan_data.get("nsfw", False),
                    overwrites=overwrites, reason="Khôi phục từ backup"
                )
        except Exception as e:
            print(f"[BackupCog] Lỗi tạo kênh {name}: {e}")
            return None

    async def load_backup(
        self,
        guild: discord.Guild,
        filename: str,
        requester: discord.User = None,
        sync_mode: bool = False,
        restore_members: bool = True,
        safety_backup: bool = True
    ):
        if guild.id in self._active_guilds:
            raise RuntimeError("Server đang trong quá trình sao lưu hoặc khôi phục khác.")

        if safety_backup:
            try:
                await self.create_backup(guild, requester or self.bot.user, "[Auto] Backup an toàn trước khi khôi phục")
            except Exception:
                pass

        self._active_guilds.add(guild.id)
        try:
            file_path = os.path.join(BACKUP_DIR, str(guild.id), filename)
            if not os.path.exists(file_path):
                raise FileNotFoundError("Không tìm thấy file sao lưu.")

            with open(file_path, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)

            # 1. XÓA HOẶC ĐỒNG BỘ CẤU TRÚC
            if not sync_mode:
                for channel in list(guild.channels):
                    try:
                        await channel.delete(reason="Khôi phục từ backup")
                        await asyncio.sleep(0.2)
                    except Exception:
                        pass
                for role in list(guild.roles):
                    if role.is_default() or role.is_bot_managed() or role.is_premium_subscriber() or role >= guild.me.top_role:
                        continue
                    try:
                        await role.delete(reason="Khôi phục từ backup")
                        await asyncio.sleep(0.2)
                    except Exception:
                        pass

            # 2. TẠO LẠI / CẬP NHẬT ROLES
            role_map = {guild.id: guild.default_role}
            for role_data in reversed(backup_data.get("roles", [])):
                if role_data.get("is_default"):
                    try:
                        await guild.default_role.edit(permissions=discord.Permissions(role_data["permissions"]))
                    except Exception:
                        pass
                    continue

                # Kiểm tra nếu ở chế độ Sync mà role đã tồn tại theo tên
                existing_role = discord.utils.get(guild.roles, name=role_data["name"]) if sync_mode else None
                if existing_role:
                    if role_data.get("id"):
                        role_map[role_data["id"]] = existing_role
                    role_map[role_data["name"]] = existing_role
                    try:
                        await existing_role.edit(
                            permissions=discord.Permissions(role_data["permissions"]),
                            color=discord.Color(role_data["color"]),
                            hoist=role_data["hoist"],
                            mentionable=role_data["mentionable"]
                        )
                    except Exception:
                        pass
                else:
                    try:
                        new_role = await guild.create_role(
                            name=role_data["name"],
                            permissions=discord.Permissions(role_data["permissions"]),
                            color=discord.Color(role_data["color"]),
                            hoist=role_data["hoist"],
                            mentionable=role_data["mentionable"],
                            reason="Khôi phục từ backup"
                        )
                        if role_data.get("id"):
                            role_map[role_data["id"]] = new_role
                        role_map[role_data["name"]] = new_role
                        await asyncio.sleep(0.2)
                    except Exception:
                        pass

            # Chuẩn hóa channels
            all_channels = backup_data.get("channels", [])
            if not all_channels:
                for c in backup_data.get("text_channels", []):
                    c["type"] = "text"
                    all_channels.append(c)
                for c in backup_data.get("voice_channels", []):
                    c["type"] = "voice"
                    all_channels.append(c)

            first_text_channel = None

            # 3. TẠO LẠI CATEGORIES & CHANNELS
            for cat_data in sorted(backup_data.get("categories", []), key=lambda c: c.get("position", 0)):
                existing_cat = discord.utils.get(guild.categories, name=cat_data["name"]) if sync_mode else None
                cat_overwrites = self._build_overwrites(guild, cat_data.get("overwrites", []), role_map)

                if existing_cat:
                    new_cat = existing_cat
                    try:
                        await new_cat.edit(overwrites=cat_overwrites)
                    except Exception:
                        pass
                else:
                    try:
                        new_cat = await guild.create_category(
                            name=cat_data["name"], overwrites=cat_overwrites, reason="Khôi phục từ backup"
                        )
                        await asyncio.sleep(0.2)
                    except Exception:
                        continue

                cat_id = cat_data.get("id")
                cat_name = cat_data.get("name")
                cat_channels = [
                    c for c in all_channels
                    if (cat_id and c.get("category_id") == cat_id) or (not cat_id and c.get("category") == cat_name)
                ]
                for chan_data in sorted(cat_channels, key=lambda x: x.get("position", 0)):
                    if sync_mode and discord.utils.get(new_cat.channels, name=chan_data["name"]):
                        continue  # Bỏ qua nếu kênh đã tồn tại để giữ tin nhắn cũ
                    created = await self._restore_channel(guild, chan_data, role_map, category=new_cat)
                    if isinstance(created, discord.TextChannel) and first_text_channel is None:
                        first_text_channel = created
                    await asyncio.sleep(0.2)

            # 4. KÊNH KHÔNG THUỘC CATEGORY
            uncategorized = [c for c in all_channels if not c.get("category_id") and not c.get("category")]
            for chan_data in sorted(uncategorized, key=lambda x: x.get("position", 0)):
                if sync_mode and discord.utils.get(guild.text_channels + guild.voice_channels, name=chan_data["name"]):
                    continue
                created = await self._restore_channel(guild, chan_data, role_map, category=None)
                if isinstance(created, discord.TextChannel) and first_text_channel is None:
                    first_text_channel = created
                await asyncio.sleep(0.2)

            # 5. KHÔI PHỤC BAN (Danh sách cấm)
            for ban_info in backup_data.get("bans", []):
                try:
                    user_obj = await self.bot.fetch_user(ban_info["user_id"])
                    await guild.ban(user_obj, reason=ban_info.get("reason", "Khôi phục từ backup"))
                    await asyncio.sleep(0.2)
                except Exception:
                    pass

            # 6. GÁN LẠI ROLE CHO THÀNH VIÊN
            if restore_members and not sync_mode:
                for member_id_str, old_role_ids in backup_data.get("member_roles", {}).items():
                    member = guild.get_member(int(member_id_str))
                    if not member:
                        continue
                    roles_to_add = [
                        role_map[r_id] for r_id in old_role_ids
                        if r_id in role_map and role_map[r_id] < guild.me.top_role and not role_map[r_id].is_default()
                    ]
                    if roles_to_add:
                        try:
                            await member.add_roles(*roles_to_add, reason="Khôi phục Role từ backup")
                            await asyncio.sleep(0.2)
                        except Exception:
                            pass

            # 7. THÔNG BÁO HOÀN TẤT
            success_msg = t(guild, "BACKUP_RESTORE_SUCCESS")
            if first_text_channel:
                try:
                    await first_text_channel.send(f"✅ {success_msg}")
                except Exception:
                    pass
            if requester:
                try:
                    await requester.send(f"✅ **{guild.name}**: {success_msg}")
                except Exception:
                    pass
        finally:
            self._active_guilds.discard(guild.id)

    async def create_backup(self, guild: discord.Guild, user: discord.User, description: str) -> str:
        if guild.id in self._active_guilds:
            raise RuntimeError("Server đang trong quá trình sao lưu hoặc khôi phục khác.")

        self._active_guilds.add(guild.id)
        try:
            guild_backup_dir = os.path.join(BACKUP_DIR, str(guild.id))
            os.makedirs(guild_backup_dir, exist_ok=True)

            now_utc = datetime.now(timezone.utc)
            backup_data = {
                "guild_name": guild.name,
                "guild_id": guild.id,
                "backup_date": now_utc.strftime("%Y-%m-%d %H:%M:%S UTC"),
                "backup_user_id": user.id,
                "backup_description": description,
                "roles": [],
                "categories": [],
                "channels": [],
                "member_roles": {},
                "bans": []
            }

            # Sao lưu Roles
            for role in sorted(guild.roles, key=lambda r: r.position, reverse=True):
                if role.is_bot_managed() or role.is_premium_subscriber():
                    continue
                backup_data["roles"].append({
                    "id": role.id, "name": role.name, "permissions": role.permissions.value,
                    "color": role.color.value, "hoist": role.hoist, "mentionable": role.mentionable,
                    "position": role.position, "is_default": role.is_default()
                })

            # Sao lưu Categories & Channels
            for category in sorted(guild.categories, key=lambda c: c.position):
                backup_data["categories"].append({
                    "id": category.id, "name": category.name, "position": category.position,
                    "overwrites": self._serialize_overwrites(category)
                })

            for channel in guild.channels:
                if isinstance(channel, discord.CategoryChannel):
                    continue
                backup_data["channels"].append(self._channel_to_dict(channel))

            # Sao lưu Bans (Danh sách người bị cấm)
            try:
                async for ban_entry in guild.bans():
                    backup_data["bans"].append({
                        "user_id": ban_entry.user.id,
                        "reason": ban_entry.reason
                    })
            except Exception:
                pass

            # Sao lưu Member Roles
            for member in guild.members:
                if member.bot:
                    continue
                m_roles = [r.id for r in member.roles if not r.is_default() and not r.is_bot_managed()]
                if m_roles:
                    backup_data["member_roles"][str(member.id)] = m_roles

            timestamp = now_utc.strftime("%Y%m%d-%H%M%S")
            file_path = os.path.join(guild_backup_dir, f"backup-{timestamp}.json")

            def _write():
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(backup_data, f, indent=4, ensure_ascii=False)
                self._enforce_backup_limit(guild.id)

            await asyncio.to_thread(_write)
            return file_path
        finally:
            self._active_guilds.discard(guild.id)

    def _serialize_overwrites(self, channel) -> list:
        result = []
        for target, overwrite in channel.overwrites.items():
            allow, deny = overwrite.pair()
            is_role = isinstance(target, discord.Role)
            result.append({
                "type": "role" if is_role else "member",
                "id": target.id, "name": target.name,
                "is_default": target.is_default() if is_role else False,
                "allow": allow.value, "deny": deny.value
            })
        return result

    def _channel_to_dict(self, channel) -> dict:
        if isinstance(channel, discord.VoiceChannel):
            c_type = "voice"
        elif isinstance(channel, discord.StageChannel):
            c_type = "stage"
        elif isinstance(channel, discord.ForumChannel):
            c_type = "forum"
        else:
            c_type = "text"

        d = {
            "id": channel.id, "name": channel.name, "type": c_type,
            "position": channel.position,
            "category": channel.category.name if channel.category else None,
            "category_id": channel.category.id if channel.category else None,
            "overwrites": self._serialize_overwrites(channel)
        }
        if isinstance(channel, (discord.TextChannel, discord.ForumChannel)):
            d["topic"] = channel.topic
            d["slowmode_delay"] = channel.slowmode_delay
            d["nsfw"] = channel.is_nsfw()
        elif isinstance(channel, discord.VoiceChannel):
            d["bitrate"] = channel.bitrate
            d["user_limit"] = channel.user_limit
        elif isinstance(channel, discord.StageChannel):
            d["topic"] = channel.topic
        return d

    @commands.hybrid_group(name="backup", description="Quản lý sao lưu và khôi phục server.")
    @commands.has_permissions(administrator=True)
    async def backup(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(
                title=t(ctx.guild, "BACKUP_PANEL_TITLE"),
                description=t(ctx.guild, "BACKUP_PANEL_DESC"),
                color=discord.Color.dark_blue()
            )
            embed.set_footer(text=t(ctx.guild, "BACKUP_PANEL_FOOTER"))
            await ctx.send(embed=embed, view=BackupControlView(ctx.author.id, self), ephemeral=True)

    @backup.command(name="create", description="Tạo một bản sao lưu mới cho server.")
    @app_commands.describe(description="Mô tả ngắn gọn cho bản sao lưu này.")
    async def create_cmd(self, ctx: commands.Context, *, description: str = "Không có mô tả"):
        await ctx.defer(ephemeral=True)
        try:
            path = await self.create_backup(ctx.guild, ctx.author, description)
            embed = discord.Embed(
                title=t(ctx.guild, "BACKUP_SUCCESS_TITLE"),
                description=t(ctx.guild, "BACKUP_SUCCESS_DESC", guild_name=ctx.guild.name, filename=os.path.basename(path)),
                color=discord.Color.green()
            )
            await ctx.send(embed=embed, ephemeral=True)
        except Exception as e:
            await ctx.send(t(ctx.guild, "BACKUP_CREATE_ERROR", error=e), ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(BackupCog(bot))
