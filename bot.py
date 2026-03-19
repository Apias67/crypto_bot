import os
import time
from telegram import Bot

print("🔥 START TEST")

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

print("TOKEN:", TELEGRAM_TOKEN)
print("CHAT ID:", TELEGRAM_CHAT_ID)

bot = Bot(token=TELEGRAM_TOKEN)

bot.send_message(chat_id=TELEGRAM_CHAT_ID, text="✅ TEST działa!")

while True:
    print("Bot żyje...")
    time.sleep(60)
