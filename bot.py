import os
import time
import requests
import pandas as pd
from telegram import Bot

# =========================
# TELEGRAM (lokalnie wpisz dane)
# =========================
TELEGRAM_TOKEN = "8763631522:AAGbFUF-q8Bw1hDhP8B8NdjZ78Bnup57eVY"
TELEGRAM_CHAT_ID = 16702443414

bot = Bot(token=TELEGRAM_TOKEN)

print("🔥 BOT START (ETAP 2)")

# =========================
# POBIERANIE TOP COINÓW
# =========================
def get_top_coins(limit=10):
    url = "https://api.binance.com/api/v3/ticker/24hr"
    data = requests.get(url).json()

    df = pd.DataFrame(data)

    # konwersja na liczby
    df['quoteVolume'] = pd.to_numeric(df['quoteVolume'], errors='coerce').fillna(0)

    # sortowanie
    df = df.sort_values(by='quoteVolume', ascending=False)

    # TOP coiny
    top = df.head(limit)

    return list(top['symbol'])

# =========================
# WYSYŁKA NA TELEGRAM
# =========================
def send_top_coins():
    coins = get_top_coins(10)

    msg = "🔥 TOP 10 COINS (24h volume):\n\n"
    for i, coin in enumerate(coins, 1):
        msg += f"{i}. {coin}\n"

    bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg)
    print(msg)

# =========================
# START
# =========================
send_top_coins()

# pętla co 10 min
while True:
    time.sleep(600)
    send_top_coins()
