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

# ==================================================
# BOT TOKEN
# ==================================================

TOKEN = "8825245676:AAEQVqJrbHySGbKW6M9DQx9c2sFehIdXHeY"


# ==================================================
# SCIENTIFIC FUNCTIONS
# ==================================================

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

    "sinh": sp.sinh,
    "cosh": sp.cosh,
    "tanh": sp.tanh,

    "log": sp.log,
    "ln": sp.log,

    "abs": sp.Abs,

    "factorial": sp.factorial,

    "floor": sp.floor,
    "ceil": sp.ceiling,

    "exp": sp.exp
}


# ==================================================
# UNIT CONVERSION
# ==================================================

UNITS = {

    # Length
    "km": 1000,
    "m": 1,
    "cm": 0.01,
    "mm": 0.001,

    "mile": 1609.344,
    "mi": 1609.344,

    "yard": 0.9144,
    "yd": 0.9144,

    "foot": 0.3048,
    "feet": 0.3048,
    "ft": 0.3048,

    "inch": 0.0254,
    "in": 0.0254,

    # Weight
    "kg": 1,
    "g": 0.001,
    "mg": 0.000001,

    "lb": 0.45359237,
    "pound": 0.45359237,

    "oz": 0.028349523125,
    "ounce": 0.028349523125,

    # Volume
    "l": 1,
    "liter": 1,
    "litre": 1,

    "ml": 0.001,
    "milliliter": 0.001,

    "gallon": 3.785411784,
    "gal": 3.785411784,

    "quart": 0.946352946,
    "qt": 0.946352946,

    "pint": 0.473176473,
    "pt": 0.473176473
}


# ==================================================
# SHORT NUMBERS
# ==================================================

def convert_short_numbers(text):

    multipliers = {
        "k": 1000,
        "K": 1000,

        "m": 1000000,
        "M": 1000000,

        "b": 1000000000,
        "B": 1000000000
    }

    pattern = r'(?<![a-zA-Z0-9.])(\d+(?:\.\d+)?)([kKmMbB])'

    def replace(match):

        number = float(match.group(1))
        suffix = match.group(2)

        value = number * multipliers[suffix]

        if value.is_integer():
            return str(int(value))

        return str(value)

    return re.sub(pattern, replace, text)


# ==================================================
# PERCENTAGE
# ==================================================

def convert_percentage(text):

    return re.sub(
        r'(\d+(?:\.\d+)?)%',
        r'(\1/100)',
        text
    )


# ==================================================
# UNIT CONVERSION
# Example:
# 10 km to mile
# 5 kg to lb
# ==================================================

def unit_conversion(text):

    pattern = (
        r'^\s*'
        r'([-+]?\d+(?:\.\d+)?)'
        r'\s*'
        r'([a-zA-Z]+)'
        r'\s+(?:to|in|into)\s+'
        r'([a-zA-Z]+)'
        r'\s*$'
    )

    match = re.match(pattern, text.lower())

    if not match:
        return None

    value = float(match.group(1))
    from_unit = match.group(2)
    to_unit = match.group(3)

    if from_unit not in UNITS:
        raise ValueError("Unknown unit")

    if to_unit not in UNITS:
        raise ValueError("Unknown unit")

    meters_or_base = value * UNITS[from_unit]

    result = meters_or_base / UNITS[to_unit]

    return result


# ==================================================
# TEMPERATURE
# ==================================================

def temperature_conversion(text):

    pattern = (
        r'^\s*'
        r'([-+]?\d+(?:\.\d+)?)'
        r'\s*'
        r'(c|f|k)'
        r'\s+(?:to|in|into)\s+'
        r'(c|f|k)'
        r'\s*$'
    )

    match = re.match(pattern, text.lower())

    if not match:
        return None

    value = float(match.group(1))

    from_unit = match.group(2)
    to_unit = match.group(3)

    # Celsius -> Celsius
    if from_unit == "c":
        celsius = value

    # Fahrenheit -> Celsius
    elif from_unit == "f":
        celsius = (value - 32) * 5 / 9

    # Kelvin -> Celsius
    else:
        celsius = value - 273.15

    # Celsius -> target
    if to_unit == "c":
        return celsius

    if to_unit == "f":
        return (celsius * 9 / 5) + 32

    if to_unit == "k":
        return celsius + 273.15


# ==================================================
# COMBINATION nCr
# Example: 5C2
# ==================================================

def combination(text):

    match = re.fullmatch(
        r'\s*(\d+)\s*[cC]\s*(\d+)\s*',
        text
    )

    if not match:
        return None

    n = int(match.group(1))
    r = int(match.group(2))

    if r > n:
        raise ValueError()

    return math.comb(n, r)


# ==================================================
# PERMUTATION nPr
# Example: 5P2
# ==================================================

def permutation(text):

    match = re.fullmatch(
        r'\s*(\d+)\s*[pP]\s*(\d+)\s*',
        text
    )

    if not match:
        return None

    n = int(match.group(1))
    r = int(match.group(2))

    if r > n:
        raise ValueError()

    return math.perm(n, r)


# ==================================================
# PREPARE EXPRESSION
# ==================================================

def prepare_expression(text):

    text = text.strip()

    text = text.replace(" ", "")

    text = text.replace("×", "*")

    text = text.replace("÷", "/")

    text = text.replace("^", "**")

    text = text.replace("π", "pi")

    text = convert_percentage(text)

    text = convert_short_numbers(text)

    return text


# ==================================================
# CALCULATE
# ==================================================

