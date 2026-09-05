"""
Telegram Full Calculator Bot
- Basic arithmetic, brackets, powers, percentages
- Scientific functions and constants
- Factorial, nCr, nPr
- Complex numbers
- Common unit conversions
- Temperature conversion
- Time/date calculations
- Natural-language shortcuts such as "20% of 500"
- k/m/b number suffixes
- Safe SymPy expression evaluation (no Python eval)
"""

import re
import math
import cmath
import time
from datetime import datetime, timedelta, date

import httpx
import sympy as sp
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ============================================================
# BOT TOKEN — put your NEW BotFather token here
# ============================================================
TOKEN = "8825245676:AAFPYAmmLB2cul4GQKTC3zan3X-RMMlglBU"

# ============================================================
# SCIENTIFIC FUNCTIONS / CONSTANTS
# ============================================================
ALLOWED = {
    "pi": sp.pi,
    "e": sp.E,
    "tau": 2 * sp.pi,

    "sqrt": sp.sqrt,
    "cbrt": sp.real_root,

    "sin": sp.sin,
    "cos": sp.cos,
    "tan": sp.tan,
    "cot": sp.cot,
    "sec": sp.sec,
    "csc": sp.csc,

    "asin": sp.asin,
    "acos": sp.acos,
    "atan": sp.atan,

    "sinh": sp.sinh,
    "cosh": sp.cosh,
    "tanh": sp.tanh,

    "asinh": sp.asinh,
    "acosh": sp.acosh,
    "atanh": sp.atanh,

    "log": sp.log,
    "ln": sp.log,
    "log10": lambda x: sp.log(x, 10),
    "log2": lambda x: sp.log(x, 2),

    "abs": sp.Abs,
    "floor": sp.floor,
    "ceil": sp.ceiling,

    "factorial": sp.factorial,
    "exp": sp.exp,

    "gcd": sp.gcd,
    "lcm": sp.ilcm,
}

