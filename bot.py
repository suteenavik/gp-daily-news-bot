import os
import requests
import feedparser

TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

# RSS ข่าวสำหรับทดสอบ
RSS_URL = "https://www.thairath.co.th/rss/news"

feed = feedparser.parse(RSS_URL)

message = "📰 GP Daily News Bot\n\n"
message += "🔥 ข่าวล่าสุดจากไทยรัฐ\n\n"

for item in feed.entries[:5]:
    title = item.get("title", "ไม่มีหัวข้อ")
    link = item.get("link", "")

    message += f"• {title}\n"
    message += f"{link}\n\n"

if len(feed.entries) == 0:
    message += "⚠️ ยังไม่พบข่าวจาก RSS"

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

print("News sent successfully.")