def calculate(text):

    # Unit conversion
    result = unit_conversion(text)

    if result is not None:
        return result

    # Temperature
    result = temperature_conversion(text)

    if result is not None:
        return result

    # nCr
    result = combination(text)

    if result is not None:
        return result

    # nPr
    result = permutation(text)

    if result is not None:
        return result

    expression = prepare_expression(text)

    if len(expression) > 300:
        raise ValueError()

    if not re.fullmatch(
        r'[0-9a-zA-Z_+\-*/().,%\s]+',
        expression
    ):
        raise ValueError()

    result = sp.sympify(
        expression,
        locals=ALLOWED
    )

    if not result.is_number:
        raise ValueError()

    return result


# ==================================================
# FORMAT RESULT
# ==================================================

def format_result(result):

    try:

        if isinstance(result, int):
            return str(result)

        if isinstance(result, float):

            if result.is_integer():
                return str(int(result))

            return f"{result:.12g}"

        if result.is_Integer:
            return str(result)

        value = sp.N(result, 15)

        if value.is_real:

            number = float(value)

            if number.is_integer():
                return str(int(number))

        return str(value)

    except:

        return str(result)


# ==================================================
# START
# ==================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "🧮 FULL CALCULATOR BOT\n\n"

        "Basic:\n"
        "25+35\n"
        "100/4\n"
        "(10+5)*2\n\n"

        "Scientific:\n"
        "sqrt(144)\n"
        "2^10\n"
        "sin(pi/2)\n"
        "log(100)\n\n"

        "Percentage:\n"
        "50%\n\n"

        "Units:\n"
        "10 km to mile\n"
        "5 kg to lb\n"
        "100 cm to m\n\n"

        "Temperature:\n"
        "100 c to f\n"
        "32 f to c\n\n"

        "Combinations:\n"
        "5C2\n\n"

        "Permutations:\n"
        "5P2\n\n"

        "সব command দেখতে /help লিখুন।"
    )


# ==================================================
# HELP
# ==================================================

async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "🧮 CALCULATOR HELP\n\n"

        "━━━━━━━━━━━━━━\n"
        "BASIC\n"
        "━━━━━━━━━━━━━━\n"
        "25+35\n"
        "100-25\n"
        "12*8\n"
        "100/4\n"
        "(10+5)*2\n\n"

        "━━━━━━━━━━━━━━\n"
        "POWER\n"
        "━━━━━━━━━━━━━━\n"
        "2^10\n"
        "5^3\n\n"

        "━━━━━━━━━━━━━━\n"
        "PERCENTAGE\n"
        "━━━━━━━━━━━━━━\n"
        "50%\n"
        "15%*200\n\n"

        "━━━━━━━━━━━━━━\n"
        "SCIENTIFIC\n"
        "━━━━━━━━━━━━━━\n"
        "sqrt(144)\n"
        "sin(pi/2)\n"
        "cos(0)\n"
        "tan(pi/4)\n"
        "log(100)\n"
        "ln(e)\n"
        "abs(-25)\n"
        "factorial(5)\n\n"

        "━━━━━━━━━━━━━━\n"
        "SHORT NUMBERS\n"
        "━━━━━━━━━━━━━━\n"
        "6k\n"
        "2m\n"
        "1.5k\n"
        "6k*2k\n\n"

        "━━━━━━━━━━━━━━\n"
        "UNIT CONVERSION\n"
        "━━━━━━━━━━━━━━\n"
        "10 km to mile\n"
        "5 mile to km\n"
        "100 cm to m\n"
        "2 m to feet\n"
        "5 kg to lb\n"
        "1000 g to kg\n"
        "2 l to ml\n"
        "1 gallon to liter\n\n"

        "━━━━━━━━━━━━━━\n"
        "TEMPERATURE\n"
        "━━━━━━━━━━━━━━\n"
        "100 c to f\n"
        "32 f to c\n"
        "0 c to k\n\n"

        "━━━━━━━━━━━━━━\n"
        "COMBINATION\n"
        "━━━━━━━━━━━━━━\n"
        "5C2\n"
        "10C3\n\n"

        "━━━━━━━━━━━━━━\n"
        "PERMUTATION\n"
        "━━━━━━━━━━━━━━\n"
        "5P2\n"
        "10P3\n\n"

        "━━━━━━━━━━━━━━\n"
        "CONSTANTS\n"
        "━━━━━━━━━━━━━━\n"
        "pi\n"
        "π\n"
        "e"
    )


# ==================================================
# CALCULATOR MESSAGE
# ==================================================

async def calculator(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    text = update.message.text.strip()

    try:

        result = calculate(text)

        answer = format_result(result)

        await update.message.reply_text(
            f"🧮 {text}\n\n"
            f"= {answer}"
        )

    except ZeroDivisionError:

        await update.message.reply_text(
            "❌ 0 দিয়ে ভাগ করা যায় না।"
        )

    except Exception:

        await update.message.reply_text(
            "❌ হিসাবটি বুঝতে পারিনি।\n\n"
            "উদাহরণ:\n"
            "25+35\n"
            "sqrt(144)\n"
            "10 km to mile\n"
            "5C2"
        )


# ==================================================
# MAIN
# ==================================================

def main():

    if TOKEN == "8825245676:AAEQVqJrbHySGbKW6M9DQx9c2sFehIdXHeY":

        print("8825245676:AAEQVqJrbHySGbKW6M9DQx9c2sFehIdXHeY")
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

    print("🤖 FULL Calculator Bot is running...")

    app.run_polling()


# ==================================================
# RUN
# ==================================================

if __name__ == "__main__":
    main()
