import os
import requests

TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

message = """
📰 GP Daily News Bot

✅ ระบบเชื่อมต่อ GitHub → Telegram สำเร็จแล้ว

นี่คือการทดสอบ V1 ครั้งแรกครับ

ขั้นต่อไป GP จะเริ่มเพิ่มระบบ:
• 🏛️ ข่าวการเมือง
• 💻 IT / Technology
• ⚽ ผลกีฬา
• 📈 หุ้นที่น่าสนใจ
• 📰 ข่าวเด่นรอบ 24 ชั่วโมง

รอติดตาม Morning Brief ได้เลยครับ ☕
"""

url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

response = requests.post(
    url,
    data={
        "chat_id": CHAT_ID,
        "text": message,
    },
    timeout=30,
)

response.raise_for_status()

print("Telegram message sent successfully.")
