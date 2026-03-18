
TELEGRAM_TOKEN = "8763631522:AAGbFUF-q8Bw1hDhP8B8NdjZ78Bnup57eVY"
TELEGRAM_CHAT_ID = 6702443414
import os
import time
import threading
import json
import numpy as np
import pandas as pd
from websocket import WebSocketApp
from telegram import Bot
import requests

# ==========================
# TU WPROWADŹ SWOJE DANE
# ==========================
TELEGRAM_TOKEN = "8763631522:AAGbFUF-q8Bw1hDhP8B8NdjZ78Bnup57eVY"  # Twój token w cudzysłowie
TELEGRAM_CHAT_ID = 6702443414  # Twój chat ID jako liczba

# ==========================
# Bitget API – opcjonalnie dla futures
# ==========================
BITGET_API_KEY = "TU_WPROWADŹ_API_KEY_BITGET"
BITGET_API_SECRET = "TU_WPROWADŹ_API_SECRET_BITGET"
BITGET_API_PASSPHRASE = "TU_WPROWADŹ_PASSPHRASE_BITGET"
USE_FUTURES = False  # True jeśli masz konto futures na Bitget

# ==========================
# Tworzymy bota Telegram
# ==========================
bot = Bot(token=TELEGRAM_TOKEN)

def send_alert(message):
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        print(message)
    except Exception as e:
        print("❌ Błąd wysyłki:", e)

# ==========================
# Funkcje do pobierania TOP i ryzykownych altów (USDC)
# ==========================
def get_top_coins(top_n=10):
    url = "https://api.binance.com/api/v3/ticker/24hr"
    data = requests.get(url).json()
    df = pd.DataFrame(data)
    df['quoteVolume'] = df['quoteVolume'].astype(float)
    df_usdc = df[df['symbol'].str.endswith('USDC')]
    top_coins = df_usdc.sort_values(by='quoteVolume', ascending=False).head(top_n)
    return list(top_coins['symbol'])

def get_risk_alts(top_n=15):
    url = "https://api.binance.com/api/v3/ticker/24hr"
    data = requests.get(url).json()
    df = pd.DataFrame(data)
    df['quoteVolume'] = df['quoteVolume'].astype(float)
    df['priceChangePercent'] = df['priceChangePercent'].astype(float)
    df_usdc = df[df['symbol'].str.endswith('USDC')]
    df_usdc['risk_score'] = df_usdc['priceChangePercent'].abs() / (df_usdc['quoteVolume'] + 1)
    risk_alts = df_usdc.sort_values(by='risk_score', ascending=False).head(top_n)
    return list(risk_alts['symbol'])

# ==========================
# Bufory wolumenów i interwały
# ==========================
WINDOW_TOP = 10
WINDOW_RISK = 20
PUMP_THRESHOLD = 2.5
WHALE_THRESHOLD = 1_000_000

INTERVAL_TOP = 4*60*60
INTERVAL_RISK = 60*60

volume_top = {}
volume_risk = {}

# ==========================
# Wykrywanie pumptów, whale buys i TP/SL
# ==========================
def detect_pump_or_whale(symbol, volume, price, amount, is_risk=False):
    buffer = volume_risk if is_risk else volume_top
    window = WINDOW_RISK if is_risk else WINDOW_TOP
    if symbol not in buffer:
        buffer[symbol] = []

    avg_volume = np.mean(buffer[symbol]) if buffer[symbol] else 0

    # Pump alert
    if avg_volume > 0 and volume > PUMP_THRESHOLD * avg_volume:
        send_alert(f"🚨 Pump detected! {symbol} Volume: {volume:.2f} (avg: {avg_volume:.2f})")

    # Whale buy alert
    if amount*price >= WHALE_THRESHOLD:
        send_alert(f"🐋 Whale buy! {symbol} Amount: {amount:.4f} Price: {price}")

    # Demo TP/SL logic
    tp = price * 1.05  # +5% target
    sl = price * 0.97  # -3% stop loss
    send_alert(f"📈 Demo entry {symbol} Price: {price:.2f} TP: {tp:.2f} SL: {sl:.2f}")

    # Bufor wolumenów
    buffer[symbol].append(volume)
    if len(buffer[symbol]) > window:
        buffer[symbol].pop(0)

# ==========================
# WebSocket do Binance
# ==========================
def create_ws(symbol, is_risk=False):
    ws_url = f"wss://stream.binance.com:9443/ws/{symbol.lower()}@trade"

    def on_message(ws, message):
        data = json.loads(message)
        trade_volume = float(data['q'])
        trade_price = float(data['p'])
        detect_pump_or_whale(symbol, trade_volume, trade_price, trade_volume, is_risk)

    def on_error(ws, error):
        print(f"❌ WS error for {symbol}: {error}")

    def on_close(ws, close_status_code, close_msg):
        print(f"WS closed for {symbol}")

    def on_open(ws):
        print(f"WS opened for {symbol}")

    ws = WebSocketApp(ws_url, on_message=on_message, on_error=on_error, on_close=on_close)
    ws.on_open = on_open
    threading.Thread(target=ws.run_forever, daemon=True).start()

# ==========================
# Aktualizacja list coinów
# ==========================
def update_coin_lists():
    global top_coins, risk_alts
    top_coins = get_top_coins()
    risk_alts = get_risk_alts()
    send_alert(f"🔄 Aktualizacja list:\nTOP: {top_coins}\nRyzykowne: {risk_alts}")

# ==========================
# Start bota
# ==========================
send_alert("🔥 Bot LEVEL 5.9 USDC wystartował! 🔥")
update_coin_lists()

# Uruchamiamy WebSockety
for coin in top_coins:
    create_ws(coin, is_risk=False)
for coin in risk_alts:
    create_ws(coin, is_risk=True)

# ==========================
# Pętle odświeżania list
# ==========================
def loop_top():
    while True:
        time.sleep(INTERVAL_TOP)
        update_coin_lists()

def loop_risk():
    while True:
        time.sleep(INTERVAL_RISK)
        update_coin_lists()

threading.Thread(target=loop_top, daemon=True).start()
threading.Thread(target=loop_risk, daemon=True).start()

# ==========================
# Pętla główna utrzymująca bota online
# ==========================
while True:
    time.sleep(60)
