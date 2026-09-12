import os
import requests
import feedparser

TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

# RSS แหล่งข่าว
NEWS_RSS = "https://www.thairath.co.th/rss/news"
TECH_RSS = "https://feeds.arstechnica.com/arstechnica/index"
POLITICS_RSS = "http://rssfeeds.sanook.com/rss/feeds/sanook/news.politic.xml"

# อ่านข่าว
news_feed = feedparser.parse(NEWS_RSS)
tech_feed = feedparser.parse(TECH_RSS)
politics_feed = feedparser.parse(POLITICS_RSS)

message = "☀️ GP MORNING BRIEF\n\n"

# =========================
# 📰 ข่าวเด่น
# =========================

message += "📰 ข่าวเด่น\n\n"

for item in news_feed.entries[:5]:
    title = item.get("title", "ไม่มีหัวข้อ")
    link = item.get("link", "")

    message += f"• {title}\n"
    message += f"{link}\n\n"

# =========================
# 💻 IT / TECHNOLOGY
# =========================

message += "💻 IT / TECHNOLOGY\n\n"

for item in tech_feed.entries[:5]:
    title = item.get("title", "ไม่มีหัวข้อ")
    link = item.get("link", "")

    message += f"• {title}\n"
    message += f"{link}\n\n"

# =========================
# 🏛️ การเมือง
# =========================

message += "🏛️ การเมือง\n\n"

for item in politics_feed.entries[:5]:
    title = item.get("title", "ไม่มีหัวข้อ")
    link = item.get("link", "")

    message += f"• {title}\n"
    message += f"{link}\n\n"

# =========================
# ส่ง Telegram
# =========================

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

print("Morning Brief sent successfully.")
