import os
import time
import requests
import pandas as pd
from telegram import Bot

# =========================
# TELEGRAM (Render ENV)
# =========================
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
    raise ValueError("❌ Brak TELEGRAM_BOT_TOKEN lub TELEGRAM_CHAT_ID")

bot = Bot(token=TELEGRAM_TOKEN)

print("🔥 BOT START (ETAP 2 - RENDER)")

# =========================
# POBIERANIE TOP COINÓW
# =========================
def get_top_coins(limit=10):
    url = "https://api.binance.com/api/v3/ticker/24hr"
    data = requests.get(url).json()

    import pandas as pd
    df = pd.DataFrame(data)

    if 'quoteVolume' not in df:
        print("❌ Błąd API:", data)
        return []

    df['quoteVolume'] = pd.to_numeric(df['quoteVolume'], errors='coerce').fillna(0)
    df = df.sort_values(by='quoteVolume', ascending=False)

    return list(df.head(limit)['symbol'])

# =========================
# WYSYŁKA
# =========================
def send_top_coins():
    coins = get_top_coins(10)

    if not coins:
        print("❌ Brak coinów")
        return

    msg = "🔥 TOP 10 COINS:\n\n"
    for i, coin in enumerate(coins, 1):
        msg += f"{i}. {coin}\n"

    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg)
        print("✅ Wysłano na Telegram")
    except Exception as e:
        print("❌ Telegram error:", e)

# =========================
# START
# =========================
send_top_coins()

while True:
    print("⏳ Czekam 10 min...")
    time.sleep(600)
    send_top_coins()
