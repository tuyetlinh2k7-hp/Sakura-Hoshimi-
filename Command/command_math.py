from Check.i18n import t, is_vietnamese
import discord
from discord.ext import commands
from discord import app_commands
import ast
import operator
import math
import time
from typing import Union, Optional

# Giới hạn an toàn chống tràn số / CPU denial of service
MAX_POWER = 10000
MAX_FACTORIAL = 1000

# Bảng toán tử an toàn
OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

# Các hàm và hằng số toán học được phép gọi
SAFE_MATH_FUNCTIONS = {
    "sqrt": math.sqrt,
    "cbrt": lambda x: math.pow(x, 1/3) if x >= 0 else -math.pow(-x, 1/3),
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "asin": math.asin,
    "acos": math.acos,
    "atan": math.atan,
    "radians": math.radians,
    "degrees": math.degrees,
    "log": math.log,
    "log10": math.log10,
    "log2": math.log2,
    "exp": math.exp,
    "abs": abs,
    "round": round,
    "floor": math.floor,
    "ceil": math.ceil,
    "factorial": lambda x: math.factorial(int(x)) if 0 <= int(x) <= MAX_FACTORIAL else (_ for _ in ()).throw(ValueError(f"Giai thừa tối đa {MAX_FACTORIAL}")),
    "gcd": math.gcd,
    "lcm": math.lcm,
}

SAFE_CONSTANTS = {
    "pi": math.pi,
    "e": math.e,
    "tau": math.tau,
}

class SafeEvaluator(ast.NodeVisitor):
    def visit_BinOp(self, node):
        left = self.visit(node.left)
        right = self.visit(node.right)
        op_type = type(node.op)
        if op_type not in OPERATORS:
            raise ValueError(f"Toán tử không được hỗ trợ: {op_type.__name__}")
        
        # Chặn lũy thừa quá lớn
        if op_type == ast.Pow:
            if isinstance(right, (int, float)) and abs(right) > MAX_POWER:
                raise ValueError(f"Số mũ quá lớn (tối đa {MAX_POWER})")
            if isinstance(left, (int, float)) and abs(left) > 1e100 and right > 10:
                raise ValueError("Kết quả vượt quá giới hạn tính toán")

        try:
            return OPERATORS[op_type](left, right)
        except ZeroDivisionError:
            raise ValueError("Lỗi chia cho 0 (Division by zero)")

    def visit_UnaryOp(self, node):
        operand = self.visit(node.operand)
        op_type = type(node.op)
        if op_type not in OPERATORS:
            raise ValueError(f"Toán tử một ngôi không hỗ trợ: {op_type.__name__}")
        return OPERATORS[op_type](operand)

    def visit_Constant(self, node):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError(f"Giá trị không hợp lệ: {node.value}")

    def visit_Name(self, node):
        name = node.id.lower()
        if name in SAFE_CONSTANTS:
            return SAFE_CONSTANTS[name]
        raise ValueError(f"Tên hoặc biến không xác định: {node.id}")

    def visit_Call(self, node):
        if not isinstance(node.func, ast.Name):
            raise ValueError("Chỉ hỗ trợ gọi hàm toán học chuẩn")
        func_name = node.func.id.lower()
        if func_name not in SAFE_MATH_FUNCTIONS:
            raise ValueError(f"Hàm toán học không được hỗ trợ: {node.func.id}")

        args = [self.visit(arg) for arg in node.args]
        try:
            return SAFE_MATH_FUNCTIONS[func_name](*args)
        except Exception as e:
            raise ValueError(f"Lỗi khi tính {func_name}(): {e}")

    def generic_visit(self, node):
        raise ValueError(f"Cú pháp biểu thức không được phép: {type(node).__name__}")


def evaluate_expression(expr: str) -> float:
    """Đánh giá an toàn biểu thức toán học."""
    clean_expr = expr.strip().replace("^", "**").replace("×", "*").replace("÷", "/")
    # Hỗ trợ cú pháp phần trăm cơ bản: "X% of Y" -> "(X / 100) * Y"
    import re
    pct_match = re.match(r"^([0-9.]+)\s*%\s+of\s+([0-9.]+)$", clean_expr, re.IGNORECASE)
    if pct_match:
        pct, total = float(pct_match.group(1)), float(pct_match.group(2))
        return (pct / 100.0) * total

    parsed = ast.parse(clean_expr, mode="eval")
    evaluator = SafeEvaluator()
    return evaluator.visit(parsed.body)


