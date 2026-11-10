from discord import app_commands
import asyncio
import os
import random
from typing import Optional

import discord
from discord.ext import commands
from openai import AsyncOpenAI

from Command.checks import (
    load_questions,
    PRIZES,
    MillionaireView,
    PRIZE_VALUES,
    update_rank,
    load_rank,
)
from Check.i18n import t

# --- CẤU HÌNH XKIRO API ---
API_KEY = None
try:
    from config import XKIRO_API_KEY as API_KEY
except ImportError:
    try:
        from config import GEMINI_API_KEY as API_KEY
    except ImportError:
        API_KEY = os.getenv("XKIRO_API_KEY") or os.getenv("GEMINI_API_KEY")

xkiro_client = AsyncOpenAI(
    api_key=API_KEY or "missing-api-key",
    base_url="https://api.xkiro.com/v1",
)

try:
    from config import AI_MODEL
except ImportError:
    AI_MODEL = "sensenova/sensenova-6.8-flash-lite"


class MiniGame(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def _get_target_language(self, guild: Optional[discord.Guild]) -> tuple[str, str]:
        """Xác định ngôn ngữ mục tiêu dựa trên ngôn ngữ mặc định (preferred_locale) của máy chủ."""
        if not guild:
            return ("vi", "Tiếng Việt")

        locale_str = str(guild.preferred_locale)

        language_map = {
            "vi": "Tiếng Việt",
            "en-US": "English",
            "en-GB": "English",
            "ja": "Japanese (日本語)",
            "ko": "Korean (한국어)",
            "zh-CN": "Simplified Chinese (简体中文)",
            "zh-TW": "Traditional Chinese (繁體中文)",
            "fr": "French (Français)",
            "de": "German (Deutsch)",
            "es-ES": "Spanish (Español)",
            "ru": "Russian (Русский)",
            "th": "Thai (ไทย)",
            "id": "Indonesian (Bahasa Indonesia)",
        }

        lang_name = language_map.get(locale_str, locale_str or "Tiếng Việt")
        return (locale_str, lang_name)

    async def _call_xkiro_ai(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 500,
    ) -> str:
        """Hàm gọi xKiro API bất đồng bộ kèm tự động retry khi quá tải."""
        last_error = None
        for attempt in range(3):
            try:
                resp = await xkiro_client.chat.completions.create(
                    model=AI_MODEL,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                if resp.choices and resp.choices[0].message.content:
                    return resp.choices[0].message.content.strip()
                return "..."
            except Exception as e:
                last_error = e
                error_str = str(e).lower()
                status_code = getattr(e, "status_code", None)
                if status_code in (429, 500, 502, 503, 504) or "429" in error_str or "503" in error_str:
                    if attempt < 2:
                        await asyncio.sleep(1.5 * (attempt + 1))
                        continue
                raise e
        if last_error is not None:
            raise last_error
        raise RuntimeError("Không thể nhận phản hồi từ AI sau nhiều lần thử.")

    @commands.command()
    async def quest(self, ctx: commands.Context, *, question: Optional[str] = None):
        """Quả cầu tiên tri sử dụng model mistralai/mistral-large-4-0 qua xKiro."""
        if not question:
            return await ctx.send(t(ctx.guild, "QUEST_NEED_QUESTION"))

        async with ctx.typing():
            try:
                messages = [
                    {
                        "role": "system",
                        "content": (
                            "Bạn là một quả cầu tiên tri bí ẩn. "
                            "Trả lời ngắn gọn (1-2 câu), vui vẻ, mang tính giải trí. "
                            "Không khẳng định chắc chắn tương lai."
                        ),
                    },
                    {"role": "user", "content": question},
                ]

                result = await self._call_xkiro_ai(
                    messages=messages,
                    temperature=1.1,
                    max_tokens=150,
                )

                embed = discord.Embed(
                    title=t(ctx.guild, "QUEST_TITLE"),
                    description=t(ctx.guild, "QUEST_DESC", question=question, result=result),
                    color=discord.Color.purple(),
                )
                embed.set_footer(text=f"Model: {AI_MODEL}")
                await ctx.send(embed=embed)
            except Exception as e:
                await ctx.send(t(ctx.guild, "QUEST_ERROR", error=e))

    @commands.command(aliases=["altp"])
    async def ailatrieuphu(self, ctx: commands.Context):
        """Mini-game tương tác Ai Là Triệu Phú."""
        questions = load_questions()
        if not questions:
            return await ctx.send(t(ctx.guild, "ALTP_NO_QUESTIONS"))

        # Kiểm tra nếu file json có bọc key "questions"
        if isinstance(questions, dict) and "questions" in questions:
            questions = questions["questions"]

        selected_questions = random.sample(questions, min(10, len(questions)))

        score = 0
        money = 0
        msg = None

        # Trạng thái các quyền trợ giúp xuyên suốt lượt chơi
        used_5050_global = False
        used_audience_global = False
        used_phone_global = False

        letters = ["A", "B", "C", "D"]

        for level, q in enumerate(selected_questions):
            q_answers = q.get("answers") or q.get("options")
            if not q_answers or len(q_answers) < 4:
                return await ctx.send(t(ctx.guild, "ALTP_INVALID_STRUCT", num=level + 1))

            answers = list(enumerate(q_answers))
            random.shuffle(answers)

            # Lấy vị trí đáp án đúng sau khi đã xáo trộn
            correct_index = next(
                (i for i, (old_idx, _) in enumerate(answers) if old_idx == q.get("correct")),
                None,
            )
            if correct_index is None:
                return await ctx.send(t(ctx.guild, "ALTP_INVALID_STRUCT", num=level + 1))

            answer_text = "\n".join(
                f"**{letters[i]}.** {answer}" for i, (_, answer) in enumerate(answers)
            )

            embed = discord.Embed(
                title=t(ctx.guild, "ALTP_TITLE", num=level + 1),
                description=f"**{q['question']}**",
                color=discord.Color.gold(),
            )
            embed.add_field(
                name=t(ctx.guild, "ALTP_FIELD_ANSWERS"),
                value=answer_text,
                inline=False,
            )
            embed.add_field(
                name=t(ctx.guild, "ALTP_FIELD_PRIZE"),
                value=PRIZES[min(level, len(PRIZES) - 1)],
                inline=False,
            )

            # Khởi tạo View mới cho mỗi câu hỏi để hồi phục 30s đếm ngược
            view = MillionaireView(ctx.author)
            view.ctx = ctx
            view.correct_index = correct_index
            view.answers_text = [a for _, a in answers]
            view.current_question = q["question"]
            view.answer = None

            # Đồng bộ các trợ giúp đã sử dụng
            view.used_5050 = used_5050_global
            view.used_audience = used_audience_global
            view.used_phone = used_phone_global

            # Khóa các nút trợ giúp đã tiêu tốn
            for item in view.children:
                if isinstance(item, discord.ui.Button) and item.label:
                    if "50:50" in item.label and used_5050_global:
                        item.disabled = True
                    elif "Khán giả" in item.label and used_audience_global:
                        item.disabled = True
                    elif "Gọi điện" in item.label and used_phone_global:
                        item.disabled = True

            # Gán nhãn các phím đáp án
            for i in range(min(4, len(view.children))):
                view.children[i].label = letters[i]

            if msg is None:
                msg = await ctx.send(embed=embed, view=view)
            else:
                await msg.edit(embed=embed, view=view)

            view.message = msg
            await view.wait()

            # Cập nhật quyền trợ giúp sau tương tác
            used_5050_global = view.used_5050
            used_audience_global = view.used_audience
            used_phone_global = view.used_phone

            # Người chơi bấm nút dừng cuộc chơi
            if getattr(view, "ended", False):
                update_rank(ctx.author.id, money)
                for item in view.children:
                    item.disabled = True
                await msg.edit(view=view)
                prize = PRIZES[max(0, score - 1)] if score > 0 else "0₫"
                return await ctx.send(
                    t(ctx.guild, "ALTP_STOPPED", mention=ctx.author.mention, score=score, prize=prize)
                )

            # Hết thời gian chờ phản hồi
            if view.answer is None:
                for item in view.children:
                    item.disabled = True
                await msg.edit(view=view)
                return await ctx.send(t(ctx.guild, "ALTP_TIMEOUT", score=score))

            # Kiểm tra đáp án
            if view.answer == correct_index:
                score += 1
                money = PRIZE_VALUES[min(score - 1, len(PRIZE_VALUES) - 1)]

                temp_msg = await ctx.send(t(ctx.guild, "ALTP_CORRECT", mention=ctx.author.mention, score=score))
                await asyncio.sleep(2)
                try:
                    await temp_msg.delete()
                except discord.HTTPException:
                    pass
                continue
            else:
                for item in view.children:
                    item.disabled = True
                await msg.edit(view=view)
                return await ctx.send(
                    t(ctx.guild, "ALTP_WRONG", letter=letters[correct_index], score=score)
                )

        # Trả lời đúng toàn bộ câu hỏi: Lưu tiền thưởng cao nhất vào rank
        update_rank(ctx.author.id, money)
        for item in view.children:
            item.disabled = True
        await msg.edit(view=view)
        await ctx.send(t(ctx.guild, "ALTP_WIN", mention=ctx.author.mention))

    @commands.command(name="trieuphu_top", aliases=["top_altp"])
    async def trieuphu_top(self, ctx: commands.Context):
        """Bảng xếp hạng tiền thưởng Ai Là Triệu Phú."""
        rank_data = load_rank()
        if not rank_data:
            return await ctx.send(t(ctx.guild, "ALTP_RANK_EMPTY"))

        sorted_users = sorted(rank_data.items(), key=lambda x: x[1], reverse=True)

        embed = discord.Embed(
            title=t(ctx.guild, "ALTP_RANK_TITLE"),
            color=discord.Color.orange(),
        )

        text_lines = []
        for rank, (uid, money) in enumerate(sorted_users[:10], start=1):
            try:
                user = self.bot.get_user(int(uid)) or await self.bot.fetch_user(int(uid))
                name = user.name
            except Exception:
                name = t(ctx.guild, "ALTP_RANK_ANON", uid=uid)
            text_lines.append(f"**#{rank}** {name} — `{money:,}₫`")

        embed.description = "\n".join(text_lines)
        await ctx.send(embed=embed)

    @commands.command(name="altp_rank")
    async def altp_rank(self, ctx: commands.Context):
        """Kiểm tra thứ hạng tiền thưởng Ai Là Triệu Phú hiện tại của bản thân."""
        rank_data = load_rank()
        if not rank_data:
            return await ctx.send(t(ctx.guild, "RANK_NO_DATA"))

        sorted_users = sorted(rank_data.items(), key=lambda x: x[1], reverse=True)
        user_id_str = str(ctx.author.id)

        for rank, (uid, money) in enumerate(sorted_users, start=1):
            if user_id_str == str(uid):
                embed = discord.Embed(
                    title=t(ctx.guild, "RANK_TITLE"),
                    color=discord.Color.blurple(),
                )
                embed.add_field(name=t(ctx.guild, "RANK_FIELD_RANK"), value=f"#{rank}")
                embed.add_field(name=t(ctx.guild, "RANK_FIELD_RECORD"), value=f"{money:,}₫")
                return await ctx.send(embed=embed)

        await ctx.send(t(ctx.guild, "RANK_NO_RECORD"))

    @commands.hybrid_command(name="translate", aliases=["t", "dich"], description="Dịch văn bản tự động sang ngôn ngữ server bằng AI")
    @app_commands.describe(text="Đoạn văn bản cần dịch sang ngôn ngữ của máy chủ")
    async def translate(self, ctx: commands.Context, *, text: Optional[str] = None):
        """Dịch văn bản tự động sang ngôn ngữ server bằng mistralai/mistral-large-4-0."""
        from Command.vote import require_vote_or_notify
        if not await require_vote_or_notify(ctx, "/translate (Dịch Thuật Đa Ngôn Ngữ AI)"):
            return

        if not text:
            return await ctx.send("⚠️ Vui lòng cung cấp nội dung cần dịch. Ví dụ: `/translate text:Hello world` hoặc `!dich Hello world`", ephemeral=True)

        if len(text) > 2000:
            return await ctx.send("⚠️ Văn bản quá dài (giới hạn tối đa 2000 ký tự).")

        _, target_language_name = self._get_target_language(ctx.guild)

        async with ctx.typing():
            try:
                messages = [
                    {
                        "role": "system",
                        "content": (
                            f"Bạn là một dịch giả chuyên nghiệp. "
                            f"Hãy dịch chính xác nội dung người dùng gửi sang {target_language_name}.\n"
                            f"Yêu cầu:\n"
                            f"- Giữ nguyên sắc thái, định dạng markdown và các biểu tượng cảm xúc (emoji/mentions).\n"
                            f"- Chỉ trả lời duy nhất bản dịch hoàn chỉnh, không thêm lời chào, không giải thích hay mở đầu."
                        ),
                    },
                    {"role": "user", "content": text},
                ]

                translated = await self._call_xkiro_ai(
                    messages=messages,
                    temperature=0.3,
                    max_tokens=1000,
                )

                # Giới hạn an toàn 1024 ký tự cho mỗi Field trong Discord Embed
                val_original = (text[:1020] + "...") if len(text) > 1024 else text
                val_translated = (translated[:1020] + "...") if len(translated) > 1024 else translated

                embed = discord.Embed(
                    title=f"🌐 Bản dịch ({target_language_name})",
                    color=0x4285F4,
                )
                embed.add_field(
                    name=t(ctx.guild, "TRANSLATE_FIELD_ORIGINAL") or "Văn bản gốc",
                    value=val_original,
                    inline=False,
                )
                embed.add_field(
                    name=t(ctx.guild, "TRANSLATE_FIELD_RESULT") or f"Kết quả ({target_language_name})",
                    value=val_translated,
                    inline=False,
                )
                embed.set_footer(text=f"Model: {AI_MODEL}")

                await ctx.send(embed=embed)

            except Exception as e:
                await ctx.send(f"❌ Lỗi dịch thuật: `{e}`")

    @commands.hybrid_command(
        name="familytime",
        aliases=["family", "giadinh", "nhatusoi"],
        description="🐺 Chơi game Family Time: Sinh Tồn Gia Đình Nàng Sói (Chơi ngay trên Web)"
    )
    async def familytime_cmd(self, ctx: commands.Context):
        """Mở liên kết chơi game Family Time mô phỏng sinh tồn hoang dã và chăm sóc đàn con sói."""
        embed = discord.Embed(
            title="🐺 Family Time: Sinh Tồn Gia Đình Nàng Sói",
            description=(
                "**Mô phỏng sinh tồn hoang dã & Quản lý gia đình** dựa theo phong cách game *Family Time*!\n\n"
                "🌲 **Khai thác tài nguyên**: Chặt cây lấy gỗ, đập đá, hái quả dại, câu cá.\n"
                "🔥 **Xây dựng căn cứ**: Lửa trại sưởi ấm ban đêm, Giỏ lương thực, Nôi em bé, Nhà gỗ lớn.\n"
                "🐺 **Nàng Sói (Vợ)**: Tương tác trò chuyện, tặng quà, xoa đầu, sinh đàn con theo thời gian.\n"
                "👶 **Chăm sóc đàn con**: Cho đàn con ăn trước khi bị đói, chu kỳ ngày/đêm sống động!\n\n"
                "👉 **Bấm nút bên dưới để mở và chơi ngay trên trình duyệt (hỗ trợ cả PC & Mobile):**"
            ),
            color=discord.Color.from_rgb(255, 154, 194),
            timestamp=discord.utils.utcnow()
        )
        embed.set_thumbnail(url="https://raw.githubusercontent.com/twitter/twemoji/master/assets/72x72/1f43a.png")
        embed.set_footer(text="SakuraBot Web Games — Tích hợp sẵn không cần tải về")

        web_url = "http://sakurabot.wispbyte.org:10272/game/familytime"
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="🎮 Chơi Ngay Trên Web", url=web_url, style=discord.ButtonStyle.link, emoji="🐺"))
        view.add_item(discord.ui.Button(label="🕹️ Game Center", url="http://sakurabot.wispbyte.org:10272/games", style=discord.ButtonStyle.link, emoji="🌸"))
        await ctx.send(embed=embed, view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(MiniGame(bot))
