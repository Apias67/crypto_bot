
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
# WPROWADŹ SWOJE DANE
# ==========================
TELEGRAM_TOKEN = "8763631522:AAGbFUF-q8Bw1hDhP8B8NdjZ78Bnup57eVY"  # Twój token w cudzysłowie
TELEGRAM_CHAT_ID = 6702443414         # Twój chat ID jako liczba

BITGET_API_KEY = "TU_WPROWADŹ_API_KEY_BITGET"
BITGET_API_SECRET = "TU_WPROWADŹ_API_SECRET_BITGET"
BITGET_API_PASSPHRASE = "TU_WPROWADŹ_PASSPHRASE_BITGET"
USE_FUTURES = False  # True jeśli masz konto futures Bitget

STRATEGY_MODE = "aggressive"  # "aggressive" lub "defensive"

# ==========================
bot = Bot(token=TELEGRAM_TOKEN)
def send_alert(msg):
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg)
        print(msg)
    except Exception as e:
        print("❌ Telegram error:", e)

# ==========================
# Pobieranie coinów
# ==========================
def get_top_coins(top_n=10):
    url = "https://api.binance.com/api/v3/ticker/24hr"
    df = pd.DataFrame(requests.get(url).json())
    df['quoteVolume'] = df['quoteVolume'].astype(float)
    df_usdc = df[df['symbol'].str.endswith('USDC')]
    top = df_usdc.sort_values('quoteVolume', ascending=False).head(top_n)
    return list(top['symbol'])

def get_risk_alts(top_n=15):
    url = "https://api.binance.com/api/v3/ticker/24hr"
    df = pd.DataFrame(requests.get(url).json())
    df['quoteVolume'] = df['quoteVolume'].astype(float)
    df['priceChangePercent'] = df['priceChangePercent'].astype(float)
    df_usdc = df[df['symbol'].str.endswith('USDC')]
    df_usdc['risk_score'] = df_usdc['priceChangePercent'].abs() / (df_usdc['quoteVolume']+1)
    risk = df_usdc.sort_values('risk_score', ascending=False).head(top_n)
    return list(risk['symbol'])

# ==========================
# Bufory wolumenów
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
# TP/SL dynamiczne
# ==========================
def calculate_tp_sl(price):
    if STRATEGY_MODE == "aggressive":
        tp = price * 1.08
        sl = price * 0.95
    else:
        tp = price * 1.03
        sl = price * 0.97
    return tp, sl

# ==========================
def detect_pump_whale(symbol, volume, price, amount, is_risk=False):
    buffer = volume_risk if is_risk else volume_top
    window = WINDOW_RISK if is_risk else WINDOW_TOP
    if symbol not in buffer:
        buffer[symbol] = []

    avg_vol = np.mean(buffer[symbol]) if buffer[symbol] else 0

    if avg_vol > 0 and volume > PUMP_THRESHOLD*avg_vol:
        send_alert(f"🚨 Pump detected: {symbol} Vol: {volume:.2f} Avg: {avg_vol:.2f}")

    if amount*price >= WHALE_THRESHOLD:
        send_alert(f"🐋 Whale buy: {symbol} Amount: {amount:.4f} Price: {price}")

    tp, sl = calculate_tp_sl(price)
    send_alert(f"📊 Demo {symbol} Entry: {price:.2f} TP: {tp:.2f} SL: {sl:.2f}")

    buffer[symbol].append(volume)
    if len(buffer[symbol]) > window:
        buffer[symbol].pop(0)

# ==========================
# WebSocket
# ==========================
def create_ws(symbol, is_risk=False):
    ws_url = f"wss://stream.binance.com:9443/ws/{symbol.lower()}@trade"
    def on_msg(ws, message):
        data = json.loads(message)
        detect_pump_whale(symbol, float(data['q']), float(data['p']), float(data['q']), is_risk)
    ws = WebSocketApp(ws_url, on_message=on_msg,
                      on_error=lambda ws,e: print(f"❌ {symbol} WS error: {e}"),
                      on_close=lambda ws, code, msg: print(f"WS closed {symbol}"))
    ws.on_open = lambda ws: print(f"WS open {symbol}")
    threading.Thread(target=ws.run_forever, daemon=True).start()

# ==========================
# Aktualizacja coinów
# ==========================
def update_coins():
    global top_coins, risk_alts
    top_coins = get_top_coins()
    risk_alts = get_risk_alts()
    send_alert(f"🔄 Updated lists\nTOP: {top_coins}\nRisky: {risk_alts}")

send_alert("🔥 Bot LEVEL 5.10 USDC started!")
update_coins()

for c in top_coins:
    create_ws(c, False)
for c in risk_alts:
    create_ws(c, True)

# ==========================
# Odświeżanie list
# ==========================
def loop_top():
    while True:
        time.sleep(INTERVAL_TOP)
        update_coins()
def loop_risk():
    while True:
        time.sleep(INTERVAL_RISK)
        update_coins()

threading.Thread(target=loop_top, daemon=True).start()
threading.Thread(target=loop_risk, daemon=True).start()

# ==========================
# Pętla główna
# ==========================
while True:
    time.sleep(60)
