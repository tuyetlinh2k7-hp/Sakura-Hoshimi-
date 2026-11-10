import os
import re
import time
import json
import asyncio
from typing import Optional, Union

import discord
from discord import app_commands
from discord.ext import commands, tasks
import aiosqlite

DB_FILE = "data/role_panels.db"

BUTTON_STYLES = {
    "secondary": discord.ButtonStyle.secondary,
    "primary": discord.ButtonStyle.primary,
    "success": discord.ButtonStyle.success,
    "danger": discord.ButtonStyle.danger,
}

STYLE_NAMES = {
    "secondary": "⚪ Xám (Secondary)",
    "primary": "🔵 Xanh dương (Primary)",
    "success": "🟢 Xanh lá (Success)",
    "danger": "🔴 Đỏ (Danger)",
}

def parse_hex_color(hex_str: Optional[str]) -> discord.Color:
    if not hex_str:
        return discord.Color.blurple()
    clean = hex_str.strip().lstrip("#")
    if re.fullmatch(r"[0-9a-fA-F]{6}", clean):
        return discord.Color(int(clean, 16))
    return discord.Color.blurple()

def resolve_emoji(guild: discord.Guild, emoji_input: Optional[str]) -> Optional[Union[discord.Emoji, discord.PartialEmoji, str]]:
    if not emoji_input:
        return None
    raw = emoji_input.strip()
    if not raw:
        return None

    if raw.startswith("<") and raw.endswith(">"):
        try:
            partial = discord.PartialEmoji.from_str(raw)
            if partial.id:
                found = guild.get_emoji(partial.id)
                return found if found else partial
        except Exception:
            pass

    clean_name = raw.strip(":")
    found = discord.utils.get(guild.emojis, name=clean_name)
    if found:
        return found
    if clean_name.isdigit():
        found = guild.get_emoji(int(clean_name))
        if found:
            return found
    if all(ord(c) < 128 and (c.isalnum() or c in "_- ") for c in raw):
        return None
    return raw

def matches_reaction(reaction_emoji: discord.PartialEmoji, role_info: dict) -> bool:
    stored_id = role_info.get("emoji_id")
    stored_name = role_info.get("emoji_name")
    stored_str = role_info.get("emoji_str")

    if reaction_emoji.id and stored_id:
        return reaction_emoji.id == stored_id
    if not reaction_emoji.id and not stored_id:
        return (str(reaction_emoji.name) == str(stored_name) or str(reaction_emoji) == str(stored_str))
    return reaction_emoji.name == stored_name or str(reaction_emoji) == str(stored_str)

def get_server_emoji_options(guild: discord.Guild, page: int = 0) -> list[discord.SelectOption]:
    emojis = guild.emojis
    start = page * 25
    page_emojis = emojis[start : start + 25]

    options = []
    if not page_emojis:
        for d in ["⭐", "🎮", "🔥", "👑", "💎", "🛡️", "🎯", "📌", "✨", "🚀"]:
            options.append(discord.SelectOption(label=f"Emoji {d}", value=f"unicode:{d}", emoji=d))
        return options

    for em in page_emojis:
        options.append(discord.SelectOption(
            label=em.name[:100], value=f"custom:{em.id}", description=f":{em.name}:", emoji=em
        ))
    return options

def build_panel_embed(title: str, user_desc: str, color_hex: str, image_url: str, panel_type: str, mode: str, roles_data: list[dict], guild: discord.Guild) -> discord.Embed:
    bot_legend = "\n\n━━━━━━━━━━━━━━━━━━━━━━\n📌 **Chi tiết phân quyền tương ứng:**\n"
    for item in roles_data:
        role_obj = guild.get_role(item.get("role_id"))
        role_mention = role_obj.mention if role_obj else f"`Role ID: {item.get('role_id')}`"
        emj_str = item.get("emoji_str", "")
        label = item.get("label", role_obj.name if role_obj else "Role")

        if panel_type == "button":
            emj_txt = f"{emj_str} " if emj_str else ""
            bot_legend += f"• Nút **[{emj_txt}{label}]** ➔ Cấp role: {role_mention}\n"
        else:
            bot_legend += f"• Thả {emj_str} ➔ Nhận role: {role_mention}\n"

    mode_note = "💡 *Chế độ:* **Chỉ được giữ 1 role** (chọn role mới sẽ tự hủy role cũ)." if mode == "single" else "💡 *Chế độ:* **Nhận nhiều role** (tự do chọn nhiều role)."
    
    embed = discord.Embed(
        title=title,
        description=f"{user_desc}{bot_legend}\n\n{mode_note}",
        color=parse_hex_color(color_hex),
    )
    img = (image_url or "").strip()
    if img and (img.startswith("http://") or img.startswith("https://")):
        embed.set_image(url=img)
    return embed