# ============================================================
# UNIT TABLES
# Base unit for each category:
# length = meter
# mass   = kilogram
# volume = liter
# area   = square meter
# speed  = meter/second
# time   = second
# ============================================================
UNITS = {
    # length
    "mm": ("length", 0.001),
    "cm": ("length", 0.01),
    "m": ("length", 1.0),
    "meter": ("length", 1.0),
    "meters": ("length", 1.0),
    "km": ("length", 1000.0),
    "kilometer": ("length", 1000.0),
    "kilometers": ("length", 1000.0),
    "in": ("length", 0.0254),
    "inch": ("length", 0.0254),
    "inches": ("length", 0.0254),
    "ft": ("length", 0.3048),
    "foot": ("length", 0.3048),
    "feet": ("length", 0.3048),
    "yd": ("length", 0.9144),
    "yard": ("length", 0.9144),
    "mi": ("length", 1609.344),
    "mile": ("length", 1609.344),
    "miles": ("length", 1609.344),
    "nmi": ("length", 1852.0),
    "nauticalmile": ("length", 1852.0),

    # mass
    "mg": ("mass", 1e-6),
    "g": ("mass", 0.001),
    "gram": ("mass", 0.001),
    "grams": ("mass", 0.001),
    "kg": ("mass", 1.0),
    "kilogram": ("mass", 1.0),
    "kilograms": ("mass", 1.0),
    "t": ("mass", 1000.0),
    "tonne": ("mass", 1000.0),
    "lb": ("mass", 0.45359237),
    "lbs": ("mass", 0.45359237),
    "pound": ("mass", 0.45359237),
    "pounds": ("mass", 0.45359237),
    "oz": ("mass", 0.028349523125),
    "ounce": ("mass", 0.028349523125),
    "ounces": ("mass", 0.028349523125),

    # volume
    "ml": ("volume", 0.001),
    "milliliter": ("volume", 0.001),
    "milliliters": ("volume", 0.001),
    "l": ("volume", 1.0),
    "liter": ("volume", 1.0),
    "liters": ("volume", 1.0),
    "litre": ("volume", 1.0),
    "litres": ("volume", 1.0),
    "usgallon": ("volume", 3.785411784),
    "gallon": ("volume", 3.785411784),
    "gal": ("volume", 3.785411784),
    "quart": ("volume", 0.946352946),
    "qt": ("volume", 0.946352946),
    "pint": ("volume", 0.473176473),
    "pt": ("volume", 0.473176473),
    "cup": ("volume", 0.2365882365),
    "tbsp": ("volume", 0.0147867648),
    "tsp": ("volume", 0.00492892159),

    # area
    "mm2": ("area", 1e-6),
    "cm2": ("area", 1e-4),
    "m2": ("area", 1.0),
    "km2": ("area", 1e6),
    "in2": ("area", 0.00064516),
    "ft2": ("area", 0.09290304),
    "yd2": ("area", 0.83612736),
    "acre": ("area", 4046.8564224),
    "hectare": ("area", 10000.0),
    "ha": ("area", 10000.0),

    # speed
    "mps": ("speed", 1.0),
    "kmh": ("speed", 1000 / 3600),
    "kph": ("speed", 1000 / 3600),
    "mph": ("speed", 1609.344 / 3600),
    "fps": ("speed", 0.3048),
    "knot": ("speed", 1852 / 3600),
    "knots": ("speed", 1852 / 3600),

    # time
    "ms": ("time", 0.001),
    "millisecond": ("time", 0.001),
    "s": ("time", 1.0),
    "sec": ("time", 1.0),
    "second": ("time", 1.0),
    "min": ("time", 60.0),
    "minute": ("time", 60.0),
    "minutes": ("time", 60.0),
    "h": ("time", 3600.0),
    "hr": ("time", 3600.0),
    "hour": ("time", 3600.0),
    "hours": ("time", 3600.0),
    "day": ("time", 86400.0),
    "days": ("time", 86400.0),
    "week": ("time", 604800.0),
    "weeks": ("time", 604800.0),
}

# ============================================================
# CRYPTOCURRENCY MARKET
# Fast CoinGecko lookup with correct symbol selection + caching
# ============================================================
COINGECKO_BASE = "https://api.coingecko.com/api/v3"

# Common coins: guarantees symbols like SOL/ETH/BTC resolve correctly.
COMMON_COINS = {
    "btc": ("bitcoin", "Bitcoin", "btc"),
    "bitcoin": ("bitcoin", "Bitcoin", "btc"),
    "eth": ("ethereum", "Ethereum", "eth"),
    "ethereum": ("ethereum", "Ethereum", "eth"),
    "sol": ("solana", "Solana", "sol"),
    "solana": ("solana", "Solana", "sol"),
    "bnb": ("binancecoin", "BNB", "bnb"),
    "binancecoin": ("binancecoin", "BNB", "bnb"),
    "xrp": ("ripple", "XRP", "xrp"),
    "ripple": ("ripple", "XRP", "xrp"),
    "doge": ("dogecoin", "Dogecoin", "doge"),
    "dogecoin": ("dogecoin", "Dogecoin", "doge"),
    "ada": ("cardano", "Cardano", "ada"),
    "cardano": ("cardano", "Cardano", "ada"),
    "trx": ("tron", "TRON", "trx"),
    "tron": ("tron", "TRON", "trx"),
    "ton": ("the-open-network", "Toncoin", "ton"),
    "toncoin": ("the-open-network", "Toncoin", "ton"),
    "avax": ("avalanche-2", "Avalanche", "avax"),
    "dot": ("polkadot", "Polkadot", "dot"),
    "matic": ("matic-network", "Polygon", "matic"),
    "pol": ("polygon-ecosystem-token", "POL", "pol"),
    "link": ("chainlink", "Chainlink", "link"),
    "shib": ("shiba-inu", "Shiba Inu", "shib"),
    "ltc": ("litecoin", "Litecoin", "ltc"),
    "bch": ("bitcoin-cash", "Bitcoin Cash", "bch"),
    "atom": ("cosmos", "Cosmos", "atom"),
    "uni": ("uniswap", "Uniswap", "uni"),
    "etc": ("ethereum-classic", "Ethereum Classic", "etc"),
    "xlm": ("stellar", "Stellar", "xlm"),
    "near": ("near", "NEAR Protocol", "near"),
    "apt": ("aptos", "Aptos", "apt"),
    "arb": ("arbitrum", "Arbitrum", "arb"),
    "op": ("optimism", "Optimism", "op"),
    "fil": ("filecoin", "Filecoin", "fil"),
    "sui": ("sui", "Sui", "sui"),
    "inj": ("injective-protocol", "Injective", "inj"),
    "pepe": ("pepe", "Pepe", "pepe"),
    "usdt": ("tether", "Tether", "usdt"),
    "usdc": ("usd-coin", "USDC", "usdc"),
    "dai": ("dai", "Dai", "dai"),
}

