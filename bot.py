import os
import json
import time
import threading
import numpy as np
import pandas as pd
from websocket import WebSocketApp
from telegram import Bot
import requests

# =========================
# CONFIG
# =========================
TELEGRAM_TOKEN = os.environ.get(8763631522:AAGbFUF-q8Bw1hDhP8B8NdjZ78Bnup57eVY)  # TODO: Twój token bota
TELEGRAM_CHAT_ID = os.environ.get(6702443414)  # TODO: Twój chat ID
bot = Bot(token=TELEGRAM_TOKEN)

# Bitget Futures API - TODO: Uzupełnij swoimi danymi
BITGET_API_KEY = "YOUR_BITGET_API_KEY"
BITGET_SECRET = "YOUR_BITGET_SECRET"
BITGET_PASSPHRASE = "YOUR_BITGET_PASSPHRASE"

# Trading modes
MODES = {
    "aggressive": {"TP_pct": 0.10, "SL_pct": 0.03, "trailing": 0.02},
    "defensive": {"TP_pct": 0.05, "SL_pct": 0.02, "trailing": 0.01}
}

# Coins
LARGE_CAPS = ["BTC","ETH","SOL","BNB","ADA"]
RISK_ALTS = ["DOGE","XRP","SUI","PEPE","LINK","ZEC","AAVE","AVAX"]

# Tracking
volume_history = {}
price_history = {}
open_positions = {}  # spot + futures

# =========================
# UTILITY FUNCTIONS
# =========================
def send_alert(msg):
    bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg)

def fetch_top_risky():
    top = []
    for coin in RISK_ALTS:
        hist = volume_history.get(coin.lower()+"usdt", [])
        if len(hist) >= 5:
            if hist[-1] > 1.5*np.mean(hist[-5:]):
                top.append(coin)
    return top[:10]

def calculate_tp_sl(entry_price, mode):
    cfg = MODES[mode]
    TP = entry_price*(1+cfg["TP_pct"])
    SL = entry_price*(1-cfg["SL_pct"])
    return TP, SL

def update_trailing(symbol, current_price):
    if symbol not in open_positions:
        return
    pos = open_positions[symbol]
    cfg = MODES[pos["mode"]]
    # trailing SL
    if current_price > pos["entry"]:
        pos["SL"] = max(pos["SL"], current_price*(1-cfg["trailing"]))
    # dynamic TP
    if current_price / pos["entry"] > 1 + cfg["TP_pct"]:
        pos["TP"] = current_price*(1+cfg["trailing"])

def check_trade_exit(symbol, current_price):
    if symbol not in open_positions:
        return
    pos = open_positions[symbol]
    if current_price >= pos["TP"]:
        send_alert(f"[DEMO EXIT] {symbol} Entry: {pos['entry']:.2f} Exit: {current_price:.2f} Gain ✅ Mode: {pos['mode'].upper()} Side: {pos.get('side','SPOT')}")
        del open_positions[symbol]
    elif current_price <= pos["SL"]:
        send_alert(f"[DEMO EXIT] {symbol} Entry: {pos['entry']:.2f} Exit: {current_price:.2f} Loss ❌ Mode: {pos['mode'].upper()} Side: {pos.get('side','SPOT')}")
        del open_positions[symbol]

# =========================
# SPOT TRADING (demo)
# =========================
def enter_demo_spot(symbol, price, mode):
    TP, SL = calculate_tp_sl(price, mode)
    open_positions[symbol] = {"entry": price, "TP": TP, "SL": SL, "mode": mode, "side":"SPOT"}
    send_alert(f"[DEMO BUY] {symbol} Entry: {price:.2f} TP: {TP:.2f} SL: {SL:.2f} Mode: {mode.upper()}")

# =========================
# FUTURES TRADING (demo / Bitget)
# =========================
def enter_demo_futures(symbol, price, side, mode):
    TP, SL = calculate_tp_sl(price, mode)
    open_positions[symbol] = {"entry": price, "TP": TP, "SL": SL, "mode": mode, "side": side}
    send_alert(f"[DEMO FUTURES] {symbol} {side.upper()} Entry: {price:.2f} TP: {TP:.2f} SL: {SL:.2f} Mode: {mode.upper()}")

# TODO: Bitget real API functions
# def bitget_place_order(symbol, side, price, quantity):
#     endpoint = "https://api.bitget.com/api/mix/v1/order/placeOrder"
#     # Autoryzacja i POST request
#     pass

# =========================
# MOMENTUM INDICATORS
# =========================
def calc_rsi(symbol, prices, period=14):
    if len(prices) < period:
        return 50
    delta = np.diff(prices[-period:])
    up = delta[delta>0].sum()
    down = -delta[delta<0].sum()
    rsi = 100*up/(up+down) if (up+down)!=0 else 50
    return rsi

# =========================
# WEBSOCKET HANDLER
# =========================
def on_message(ws, message):
    data = json.loads(message)
    symbol = data['s']
    price = float(data['p'])
    vol = float(data['q'])

    # histories
    volume_history.setdefault(symbol, []).append(vol)
    price_history.setdefault(symbol, []).append(price)
    if len(volume_history[symbol]) > 20: volume_history[symbol].pop(0)
    if len(price_history[symbol]) > 50: price_history[symbol].pop(0)

    avg_vol = np.mean(volume_history[symbol])
    rsi = calc_rsi(symbol, price_history[symbol])

    # Determine mode
    mode = "aggressive" if symbol in [a.lower()+"usdt" for a in RISK_ALTS] else "defensive"

    # Pre-pump + RSI filter
    if vol > 3*avg_vol and rsi > 55:
        enter_demo_spot(symbol, price, mode)
        # Example: also futures demo for BTC/ETH/SOL
        if symbol in ["btcusdt","ethusdt","solusdt"]:
            enter_demo_futures(symbol, price, "long", mode)  # TODO: can choose "short" if trend down

    update_trailing(symbol, price)
    check_trade_exit(symbol, price)

def on_error(ws, error):
    print("❌ WS error:", error)

def on_close(ws, code, msg):
    print("❌ WS closed", code, msg)

def on_open(ws):
    print("🔥 BOT STARTUJE 🔥")

# =========================
# START WS THREADS
# =========================
def start_ws(symbol):
    ws_url = f"wss://stream.binance.com:9443/ws/{symbol}@trade"  # TODO: Binance spot
    ws = WebSocketApp(ws_url, on_message=on_message, on_error=on_error, on_close=on_close)
    ws.on_open = on_open
    ws.run_forever()

# Binance spot symbols
SYMBOLS = ["btcusdt","ethusdt","solusdt"] + [f"{a.lower()}usdt" for a in fetch_top_risky()]

for sym in SYMBOLS:
    t = threading.Thread(target=start_ws, args=(sym,))
    t.start()
