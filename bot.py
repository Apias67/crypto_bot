import json
import time
import threading
import requests
import os
from websocket import WebSocketApp
from http.server import HTTPServer, BaseHTTPRequestHandler

# ---------------- Telegram ----------------
TOKEN = os.getenv("8763631522:AAGbFUF-q8Bw1hDhP8B8NdjZ78Bnup57eVY")
CHAT_ID = os.getenv("6702443414")

def send_telegram(message):
    try:
        requests.get(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            params={"chat_id": CHAT_ID, "text": message}
        )
        print("✅ Telegram sent")
    except Exception as e:
        print("❌ Telegram error:", e)

# ---------------- Dummy server ----------------
class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

def run_server():
    HTTPServer(('', 10000), DummyHandler).serve_forever()

threading.Thread(target=run_server, daemon=True).start()

# ---------------- KONFIG ----------------
SYMBOLS = [
    "btcusdt","ethusdt","xrpusdt","solusdt","bnbusdt",
    "dogeusdt","adausdt","linkusdt","maticusdt","dotusdt",
    "avaxusdt","shibusdt","ltcusdt","uniusdt","atomusdt"
]

STREAMS = "/".join([f"{s}@trade" for s in SYMBOLS])
WS_URL = f"wss://stream.binance.com:9443/stream?streams={STREAMS}"

VOLUME_WINDOW = 10
PUMP_THRESHOLD = 2
WHALE_THRESHOLD = 500_000
ALERT_INTERVAL = 300

GROUPS = [20,30,40,50,80,100]

volume_history = {s: [] for s in SYMBOLS}
price_history = {s: [] for s in SYMBOLS}
pump_alerts = {}
whale_alerts = {}

# ---------------- DETEKCJA ----------------
def detect(symbol, volume, price):
    volume_history[symbol].append(volume)
    price_history[symbol].append(price)

    if len(volume_history[symbol]) > VOLUME_WINDOW:
        volume_history[symbol].pop(0)
        price_history[symbol].pop(0)

    avg_vol = sum(volume_history[symbol]) / len(volume_history[symbol])

    # PUMP
    if avg_vol > 0 and volume > avg_vol * PUMP_THRESHOLD:
        old_price = price_history[symbol][0]
        pct = ((price - old_price) / old_price) * 100

        for g in GROUPS:
            if pct >= g:
                pump_alerts.setdefault(g, []).append(f"{symbol.upper()} +{pct:.1f}%")
                break

    # WHALE
    if volume * price >= WHALE_THRESHOLD:
        whale_alerts[symbol] = max(whale_alerts.get(symbol, 0), volume*price)

# ---------------- WEBSOCKET ----------------
def on_message(ws, message):
    data = json.loads(message)
    d = data['data']

    symbol = d['s'].lower()
    volume = float(d['q'])
    price = float(d['p'])

    detect(symbol, volume, price)

def on_open(ws):
    print("✅ WebSocket connected")

def on_error(ws, error):
    print("❌ WS error:", error)

def on_close(ws):
    print("❌ WS closed")

# ---------------- ALERTY ----------------
def alert_loop():
    send_telegram("🚀 BOT FINAL działa")

    while True:
        time.sleep(ALERT_INTERVAL)

        msg = []

        if pump_alerts:
            msg.append("🔥 PUMPY (5 min):")
            for g in sorted(pump_alerts):
                msg.append(f"{g}%+ → {', '.join(pump_alerts[g][:5])}")

        if whale_alerts:
            msg.append("\n🐋 WHALE:")
            top = sorted(whale_alerts.items(), key=lambda x: x[1], reverse=True)[:5]
            for s,v in top:
                msg.append(f"{s.upper()} ${v:,.0f}")

        if msg:
            send_telegram("\n".join(msg))

        pump_alerts.clear()
        whale_alerts.clear()

# ---------------- START ----------------
threading.Thread(target=alert_loop, daemon=True).start()

ws = WebSocketApp(
    WS_URL,
    on_message=on_message,
    on_open=on_open,
    on_error=on_error,
    on_close=on_close
)

ws.run_forever()