COIN_RESOLUTION_CACHE = {}
COIN_RESOLUTION_CACHE_TTL = 6 * 3600
COIN_PRICE_CACHE = {}
COIN_PRICE_CACHE_TTL = 45


def _cache_fresh(ts, ttl):
    return (time.time() - ts) < ttl


async def resolve_coin(coin_query: str):
    q = coin_query.strip().lower()

    cached = COIN_RESOLUTION_CACHE.get(q)
    if cached and _cache_fresh(cached[1], COIN_RESOLUTION_CACHE_TTL):
        return cached[0]

    if q in COMMON_COINS:
        result = COMMON_COINS[q]
        COIN_RESOLUTION_CACHE[q] = (result, time.time())
        return result

    # CoinGecko search is much faster than downloading the entire coin list.
    async with httpx.AsyncClient(timeout=8) as client:
        r = await client.get(
            f"{COINGECKO_BASE}/search",
            params={"query": q},
        )
        r.raise_for_status()
        coins = r.json().get("coins", [])

    if not coins:
        return None

    q_compact = re.sub(r"[^a-z0-9]", "", q)

    # Prefer exact symbol/name. If several match, prefer the best market-cap rank.
    exact = []
    for c in coins:
        name = (c.get("name") or "").strip()
        symbol = (c.get("symbol") or "").strip().lower()
        cid = c.get("id")
        if not cid:
            continue
        name_compact = re.sub(r"[^a-z0-9]", "", name.lower())
        if symbol == q or name_compact == q_compact or cid.lower() == q:
            rank = c.get("market_cap_rank")
            exact.append((999999 if rank is None else rank, cid, name, symbol))

    candidates = exact or [
        (
            999999 if c.get("market_cap_rank") is None else c.get("market_cap_rank"),
            c.get("id"),
            c.get("name") or c.get("id"),
            (c.get("symbol") or "").lower(),
        )
        for c in coins
        if c.get("id")
    ]

    if not candidates:
        return None

    candidates.sort(key=lambda x: x[0])
    _, cid, name, symbol = candidates[0]
    result = (cid, name, symbol)
    COIN_RESOLUTION_CACHE[q] = (result, time.time())
    return result


def crypto_query_parts(text: str):
    t = text.strip().lower()

    # Examples: btc, 1 btc, 0.024 sol, 5*0.7 eth
    if re.fullmatch(r"[a-zA-Z][a-zA-Z0-9._-]*", t):
        return "1", t, "usd"

    m = re.fullmatch(
        r"(.+?)\s+([a-zA-Z][a-zA-Z0-9._-]*)",
        t,
    )
    if not m:
        return None

    amount_expr = m.group(1).strip()
    coin = m.group(2).strip()

    # Do not steal normal unit conversions such as "10 km to mile".
    if coin in UNITS:
        return None

    # Require the amount expression to look numeric/math-like.
    if not re.fullmatch(r"[0-9+\-*/().\s^%kKmMbB]+", amount_expr):
        return None

    return amount_expr, coin, "usd"


