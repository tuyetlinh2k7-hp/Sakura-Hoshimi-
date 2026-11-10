import asyncio
import io
import os
import sqlite3
import tempfile
import zipfile
import discord
from discord import app_commands
from discord.ext import commands

# Cấu hình danh sách loại trừ
IGNORED_DIRS = {
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "cache",
    "temp",
    "downloads",
    ".pytest_cache",
}

IGNORED_FILES = {
    ".env",  # Tuyệt đối không leak token
    ".DS_Store",
    "bot_backup.zip",
}

IGNORED_EXTS = {
    ".pyc",
    ".zip",
    ".tar",
    ".gz",
    ".log",
    ".mp3",
    ".mp4",
    ".webm",
    ".opus",
    ".m4a",
    ".wav",
}

MAX_FILE_SIZE_MB = 8.0  # Bỏ qua các file đơn lẻ lớn hơn mức này


def _create_zip_worker(root_dir: str) -> tuple[io.BytesIO, list[str]]:
    """Worker chạy trên Thread riêng: xử lý SQLite an toàn và nén source code."""
    buffer = io.BytesIO()
    skipped_items = []

    with tempfile.TemporaryDirectory() as temp_dir:
        with zipfile.ZipFile(
            buffer, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=1
        ) as zf:
            for current_root, dirs, files in os.walk(root_dir):
                # Bỏ qua thư mục rác và thư mục ẩn
                dirs[:] = [
                    d
                    for d in dirs
                    if d not in IGNORED_DIRS and not d.startswith(".")
                ]

                for filename in files:
                    if filename in IGNORED_FILES or filename.startswith("."):
                        continue

                    _, ext = os.path.splitext(filename)
                    if ext.lower() in IGNORED_EXTS:
                        continue

                    full_path = os.path.join(current_root, filename)
                    relative_path = os.path.relpath(full_path, root_dir)

                    try:
                        # Kiểm tra kích thước file
                        if (
                            os.path.getsize(full_path) / (1024 * 1024)
                            > MAX_FILE_SIZE_MB
                        ):
                            skipped_items.append(
                                f"{relative_path} (> {MAX_FILE_SIZE_MB}MB)"
                            )
                            continue

                        # Snapshot an toàn cho file SQLite DB tránh lỗi file đang bị ghi
                        if ext.lower() in {".db", ".sqlite", ".sqlite3"}:
                            safe_db_copy = os.path.join(
                                temp_dir, f"safe_{filename}"
                            )
                            try:
                                with sqlite3.connect(full_path) as src:
                                    with sqlite3.connect(safe_db_copy) as dst:
                                        src.backup(dst)
                                zf.write(safe_db_copy, arcname=relative_path)
                                continue
                            except Exception:
                                pass  # Nếu không snapshot được, fallback đọc bình thường

                        zf.write(full_path, arcname=relative_path)

                    except (PermissionError, OSError):
                        skipped_items.append(
                            f"{relative_path} (Đang bận/Khóa)"
                        )

    buffer.seek(0)
    return buffer, skipped_items


class SystemBackup(commands.Cog, name="SystemBackup"):
    """Cog hệ thống phục vụ việc bảo trì và trích xuất source code an toàn."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Xác định thư mục gốc của bot
        try:
            self.root_dir = os.path.dirname(
                os.path.abspath(self.bot.__file__)  # type: ignore
            )
        except (AttributeError, TypeError):
            self.root_dir = os.path.abspath(".")

    async def _execute_backup(self) -> tuple[discord.File | None, str]:
        """Thực thi tác vụ nén ở background thread."""
        zip_buffer, skipped = await asyncio.to_thread(
            _create_zip_worker, self.root_dir
        )
        size_mb = len(zip_buffer.getvalue()) / (1024 * 1024)

        if size_mb > 24.0:  # Ngưỡng file upload của Discord
            return (
                None,
                f"File nén quá lớn (`{size_mb:.2f} MB`), vượt quá giới hạn tải lên của Discord.",
            )

        report = f"**Đóng gói hoàn tất!**\n- Dung lượng: `{size_mb:.2f} MB`\n- Thư mục gốc: `{os.path.basename(self.root_dir)}`"
        if skipped:
            report += f"\n- Bỏ qua {len(skipped)} file (file bận hoặc > {MAX_FILE_SIZE_MB}MB)."

        file = discord.File(fp=zip_buffer, filename="bot_full_backup.zip")
        return file, report

    # 1. Prefix command dạng Group: `!system backup` hoặc `!sys backup` (Tránh trùng với `!backup` của server)
    @commands.group(
        name="system",
        aliases=["sys", "botadmin"],
        invoke_without_command=True,
    )
    @commands.is_owner()
    async def system_group(self, ctx: commands.Context):
        await ctx.send("Sử dụng lệnh: `!system backup`")

    @system_group.command(name="backup", aliases=["pack", "export"])
    @commands.is_owner()
    async def system_backup_cmd(self, ctx: commands.Context):
        msg = await ctx.send("Đang quét toàn bộ file và database...")
        file, report = await self._execute_backup()

        if file is None:
            await msg.edit(content=report)
            return

        await ctx.send(content=report, file=file)
        await msg.delete()

    # 2. Slash command dạng Group: `/dev backup` (Hiển thị Ephemeral chỉ bạn thấy)
    dev_group = app_commands.Group(
        name="dev", description="Lệnh quản trị dành riêng cho Developer"
    )

    @dev_group.command(
        name="backup",
        description="Đóng gói mã nguồn và dữ liệu bot (Chỉ Owner)",
    )
    async def slash_backup(self, interaction: discord.Interaction):
        # Kiểm tra quyền Owner cho slash command
        if not await self.bot.is_owner(interaction.user):
            await interaction.response.send_message(
                "Bạn không có quyền thực hiện lệnh này!", ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)
        file, report = await self._execute_backup()

        if file is None:
            await interaction.followup.send(report, ephemeral=True)
            return

        await interaction.followup.send(content=report, file=file, ephemeral=True)


# Entrypoint để bot load file này thành extension
async def setup(bot: commands.Bot):
    await bot.add_cog(SystemBackup(bot))
