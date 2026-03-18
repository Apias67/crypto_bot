import requests
import time

TOKEN = "8763631522:AAGbFUF-q8Bw1hDhP8B8NdjZ78Bnup57eVY"
CHAT_ID = "6702443414"

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    r = requests.get(url, params={"chat_id": CHAT_ID, "text": msg})
    print("STATUS:", r.status_code)
    print("ODPOWIEDŹ:", r.text)

print("🔥 BOT STARTUJE 🔥")

send_telegram("🔥 TEST 1")

time.sleep(5)

send_telegram("🔥 TEST 2")