class RoleButton(discord.ui.Button):
    def __init__(self, item: dict, mode: str):
        style_key = item.get("style", "secondary")
        
        emj_val = item.get("emoji_str")
        if emj_val and emj_val.startswith("<") and emj_val.endswith(">"):
            try:
                emj_val = discord.PartialEmoji.from_str(emj_val)
            except Exception:
                pass
                
        super().__init__(
            label=item.get("label", "Role"),
            style=BUTTON_STYLES.get(style_key, discord.ButtonStyle.secondary),
            custom_id=f"rolepanel_{item['role_id']}",
            emoji=emj_val if emj_val else None
        )
        self.target_role_id = item["role_id"]
        self.mode = mode

    async def callback(self, interaction: discord.Interaction):
        cog: RolePanelCog = self.view.cog
        guild = interaction.guild
        member = interaction.user

        retry_after = cog.check_cooldown(member.id, cooldown_sec=1.5)
        if retry_after > 0:
            await interaction.response.send_message(f"⏳ Thao tác quá nhanh! Thử lại sau **{retry_after:.1f}s**.", ephemeral=True)
            return

        target_role = guild.get_role(self.target_role_id)
        if not target_role:
            await interaction.response.send_message("❌ Role này không còn tồn tại trên máy chủ!", ephemeral=True)
            return

        if guild.me.top_role <= target_role:
            await interaction.response.send_message("⚠️ Bot không đủ quyền cấp role này (Role của Bot đang nằm dưới).", ephemeral=True)
            return

        try:
            if target_role in member.roles:
                await member.remove_roles(target_role, reason="Reaction Role (Button)")
                await interaction.response.send_message(f"➖ Đã gỡ role **{target_role.name}**.", ephemeral=True)
            else:
                if self.mode == "single":
                    panel_role_ids = [child.target_role_id for child in self.view.children if isinstance(child, RoleButton)]
                    to_remove = [
                        r for r_id in panel_role_ids 
                        if r_id != target_role.id and (r := guild.get_role(r_id)) and r in member.roles and guild.me.top_role > r
                    ]
                    if to_remove:
                        await member.remove_roles(*to_remove, reason="Reaction Role (Single Switch)")
                    await member.add_roles(target_role, reason="Reaction Role (Button)")
                    await interaction.response.send_message(f"✅ Đã chọn **{target_role.name}** (Đã hủy các role cũ).", ephemeral=True)
                else:
                    await member.add_roles(target_role, reason="Reaction Role (Button)")
                    await interaction.response.send_message(f"✅ Đã nhận role **{target_role.name}**.", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("❌ Bot bị thiếu quyền `Manage Roles`!", ephemeral=True)

class RolePanelView(discord.ui.View):
    def __init__(self, cog, panel_data: dict):
        super().__init__(timeout=None)
        self.cog = cog
        mode = panel_data.get("mode", "multi")
        for item in panel_data.get("roles", []):
            self.add_item(RoleButton(item, mode))


class FinalEmbedModal(discord.ui.Modal):
    def __init__(self, cog: "RolePanelCog", target_channel: discord.TextChannel, mode: str, panel_type: str, configured_roles: list[dict]):
        super().__init__(title="Hoàn Tất Thiết Lập Bảng Role")
        self.cog = cog
        self.target_channel = target_channel
        self.mode = mode
        self.panel_type = panel_type
        self.configured_roles = configured_roles

        self.panel_title = discord.ui.TextInput(label="Tiêu đề bảng Role", default="BẢNG CHỌN VAI TRÒ", required=True)
        self.add_item(self.panel_title)
        self.panel_desc = discord.ui.TextInput(label="Nội dung thông báo", style=discord.TextStyle.paragraph, required=True)
        self.add_item(self.panel_desc)
        self.embed_color = discord.ui.TextInput(label="Mã màu Hex (Tùy chọn)", placeholder="#5865F2", required=False)
        self.add_item(self.embed_color)
        self.image_url = discord.ui.TextInput(label="Link Banner (Tùy chọn)", required=False)
        self.add_item(self.image_url)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        roles_data_clean = [
            {
                "role_id": item["role"].id,
                "emoji_id": item["emoji_id"],
                "emoji_name": item["emoji_name"],
                "emoji_str": item["emoji_str"],
                "label": item["label"],
                "style": item.get("style", "secondary"),
            } for item in self.configured_roles
        ]
        
        panel_data = {
            "guild_id": self.target_channel.guild.id,
            "channel_id": self.target_channel.id,
            "title": self.panel_title.value,
            "description": self.panel_desc.value,
            "color": self.embed_color.value.strip(),
            "image_url": self.image_url.value.strip(),
            "type": self.panel_type,
            "mode": self.mode,
            "roles": roles_data_clean,
        }

        embed = build_panel_embed(
            self.panel_title.value, self.panel_desc.value, self.embed_color.value, self.image_url.value,
            self.panel_type, self.mode, roles_data_clean, self.target_channel.guild
        )

        try:
            if self.panel_type == "button":
                view = RolePanelView(self.cog, panel_data)
                sent_msg = await self.target_channel.send(embed=embed, view=view)
            else:
                sent_msg = await self.target_channel.send(embed=embed)
                for item in self.configured_roles:
                    if item["emoji_obj"]:
                        try:
                            await sent_msg.add_reaction(item["emoji_obj"])
                        except Exception:
                            pass
        except discord.Forbidden:
            await interaction.followup.send("❌ Bot thiếu quyền gửi tin nhắn hoặc nhúng link ở kênh này!", ephemeral=True)
            return

        await self.cog.save_panel_db(str(sent_msg.id), panel_data)
        await interaction.followup.send(f"✅ **Đã tạo bảng role thành công!** 🆔 ID: `{sent_msg.id}`", ephemeral=True)


class CustomEmojiInputModal(discord.ui.Modal):
    def __init__(self, parent_view: "RoleConfigView"):
        super().__init__(title="Nhập Emoji Thủ Công")
        self.parent_view = parent_view
        self.emoji_text = discord.ui.TextInput(label="Emoji (Unicode hoặc tên/ID)", placeholder="Ví dụ: 🎮 hoặc pepe", required=True)
        self.add_item(self.emoji_text)

    async def on_submit(self, interaction: discord.Interaction):
        resolved = resolve_emoji(interaction.guild, self.emoji_text.value)
        if not resolved:
            await interaction.response.send_message("❌ Không tìm thấy emoji hợp lệ!", ephemeral=True)
            return
        self.parent_view.curr_emoji_obj = resolved
        self.parent_view.curr_emoji_str = str(resolved)
        await self.parent_view.update_view(interaction)


class CustomLabelInputModal(discord.ui.Modal):
    def __init__(self, parent_view: "RoleConfigView"):
        super().__init__(title="Đổi Tên Nút Bấm")
        self.parent_view = parent_view
        self.label_text = discord.ui.TextInput(label="Tên hiển thị trên nút", default=self.parent_view.curr_label or "", max_length=80, required=True)
        self.add_item(self.label_text)

    async def on_submit(self, interaction: discord.Interaction):
        self.parent_view.curr_label = self.label_text.value.strip()
        await self.parent_view.update_view(interaction)


class EditPanelModal(discord.ui.Modal):
    def __init__(self, cog: "RolePanelCog", message_id: str, panel_data: dict):
        super().__init__(title="Chỉnh Sửa Bảng Role")
        self.cog = cog
        self.message_id = message_id
        self.panel_data = panel_data

        self.panel_title = discord.ui.TextInput(label="Tiêu đề bảng Role", default=panel_data.get("title", ""), max_length=200, required=True)
        self.add_item(self.panel_title)
        self.panel_desc = discord.ui.TextInput(label="Nội dung thông báo", style=discord.TextStyle.paragraph, default=panel_data.get("description", ""), required=True)
        self.add_item(self.panel_desc)
        self.embed_color = discord.ui.TextInput(label="Mã màu Embed Hex", default=panel_data.get("color", ""), required=False)
        self.add_item(self.embed_color)
        self.image_url = discord.ui.TextInput(label="Link Banner", default=panel_data.get("image_url", ""), required=False)
        self.add_item(self.image_url)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        channel = interaction.guild.get_channel(self.panel_data.get("channel_id"))
        if not channel:
            return await interaction.followup.send("❌ Không tìm thấy kênh!", ephemeral=True)

        try:
            msg = await channel.fetch_message(int(self.message_id))
        except discord.NotFound:
            return await interaction.followup.send("❌ Tin nhắn gốc đã bị xóa!", ephemeral=True)

        self.panel_data["title"] = self.panel_title.value
        self.panel_data["description"] = self.panel_desc.value
        self.panel_data["color"] = self.embed_color.value.strip()
        self.panel_data["image_url"] = self.image_url.value.strip()

        new_embed = build_panel_embed(
            self.panel_title.value, self.panel_desc.value, self.embed_color.value, self.image_url.value,
            self.panel_data.get("type", "button"), self.panel_data.get("mode", "multi"),
            self.panel_data.get("roles", []), interaction.guild
        )

        await msg.edit(embed=new_embed)
        await self.cog.save_panel_db(self.message_id, self.panel_data)
        await interaction.followup.send("✅ Cập nhật giao diện thành công!", ephemeral=True)


class RoleConfigView(discord.ui.View):
    def __init__(self, cog: "RolePanelCog", target_channel: discord.TextChannel, mode: str, panel_type: str, total_count: int):
        super().__init__(timeout=900)
        self.cog = cog
        self.target_channel = target_channel
        self.mode = mode
        self.panel_type = panel_type
        self.total_count = total_count

        self.configured_roles: list[dict] = []
        self.current_idx: int = 0
        self.emoji_page: int = 0

        self.curr_role = None
        self.curr_emoji_obj = None
        self.curr_emoji_str = ""
        self.curr_label = None
        self.curr_style = "secondary"

        self.rebuild_components()

    def get_embed(self) -> discord.Embed:
        role_txt = self.curr_role.mention if self.curr_role else "*Chưa chọn*"
        emoji_txt = self.curr_emoji_str if self.curr_emoji_str else "*Chưa chọn*"
        label_txt = f"`{self.curr_label}`" if self.curr_label else "*Lấy theo tên Role*"
        
        desc = f"**• Role:** {role_txt}\n**• Emoji:** {emoji_txt}\n"
        if self.panel_type == "button":
            desc += f"**• Tên nút:** {label_txt}\n**• Màu nút:** {STYLE_NAMES.get(self.curr_style)}\n"

        desc += "\n💡 *Bạn có thể tinh chỉnh tự do. Khi ưng ý, bấm Lưu để chuyển sang Role tiếp theo.*"
        return discord.Embed(title=f"⚙️ Cấu hình Role [{self.current_idx + 1}/{self.total_count}]", description=desc, color=discord.Color.gold())

    def rebuild_components(self):
        self.clear_items()
        guild = self.target_channel.guild

        role_select = discord.ui.RoleSelect(placeholder="1. Chọn Role", min_values=1, max_values=1, row=0)
        role_select.callback = self.on_role_select
        self.add_item(role_select)

        emoji_select = discord.ui.Select(placeholder="2. Chọn Emoji Server", options=get_server_emoji_options(guild, self.emoji_page), row=1)
        emoji_select.callback = self.on_emoji_select
        self.add_item(emoji_select)

        if self.panel_type == "button":
            style_select = discord.ui.Select(
                placeholder="3. Chọn màu nút",
                options=[
                    discord.SelectOption(label="Xám (Secondary)", value="secondary", emoji="⚪", default=self.curr_style=="secondary"),
                    discord.SelectOption(label="Xanh Dương (Primary)", value="primary", emoji="🔵", default=self.curr_style=="primary"),
                    discord.SelectOption(label="Xanh Lá (Success)", value="success", emoji="🟢", default=self.curr_style=="success"),
                    discord.SelectOption(label="Đỏ (Danger)", value="danger", emoji="🔴", default=self.curr_style=="danger"),
                ], row=2
            )
            style_select.callback = self.on_style_select
            self.add_item(style_select)

        nav_btn = discord.ui.Button(label="Trang Emoji 🔄", style=discord.ButtonStyle.secondary, row=3)
        nav_btn.callback = self.on_next_emoji_page
        self.add_item(nav_btn)

        manual_emj = discord.ui.Button(label="🔤 Nhập Emoji Khác", style=discord.ButtonStyle.secondary, row=3)
        manual_emj.callback = self.on_manual_emoji
        self.add_item(manual_emj)

        if self.panel_type == "button":
            lbl_btn = discord.ui.Button(label="✏️ Đổi Tên Nút", style=discord.ButtonStyle.secondary, row=3)
            lbl_btn.callback = self.on_change_label
            self.add_item(lbl_btn)

        save_btn = discord.ui.Button(label="Lưu Role Này ➔" if self.current_idx + 1 < self.total_count else "Hoàn tất chọn Role ➔", style=discord.ButtonStyle.success, row=4)
        save_btn.callback = self.on_save_role
        self.add_item(save_btn)

    async def update_view(self, interaction: discord.Interaction):
        self.rebuild_components()
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

    async def on_role_select(self, interaction: discord.Interaction):
        role = interaction.guild.get_role(int(interaction.data["values"][0]))
        if not role or role.is_default() or role.managed:
            return await interaction.response.send_message("❌ Không chọn được role Everyone hoặc của Bot!", ephemeral=True)
        self.curr_role = role
        if not self.curr_label: self.curr_label = role.name
        await self.update_view(interaction)

    async def on_emoji_select(self, interaction: discord.Interaction):
        val = interaction.data["values"][0]
        if val.startswith("custom:"):
            emj = interaction.guild.get_emoji(int(val.split(":")[1]))
            self.curr_emoji_obj = emj
            self.curr_emoji_str = str(emj) if emj else ""
        else:
            self.curr_emoji_obj = self.curr_emoji_str = val.split(":")[1]
        await self.update_view(interaction)

    async def on_style_select(self, interaction: discord.Interaction):
        self.curr_style = interaction.data["values"][0]
        await self.update_view(interaction)

    async def on_next_emoji_page(self, interaction: discord.Interaction):
        self.emoji_page = (self.emoji_page + 1) % max(1, (len(interaction.guild.emojis) - 1) // 25 + 1)
        await self.update_view(interaction)

    async def on_manual_emoji(self, interaction: discord.Interaction):
        await interaction.response.send_modal(CustomEmojiInputModal(self))

    async def on_change_label(self, interaction: discord.Interaction):
        await interaction.response.send_modal(CustomLabelInputModal(self))

    async def on_save_role(self, interaction: discord.Interaction):
        if not self.curr_role:
            return await interaction.response.send_message("❌ Chưa chọn Role!", ephemeral=True)
        
        if any(r["role"].id == self.curr_role.id for r in self.configured_roles):
            return await interaction.response.send_message(f"❌ Role {self.curr_role.mention} đã tồn tại trong bảng!", ephemeral=True)

        if self.panel_type == "reaction" and not self.curr_emoji_obj:
            return await interaction.response.send_message("❌ Bảng dạng Thả Emoji bắt buộc phải chọn Emoji tương ứng!", ephemeral=True)

        emj_id = getattr(self.curr_emoji_obj, "id", None)
        emj_name = getattr(self.curr_emoji_obj, "name", str(self.curr_emoji_obj) if self.curr_emoji_obj else "")

        self.configured_roles.append({
            "role": self.curr_role, "emoji_obj": self.curr_emoji_obj, "emoji_id": emj_id,
            "emoji_name": emj_name, "emoji_str": self.curr_emoji_str,
            "label": self.curr_label or self.curr_role.name, "style": self.curr_style,
        })
        self.current_idx += 1

        if self.current_idx < self.total_count:
            self.curr_role, self.curr_emoji_obj, self.curr_emoji_str, self.curr_label, self.curr_style = None, None, "", None, "secondary"
            await self.update_view(interaction)
        else:
            final_view = discord.ui.View()
            btn = discord.ui.Button(label="📝 Nhập Nội Dung & Gửi Bảng", style=discord.ButtonStyle.primary)
            btn.callback = lambda i: i.response.send_modal(FinalEmbedModal(self.cog, self.target_channel, self.mode, self.panel_type, self.configured_roles))
            final_view.add_item(btn)
            await interaction.response.edit_message(embed=discord.Embed(title="🎉 Hoàn tất chọn Role! Bấm nút bên dưới để chốt bảng.", color=discord.Color.green()), view=final_view)


class InitialSetupView(discord.ui.View):
    def __init__(self, cog: "RolePanelCog", target_channel: discord.TextChannel):
        super().__init__(timeout=600)
        self.cog = cog
        self.target_channel = target_channel
        self.mode = "multi"
        self.panel_type = "button"
        self.count = 1

    @discord.ui.select(placeholder="1. Chế độ nhận role", options=[
        discord.SelectOption(label="Nhận nhiều role", value="multi", default=True),
        discord.SelectOption(label="Chỉ chọn 1 role duy nhất", value="single")
    ])
    async def select_mode(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.mode = select.values[0]
        for opt in select.options: opt.default = opt.value == self.mode
        await interaction.response.edit_message(view=self)

    @discord.ui.select(placeholder="2. Hình thức tương tác", options=[
        discord.SelectOption(label="Bằng nút bấm (Buttons)", value="button", default=True),
        discord.SelectOption(label="Bằng thả Emoji (Reactions)", value="reaction")
    ])
    async def select_type(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.panel_type = select.values[0]
        for opt in select.options: opt.default = opt.value == self.panel_type
        await interaction.response.edit_message(view=self)

    @discord.ui.select(placeholder="3. Số lượng Role (Tối đa 20)", options=[
        discord.SelectOption(label=f"{i} Role", value=str(i), default=(i == 1)) for i in range(1, 21)
    ])
    async def select_count(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.count = int(select.values[0])
        for opt in select.options: opt.default = opt.value == str(self.count)
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="Tiến hành cấu hình Role ➔", style=discord.ButtonStyle.success, row=4)
    async def next_step(self, interaction: discord.Interaction, button: discord.ui.Button):
        config_view = RoleConfigView(self.cog, self.target_channel, self.mode, self.panel_type, self.count)
        await interaction.response.edit_message(embed=config_view.get_embed(), view=config_view)


class RolePanelCog(commands.GroupCog, group_name="reactionrole"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.panels_cache: dict = {}
        self._cooldowns: dict[int, float] = {}
        self._suppress_reaction_remove: dict[tuple, float] = {}

    async def cog_load(self):
        os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
        async with aiosqlite.connect(DB_FILE) as db:
            await db.execute("CREATE TABLE IF NOT EXISTS panels (message_id TEXT PRIMARY KEY, data TEXT)")
            await db.commit()
            async with db.execute("SELECT message_id, data FROM panels") as cursor:
                async for row in cursor:
                    try:
                        panel_data = json.loads(row[1])
                        self.panels_cache[row[0]] = panel_data
                        if panel_data.get("type") == "button":
                            self.bot.add_view(RolePanelView(self, panel_data), message_id=int(row[0]))
                    except Exception as e:
                        print(f"[RolePanel] Lỗi Load JSON cho ID {row[0]}: {e}")
        self.garbage_collector.start()

    async def cog_unload(self):
        self.garbage_collector.cancel()

    async def save_panel_db(self, message_id: str, data: dict):
        self.panels_cache[message_id] = data
        async with aiosqlite.connect(DB_FILE) as db:
            await db.execute("INSERT OR REPLACE INTO panels (message_id, data) VALUES (?, ?)", (message_id, json.dumps(data, ensure_ascii=False)))
            await db.commit()

    async def delete_panel_db(self, message_id: str):
        if message_id in self.panels_cache:
            del self.panels_cache[message_id]
        async with aiosqlite.connect(DB_FILE) as db:
            await db.execute("DELETE FROM panels WHERE message_id = ?", (message_id,))
            await db.commit()

    @tasks.loop(minutes=5.0)
    async def garbage_collector(self):
        now = time.monotonic()
        self._cooldowns = {uid: ts for uid, ts in self._cooldowns.items() if now - ts < 10.0}
        self._suppress_reaction_remove = {k: ts for k, ts in self._suppress_reaction_remove.items() if now - ts < 15.0}

    def check_cooldown(self, user_id: int, cooldown_sec: float = 2.0) -> float:
        now = time.monotonic()
        last_used = self._cooldowns.get(user_id, 0.0)
        if now - last_used < cooldown_sec:
            return cooldown_sec - (now - last_used)
        self._cooldowns[user_id] = now
        return 0.0

    async def panel_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        choices = []
        guild = interaction.guild
        if not guild: return []
        for msg_id, data in self.panels_cache.items():
            if data.get("guild_id") == guild.id:
                title = data.get("title", "Bảng Role")
                ptype = "🔘 Nút" if data.get("type") == "button" else "😀 Reaction"
                label = f"{title} ({ptype}) - ID: {msg_id}"[:100]
                if current.lower() in label.lower() or current in msg_id:
                    choices.append(app_commands.Choice(name=label, value=msg_id))
        return choices[:25]

    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        msg = "🚫 Bạn cần quyền **Quản lý Vai trò (Manage Roles)**!" if isinstance(error, app_commands.MissingPermissions) else f"⚠️ Lỗi: `{error}`"
        if interaction.response.is_done(): await interaction.followup.send(msg, ephemeral=True)
        else: await interaction.response.send_message(msg, ephemeral=True)

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload: discord.RawMessageDeleteEvent):
        msg_id = str(payload.message_id)
        if msg_id in self.panels_cache:
            await self.delete_panel_db(msg_id)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if not self.bot.user or payload.user_id == self.bot.user.id: return
        msg_id = str(payload.message_id)
        panel = self.panels_cache.get(msg_id)
        if not panel or panel.get("type") != "reaction": return

        guild = self.bot.get_guild(payload.guild_id)
        if not guild: return

        member = payload.member
        if not member or member.bot or self.check_cooldown(member.id, 1.5) > 0: return

        target_role = None
        for item in panel.get("roles", []):
            if matches_reaction(payload.emoji, item):
                target_role = guild.get_role(item["role_id"])
                break
        if not target_role or guild.me.top_role <= target_role: return

        if panel.get("mode") == "single":
            channel = guild.get_channel(payload.channel_id)
            try: msg = await channel.fetch_message(payload.message_id) if channel else None
            except Exception: msg = None

            roles_to_remove = []
            for item in panel.get("roles", []):
                if item["role_id"] != target_role.id:
                    other_role = guild.get_role(item["role_id"])
                    if other_role and other_role in member.roles and guild.me.top_role > other_role:
                        roles_to_remove.append(other_role)

                    if msg:
                        emj_to_remove = guild.get_emoji(item["emoji_id"]) if item.get("emoji_id") else item.get("emoji_str")
                        if emj_to_remove:
                            suppress_key = (payload.message_id, member.id, str(item.get("emoji_str")))
                            self._suppress_reaction_remove[suppress_key] = time.monotonic()
                            try: await msg.remove_reaction(emj_to_remove, member)
                            except Exception: pass

            if roles_to_remove:
                try: await member.remove_roles(*roles_to_remove, reason="Reaction Role (Single Switch)")
                except Exception: pass

        if target_role not in member.roles:
            try: await member.add_roles(target_role, reason="Reaction Role (Add)")
            except Exception: pass

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        if not self.bot.user or payload.user_id == self.bot.user.id: return
        msg_id = str(payload.message_id)
        panel = self.panels_cache.get(msg_id)
        if not panel or panel.get("type") != "reaction": return

        guild = self.bot.get_guild(payload.guild_id)
        if not guild: return

        for item in panel.get("roles", []):
            if matches_reaction(payload.emoji, item):
                suppress_key = (payload.message_id, payload.user_id, str(item.get("emoji_str")))
                if suppress_key in self._suppress_reaction_remove:
                    del self._suppress_reaction_remove[suppress_key]
                    return

                try: member = await guild.fetch_member(payload.user_id)
                except Exception: return

                role = guild.get_role(item["role_id"])
                if role and role in member.roles and guild.me.top_role > role:
                    try: await member.remove_roles(role, reason="Reaction Role (Remove)")
                    except Exception: pass
                break

    @app_commands.command(name="setup", description="Khởi tạo bảng chọn role")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def setup_panel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await interaction.response.send_message("🛠️ **BƯỚC 1: CẤU HÌNH BAN ĐẦU**", view=InitialSetupView(self, channel), ephemeral=True)

    @app_commands.command(name="edit", description="Sửa tiêu đề/nội dung bảng role")
    @app_commands.autocomplete(panel=panel_autocomplete)
    @app_commands.checks.has_permissions(manage_roles=True)
    async def edit_panel(self, interaction: discord.Interaction, panel: str):
        msg_id = re.search(r"/(\d+)$", panel.strip()).group(1) if "/" in panel else panel.strip()
        if msg_id not in self.panels_cache: return await interaction.response.send_message("❌ Bảng không tồn tại!", ephemeral=True)
        await interaction.response.send_modal(EditPanelModal(self, msg_id, self.panels_cache[msg_id]))

    @app_commands.command(name="delete", description="Xóa bảng role")
    @app_commands.autocomplete(panel=panel_autocomplete)
    @app_commands.checks.has_permissions(manage_roles=True)
    async def delete_panel(self, interaction: discord.Interaction, panel: str):
        msg_id = re.search(r"/(\d+)$", panel.strip()).group(1) if "/" in panel else panel.strip()
        if msg_id not in self.panels_cache: return await interaction.response.send_message("❌ Bảng không tồn tại!", ephemeral=True)
        
        channel = interaction.guild.get_channel(self.panels_cache[msg_id]["channel_id"])
        if channel:
            try:
                msg = await channel.fetch_message(int(msg_id))
                await msg.delete()
            except Exception: pass
        await self.delete_panel_db(msg_id)
        await interaction.response.send_message("🗑️ Đã xóa bảng role thành công!", ephemeral=True)

    @app_commands.command(name="add_role", description="Thêm Role mới vào bảng Button")
    @app_commands.autocomplete(message_id=panel_autocomplete)
    @app_commands.checks.has_permissions(manage_roles=True)
    async def panel_add_role(self, interaction: discord.Interaction, message_id: str, role: discord.Role, label: str, emoji: str = None, style: str = "secondary"):
        msg_id = re.search(r"/(\d+)$", message_id.strip()).group(1) if "/" in message_id else message_id.strip()
        if msg_id not in self.panels_cache: return await interaction.response.send_message("❌ Bảng không tồn tại!", ephemeral=True)
        
        panel = self.panels_cache[msg_id]
        if panel["type"] != "button": return await interaction.response.send_message("❌ Hiện chỉ hỗ trợ thêm role cho bảng dạng Nút!", ephemeral=True)

        emj = resolve_emoji(interaction.guild, emoji)
        emj_str = str(emj) if emj else ""

        panel["roles"].append({
            "role_id": role.id, "emoji_id": getattr(emj, "id", None),
            "emoji_name": getattr(emj, "name", emj_str), "emoji_str": emj_str,
            "label": label, "style": style
        })
        
        await self.save_panel_db(msg_id, panel)
        channel = interaction.guild.get_channel(panel["channel_id"])
        msg = await channel.fetch_message(int(msg_id))
        
        await msg.edit(
            embed=build_panel_embed(panel["title"], panel["description"], panel["color"], panel["image_url"], panel["type"], panel["mode"], panel["roles"], interaction.guild),
            view=RolePanelView(self, panel)
        )
        await interaction.response.send_message(f"✅ Đã thêm Role {role.mention} vào bảng!", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(RolePanelCog(bot))
