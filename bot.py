import os
import requests
import feedparser
from datetime import datetime, timedelta, timezone


TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]


# =========================
# RSS แหล่งข่าว
# =========================

NEWS_RSS = "https://www.thairath.co.th/rss/news"
TECH_RSS = "https://feeds.arstechnica.com/arstechnica/index"
POLITICS_RSS = "http://rssfeeds.sanook.com/rss/feeds/sanook/news.politic.xml"
SPORTS_RSS = "https://www.thairath.co.th/rss/sport"
ECONOMIC_RSS = "http://rssfeeds.sanook.com/rss/feeds/sanook/news.economic.xml"


# =========================
# อ่าน RSS
# =========================

news_feed = feedparser.parse(NEWS_RSS)
tech_feed = feedparser.parse(TECH_RSS)
politics_feed = feedparser.parse(POLITICS_RSS)
sports_feed = feedparser.parse(SPORTS_RSS)
economic_feed = feedparser.parse(ECONOMIC_RSS)


# =========================
# ฟังก์ชันกรองข่าว 24 ชั่วโมง
# =========================

def get_recent_news(feed, limit=5):
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=24)

    recent_news = []

    for item in feed.entries:
        published_time = item.get("published_parsed")

        # ถ้า RSS ไม่มีวันเวลา ให้ข้ามข่าวนี้
        if not published_time:
            continue

        try:
            published_dt = datetime(
                published_time.tm_year,
                published_time.tm_mon,
                published_time.tm_mday,
                published_time.tm_hour,
                published_time.tm_min,
                published_time.tm_sec,
                tzinfo=timezone.utc,
            )

            # เอาเฉพาะข่าวย้อนหลังไม่เกิน 24 ชั่วโมง
            if published_dt >= cutoff:
                recent_news.append(item)

        except Exception:
            continue

    # เรียงจากข่าวใหม่สุดก่อน
    recent_news.sort(
        key=lambda item: item.get("published_parsed"),
        reverse=True,
    )

    return recent_news[:limit]


# =========================
# ดึงข่าวแต่ละหมวด
# =========================

news_items = get_recent_news(news_feed, 5)
tech_items = get_recent_news(tech_feed, 5)
politics_items = get_recent_news(politics_feed, 5)
sports_items = get_recent_news(sports_feed, 5)
economic_items = get_recent_news(economic_feed, 5)


# =========================
# สร้างข้อความ
# =========================

message = "☀️ GP MORNING BRIEF\n"
message += "🕐 ข่าวย้อนหลัง 24 ชั่วโมง\n\n"


# =========================
# ฟังก์ชันสร้างหมวดข่าว
# =========================

def add_section(title, items):
    global message

    message += f"{title}\n\n"

    if not items:
        message += "ไม่มีข่าวในช่วง 24 ชั่วโมงล่าสุด\n\n"
        return

    for item in items:
        title_text = item.get("title", "ไม่มีหัวข้อ")
        link = item.get("link", "")

        message += f"• {title_text}\n"

        if link:
            message += f"{link}\n"

        message += "\n"


# =========================
# เพิ่มข่าว 5 หมวด
# =========================

add_section("📰 ข่าวเด่น", news_items)

add_section("💻 IT / TECHNOLOGY", tech_items)

add_section("🏛️ การเมือง", politics_items)

add_section("⚽ SPORTS", sports_items)

add_section("📈 หุ้น / เศรษฐกิจ", economic_items)


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