def _money(value):
    if value is None:
        return "N/A"
    value = float(value)
    if value == 0:
        return "0"
    if abs(value) >= 1000:
        return f"{value:,.2f}".rstrip("0").rstrip(".")
    if abs(value) >= 1:
        return f"{value:,.2f}".rstrip("0").rstrip(".")
    if abs(value) >= 0.01:
        return f"{value:,.4f}".rstrip("0").rstrip(".")
    return f"{value:.8f}".rstrip("0").rstrip(".")


def _crypto_amount(value):
    value = float(value)
    if value.is_integer():
        return f"{int(value):,}"
    return f"{value:.8f}".rstrip("0").rstrip(".")


async def crypto_price(text: str):
    t = text.strip().lower()

    # Optional "price" / "market" prefix.
    market_match = re.fullmatch(r"(?:price|market)\s+(.+)", t)
    if market_match:
        t = market_match.group(1).strip()

    # Optional trailing fiat currency.
    fiat = "usd"
    fiat_match = re.fullmatch(r"(.+?)\s+(usd|eur|gbp|bdt)", t)
    if fiat_match:
        t = fiat_match.group(1).strip()
        fiat = fiat_match.group(2)

    parts = crypto_query_parts(t)
    if not parts:
        return None

    amount_expr, coin_query, _ = parts

    try:
        quantity = float(calculate_expression(amount_expr))
    except Exception:
        return None

    if not math.isfinite(quantity):
        return None

    resolved = await resolve_coin(coin_query)
    if not resolved:
        return None

    coin_id, coin_name, symbol = resolved

    cache_key = (coin_id, fiat)
    cached = COIN_PRICE_CACHE.get(cache_key)
    if cached and _cache_fresh(cached[1], COIN_PRICE_CACHE_TTL):
        info = cached[0]
    else:
        async with httpx.AsyncClient(timeout=8) as client:
            r = await client.get(
                f"{COINGECKO_BASE}/simple/price",
                params={
                    "ids": coin_id,
                    "vs_currencies": fiat,
                    "include_24hr_change": "true",
                },
            )
            r.raise_for_status()
            data = r.json()

        info = data.get(coin_id, {})
        COIN_PRICE_CACHE[cache_key] = (info, time.time())

    unit_price = info.get(fiat)
    if unit_price is None:
        return None

    unit_price = float(unit_price)
    total = quantity * unit_price
    change = info.get(f"{fiat}_24h_change")

    change_text = ""
    if change is not None:
        sign = "+" if float(change) >= 0 else ""
        change_text = f" | {sign}{float(change):.2f}%"

    # Google-style compact result.
    return (
        f"{_crypto_amount(quantity)} {coin_name} ({symbol}):\n"
        f"{_money(total)} {fiat}\n"
        f"{_crypto_amount(quantity)} {symbol}{change_text}"
    )


async def top_crypto(limit=10):
    limit = max(1, min(int(limit), 100))
    async with httpx.AsyncClient(timeout=8) as client:
        r = await client.get(
            f"{COINGECKO_BASE}/coins/markets",
            params={
                "vs_currency": "usd",
                "order": "market_cap_desc",
                "per_page": limit,
                "page": 1,
                "sparkline": "false",
            },
        )
        r.raise_for_status()
        data = r.json()

    lines = [f"🏆 TOP {limit} CRYPTO (USD)\n"]
    for i, coin in enumerate(data, 1):
        symbol = (coin.get("symbol") or "").upper()
        price = coin.get("current_price")
        change = coin.get("price_change_percentage_24h")
        change_text = "N/A" if change is None else f"{'+' if change >= 0 else ''}{change:.2f}%"
        lines.append(
            f"{i}. {coin.get('name')} ({symbol}) — ${price:,.12g} | 24h {change_text}"
        )

    return "\n".join(lines)

