import re
import math
import sympy as sp

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# =========================
# BOT TOKEN
# =========================

TOKEN = "8825245676:AAEQVqJrbHySGbKW6M9DQx9c2sFehIdXHeY"


# =========================
# CONSTANTS
# =========================

x = sp.Symbol("x")

ALLOWED = {
    "pi": sp.pi,
    "e": sp.E,
    "sqrt": sp.sqrt,
    "sin": sp.sin,
    "cos": sp.cos,
    "tan": sp.tan,
    "asin": sp.asin,
    "acos": sp.acos,
    "atan": sp.atan,
    "log": sp.log,
    "ln": sp.log,
    "abs": sp.Abs,
    "factorial": sp.factorial,
    "floor": sp.floor,
    "ceil": sp.ceiling,
}


# =========================
# NUMBER SHORTCUTS
# =========================

def convert_short_numbers(text):

    # 1k = 1000
    # 1.5k = 1500
    # 2m = 2000000
    # 3b = 3000000000

    multipliers = {
        "k": 1000,
        "K": 1000,
        "m": 1000000,
        "M": 1000000,
        "b": 1000000000,
        "B": 1000000000,
    }

    pattern = r'(?<![a-zA-Z0-9_.])(\d+(?:\.\d+)?)([kKmMbB])'

    def replace(match):
        number = float(match.group(1))
        suffix = match.group(2)

        value = number * multipliers[suffix]

        if value.is_integer():
            return str(int(value))

        return str(value)

    return re.sub(pattern, replace, text)


# =========================
# PERCENTAGE
# =========================

def convert_percentage(text):

    # 50% → 0.5
    text = re.sub(
        r'(\d+(?:\.\d+)?)%',
        r'(\1/100)',
        text
    )

    return text


# =========================
# PREPARE EXPRESSION
# =========================

def prepare_expression(text):

    text = text.strip()

    # Remove spaces
    text = text.replace(" ", "")

    # Multiplication symbols
    text = text.replace("×", "*")
    text = text.replace("÷", "/")

    # Power
    text = text.replace("^", "**")

    # Percentage
    text = convert_percentage(text)

    # k / m / b
    text = convert_short_numbers(text)

    # Degree support
    text = text.replace("degrees", "deg")

    return text


# =========================
# CALCULATOR
# =========================

def calculate(text):

    expression = prepare_expression(text)

    # Basic security check
    if len(expression) > 300:
        raise ValueError("Expression too long")

    # Only allow safe characters
    if not re.fullmatch(
        r'[0-9a-zA-Z_+\-*/().,%\s]+',
        expression
    ):
        raise ValueError("Invalid characters")

    result = sp.sympify(
        expression,
        locals=ALLOWED
    )

    # Make sure it is actually a number
    if not result.is_number:
        raise ValueError("Not a number")

    return result


# =========================
# FORMAT RESULT
# =========================

def format_result(result):

    # Integer
    if result.is_Integer:
        return str(result)

    # Float / decimal
    try:
        numeric = sp.N(result, 15)

        if abs(float(numeric)) >= 1e12:
            return f"{float(numeric):,.10g}"

        return str(numeric)

    except:
        return str(result)


# =========================
# START
# =========================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "🧮 Google-style Calculator\n\n"
        "আমি বিভিন্ন ধরনের হিসাব করতে পারি।\n\n"

        "Examples:\n"
        "25+35\n"
        "150/50*3\n"
        "6k*2k\n"
        "50%\n"
        "sqrt(144)\n"
        "2^10\n"
        "sin(pi/2)\n"
        "log(100)\n"
        "factorial(5)\n\n"

        "📌 /help লিখে সব function দেখুন।"
    )


# =========================
# HELP
# =========================

async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "🧮 Calculator Functions\n\n"

        "Basic:\n"
        "25+35\n"
        "100-25\n"
        "12*8\n"
        "100/4\n\n"

        "Power:\n"
        "2^10\n"
        "5^3\n\n"

        "Percentage:\n"
        "50%\n"
        "15%*200\n\n"

        "Short numbers:\n"
        "6k\n"
        "2m\n"
        "1.5k\n"
        "6k*2k\n\n"

        "Math functions:\n"
        "sqrt(144)\n"
        "sin(pi/2)\n"
        "cos(0)\n"
        "tan(pi/4)\n"
        "log(100)\n"
        "ln(e)\n"
        "abs(-25)\n"
        "factorial(5)\n\n"

        "Constants:\n"
        "pi\n"
        "e"
    )


# =========================
# CALCULATOR MESSAGE
# =========================

async def calculator(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    text = update.message.text.strip()

    try:

        result = calculate(text)

        formatted = format_result(result)

        await update.message.reply_text(
            f"🧮 {text}\n\n"
            f"= {formatted}"
        )

    except ZeroDivisionError:

        await update.message.reply_text(
            "❌ 0 দিয়ে ভাগ করা যাবে না।"
        )

    except Exception:

        await update.message.reply_text(
            "❌ হিসাবটি বুঝতে পারিনি।\n\n"
            "Example:\n"
            "25+35\n"
            "150/50*3\n"
            "sqrt(144)\n"
            "2^10"
        )


# =========================
# RUN BOT
# =========================

def main():

    if TOKEN == "তোমার_BOT_TOKEN":

        print("❌ Bot Token বসাও।")
        return

    app = Application.builder().token(TOKEN).build()

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


# =========================
# START
# =========================

if __name__ == "__main__":
    main()
