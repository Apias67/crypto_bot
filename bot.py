# bot_level5_11_render.py

import os
import json
import time
import threading
import numpy as np
import pandas as pd
from websocket import WebSocketApp
from telegram import Bot
import requests

# ===========================
# 1️⃣ TELEGRAM - wprowadź swoje dane w ENV Render
# ===========================
# Environment Variables w Render:
# Key: TELEGRAM_BOT_TOKEN -> Twój token z BotFather (bez cudzysłowów)
# Key: TELEGRAM_CHAT_ID   -> Twój chat ID (liczba, np. 6702443414)
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
    raise ValueError("❌ Brak zmiennej środowiskowej TELEGRAM_BOT_TOKEN lub TELEGRAM_CHAT_ID!")

bot = Bot(token=TELEGRAM_TOKEN)

# ===========================
# 2️⃣ KONFIGURACJA BOTA
# ===========================
USE_FUTURES = False        # True jeśli masz API Bitget / Binance futures
TOP_COIN_LIMIT = 100       # pierwsza setka wg wolumenu
RISKY_COIN_LIMIT = 150     # ryzykowne alty
VOLUME_WINDOW_TOP = 4      # interwał 4h dla top coinów
VOLUME_WINDOW_RISKY = 1    # interwał 1h dla ryzykownych altów
PUMP_THRESHOLD = 3         # 3x średni wolumen = potencjalny pump
WHALE_THRESHOLD = 5_000_000  # minimalna pojedyncza transakcja w USDT

# ===========================
# 3️⃣ Bufory wolumenów
# ===========================
volume_history_top = {}
volume_history_risky = {}

# ===========================
# 4️⃣ Funkcje pomocnicze
# ===========================
def send_telegram(msg):
    """Wysyłanie alertu do Telegram"""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg)
        print("Telegram alert:", msg)
    except Exception as e:
        print("Błąd wysyłki Telegram:", e)

def detect_pump_or_whale(symbol, volume, price, amount, volume_buffer):
    """Wykrywanie pumpów i whale buys"""
    avg_volume = sum(volume_buffer.get(symbol, []))/len(volume_buffer.get(symbol, [])) if volume_buffer.get(symbol) else 0

    # Pump
    if avg_volume > 0 and volume > PUMP_THRESHOLD * avg_volume:
        send_telegram(f"🚨 Pump detected! Coin: {symbol.upper()} Volume: {volume} (avg: {avg_volume:.2f})")

    # Whale buy
    if amount*price >= WHALE_THRESHOLD:
        send_telegram(f"🐋 Whale buy! Coin: {symbol.upper()} Amount: {amount} Price: {price}")

def update_volume_buffer(symbol, trade_volume, buffer_dict, window_size):
    """Aktualizacja bufora wolumenu"""
    if symbol not in buffer_dict:
        buffer_dict[symbol] = []
    buffer_dict[symbol].append(trade_volume)
    if len(buffer_dict[symbol]) > window_size:
        buffer_dict[symbol].pop(0)

# ===========================
# 5️⃣ WebSocket Binance dla USDC coins
# ===========================
def on_message(ws, message, buffer_dict):
    data = json.loads(message)
    symbol = data['s'].lower()
    trade_volume = float(data['q'])
    trade_price = float(data['p'])

    update_volume_buffer(symbol, trade_volume, buffer_dict, VOLUME_WINDOW_TOP)
    detect_pump_or_whale(symbol, trade_volume, trade_price, trade_volume, buffer_dict)

def on_error(ws, error):
    print("WS error:", error)

def on_close(ws, close_status_code, close_msg):
    print("WS closed:", close_status_code, close_msg)

def on_open(ws):
    print("WS connected")

# ===========================
# 6️⃣ Pobieranie top i ryzykownych coinów
# ===========================
def get_top_coins():
    # USDC market
    url = "https://api.binance.com/api/v3/ticker/24hr"
    data = requests.get(url).json()
    df = pd.DataFrame(data)
    df = df[df['quoteVolume'].astype(float) > 0]
    df['quoteVolume'] = df['quoteVolume'].astype(float)
    top_df = df.sort_values(by='quoteVolume', ascending=False).head(TOP_COIN_LIMIT)
    return list(top_df['symbol'].str.lower())

def get_risky_coins():
    url = "https://api.binance.com/api/v3/ticker/24hr"
    data = requests.get(url).json()
    df = pd.DataFrame(data)
    df = df[df['quoteVolume'].astype(float) > 0]
    df['priceChangePercent'] = df['priceChangePercent'].astype(float)
    df['quoteVolume'] = df['quoteVolume'].astype(float)
    risky_df = df.sort_values(by='priceChangePercent', ascending=False).head(RISKY_COIN_LIMIT)
    return list(risky_df['symbol'].str.lower())

# ===========================
# 7️⃣ Aktualizacja coinów co interwał
# ===========================
def update_coins():
    global top_coins, risky_coins
    while True:
        try:
            top_coins = get_top_coins()
            risky_coins = get_risky_coins()
            print("Top coins:", top_coins[:10])
            print("Risky coins:", risky_coins[:10])
        except Exception as e:
            print("Błąd aktualizacji coinów:", e)
        time.sleep(60*60)  # co 1h dla uproszczenia, można rozdzielić 4H/1H

# ===========================
# 8️⃣ Uruchamianie WebSocket dla każdej grupy
# ===========================
def run_ws(symbols, buffer_dict):
    for symbol in symbols:
        ws_url = f"wss://stream.binance.com:9443/ws/{symbol}@trade"
        ws = WebSocketApp(ws_url, on_message=lambda ws,msg: on_message(ws,msg,buffer_dict),
                          on_error=on_error, on_close=on_close)
        threading.Thread(target=ws.run_forever, daemon=True).start()

# ===========================
# 9️⃣ START BOTA
# ===========================
print("🔥 Bot LEVEL 5.11 USDC started!")

import threading
import requests

def self_ping():
    while True:
        try:
            requests.get("https://twoj-bot-url.onrender.com")
            print("Self-ping OK")
        except:
            pass
        time.sleep(5*60)  # co 5 minut

threading.Thread(target=self_ping, daemon=True).start()

# Aktualizacja coinów w tle
threading.Thread(target=update_coins, daemon=True).start()

# Poczekaj chwilę, żeby top_coins i risky_coins się zaktualizowały
time.sleep(10)

# Uruchamiamy WebSockety
run_ws(top_coins, volume_history_top)
run_ws(risky_coins, volume_history_risky)

# Pętla główna, bot działa w tle
while True:
    time.sleep(60)