# ============================================================
# SAFE INPUT NORMALIZATION
# ============================================================
def convert_short_numbers(text: str) -> str:
    multipliers = {
        "k": 1000,
        "K": 1000,
        "m": 1000000,
        "M": 1000000,
        "b": 1000000000,
        "B": 1000000000,
    }

    pattern = r"(?<![A-Za-z0-9_.])(\d+(?:\.\d+)?)([kKmMbB])\b"

    def repl(match):
        n = float(match.group(1))
        v = n * multipliers[match.group(2)]
        return str(int(v)) if v.is_integer() else str(v)

    return re.sub(pattern, repl, text)


def convert_percentage(text: str) -> str:
    # x% -> x/100
    return re.sub(r"(\d+(?:\.\d+)?)%", r"(\1/100)", text)


def normalize_expression(text: str) -> str:
    text = text.strip()
    text = text.replace("×", "*")
    text = text.replace("÷", "/")
    text = text.replace("−", "-")
    text = text.replace("π", "pi")
    text = text.replace("^", "**")
    text = convert_percentage(text)
    text = convert_short_numbers(text)

    # Common implicit multiplication:
    # 2pi -> 2*pi, 2(3+4) -> 2*(3+4)
    text = re.sub(r"(\d)(pi|e|sqrt|sin|cos|tan|log|ln)", r"\1*\2", text)
    text = re.sub(r"(\d)\(", r"\1*(", text)
    text = re.sub(r"\)(\d|pi|e)", r")*\1", text)

    return text


# ============================================================
# NATURAL-LANGUAGE CALCULATIONS
# ============================================================
def natural_percentage(text: str):
    patterns = [
        r"^\s*(\d+(?:\.\d+)?)\s*%\s+of\s+(.+?)\s*$",
        r"^\s*what\s+is\s+(\d+(?:\.\d+)?)\s*%\s+of\s+(.+?)\s*$",
    ]

    for pattern in patterns:
        m = re.match(pattern, text, re.I)
        if m:
            percent = float(m.group(1))
            base = calculate_expression(m.group(2))
            return base * percent / 100

    return None


def calculate_expression(text: str):
    expr = normalize_expression(text)

    if len(expr) > 500:
        raise ValueError("Expression too long")

    # SymPy parser symbols/functions only; no Python eval.
    if not re.fullmatch(r"[0-9A-Za-z_+\-*/().,\s]+", expr):
        raise ValueError("Invalid characters")

    result = sp.sympify(expr, locals=ALLOWED)

    if not result.is_number:
        raise ValueError("Not numeric")

    return result


# ============================================================
# UNIT CONVERSION
# ============================================================
def unit_conversion(text: str):
    m = re.fullmatch(
        r"\s*([-+]?\d+(?:\.\d+)?)\s*([A-Za-z0-9]+)"
        r"\s+(?:to|in|into)\s+([A-Za-z0-9]+)\s*",
        text,
        re.I,
    )

    if not m:
        return None

    value = float(m.group(1))
    source = m.group(2).lower()
    target = m.group(3).lower()

    if source not in UNITS or target not in UNITS:
        raise ValueError("Unknown unit")

    source_cat, source_factor = UNITS[source]
    target_cat, target_factor = UNITS[target]

    if source_cat != target_cat:
        raise ValueError("Different unit categories")

    return value * source_factor / target_factor


# ============================================================
# TEMPERATURE
# ============================================================
def temperature_conversion(text: str):
    m = re.fullmatch(
        r"\s*([-+]?\d+(?:\.\d+)?)\s*(c|f|k)"
        r"\s+(?:to|in|into)\s+(c|f|k)\s*",
        text,
        re.I,
    )

    if not m:
        return None

    value = float(m.group(1))
    source = m.group(2).lower()
    target = m.group(3).lower()

    if source == "c":
        c = value
    elif source == "f":
        c = (value - 32) * 5 / 9
    else:
        c = value - 273.15

    if target == "c":
        return c
    if target == "f":
        return c * 9 / 5 + 32
    return c + 273.15


