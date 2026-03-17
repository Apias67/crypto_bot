import json
import time
import threading
from websocket import WebSocketApp
from telegram import Bot

# ---------------- Telegram ----------------
TOKEN = "8763631522:AAGbFUF-q8Bw1hDhP8B8NdjZ78Bnup57eVY"
CHAT_ID = "6702443414"
bot = Bot(token=TOKEN)

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
ALERT_INTERVAL = 5  # sekundy między alertami

# ---------------- Bufory danych ----------------
volume_history = {symbol: [] for symbol in SYMBOLS}
alert_buffer = []

# ---------------- Funkcja wykrywająca pumpty i whale buys ----------------
def detect_pump_or_whale(symbol, volume, price, amount):
    avg_volume = sum(volume_history[symbol])/len(volume_history[symbol]) if volume_history[symbol] else 0

    if avg_volume > 0 and volume > PUMP_THRESHOLD * avg_volume:
        alert_buffer.append(f"🚨 Pump detected! Coin: {symbol.upper()} Volume: {volume:.4f} (avg: {avg_volume:.4f})")

    if amount * price >= WHALE_THRESHOLD:
        alert_buffer.append(f"🐋 Whale buy! Coin: {symbol.upper()} Amount: {amount:.4f} Price: {price:.2f}")

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

# ---------------- Funkcja wysyłająca zbiorcze alerty ----------------
def alert_sender():
    while True:
        time.sleep(ALERT_INTERVAL)
        if alert_buffer:
            bot.send_message(chat_id=CHAT_ID, text="\n".join(alert_buffer))
            alert_buffer.clear()

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

# ---------------- Wątek alert_sender ----------------
threading.Thread(target=alert_sender, daemon=True).start()

# ---------------- Uruchomienie każdego WebSocket w osobnym wątku ----------------
for ws in websockets:
    t = threading.Thread(target=ws.run_forever, daemon=True)
    t.start()

# ---------------- Pętla główna ----------------
while True:
    time.sleep(1)
