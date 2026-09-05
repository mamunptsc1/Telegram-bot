import os
import ast
import math
import operator

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# =========================
# BOT TOKEN
# =========================
BOT_TOKEN = "8825245676:AAEQVqJrbHySGbKW6M9DQx9c2sFehIdXHeY"


# =========================
# SAFE CALCULATOR
# =========================
OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def calculate(expression):
    expression = expression.replace("×", "*")
    expression = expression.replace("÷", "/")
    expression = expression.replace("^", "**")

    tree = ast.parse(expression, mode="eval")

    def solve(node):

        if isinstance(node, ast.Expression):
            return solve(node.body)

        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError()

        if isinstance(node, ast.BinOp):

            if type(node.op) not in OPERATORS:
                raise ValueError()

            left = solve(node.left)
            right = solve(node.right)

            if isinstance(node.op, ast.Pow) and abs(right) > 100:
                raise ValueError()

            return OPERATORS[type(node.op)](left, right)

        if isinstance(node, ast.UnaryOp):

            if type(node.op) not in OPERATORS:
                raise ValueError()

            return OPERATORS[type(node.op)](
                solve(node.operand)
            )

        raise ValueError()

    result = solve(tree)

    if not math.isfinite(result):
        raise ValueError()

    return result


# =========================
# START COMMAND
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "🧮 Welcome to Calculator Bot!\n\n"
        "Send me any calculation.\n\n"
        "Examples:\n"
        "25+35\n"
        "100/4\n"
        "12*8\n"
        "(10+5)*2\n"
        "2^10\n\n"
        "Use /help for more information."
    )


# =========================
# HELP COMMAND
# =========================
async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "🧮 Calculator Help\n\n"
        "Supported operators:\n\n"
        "+  Addition\n"
        "-  Subtraction\n"
        "*  Multiplication\n"
        "/  Division\n"
        "^  Power\n"
        "%  Modulo\n\n"
        "Example:\n"
        "(25+15)*2"
    )


# =========================
# CALCULATOR
# =========================
async def calculator(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    expression = update.message.text.strip()

    try:

        result = calculate(expression)

        if isinstance(result, float) and result.is_integer():
            result = int(result)

        await update.message.reply_text(
            f"🧮 {expression}\n\n"
            f"= {result}"
        )

    except ZeroDivisionError:

        await update.message.reply_text(
            "❌ 0 দিয়ে ভাগ করা যাবে না।"
        )

    except Exception:

        await update.message.reply_text(
            "❌ ভুল হিসাব!\n\n"
            "Example:\n"
            "25+35\n"
            "100/4\n"
            "(10+5)*2"
        )


# =========================
# RUN BOT
# =========================
def main():

    if BOT_TOKEN == "PASTE_YOUR_BOT_TOKEN_HERE":
        print("❌ Please add your Bot Token.")
        return

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        CommandHandler("help", help_command)
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            calculator
        )
    )

    print("🤖 Calculator Bot is running...")

    app.run_polling()


if __name__ == "__main__":
    main()