# ============================================================
# TIME / DATE HELPERS
# ============================================================
def time_conversion(text: str):
    m = re.fullmatch(
        r"\s*(\d+(?:\.\d+)?)\s*(seconds?|secs?|s|minutes?|mins?|m|hours?|hrs?|h)"
        r"\s+(?:to|in)\s+"
        r"(seconds?|secs?|s|minutes?|mins?|m|hours?|hrs?|h)\s*",
        text,
        re.I,
    )

    if not m:
        return None

    value = float(m.group(1))
    source = m.group(2).lower()
    target = m.group(3).lower()

    def factor(unit):
        if unit.startswith("s"):
            return 1
        if unit.startswith("m"):
            return 60
        return 3600

    return value * factor(source) / factor(target)


def date_difference(text: str):
    # Example: days between 2026-01-01 and 2026-02-01
    m = re.fullmatch(
        r"\s*days?\s+between\s+(\d{4}-\d{2}-\d{2})"
        r"\s+and\s+(\d{4}-\d{2}-\d{2})\s*",
        text,
        re.I,
    )

    if not m:
        return None

    d1 = date.fromisoformat(m.group(1))
    d2 = date.fromisoformat(m.group(2))
    return abs((d2 - d1).days)


# ============================================================
# COMBINATIONS / PERMUTATIONS
# ============================================================
def ncr_npr(text: str):
    m = re.fullmatch(r"\s*(\d+)\s*([cCpP])\s*(\d+)\s*", text)

    if not m:
        return None

    n = int(m.group(1))
    r = int(m.group(3))

    if r > n:
        raise ValueError("r cannot exceed n")

    if m.group(2).lower() == "c":
        return math.comb(n, r)

    return math.perm(n, r)


# ============================================================
# RESULT FORMATTING
# ============================================================
def format_result(value):
    if isinstance(value, bool):
        return str(value)

    if isinstance(value, int):
        return f"{value:,}"

    if isinstance(value, float):
        if math.isfinite(value) and value.is_integer():
            return f"{int(value):,}"
        return f"{value:.12g}"

    try:
        if value.is_Integer:
            return f"{int(value):,}"

        numeric = sp.N(value, 15)

        if numeric.is_real:
            f = float(numeric)
            if math.isfinite(f) and f.is_integer():
                return f"{int(f):,}"

        return str(numeric)

    except Exception:
        return str(value)


# ============================================================
# MAIN CALCULATOR ROUTER
# ============================================================
def calculate(text: str):
    # Natural language percentage
    result = natural_percentage(text)
    if result is not None:
        return result

    # Units
    result = unit_conversion(text)
    if result is not None:
        return result

    # Temperature
    result = temperature_conversion(text)
    if result is not None:
        return result

    # Time
    result = time_conversion(text)
    if result is not None:
        return result

    # Date difference
    result = date_difference(text)
    if result is not None:
        return result

    # nCr / nPr
    result = ncr_npr(text)
    if result is not None:
        return result

    # Standard math
    return calculate_expression(text)


