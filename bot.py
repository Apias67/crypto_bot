import json
import time
import threading
import requests
from websocket import WebSocketApp

# ---------------- Telegram ----------------
TOKEN = "8763631522:AAGbFUF-q8Bw1hDhP8B8NdjZ78Bnup57eVY"
CHAT_ID = "6702443414"

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print("Błąd wysyłania Telegram:", e)

# ---------------- Konfiguracja ----------------
SYMBOLS = [
    "btcusdt", "ethusdt", "xrpusdt", "solusdt", "bnbusdt", "dogeusdt", "linkusdt", "zecusdt",
    "adausdt", "suiusdt", "pepeusdt", "trxusdt", "hypeusdt", "aaveusdt", "fdusdusdt",
    "avaxusdt", "taousdt", "ltcusdt", "xautusdt", "asterusdt", "uniusdt", "bchusdt",
    "nearusdt", "dotusdt", "fetusdt", "trumpusdt", "daiusdt", "paxgusdt", "rlusdusdt",
    "pyusdusdt", "xlmusdt", "wldusdt", "filusdt", "shibusdt", "hbarusdt", "nightusdt",
    "penguusdt", "dashusdt", "pumpusdt", "tonusdt", "enausdt", "virtualusdt", "kiteusdt",
    "icpusdt", "xmnusdt", "wifusdt", "husdt", "pippinusdt", "fartcoinusdt", "rvnusdt",
    "opusdt", "ffusdt", "ipusdt", "injusdt", "ensusdt", "eigenusdt", "litusdt", "compusdt",
    "ldousdt", "axsusdt", "monusdt", "sunusdt", "tiausdt", "zenusdt", "flokusdt", "sentusdt",
    "runeusdt", "yfiusdt", "berausdt", "pendleusdt", "sandusdt", "grtusdt", "zkusdt",
    "strkusdt", "cfxusdt", "wusdt", "aktusdt", "grassusdt", "zrxusdt", "susdt", "manausdt",
    "bsvusdt", "batusdt", "beatusdt", "galausdt", "arusdt", "neousdt", "rayusdt", "jasmyusdt",
    "aerousdt", "cvxusdt", "bardusdt", "vvvusdt", "aweusdt", "0gusdt", "syrupusdt", "snxusdt",
    "athusdt", "melaniausdt", "iotausdt", "pythusdt", "lptusdt", "nftusdt", "1inchusdt",
    "spxusdt", "skrusdt", "qtumusdt", "luncusdt", "twtusdt", "jtousdt", "glmusdt", "thetausdt",
    "busdt", "toshiusdt", "ausdt", "deepusdt", "2zusdt", "roseusdt", "kmnousdt", "xcnusdt",
    "egldusdt", "rsrusdt", "walusdt", "formusdt", "tracusdt", "zbcnusdt", "xecusdt", "beamusdt",
    "mxusdt", "gasusdt", "stgusdt", "ampusdt", "cowusdt", "tfuelusdt", "abusdt", "sfpusdt",
    "hntusdt", "fluidusdt", "vsnusdt", "fttusdt", "cheemusdt", "telusdt", "wemixusdt", "yzyusdt"
]

VOLUME_WINDOW = 10
PUMP_THRESHOLD = 3
WHALE_THRESHOLD = 5_000_000
ALERT_INTERVAL = 300  # 5 minut = 300 sekund

# ---------------- Bufory danych ----------------
volume_history = {symbol: [] for symbol in SYMBOLS}
pump_alerts = {}
whale_alerts = {}

# ---------------- Funkcja wykrywająca pumpty i whale buys ----------------
def detect_pump_or_whale(symbol, volume, price, amount):
    avg_volume = sum(volume_history[symbol])/len(volume_history[symbol]) if volume_history[symbol] else 0

    if avg_volume > 0 and volume > PUMP_THRESHOLD * avg_volume:
        pump_alerts[symbol] = volume

    if amount * price >= WHALE_THRESHOLD:
        whale_alerts[symbol] = max(whale_alerts.get(symbol, 0), amount*price)

# ---------------- Funkcja WebSocket ----------------
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

# ---------------- Funkcja wysyłająca ranking alertów co 5 minut ----------------
def alert_sender():
    while True:
        time.sleep(ALERT_INTERVAL)
        messages = []

        if pump_alerts:
            top_pumps = sorted(pump_alerts.items(), key=lambda x: x[1], reverse=True)[:10]
            messages.append("🔥 Top Pumps (5 min):")
            for sym, vol in top_pumps:
                messages.append(f"{sym.upper()}: Volume {vol:.4f}")

        if whale_alerts:
            top_whales = sorted(whale_alerts.items(), key=lambda x: x[1], reverse=True)[:10]
            messages.append("\n🐋 Top Whale Buys (5 min):")
            for sym, val in top_whales:
                messages.append(f"{sym.upper()}: ${val:.2f}")

        if messages:
            send_telegram("\n".join(messages))

        pump_alerts.clear()
        whale_alerts.clear()

# ---------------- Uruchomienie WebSocket ----------------
websockets = []
for symbol in SYMBOLS:
    ws_url = f"wss://stream.binance.com:9443/ws/{symbol}@trade"
    ws = WebSocketApp(ws_url,
                      on_message=make_on_message(symbol),
                      on_error=on_error,
                      on_close=on_close)
    ws.on_open = on_open
    websockets.append(ws)

# ---------------- Uruchomienie wątku alert_sender ----------------
threading.Thread(target=alert_sender, daemon=True).start()

# ---------------- Uruchomienie WebSocket w osobnych wątkach ----------------
for ws in websockets:
    t = threading.Thread(target=ws.run_forever, daemon=True)
    t.start()

# ---------------- Pętla główna ----------------
while True:
    time.sleep(1)