class MathCog(commands.Cog, name="Math"):
    """Cog máy tính toán thông minh & khoa học, yêu cầu Vote Top.gg để mở khóa."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(
        name="math",
        aliases=["calc", "tinh", "calculator", "tinhtoan"],
        description="Smart Math Calculator / Máy tính toán học (+,-,*,/,^, sqrt, sin, cos, log...)"
    )
    @app_commands.describe(
        bieu_thuc="Math expression / Biểu thức toán học (e.g. (150*12)/4, sqrt(144), 2^10, sin(pi/2), 15% of 850...)"
    )
    async def math_cmd(self, ctx: commands.Context, *, bieu_thuc: str):
        guild = ctx.guild
        vi = is_vietnamese(guild)

        # Kiểm tra điều kiện mở khóa Vote
        from Command.vote import require_vote_or_notify
        vote_feature_name = "/math (Máy Tính Toán Nâng Cao)" if vi else "/math (Advanced Math Calculator)"
        if not await require_vote_or_notify(ctx, vote_feature_name):
            return

        t_start = time.perf_counter()
        raw_expr = bieu_thuc.strip()
        if not raw_expr:
            err_msg = "⚠️ Vui lòng nhập biểu thức toán học cần tính toán!" if vi else "⚠️ Please enter a mathematical expression to calculate!"
            return await ctx.send(err_msg, ephemeral=True)

        if len(raw_expr) > 200:
            len_msg = "⚠️ Biểu thức quá dài! Vui lòng nhập tối đa 200 ký tự." if vi else "⚠️ Expression too long! Please enter at most 200 characters."
            return await ctx.send(len_msg, ephemeral=True)

        try:
            result = evaluate_expression(raw_expr)
            t_elapsed = (time.perf_counter() - t_start) * 1000

            # Định dạng kết quả số nguyên hoặc số thực
            if isinstance(result, float) and result.is_integer():
                formatted_res = f"{int(result):,}"
            elif isinstance(result, float):
                formatted_res = f"{result:,.6f}".rstrip("0").rstrip(".")
            else:
                formatted_res = f"{result:,}"

            title = "🧮 Kết Quả Tính Toán (Sakura Math)" if vi else "🧮 Calculation Result (Sakura Math)"
            expr_label = "📥 Biểu Thức" if vi else "📥 Expression"
            res_label = "📤 Kết Quả" if vi else "📤 Result"
            footer_text = (
                f"Thời gian tính: {t_elapsed:.2f}ms • Mở khóa bởi Sakura Vote System 🌸" if vi
                else f"Execution time: {t_elapsed:.2f}ms • Unlocked by Sakura Vote System 🌸"
            )

            embed = discord.Embed(
                title=title,
                color=discord.Color.from_rgb(123, 223, 242)
            )
            embed.add_field(name=expr_label, value=f"```fix\n{raw_expr}\n```", inline=False)
            embed.add_field(name=res_label, value=f"```yaml\n= {formatted_res}\n```", inline=False)
            embed.set_footer(
                text=footer_text,
                icon_url=ctx.author.display_avatar.url
            )

            await ctx.send(embed=embed)

        except ValueError as ve:
            err_title = "❌ Lỗi Tính Toán" if vi else "❌ Calculation Error"
            err_desc = f"Không thể xử lý biểu thức:\n`{ve}`" if vi else f"Unable to process expression:\n`{ve}`"
            hints_label = "💡 Gợi Ý Cú Pháp" if vi else "💡 Syntax Suggestions"
            hints_value = (
                "• Phép tính cơ bản: `+`, `-`, `*`, `/`, `^` (lũy thừa)\n"
                "• Hàm số: `sqrt(x)`, `sin(x)`, `cos(x)`, `abs(x)`, `log(x)`\n"
                "• Hằng số: `pi`, `e`, `tau`\n"
                "• Phần trăm: `15% of 500`"
                if vi else
                "• Basic math: `+`, `-`, `*`, `/`, `^` (power)\n"
                "• Functions: `sqrt(x)`, `sin(x)`, `cos(x)`, `abs(x)`, `log(x)`\n"
                "• Constants: `pi`, `e`, `tau`\n"
                "• Percentages: `15% of 500`"
            )

            embed = discord.Embed(
                title=err_title,
                description=err_desc,
                color=discord.Color.red()
            )
            embed.add_field(name=hints_label, value=hints_value, inline=False)
            await ctx.send(embed=embed, ephemeral=True)
        except Exception as e:
            invalid_msg = f"❌ Biểu thức không hợp lệ: `{e}`" if vi else f"❌ Invalid expression: `{e}`"
            await ctx.send(invalid_msg, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(MathCog(bot))

