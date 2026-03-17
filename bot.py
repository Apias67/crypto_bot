import requests
import time
from telegram import Bot

TOKEN = "8763631522:AAGbFUF-q8Bw1hDhP8B8NdjZ78Bnup57eVY"
CHAT_ID = "6702443414"

bot = Bot(token=8763631522:AAGbFUF-q8Bw1hDhP8B8NdjZ78Bnup57eVY)

def get_data():
    all_coins = []
    for page in range(1, 5):
        url = f"https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=250&page={page}&price_change_percentage=24h"
        data = requests.get(url).json()
        all_coins.extend(data)
    return all_coins

def check():
    coins = get_data()
    alerts = []

    for coin in coins:
        price_change = coin.get("price_change_percentage_24h")
        volume = coin.get("total_volume")
        market_cap = coin.get("market_cap")

        if not price_change or not volume or not market_cap:
            continue

        # 🔥 SMART FILTER
        if (
            price_change > 8 and              # rośnie
            volume > 2_000_000 and           # realny wolumen
            market_cap < 500_000_000         # mid/small cap
        ):
            alerts.append(
                f"🚨 SMART MONEY ALERT\n"
                f"{coin['name']} ({coin['symbol'].upper()})\n"
                f"Price Change: {round(price_change,2)}%\n"
                f"Volume: ${volume:,}\n"
                f"Market Cap: ${market_cap:,}"
            )

    return alerts[:10]

def send_alerts():
    alerts = check()

    if not alerts:
        bot.send_message(chat_id=CHAT_ID, text="😴 Brak smart money (cisza)")
    else:
        for msg in alerts:
            bot.send_message(chat_id=CHAT_ID, text=msg)

while True:
    try:
        send_alerts()
        print("OK - scan done")
    except Exception as e:
        print("ERROR:", e)

    time.sleep(3600)