# ============================================================
# TELEGRAM COMMANDS
# ============================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🧮 FULL CALCULATOR\n\n"
        "Basic: 25+35 | (10+5)*2 | 2^10\n"
        "Scientific: sqrt(144) | sin(pi/2) | log(100)\n"
        "Percentage: 20% of 500 | 15%*200\n"
        "Short numbers: 6k | 2m | 6k*2k\n"
        "Units: 10 km to mile | 5 kg to lb\n"
        "Temperature: 100 c to f\n"
        "Time: 2 hours to minutes\n"
        "Date: days between 2026-01-01 and 2026-02-01\n"
        "Combinations: 5C2\n"
        "Permutations: 5P2\n\n"
        "🪙 CRYPTO: btc | 2 eth | 5*0.7 sol | btc usd\n"
        "🏆 /topcrypto for top crypto market.\n"
        "📚 /help for full list."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🧮 FULL CALCULATOR HELP\n\n"
        "BASIC\n"
        "25+35\n"
        "100-25\n"
        "12*8\n"
        "100/4\n"
        "(10+5)*2\n\n"

        "POWER / ROOT\n"
        "2^10\n"
        "sqrt(144)\n"
        "cbrt(27)\n\n"

        "PERCENTAGE\n"
        "50%\n"
        "20% of 500\n"
        "15%*200\n\n"

        "SCIENTIFIC\n"
        "sin(pi/2)\n"
        "cos(0)\n"
        "tan(pi/4)\n"
        "asin(1)\n"
        "log(100)\n"
        "log10(1000)\n"
        "ln(e)\n"
        "abs(-25)\n"
        "floor(5.9)\n"
        "ceil(5.1)\n"
        "factorial(5)\n"
        "exp(1)\n"
        "gcd(24,18)\n"
        "lcm(12,18)\n\n"

        "CONSTANTS\n"
        "pi / π\n"
        "e\n"
        "tau\n\n"

        "SHORT NUMBERS\n"
        "6k = 6,000\n"
        "2m = 2,000,000\n"
        "1.5k = 1,500\n"
        "6k*2k\n\n"

        "LENGTH\n"
        "10 km to mile\n"
        "5 mile to km\n"
        "100 cm to m\n"
        "2 m to feet\n"
        "12 inch to cm\n\n"

        "MASS\n"
        "5 kg to lb\n"
        "1000 g to kg\n"
        "10 oz to g\n\n"

        "VOLUME\n"
        "2 l to ml\n"
        "1 gallon to liter\n"
        "2 cup to ml\n\n"

        "AREA\n"
        "1 acre to m2\n"
        "1 hectare to m2\n\n"

        "SPEED\n"
        "100 kmh to mph\n"
        "60 mph to kmh\n\n"

        "TIME\n"
        "2 hours to minutes\n"
        "120 minutes to hours\n\n"

        "TEMPERATURE\n"
        "100 c to f\n"
        "32 f to c\n"
        "0 c to k\n\n"

        "DATE\n"
        "days between 2026-01-01 and 2026-02-01\n\n"

        "COMBINATION / PERMUTATION\n"
        "5C2\n"
        "10C3\n"
        "5P2\n"
        "10P3\n\n"

        "CRYPTOCURRENCY MARKET\n"
        "btc\n"
        "1 btc\n"
        "2 eth\n"
        "5*0.7 sol\n"
        "btc usd\n"
        "bitcoin price\n"
        "🏆 /topcrypto or /topcrypto 50"
    )


# ============================================================
# CRYPTO COMMAND
# ============================================================
async def topcrypto_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        limit = 10
        if context.args:
            limit = int(context.args[0])
        text = await top_crypto(limit)
        await update.message.reply_text(text)
    except Exception:
        await update.message.reply_text(
            "❌ Crypto market data এখন পাওয়া যাচ্ছে না। একটু পরে আবার চেষ্টা করো।"
        )


# ============================================================
# CALCULATOR MESSAGE HANDLER
# ============================================================
async def calculator(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    try:
        # Try cryptocurrency market lookup first.
        crypto = await crypto_price(text)
        if crypto is not None:
            await update.message.reply_text(crypto)
            return

        result = calculate(text)
        answer = format_result(result)

        await update.message.reply_text(
            f"🧮 {text}\n\n= {answer}"
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
            "20% of 500\n"
            "10 km to mile\n"
            "1 btc\n"
            "5*0.7 eth\n"
            "/topcrypto"
        )


# ============================================================
# START BOT
# ============================================================
def main():
    if TOKEN == "PASTE_YOUR_NEW_BOT_TOKEN_HERE":
        print("❌ Bot Token বসাও।")
        return

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("topcrypto", topcrypto_command))

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            calculator
        )
    )

    print("🤖 FULL Calculator Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
