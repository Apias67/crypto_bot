import os
import json
from websocket import WebSocketApp
from telegram import Bot

# ---------------- Telegram ----------------
TOKEN = "8763631522:AAGbFUF-q8Bw1hDhP8B8NdjZ78Bnup57eVY" 
CHAT_ID = "6702443414"
bot = Bot(token=TOKEN)

# ---------------- Konfiguracja ----------------
SYMBOLS = ["btcusdt", "ethusdt", "bnbusdt"]  # lista coinów
VOLUME_WINDOW = 10
PUMP_THRESHOLD = 3
WHALE_THRESHOLD = 5_000_000  # w USDT

# Bufory wolumenów dla każdego coina
volume_history = {symbol: [] for symbol in SYMBOLS}

# Funkcja wykrywająca pumpy i whale buys
def detect_pump_or_whale(symbol, volume, price, amount):
    avg_volume = sum(volume_history[symbol]) / len(volume_history[symbol]) if volume_history[symbol] else 0
    messages = []

    # Pump
    if avg_volume > 0 and volume > PUMP_THRESHOLD * avg_volume:
        messages.append(f"🚨 Pump detected! Coin: {symbol.upper()} Volume: {volume:.4f} (avg: {avg_volume:.4f})")

    # Whale buy
    if amount * price >= WHALE_THRESHOLD:
        messages.append(f"🐋 Whale buy! Coin: {symbol.upper()} Amount: {amount:.4f} Price: {price:.2f}")

    # Wyślij wszystkie wiadomości w jednej
    if messages:
        bot.send_message(chat_id=CHAT_ID, text="\n".join(messages))

# Funkcja do obsługi WebSocket
def make_on_message(symbol):
    def on_message(ws, message):
        data = json.loads(message)
        trade_volume = float(data['q'])
        trade_price = float(data['p'])
        volume_history[symbol].append(trade_volume)

        if len(volume_history[symbol]) > VOLUME_WINDOW:
            volume_history[symbol].pop(0)

        detect_pump_or_whale(symbol, trade_volume, trade_price, trade_volume)
    return on_message

def on_error(ws, error):
    print("WebSocket error:", error)

def on_close(ws):
    print("WebSocket closed")

def on_open(ws):
    print("WebSocket connection opened")

# ---------------- Uruchomienie WebSocket dla wielu coinów ----------------
websockets = []
for symbol in SYMBOLS:
    ws_url = f"wss://stream.binance.com:9443/ws/{symbol}@trade"
    ws = WebSocketApp(ws_url, on_message=make_on_message(symbol), on_error=on_error, on_close=on_close)
    ws.on_open = on_open
    websockets.append(ws)

# Uruchom każdy WebSocket w osobnym wątku
import threading
for ws in websockets:
    t = threading.Thread(target=ws.run_forever)
    t.start()
